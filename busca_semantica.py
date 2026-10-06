"""Busca aprendida: achar no acervo inteiro o fato que responde à pergunta.

O CRIVO procurava como um bibliotecário: primeiro a etiqueta (o nome do
conceito, ou o classificador de assuntos treinado sobre uma lista fechada de
ids), depois o fato. Aqui ele procura direto nos fatos, como quem lê: junta
várias evidências de que um fato responde e aprendeu quanto vale cada uma.

Evidências de cada fato candidato (TRACOS):
  palavras     BM25 sobre palavras e radicais, no acervo todo e na ficha;
  resto        BM25 só com o que a pergunta pede além do nome do assunto
               ("QUANTOS CÓDONS existem no código genético?");
  sentido      proximidade nos vetores próprios (skip-gram treinado do zero),
               que aproxima "igual em todos" de "universal";
  forma        o tipo da pergunta casa com o fato (quem → nome próprio,
               quando → data, quanto → número, por que → causa, como →
               funcionamento) e o aspecto pedido ("para que serve", "como
               surgiu", "como se sabe") casa com a marca do fato;
  ficha        o nome do assunto aparece na pergunta, inteiro ou em parte;
               posição do fato.

Um modelo de ordenação (softmax sobre os candidatos), treinado uma vez com
perguntas sintéticas de outras fichas (scripts/treinar_busca_semantica.py),
pesa as evidências. Ele não decora assuntos nem ids: as evidências valem para
qualquer fato, então um fato novo é achado sem retreinar nada. Sem modelo
aprovado, a ordem é a do BM25.

Python puro, sem NumPy: o mesmo resultado no site e no CI.
"""
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

CAMINHO_MODELO = Path(__file__).resolve().parent / "artefatos" / "busca_semantica" / "meta.json"

PARADAS = frozenset("""
a o as os um uma uns umas de do da dos das em no na nos nas por para pra pro com sem e ou que qual quais
quem como onde quando quanto quantos quantas porque se eh sao foi foram era eram ser ter tem tinha
ao aos pelo pela pelos pelas este esta esse essa isso isto ele ela eles elas seu sua seus suas me te lhe
ja so tambem mais muito muita nao sim ha sobre entre ate apos mas existe existem
""".split())

TRACOS = ("bm", "bm_ficha", "nome", "resto", "resto_topo", "sentido", "sentido_rel",
          "primeiro", "definicao", "quem_nome", "quando_data", "quanto_numero", "onde_lugar",
          "porque_causa", "como_funcionamento", "aspecto_par", "aspecto_outro", "tipo_sem_par",
          "nome_parcial", "bm_sem_nome")

# Aspecto pedido pela pergunta → marca do fato (curriculo_mundo).
_ASPECTOS = (
    ("funcao", r"\b(?:para que serve|serve para|funcao|papel|utilidade|pra que serve)\b"),
    ("funcionamento", r"\b(?:como funciona|como (?:ele|ela|isso) funciona|mecanismo|como acontece|como ocorre)\b"),
    ("formacao", r"\b(?:como surgiu|como se formou|como (?:foi )?(?:criad|form|inventad)|origem|surgimento)\w*"),
    ("evidencias", r"\b(?:como se sabe|como sabemos|evidencia|prova|como descobri|como foi descobert)\w*"),
)


def normalizar(texto):
    t = unicodedata.normalize("NFD", texto.casefold())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def palavras(texto):
    return [w for w in re.findall(r"[a-z0-9]+", normalizar(texto)) if w not in PARADAS and len(w) > 1]


def termos(texto):
    """Palavras e radicais de 5 letras ("mutacao" e "mutacoes" se encontram)."""
    return [t for w in palavras(texto) for t in (w, "r:" + w[:5])]


def fatos_do_acervo(compositor):
    """Todos os fatos das fichas, na ordem do acervo: [(id, índice, texto)]."""
    saida = []
    for ident in sorted(compositor.itens):
        for i, f in enumerate(compositor.itens[ident]["fatos"]):
            saida.append((ident, i, f["texto"] if isinstance(f, dict) else str(f)))
    return saida


class BM25:
    def __init__(self, textos, k1=1.2, b=0.75):
        docs = [termos(t) for t in textos]
        self.k1, self.b = k1, b
        self.media = sum(len(d) for d in docs) / max(1, len(docs))
        self.tam = [len(d) for d in docs]
        n = len(docs)
        self.invertido = {}
        for j, d in enumerate(docs):
            for t, c in Counter(d).items():
                self.invertido.setdefault(t, []).append((j, c))
        self.idf = {t: math.log(1 + (n - len(p) + 0.5) / (len(p) + 0.5)) for t, p in self.invertido.items()}

    def notas(self, lista_termos, docs=None):
        """{doc: nota} dos documentos com algum termo (ou só de docs)."""
        saida = {}
        for t in lista_termos:
            for j, c in self.invertido.get(t, ()):
                if docs is not None and j not in docs:
                    continue
                norm = self.k1 * (1 - self.b + self.b * self.tam[j] / self.media)
                saida[j] = saida.get(j, 0.0) + self.idf[t] * c * (self.k1 + 1) / (c + norm)
        return saida


class BuscaSemantica:
    FICHAS = 8  # fichas candidatas por pergunta

    def __init__(self, compositor, caminho_modelo=CAMINHO_MODELO, exigir_aprovacao=True, vetores=None):
        self.c = compositor
        self.fatos = fatos_do_acervo(compositor)
        self.bm = BM25([t for _, _, t in self.fatos])
        self.por_ficha = {}
        for j, (ident, _, _) in enumerate(self.fatos):
            self.por_ficha.setdefault(ident, []).append(j)
        self.nomes = {}
        for ident, it in compositor.itens.items():
            formas = [it["nome"]] + list(it.get("aliases") or ())
            self.nomes[ident] = [" ".join(palavras(f)) for f in formas if palavras(f)]
        self._vetores = vetores
        self.pesos = dict.fromkeys(TRACOS, 0.0)
        self.pesos["bm"] = 1.0
        self.aprendida = False
        try:
            meta = json.loads(Path(caminho_modelo).read_text(encoding="utf-8"))
            if meta.get("tracos") == list(TRACOS) and (meta.get("controle", {}).get("aprovado")
                                                       or not exigir_aprovacao):
                self.pesos = dict(zip(TRACOS, meta["pesos"]))
                self.aprendida = True
        except (OSError, ValueError, KeyError, TypeError):
            pass

    @property
    def vetores(self):
        if self._vetores is None:
            from leitura_ficha import _vetores
            self._vetores = _vetores()
        return self._vetores

    # ------------------------------------------------------------ evidências --

    def _sentido(self, ws_pergunta, ws_fato):
        """Média, sobre as palavras da pergunta, da melhor proximidade com uma
        palavra do fato (1 para a mesma palavra)."""
        vet = self.vetores
        if not ws_pergunta or not ws_fato:
            return 0.0
        total = 0.0
        for w in ws_pergunta:
            if w in ws_fato:
                total += 1.0
            elif vet is not None and vet.disponivel and len(w) >= 4:
                total += max(0.0, max((vet.similaridade(w, f) for f in ws_fato if len(f) >= 4), default=0.0))
        return total / len(ws_pergunta)

    def candidatos(self, pergunta, apenas=None):
        """[(id da ficha, nome citado?)]: fichas com melhor BM25 e as citadas
        pelo nome; com apenas, só essas fichas."""
        n = " " + " ".join(palavras(pergunta)) + " "
        citadas = {ident for ident, formas in self.nomes.items()
                   if any(f and " " + f + " " in n for f in formas)}
        notas = self.bm.notas(termos(pergunta))
        melhor = {}
        for j, s in notas.items():
            ident = self.fatos[j][0]
            melhor[ident] = max(melhor.get(ident, 0.0), s)
        if apenas is not None:
            fichas = {i for i in apenas if i in self.por_ficha}
        else:
            fichas = set(sorted(melhor, key=lambda i: (-melhor[i], i))[:self.FICHAS]) | citadas
        return [(i, i in citadas) for i in sorted(fichas)], notas, melhor

    def tracos(self, pergunta, apenas=None):
        """[(j, {traço: valor})] dos fatos candidatos (ou das fichas em apenas)."""
        from leitura_ficha import _CAUSAL, _DATA, _LUGAR, tipo_pergunta
        n_perg = normalizar(pergunta).strip()
        tipo = tipo_pergunta(n_perg)
        aspecto = next((a for a, p in _ASPECTOS if re.search(p, n_perg)), None)
        definicao = bool(re.match(r"(?:o que (?:e|sao|significa)|quem (?:e|foi|era)|defina|qual (?:e )?a definicao)\b",
                                  n_perg))
        fichas, notas, melhor = self.candidatos(pergunta, apenas)
        # Nenhuma ficha citada pelo nome: as palavras do fato valem mais que a
        # força da ficha (o modelo aprende quanto).
        sem_nome = not any(citada for _, citada in fichas)
        topo = max(notas.values(), default=0.0) or 1.0
        ws_perg = palavras(pergunta)
        raizes_perg = {w[:5] for w in ws_perg}
        saida = []
        for ident, citada in fichas:
            nome_ws = {w for f in self.nomes.get(ident, ()) for w in f.split()}
            nome_r = {w[:5] for w in nome_ws}
            resto = [w for w in ws_perg if w not in nome_ws and w[:5] not in nome_r]
            js = self.por_ficha[ident]
            notas_resto = self.bm.notas([t for w in resto for t in (w, "r:" + w[:5])], set(js))
            topo_resto = max(notas_resto.values(), default=0.0)
            sentidos = {}
            for j in js:
                sentidos[j] = self._sentido(resto, set(palavras(self.fatos[j][2])))
            topo_sentido = max(sentidos.values(), default=0.0)
            nome_norm = normalizar(self.c.itens[ident]["nome"])
            # Nome citado em parte ou com outra flexão: "nominalista" para
            # "nominalismo", "lagartixa" para "adesão da lagartixa".
            parcial = max((sum(1 for w in f.split() if w[:5] in raizes_perg) / len(f.split())
                           for f in self.nomes.get(ident, ()) if f), default=0.0)
            for j in js:
                _, i, texto = self.fatos[j]
                fato = self.c.itens[ident]["fatos"][i]
                marca = fato.get("aspecto") if isinstance(fato, dict) else None
                n_fato = normalizar(texto)
                proprios = [m.group(0) for m in re.finditer(r"(?<![.!?]\s)(?<!^)\b[A-ZÁÉÍÓÚÂÊÔÃÕ][\wÀ-ú]+", texto)
                            if normalizar(m.group(0)) not in nome_norm]
                compat = {
                    "quem": bool(proprios),
                    "quando": bool(_DATA.search(n_fato)),
                    "quanto": bool(re.search(r"\d", texto)) or bool(re.search(
                        r"\b(?:metade|terco|quinto|dobro|milh|bilh|dezenas|centenas)\w*", n_fato)),
                    "onde": bool(_LUGAR.search(texto)),
                    "porque": bool(_CAUSAL.search(n_fato)),
                    "como": marca == "funcionamento" or bool(_CAUSAL.search(n_fato)),
                }
                r = notas_resto.get(j, 0.0)
                saida.append((j, {
                    "bm": notas.get(j, 0.0) / topo,
                    "bm_ficha": melhor.get(ident, 0.0) / topo,
                    "nome": 1.0 if citada else 0.0,
                    "resto": r / topo_resto if topo_resto else 0.0,
                    "resto_topo": 1.0 if topo_resto and r == topo_resto else 0.0,
                    "sentido": sentidos[j],
                    "sentido_rel": sentidos[j] - topo_sentido,
                    "primeiro": 1.0 if i == 0 else 0.0,
                    "definicao": 1.0 if definicao and i == 0 else 0.0,
                    "quem_nome": 1.0 if tipo == "quem" and compat["quem"] else 0.0,
                    "quando_data": 1.0 if tipo == "quando" and compat["quando"] else 0.0,
                    "quanto_numero": 1.0 if tipo == "quanto" and compat["quanto"] else 0.0,
                    "onde_lugar": 1.0 if tipo == "onde" and compat["onde"] else 0.0,
                    "porque_causa": 1.0 if tipo == "porque" and compat["porque"] else 0.0,
                    "como_funcionamento": 1.0 if tipo == "como" and compat["como"] else 0.0,
                    "aspecto_par": 1.0 if aspecto and marca == aspecto else 0.0,
                    "aspecto_outro": 1.0 if aspecto and marca and marca != aspecto else 0.0,
                    "tipo_sem_par": 1.0 if tipo in compat and not compat[tipo] else 0.0,
                    "nome_parcial": parcial,
                    "bm_sem_nome": notas.get(j, 0.0) / topo if sem_nome else 0.0,
                }))
        return saida

    # ---------------------------------------------------------------- busca --

    def buscar_palavras(self, pergunta, k=5):
        """[(id da ficha, índice do fato)] dos k fatos com melhor BM25."""
        notas = self.bm.notas(termos(pergunta))
        ordem = sorted(notas, key=lambda j: (-notas[j], j))[:k]
        return [self.fatos[j][:2] for j in ordem]

    def buscar(self, pergunta, k=5, assuntos=None):
        """[(probabilidade, id da ficha, índice do fato)] dos k melhores, com a
        probabilidade do softmax entre os candidatos. assuntos restringe às
        fichas dadas (a pergunta já disse de quem fala)."""
        cand = self.tracos(pergunta, assuntos)
        if not cand:
            return []
        z = [sum(self.pesos[t] * x[t] for t in TRACOS) for _, x in cand]
        m = max(z)
        e = [math.exp(v - m) for v in z]
        soma = sum(e)
        ordem = sorted(range(len(cand)), key=lambda a: (-z[a], cand[a][0]))[:k]
        return [(e[a] / soma, self.fatos[cand[a][0]][0], self.fatos[cand[a][0]][1]) for a in ordem]
