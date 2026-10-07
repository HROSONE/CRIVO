"""Geração ancorada: o Transformer do CRIVO escreve a resposta a partir dos fatos.

É o mesmo Transformer causal do projeto (pesos treinados do zero, nenhum
modelo externo), ajustado com respostas de um tutor no formato

    <documento> fato <documento> fato ... <usuario> pergunta <assistente> resposta <fim>

(experimentos/geracao_ancorada/treinar_geracao_ancorada.py). Aqui ele roda em NumPy, com memória
de atenção (cache de chaves e valores), sem PyTorch no site.

A geração é presa aos fatos de três maneiras:
1. decodificação restrita: só pode escrever pedaços (tokens) que aparecem nos
   fatos ou na pergunta, mais palavras de ligação e pontuação;
2. guarda: a resposta só sai se cada palavra de conteúdo vier dos fatos ou da
   pergunta, se cada número estiver nos fatos, se cada frase se apoiar num
   único fato, se as palavras vizinhas forem costuras que já existem na fonte,
   se não repetir palavra e se não começar com "sim"/"não" (polaridade não se
   confere pelas palavras);
3. recuo: se nenhuma tentativa passar na guarda, a resposta de sempre continua.

Só é usada se meta.json disser que foi aprovada no controle.
"""
import json
import math
import re
import unicodedata
import zlib
from collections import Counter
from functools import lru_cache
from pathlib import Path

PASTA = Path(__file__).resolve().parent / "artefatos" / "geracao_pt"

LIGACAO = """a o as os um uma uns umas de do da dos das em no na nos nas por pelo pela pelos pelas para pra com sem
que qual quais quem quando onde como porque e ou mas se nao sim mais menos muito muita muitos muitas tambem ja
foi era sao ser e esta estao tem ter isso esse essa este esta ele ela eles elas seu sua seus suas ao aos à às
entao assim ou seja alem disso por isso isso porque ainda sobre ate entre cerca quase todo toda todos todas
outro outra outros outras mesmo mesma lhe lo la los las sendo foram eram havia ha pode podem deve devem""".split()
_LIGACAO = frozenset(LIGACAO)
_PONTUACAO = [",", ".", ";", ":", "(", ")", "-", "–", "%", "°"]

LIMITE_FATOS = 170   # tokens dos fatos no contexto, como no treino
LIMITE_PERGUNTA = 40
MAX_TOKENS = 70


# ------------------------------------------------------------------ guarda ---

def norm(t):
    t = unicodedata.normalize("NFD", t.casefold())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _ws(t):
    return re.findall(r"[a-z0-9]+", norm(t))


def palavras_conteudo(t):
    # Siglas como DNA, RNA, ATP e HIV também carregam conteúdo.
    return [w for w in _ws(t) if len(w) >= 3 and w not in _LIGACAO]


def fiel(resposta, fatos, pergunta):
    """Toda palavra de conteúdo tem raiz nos fatos ou na pergunta; todo número
    da resposta está nos fatos ou na pergunta."""
    fonte = " ".join(fatos) + " " + pergunta
    raizes = {w[:4] for w in palavras_conteudo(fonte)}
    numeros = set(re.findall(r"\d+(?:[.,]\d+)*", fonte))
    if any(w[:4] not in raizes for w in palavras_conteudo(resposta)):
        return False
    return all(n in numeros for n in re.findall(r"\d+(?:[.,]\d+)*", resposta))


def verificado(resposta, fatos, pergunta, minimo=0.8):
    """Fiel e, frase a frase, apoiada num único fato: ao menos 80% das palavras
    de conteúdo da frase (fora as da pergunta) estão num mesmo fato. Barra
    misturas de pedaços de fatos diferentes."""
    if not fiel(resposta, fatos, pergunta):
        return False
    da_pergunta = {w[:4] for w in palavras_conteudo(pergunta)}
    raizes_fatos = [{w[:4] for w in palavras_conteudo(f)} for f in fatos]
    for frase in re.split(r"(?<=[.;!?])\s+|:\s+", resposta):
        ws = [w[:4] for w in palavras_conteudo(frase) if w[:4] not in da_pergunta]
        if len(ws) < 2:
            continue
        if max(sum(w in r for w in ws) / len(ws) for r in raizes_fatos) < minimo:
            return False
    return True


def repete_palavra(texto, fonte="", janela=5):
    """Palavra de conteúdo repetida perto de si mesma ("políticos e políticos"),
    a menos que a própria fonte a repita assim perto."""
    def perto(t):
        ws = palavras_conteudo(t)
        return {ws[i] for i in range(len(ws)) if ws[i] in ws[max(0, i - janela):i]}
    return bool(perto(texto) - perto(fonte))


def costura(texto, fonte, minimo=0.6, minimo_frase=0.5):
    """Fração de pares de palavras vizinhas da resposta que existem na fonte.
    As respostas do tutor ficam acima de 0,56 em 99% dos casos; colagens tortas
    ("definiu a presidente e para o povo") ficam bem abaixo."""
    f = _ws(fonte)
    pares = set(zip(f, f[1:]))

    def cobertura(t):
        w = _ws(t)
        bs = list(zip(w, w[1:]))
        return sum(b in pares for b in bs) / len(bs) if bs else 1.0
    frases = [x for x in re.split(r"(?<=[.;!?])\s+", texto) if len(_ws(x)) >= 4]
    return cobertura(texto) >= minimo and all(cobertura(x) >= minimo_frase for x in frases)


def troca_de_palavra(texto, fonte):
    """Par de palavras vizinhas da resposta com uma palavra de conteúdo que não
    existe na fonte: é assim que um pedaço trocado muda o sentido ("digerir a
    lactase" no lugar de "digerir a lactose") sem inventar palavra nenhuma."""
    f = _ws(fonte)
    pares = set(zip(f, f[1:]))
    w = _ws(texto)
    conteudo = lambda x: len(x) >= 3 and x not in _LIGACAO  # noqa: E731
    return any((a, b) not in pares for a, b in zip(w, w[1:]) if conteudo(a) or conteudo(b))


def numero_fora_de_lugar(texto, fonte, janela=3):
    """Número com palavras seguintes diferentes das da fonte: "8,1 milhões de
    km²" quando a fonte diz "8,1 milhões de habitantes" (números trocados)."""
    def contextos(t):
        ws = re.findall(r"\d+(?:[.,]\d+)*|[a-z]+", norm(t))
        return [(w, tuple(ws[i + 1:i + 1 + janela])) for i, w in enumerate(ws) if w[0].isdigit()]
    da_fonte = {}
    for n, depois in contextos(fonte):
        da_fonte.setdefault(n, set()).add(depois)
    for n, depois in contextos(texto):
        if not any(d[:len(depois)] == depois or depois[:len(d)] == d for d in da_fonte.get(n, ())):
            return True
    return False


def sem_conteudo_novo(texto, pergunta):
    """Eco da pergunta: nenhuma palavra de conteúdo além das da pergunta."""
    da_pergunta = {w[:4] for w in palavras_conteudo(pergunta)}
    return not [w for w in palavras_conteudo(texto) if w[:4] not in da_pergunta]


def quem_sem_nome(texto, pergunta):
    """"Quem foi...?" respondido sem nome próprio que não esteja na pergunta."""
    if not norm(pergunta).strip().startswith("quem"):
        return False
    da_pergunta = set(_ws(pergunta))
    nomes = [m.group(0) for m in re.finditer(r"(?<!^)\b[A-ZÁÉÍÓÚÂÊÔÃÕ][\wÀ-ú]+", texto.strip())]
    return not [n for n in nomes if norm(n) not in da_pergunta]


_INTERROGATIVAS = frozenset("que qual quais quem quando onde como quanto quantos quanta quantas".split())


def comeco_torto(texto, pergunta):
    """Começo que não é de resposta: palavra de pergunta ("Quem tem 90
    minutos"), palavra repetida ("Porque, porque"), "porque, por isso", ou
    verbo sem sujeito numa pergunta "quem" ("Foi o primeiro ser humano...")."""
    ws = _ws(texto)
    if not ws or ws[0] in _INTERROGATIVAS or (len(ws) > 1 and ws[0] == ws[1]):
        return True
    if re.match(r"porque,? (?:por isso|porque)", norm(texto)):
        return True
    return norm(pergunta).strip().startswith("quem") and ws[0] in ("foi", "e", "era", "sao", "foram")


def polaridade_inventada(texto):
    w = _ws(texto)
    return bool(w) and w[0] in ("sim", "nao")


def motivo_da_guarda(texto, fatos, pergunta):
    """Código estável de recuo, sem guardar o texto rejeitado no chat."""
    if not texto or not texto.rstrip().endswith((".", "!")):
        return "resposta_incompleta"
    if not fatos:
        return "sem_evidencias"
    fonte = " ".join(fatos) + " " + pergunta
    verificacoes = (
        (numero_fora_de_lugar(texto, " ".join(fatos)), "numero_sem_suporte"),
        (sem_conteudo_novo(texto, pergunta), "eco_da_pergunta"),
        (quem_sem_nome(texto, pergunta), "identidade_ausente"),
        (comeco_torto(texto, pergunta), "comeco_inadequado"),
        (polaridade_inventada(texto), "polaridade_sem_suporte"),
        (repete_palavra(texto, fonte), "repeticao"),
        (troca_de_palavra(texto, fonte), "relacao_sem_suporte"),
        (not costura(texto, fonte), "costura_sem_suporte"),
        (not verificado(texto, fatos, pergunta), "conteudo_sem_suporte"),
    )
    return next((motivo for falhou, motivo in verificacoes if falhou), None)


def preserva_evidencia(texto, fatos):
    """Não apaga conteúdos, valores ou ressalvas da evidência selecionada.

    A guarda de suporte verifica o que foi dito; esta confere também o que
    foi omitido. A unidade já foi escolhida pelo leitor/compositor.
    """
    fonte = " ".join(fatos)
    # Raízes e conjuntos confundem governantes/governados e perdem a
    # repetição de nomes como Mato Grosso. A unidade selecionada precisa
    # conservar cada palavra de conteúdo, inclusive siglas, e suas ocorrências.
    def cobre(originais, escritos):
        return not (Counter(originais) - Counter(escritos))
    return (cobre(palavras_conteudo(fonte), palavras_conteudo(texto))
            and cobre(re.findall(r"\d+(?:[.,]\d+)*", fonte),
                      re.findall(r"\d+(?:[.,]\d+)*", texto))
            and cobre((w for w in _ws(fonte) if w in ("nao", "nem", "nunca", "jamais")),
                      (w for w in _ws(texto) if w in ("nao", "nem", "nunca", "jamais"))))


def aprovada_pela_guarda(texto, fatos, pergunta):
    return motivo_da_guarda(texto, fatos, pergunta) is None


# -------------------------------------------------------------- executor ---

class GeracaoAncorada:
    def __init__(self, pasta=PASTA, exigir_aprovacao=True):
        self.disponivel = False
        self.motivo = ""
        pasta = Path(pasta)
        try:
            meta = json.loads((pasta / "meta.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.motivo = "sem meta.json"
            return
        if exigir_aprovacao and not meta.get("controle", {}).get("aprovado"):
            self.motivo = "não aprovada no controle"
            return
        try:
            import numpy as np
        except ImportError:
            self.motivo = "NumPy ausente"
            return
        from pontuador_frases import BPE, _bytes_unicode, _erf
        try:
            pesos = np.load(pasta / "pesos_numpy.npz")
            self.bpe = BPE(pasta / "tokenizer.json")
        except (OSError, ValueError) as exc:
            self.motivo = "pesos ausentes (%s)" % type(exc).__name__
            return
        self.np, self._erf = np, _erf
        self.p = {k: pesos[k].astype(np.float32) for k in pesos.files}
        cfg = meta["base"]["config"]
        self.camadas, self.cabecas, self.contexto = cfg["camadas"], cfg["cabecas"], cfg["contexto"]
        self.meta = meta
        self._texto = {i: t for t, i in self.bpe.vocab.items()}
        self._bytes = {c: b for b, c in _bytes_unicode().items()}
        e = self.bpe.especiais
        self.doc, self.usu, self.ass, self.fim = e["<documento>"], e["<usuario>"], e["<assistente>"], e["<fim>"]
        base = set()
        for w in LIGACAO + _PONTUACAO:
            for forma in (w, " " + w, w.capitalize(), " " + w.capitalize()):
                base.update(self.bpe.codificar(forma))
        self._ligacao = base
        self.disponivel = True

    # --- tokens ---
    def decodificar(self, ids):
        texto = "".join(self._texto.get(i, "") for i in ids if i not in self.bpe.especiais.values())
        return bytes(self._bytes[c] for c in texto if c in self._bytes).decode("utf-8", "replace")

    def prompt(self, pergunta, fatos):
        ids = []
        for f in fatos:
            t = [self.doc] + self.bpe.codificar(f)
            if ids and len(ids) + len(t) > LIMITE_FATOS:
                continue
            ids += t
        ids = ids[:LIMITE_FATOS]
        return ids + [self.usu] + self.bpe.codificar(pergunta)[:LIMITE_PERGUNTA] + [self.ass]

    # --- Transformer com cache ---
    def _norm(self, x, nome):
        np = self.np
        m = x.mean(-1, keepdims=True)
        v = ((x - m) ** 2).mean(-1, keepdims=True)
        return (x - m) / np.sqrt(v + 1e-5) * self.p[nome + ".weight"] + self.p[nome + ".bias"]

    def _passo(self, ids, inicio, cache):
        """Processa ids nas posições inicio.. e devolve os logits da última;
        cache guarda (K, V) de cada camada."""
        np, p = self.np, self.p
        t = len(ids)
        h = self.cabecas
        x = p["embedding.weight"][ids] + p["posicao.weight"][inicio:inicio + t]
        d = x.shape[-1] // h
        for c in range(self.camadas):
            b = "blocos.%d." % c
            q, k, v = np.split(self._norm(x, b + "norm1") @ p[b + "qkv.weight"].T, 3, axis=-1)
            q, k, v = [a.reshape(t, h, d).transpose(1, 0, 2) for a in (q, k, v)]
            if c in cache:
                k = np.concatenate([cache[c][0], k], axis=1)
                v = np.concatenate([cache[c][1], v], axis=1)
            cache[c] = (k, v)
            s = q @ k.transpose(0, 2, 1) / math.sqrt(d)
            total = k.shape[1]
            if t > 1:
                s = s + np.triu(np.full((t, total), -np.inf, dtype=np.float32), total - t + 1)
            s = np.exp(s - s.max(-1, keepdims=True))
            s /= s.sum(-1, keepdims=True)
            a = (s @ v).transpose(1, 0, 2).reshape(t, h * d)
            x = x + a @ p[b + "projecao.weight"].T
            m = self._norm(x, b + "norm2") @ p[b + "mlp.0.weight"].T + p[b + "mlp.0.bias"]
            m = 0.5 * m * (1.0 + self._erf(m / math.sqrt(2.0), np))
            x = x + m @ p[b + "mlp.2.weight"].T + p[b + "mlp.2.bias"]
        return self._norm(x[-1:], "norm")[0] @ p["embedding.weight"].T

    def _decodificar(self, prompt, mascara, rng=None, temperatura=0.7, top_k=5, fonte=None, prefixo=""):
        np = self.np
        cache, saida = {}, self.bpe.codificar(prefixo) if prefixo else []
        entrada = prompt + saida
        logits = self._passo(entrada, 0, cache)
        pos = len(entrada)
        for _ in range(min(MAX_TOKENS - len(saida), self.contexto - len(entrada))):
            l = logits + mascara
            for t in set(saida[-3:]):
                if saida.count(t) > 2:
                    l[t] -= 5.0
            for k in range(len(saida) - 2):  # sem repetir trigramas
                if saida[k] == saida[-2] and saida[k + 1] == saida[-1]:
                    l[saida[k + 2]] = -np.inf
            if fonte is not None:
                # Confira pares de palavras já completos antes de escolher
                # o token. O último fragmento BPE ainda pode estar incompleto.
                # A guarda final continua obrigatória, com os mesmos critérios.
                candidatos = np.argsort(l)[-64:][::-1]
                validos = []
                for candidato in candidatos:
                    if not np.isfinite(l[candidato]):
                        continue
                    parcial = self.decodificar(saida + [int(candidato)])
                    completo = parcial if candidato == self.fim else re.sub(r"[\wÀ-ú]+$", "", parcial)
                    if not troca_de_palavra(completo, fonte) and not repete_palavra(completo, fonte):
                        validos.append(int(candidato))
                        if len(validos) >= top_k:
                            break
                if validos:
                    restrito = np.full_like(l, -np.inf)
                    restrito[validos] = l[validos]
                    l = restrito
            if rng is None:
                prox = int(l.argmax())
            else:
                melhores = np.argsort(l)[-top_k:]
                z = l[melhores] / temperatura
                z = np.exp(z - z.max())
                prox = int(rng.choice(melhores, p=z / z.sum()))
            if prox == self.fim:
                break
            saida.append(prox)
            logits = self._passo([prox], pos, cache)
            pos += 1
        return self.decodificar(saida).strip()

    def gerar(self, pergunta, fatos, tentativas=3, diagnostico=None):
        """Inferência determinística reutilizada ao reconstruir o histórico.

        A chave contém pergunta e evidências completas; conversas com fontes
        diferentes não compartilham uma resposta. O diagnóstico devolvido é
        uma cópia, para não misturar requisições concorrentes.
        """
        texto, trace = self._gerar_cache(pergunta, tuple(fatos), tentativas)
        if diagnostico is not None:
            diagnostico.update({k: list(v) if isinstance(v, list) else v for k, v in trace.items()})
        return texto

    @lru_cache(maxsize=128)
    def _gerar_cache(self, pergunta, fatos, tentativas):
        trace = {}
        texto = self._gerar(pergunta, fatos, tentativas, trace)
        return texto, trace

    def _gerar(self, pergunta, fatos, tentativas=3, diagnostico=None):
        """Resposta escrita a partir dos fatos, ou None. Tenta decodificação
        gulosa, amostragem determinística e um começo da evidência. Diagnóstico
        pertence à chamada, sem estado compartilhado entre requisições."""
        if diagnostico is None:
            diagnostico = {}
        diagnostico.update(tentativas=0, rejeicoes=[])
        if not self.disponivel or not fatos:
            diagnostico["motivo"] = "modelo_indisponivel" if not self.disponivel else "sem_evidencias"
            return None
        np = self.np
        prompt = self.prompt(pergunta, fatos)
        permit = self._ligacao | {t for t in prompt if t > 4} | {self.fim}
        mascara = np.full(self.p["embedding.weight"].shape[0], -np.inf, dtype=np.float32)
        mascara[sorted(permit)] = 0.0
        rng = None
        for tentativa in range(tentativas):
            # Um começo vindo da própria evidência conserva sujeito e
            # antecedente. O restante continua sendo
            # predito pelo Transformer e precisa passar pela guarda inteira.
            prefixo = " ".join(fatos[0].split()[:2]) if len(fatos) == 1 else ""
            texto = self._decodificar(prompt, mascara, rng,
                                      fonte=" ".join(fatos) + " " + pergunta, prefixo=prefixo)
            diagnostico["tentativas"] += 1
            motivo = motivo_da_guarda(texto, fatos, pergunta)
            if motivo is None and not preserva_evidencia(texto, fatos):
                motivo = "evidencia_incompleta"
            if motivo is None:
                diagnostico["motivo"] = "gerada"
                diagnostico["prefixo_fonte"] = bool(prefixo)
                return texto
            diagnostico["rejeicoes"].append(motivo)
            if rng is None:
                rng = np.random.default_rng(zlib.crc32(norm(pergunta).encode("utf-8")))
        diagnostico["motivo"] = "guarda_rejeitou"
        return None


@lru_cache(maxsize=2)
def geracao(pasta=str(PASTA), exigir_aprovacao=True):
    return GeracaoAncorada(pasta, exigir_aprovacao)
