"""Analisador de frases do português: classe, lema e ligações entre palavras.

Para cada palavra da frase, o analisador diz:
  - a classe gramatical (substantivo, verbo, artigo… no padrão UPOS);
  - o lema ("abriu" → "abrir");
  - de qual palavra ela depende e o tipo de ligação (sujeito, objeto…),
    no padrão Universal Dependencies.

Dois modelos pequenos, treinados do zero em NumPy por
scripts/treinar_analisador.py sobre o UD Portuguese-Bosque (CC BY-SA 4.0):
  - etiquetador: rede de janela (±2 palavras) para classe e lema;
  - parser por transições arc-standard (Chen & Manning, 2014), guloso.
Os pesos ficam em artefatos/analisador_pt e só são usados se o relatório
do treino passar no controle de qualidade (medido no conjunto de teste
oficial, que o treino não vê). Sem NumPy ou sem pesos aprovados, o
analisador fica desligado e o Crivo segue como antes.
"""
import json
import re
import unicodedata
from pathlib import Path

PASTA = Path(__file__).resolve().parent / "artefatos" / "analisador_pt"
PASTA_VETORES = Path(__file__).resolve().parent / "artefatos" / "vetores_pt"

# Controle de qualidade mínimo (teste oficial, tokenização de referência).
MINIMO = {"upos": 0.90, "uas": 0.75, "las": 0.70}

UNK, NULO, RAIZ = "<unk>", "<nulo>", "<raiz>"

# Fala informal → forma escrita que o treebank conhece.
INFORMAL = {
    "tô": "estou", "to": "estou", "tou": "estou", "tá": "está", "ta": "está", "tava": "estava",
    "tavam": "estavam", "tamo": "estamos", "pra": "para", "pro": "para o",
    "pros": "para os", "pras": "para as", "né": "não é", "vc": "você", "vcs": "vocês", "cê": "você",
    "q": "que", "tb": "também", "tbm": "também", "mto": "muito", "mt": "muito", "hj": "hoje",
    "pq": "porque", "pk": "porque", "porq": "porque", "msm": "mesmo", "td": "tudo", "tds": "todos",
    "dps": "depois", "agr": "agora", "cmg": "comigo", "ctg": "contigo", "qnd": "quando", "qdo": "quando",
    "oq": "o que", "naum": "não", "vdd": "verdade", "fds": "fim de semana", "blz": "beleza",
    "mds": "meu Deus", "sla": "sei lá",
}
CLITICOS = {"se", "me", "te", "lhe", "lhes", "o", "a", "os", "as", "lo", "la", "los", "las",
            "no", "na", "nos", "vos"}
_TOKEN = re.compile(r"\d+(?:[.,]\d+)*|[^\W\d_]+(?:-[^\W\d_]+)*|\S", re.UNICODE)


def sem_acento(texto):
    s = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def forma_chave(forma):
    return forma.lower()


def sufixo(forma):
    f = forma.lower()
    return f[-3:] if len(f) > 3 else f


def formato(forma):
    if forma.isdigit() or re.fullmatch(r"\d[\d.,]*", forma):
        return "num"
    if not any(c.isalnum() for c in forma):
        return "pont"
    if forma.isupper() and len(forma) > 1:
        return "maius"
    if forma[:1].isupper():
        return "inicial"
    return "minus"


class Tokenizador:
    """Separa pontuação, contrações ("do" → "de o") e clíticos ("abriu-se").

    A tabela de contrações vem dos próprios dados de treino: uma forma só
    é separada quando, no treebank, ela é separada na maioria das vezes
    ("nos" pronome × "nos" = "em os")."""

    def __init__(self, contracoes):
        self.contracoes = contracoes

    def __call__(self, texto):
        palavras = []
        for bruto in _TOKEN.findall(texto):
            baixo = bruto.lower()
            if baixo in INFORMAL and (baixo not in ("to", "ta") or len(texto.split()) > 1):
                partes = INFORMAL[baixo].split()
                if baixo in ("pq", "pk", "porq") and (not palavras or palavras[-1] in ("e", "E")) \
                        and texto.rstrip().endswith("?"):
                    partes = ["por", "que"]  # "pq ele ligou?" pergunta o motivo
                partes[0] = partes[0].capitalize() if bruto[:1].isupper() else partes[0]
                palavras.extend(partes)
                continue
            if baixo in self.contracoes:
                partes = list(self.contracoes[baixo])
                if bruto[:1].isupper():
                    partes[0] = partes[0].capitalize()
                palavras.extend(partes)
                continue
            if "-" in bruto:
                verbo, _, clitico = bruto.rpartition("-")
                if clitico.lower() in CLITICOS and len(verbo) > 2 and "-" not in verbo:
                    palavras.extend([verbo, clitico])
                    continue
            palavras.append(bruto)
        return palavras


# ---------------------------------------------------------------------------
# Características (compartilhadas com o treino)

def ids_etiquetador(formas, vocab, sufixos, formatos):
    """Janela de ±2 palavras: palavra, sufixo de 3 letras e formato."""
    n = len(formas)
    pal = [vocab.get(forma_chave(f), vocab.get(sem_acento(f), 1)) for f in formas]
    suf = [sufixos.get(sufixo(f), 1) for f in formas]
    fmt = [formatos.get(formato(f), 1) for f in formas]
    linhas = []
    for i in range(n):
        linha = []
        for d in (-2, -1, 0, 1, 2):
            j = i + d
            if 0 <= j < n:
                linha += [pal[j], suf[j], fmt[j]]
            else:
                linha += [0, 0, 0]  # 0 = <nulo>
        linhas.append(linha)
    return linhas


def ids_biafim(formas, pal_id, vet_id, suf_id, fmt_id):
    """Raiz + cada palavra: [palavra treinada, vetor do projeto, sufixo, formato]."""
    linhas = [[2, 0, 2, 2]]
    for f in formas:
        baixo, sem = forma_chave(f), sem_acento(f)
        linhas.append([pal_id.get(baixo, pal_id.get(sem, 1)), vet_id.get(sem, vet_id.get(baixo, 0)),
                       suf_id.get(sufixo(f), 1), fmt_id.get(formato(f), 1)])
    return linhas


N_PALAVRAS_PARSER, N_CLASSES_PARSER, N_LIGACOES_PARSER = 18, 18, 12


def ids_parser(pilha, buffer, filhos_esq, filhos_dir, ligacao, pal, cls):
    """Características de Chen & Manning (2014): 3 da pilha, 3 do buffer,
    filhos mais à esquerda/direita dos dois topos e netos."""
    def pega(lista, k):
        return lista[k] if k < len(lista) else -1

    s = [pilha[-1 - k] if k < len(pilha) else -1 for k in range(3)]
    b = [pega(buffer, k) for k in range(3)]

    def esq(x, k):
        return filhos_esq[x][k] if x >= 0 and k < len(filhos_esq[x]) else -1

    def dir_(x, k):
        return filhos_dir[x][-1 - k] if x >= 0 and k < len(filhos_dir[x]) else -1

    filhos = []
    for x in s[:2]:
        filhos += [esq(x, 0), dir_(x, 0), esq(x, 1), dir_(x, 1), esq(esq(x, 0), 0), dir_(dir_(x, 0), 0)]
    nos = s + b + filhos
    return ([pal[x] if x >= 0 else 0 for x in nos],
            [cls[x] if x >= 0 else 0 for x in nos],
            [ligacao[x] if x >= 0 else 0 for x in filhos])


class Configuracao:
    """Estado do arc-standard. Índice 0 é a raiz; palavras de 1 a n."""

    def __init__(self, n):
        self.pilha = [0]
        self.buffer = list(range(1, n + 1))
        self.pai = [-1] * (n + 1)
        self.lig = [0] * (n + 1)
        self.filhos_esq = [[] for _ in range(n + 1)]
        self.filhos_dir = [[] for _ in range(n + 1)]

    def terminou(self):
        return not self.buffer and len(self.pilha) == 1

    def legais(self):
        """(empilhar, esquerda, direita) permitidas."""
        empilhar = bool(self.buffer)
        esquerda = len(self.pilha) > 2  # a raiz nunca vira dependente
        direita = len(self.pilha) > 1 and (len(self.pilha) > 2 or not self.buffer)
        return empilhar, esquerda, direita

    def aplicar(self, acao, ligacao=0):
        if acao == 0:
            self.pilha.append(self.buffer.pop(0))
        elif acao == 1:  # s1 ← s0
            dep = self.pilha.pop(-2)
            cab = self.pilha[-1]
            self._ligar(cab, dep, ligacao)
        else:  # s1 → s0
            dep = self.pilha.pop()
            cab = self.pilha[-1]
            self._ligar(cab, dep, ligacao)

    def _ligar(self, cab, dep, ligacao):
        self.pai[dep], self.lig[dep] = cab, ligacao
        if dep < cab:
            self.filhos_esq[cab].append(dep)
            self.filhos_esq[cab].sort()
        else:
            self.filhos_dir[cab].append(dep)
            self.filhos_dir[cab].sort()


def aplicar_regra_lema(forma, regra):
    """Regra "corte|acréscimo": "abriu" + "2|ir" → "abrir"."""
    if regra in (None, UNK, NULO) or "|" not in regra:
        return forma.lower()
    corte, acrescimo = regra.split("|", 1)
    base = forma.lower()
    corte = int(corte)
    return (base[:-corte] if corte else base) + acrescimo


def regra_lema(forma, lema):
    f, l = forma.lower(), lema.lower()
    comum = 0
    while comum < min(len(f), len(l)) and f[comum] == l[comum]:
        comum += 1
    return "%d|%s" % (len(f) - comum, l[comum:])


# ---------------------------------------------------------------------------
# Vocabulário: palavras do treino (ajustadas) + vetores do projeto (fixos)

def carregar_vetores(np, pasta=PASTA_VETORES):
    try:
        palavras = json.loads((Path(pasta) / "vocabulario.json").read_text(encoding="utf-8"))
        matriz = np.load(Path(pasta) / "vetores.npy").astype(np.float32)
    except (OSError, ValueError):
        return [], None
    return palavras, matriz


def estender(vocab_treino, tabela, vetores, np):
    """As linhas do treino vêm dos pesos; palavras que o treino não viu mas
    estão nos vetores de palavras usam o vetor original, que é o mesmo ponto
    de partida das linhas treinadas (não são aproximadas por semelhança)."""
    vocab = {w: i for i, w in enumerate(vocab_treino)}
    palavras, matriz = vetores
    if matriz is None or matriz.shape[1] != tabela.shape[1]:
        return vocab, tabela
    extras = [(w, k) for k, w in enumerate(palavras) if w not in vocab]
    for w, _ in extras:
        vocab[w] = len(vocab)
    if extras:
        tabela = np.concatenate([tabela, matriz[[k for _, k in extras]]], axis=0)
    return vocab, tabela


# ---------------------------------------------------------------------------
# Execução

class Palavra(tuple):
    __slots__ = ()
    _campos = ("id", "forma", "lema", "classe", "pai", "ligacao")

    def __new__(cls, *valores):
        return tuple.__new__(cls, valores)

    def __getattr__(self, nome):
        try:
            return self[self._campos.index(nome)]
        except ValueError:
            raise AttributeError(nome)

    def __repr__(self):
        return "%d %s (%s, %s) → %d %s" % (self.id, self.forma, self.lema, self.classe,
                                           self.pai, self.ligacao)


class AnalisadorFrases:
    def __init__(self, pasta=PASTA):
        self.disponivel = False
        self.motivo = ""
        try:
            import numpy as np
        except ImportError:
            self.motivo = "sem NumPy"
            return
        self.np = np
        pasta = Path(pasta)
        try:
            meta = json.loads((pasta / "meta.json").read_text(encoding="utf-8"))
            pesos = np.load(pasta / "modelo.npz")
        except (OSError, ValueError):
            self.motivo = "sem pesos treinados"
            return
        teste = meta.get("avaliacao", {}).get("teste", {})
        if any(teste.get(k, 0) < v for k, v in MINIMO.items()):
            self.motivo = "não passou no controle de qualidade: %s" % teste
            return
        self.meta = meta
        self.tokenizar = Tokenizador({k: tuple(v) for k, v in meta["contracoes"].items()})
        if meta.get("arquitetura") == "biafim":
            self._biafim = AnalisadorBiafim.de_pesos({k: pesos[k] for k in pesos.files}, meta)
            self.disponivel = self._biafim is not None
            self.motivo = "" if self.disponivel else "sem vetores de palavras"
            return
        self._biafim = None
        self.p = {k: pesos[k].astype(np.float32) for k in pesos.files}
        vetores = carregar_vetores(np)
        self.vocab_et, self.p["et_pal"] = estender(meta["vocab_etiquetador"], self.p["et_pal"], vetores, np)
        self.vocab_pa, self.p["pa_pal"] = estender(meta["vocab_parser"], self.p["pa_pal"], vetores, np)
        self.sufixos = {w: i for i, w in enumerate(meta["sufixos"])}
        self.formatos = {w: i for i, w in enumerate(meta["formatos"])}
        self.classes = meta["classes"]
        self.cls_id = {w: i for i, w in enumerate(self.classes)}
        self.regras = meta["regras_lema"]
        self.ligacoes = meta["ligacoes"]
        self.lemas_fixos = meta.get("lemas_fixos", {})
        self.tokenizar = Tokenizador({k: tuple(v) for k, v in meta["contracoes"].items()})
        self.disponivel = True

    # -- etiquetador --------------------------------------------------
    def etiquetar(self, formas):
        np = self.np
        ids = np.array(ids_etiquetador(formas, self.vocab_et, self.sufixos, self.formatos))
        p = self.p
        # Mesma ordem do treino: as 5 palavras, os 5 sufixos, os 5 formatos.
        n = len(ids)
        x = np.concatenate([p["et_pal"][ids[:, 0::3]].reshape(n, -1), p["et_suf"][ids[:, 1::3]].reshape(n, -1),
                            p["et_fmt"][ids[:, 2::3]].reshape(n, -1)], axis=1)
        h = np.maximum(0, x @ p["et_W1"] + p["et_b1"])
        classes = (h @ p["et_Wc"] + p["et_bc"]).argmax(1)
        regras = (h @ p["et_Wl"] + p["et_bl"]).argmax(1)
        saida = []
        for forma, c, r in zip(formas, classes, regras):
            classe = self.classes[c]
            chave = forma.lower() + "\t" + classe
            lema = self.lemas_fixos.get(chave) or aplicar_regra_lema(forma, self.regras[r])
            if classe == "PROPN":
                lema = forma
            saida.append((classe, lema))
        return saida

    # -- parser -------------------------------------------------------
    def ligar(self, formas, classes):
        np = self.np
        p = self.p
        n = len(formas)
        pal = [2] + [self.vocab_pa.get(forma_chave(f), self.vocab_pa.get(sem_acento(f), 1)) for f in formas]
        cls = [2] + [self.cls_id[c] + 3 if c in self.cls_id else 1 for c in classes]  # 0 nulo, 1 unk, 2 raiz
        conf = Configuracao(n)
        nl = len(self.ligacoes)
        while not conf.terminou():
            w, c, l = ids_parser(conf.pilha, conf.buffer, conf.filhos_esq, conf.filhos_dir,
                                 conf.lig, pal, cls)
            x = np.concatenate([p["pa_pal"][w].ravel(), p["pa_cls"][c].ravel(), p["pa_lig"][l].ravel()])
            h = np.maximum(0, x @ p["pa_W1"] + p["pa_b1"])
            pont = h @ p["pa_W2"] + p["pa_b2"]
            empilhar, esquerda, direita = conf.legais()
            mascara = np.full(1 + 2 * nl, -np.inf)
            if empilhar:
                mascara[0] = 0
            if esquerda:
                mascara[1:1 + nl] = 0
            if direita:
                mascara[1 + nl:] = 0
            k = int((pont + mascara).argmax())
            if k == 0:
                conf.aplicar(0)
            elif k <= nl:
                conf.aplicar(1, k - 1 + 3)
            else:
                conf.aplicar(2, k - 1 - nl + 3)
        return conf.pai[1:], [self.ligacoes[x - 3] if x >= 3 else "dep" for x in conf.lig[1:]]

    def analisar(self, texto):
        if not self.disponivel or not isinstance(texto, str) or not texto.strip():
            return []
        formas = self.tokenizar(texto)[:80]
        if self._biafim is not None:
            return self._biafim.analisar_formas(formas)
        etiquetas = self.etiquetar(formas)
        pais, ligacoes = self.ligar(formas, [c for c, _ in etiquetas])
        return [Palavra(i + 1, f, lema, classe, pai, lig)
                for i, (f, (classe, lema), pai, lig) in enumerate(zip(formas, etiquetas, pais, ligacoes))]


def _sigmoide(x, np):
    return 1.0 / (1.0 + np.exp(-x))


class AnalisadorBiafim:
    """Execução em NumPy do modelo biafim treinado em PyTorch
    (scripts/treinar_analisador_biafim.py)."""

    @classmethod
    def de_pesos(cls, pesos, meta):
        import numpy as np
        palavras, matriz = carregar_vetores(np)
        if matriz is None:
            return None
        a = cls()
        a.np = np
        a.p = {k: np.asarray(v, dtype=np.float32) for k, v in pesos.items()}
        a.pre = np.concatenate([np.zeros((1, matriz.shape[1]), np.float32), matriz], axis=0)
        a.vet_id = {w: i + 1 for i, w in enumerate(palavras)}
        a.pal_id = {w: i for i, w in enumerate(meta["vocab_biafim"])}
        a.suf_id = {w: i for i, w in enumerate(meta["sufixos"])}
        a.fmt_id = {w: i for i, w in enumerate(meta["formatos"])}
        a.classes, a.regras, a.ligacoes = meta["classes"], meta["regras_lema"], meta["ligacoes"]
        a.lemas_fixos = meta.get("lemas_fixos", {})
        a.camadas = meta.get("camadas_lstm", 2)
        return a

    def _lstm(self, x, prefixo):
        np = self.np
        Wi, Wh, b = self.p[prefixo + "_Wi"], self.p[prefixo + "_Wh"], self.p[prefixo + "_b"]
        H = Wh.shape[1]
        entradas = x @ Wi.T + b
        h = np.zeros(H, np.float32)
        c = np.zeros(H, np.float32)
        saida = np.zeros((len(x), H), np.float32)
        for t in range(len(x)):
            g = entradas[t] + Wh @ h
            i, f = _sigmoide(g[:H], np), _sigmoide(g[H:2 * H], np)
            gg, o = np.tanh(g[2 * H:3 * H]), _sigmoide(g[3 * H:], np)
            c = f * c + i * gg
            h = o * np.tanh(c)
            saida[t] = h
        return saida

    def pontuacoes(self, formas):
        np, p = self.np, self.p
        ids = np.array(ids_biafim(formas, self.pal_id, self.vet_id, self.suf_id, self.fmt_id))
        x = np.concatenate([p["bi_pal"][ids[:, 0]], self.pre[ids[:, 1]], p["bi_suf"][ids[:, 2]],
                            p["bi_fmt"][ids[:, 3]]], axis=1)
        for c in range(self.camadas):
            ida = self._lstm(x, "bi_lstm%df" % c)
            volta = self._lstm(x[::-1], "bi_lstm%dr" % c)[::-1]
            x = np.concatenate([ida, volta], axis=1)
        h = x

        def mlp(nome):
            z = np.maximum(0, h @ p["bi_%s_W1" % nome].T + p["bi_%s_b1" % nome])
            return z @ p["bi_%s_W2" % nome].T + p["bi_%s_b2" % nome]

        def lin(nome):
            return np.maximum(0, h @ p["bi_%s_W" % nome].T + p["bi_%s_b" % nome])

        ad, ac = lin("arco_dep"), lin("arco_cab")
        arco = ad @ p["bi_U_arco"] @ ac.T + (ac @ p["bi_u_arco"])[None, :]
        um = np.ones((len(h), 1), np.float32)
        rd = np.concatenate([lin("rot_dep"), um], axis=1)
        rc = np.concatenate([lin("rot_cab"), um], axis=1)
        return {"arco": arco, "classe": mlp("cls"), "lema": mlp("lem"), "rd": rd, "rc": rc}

    def analisar_formas(self, formas):
        np = self.np
        if not formas:
            return []
        s = self.pontuacoes(formas)
        n = len(formas)
        arco = s["arco"].astype(np.float64)
        arco = arco - arco.max(1, keepdims=True)
        arco = arco - np.log(np.exp(arco).sum(1, keepdims=True))
        pais = arvore_maxima(arco, np)
        saida = []
        for i in range(1, n + 1):
            pai = int(pais[i])
            rot = np.einsum("d,lde,e->l", s["rd"][i], self.p["bi_U_rot"], s["rc"][pai])
            classe = self.classes[int(s["classe"][i].argmax())]
            forma = formas[i - 1]
            lema = (forma if classe == "PROPN" else
                    self.lemas_fixos.get(forma.lower() + "\t" + classe) or
                    aplicar_regra_lema(forma, self.regras[int(s["lema"][i].argmax())]))
            saida.append(Palavra(i, forma, lema, classe, pai, self.ligacoes[int(rot.argmax())]))
        return saida


def _ciclo(pais):
    n = len(pais)
    cor = [0] * n
    for inicio in range(1, n):
        caminho, x = [], inicio
        while x > 0 and cor[x] == 0:
            cor[x] = inicio
            caminho.append(x)
            x = pais[x]
        if x > 0 and cor[x] == inicio:
            return caminho[caminho.index(x):]
        for y in caminho:
            cor[y] = -1
    return None


def _cle(S, np):
    """Chu-Liu-Edmonds: S[dependente, cabeça], nó 0 é a raiz."""
    n = S.shape[0]
    S = S.copy()
    np.fill_diagonal(S, -np.inf)
    S[0, :] = -np.inf
    pais = S.argmax(1)
    pais[0] = -1
    ciclo = _ciclo(list(pais))
    if not ciclo:
        return pais
    C = set(ciclo)
    fora = [i for i in range(n) if i not in C]
    idx = {v: i for i, v in enumerate(fora)}
    c = len(fora)
    T = np.full((c + 1, c + 1), -np.inf)
    T[:c, :c] = S[np.ix_(fora, fora)]
    pont_ciclo = sum(S[d, pais[d]] for d in ciclo)
    melhor_cab, melhor_dep = {}, {}
    for d in fora:
        h = max(ciclo, key=lambda h: S[d, h])
        T[idx[d], c] = S[d, h]
        melhor_cab[d] = h
    for h in fora:
        d = max(ciclo, key=lambda d: S[d, h] - S[d, pais[d]])
        T[c, idx[h]] = S[d, h] - S[d, pais[d]] + pont_ciclo
        melhor_dep[h] = d
    sub = _cle(T, np)
    resultado = pais.copy()
    for d in fora[1:]:
        h = sub[idx[d]]
        resultado[d] = fora[h] if h != c else melhor_cab[d]
    hc = fora[sub[c]]
    resultado[melhor_dep[hc]] = hc
    return resultado


def arvore_maxima(S, np):
    """Árvore de maior pontuação com uma única palavra ligada à raiz."""
    pais = _cle(S, np)
    filhos_raiz = [d for d in range(1, len(pais)) if pais[d] == 0]
    if len(filhos_raiz) <= 1:
        return pais
    melhor, melhor_pont = None, -np.inf
    for r in filhos_raiz:
        T = S.copy()
        for d in range(1, len(pais)):
            if d != r:
                T[d, 0] = -np.inf
        cand = _cle(T, np)
        pont = sum(S[d, cand[d]] for d in range(1, len(cand)))
        if pont > melhor_pont:
            melhor, melhor_pont = cand, pont
    return melhor


_UNICO = []


def analisador():
    if not _UNICO:
        _UNICO.append(AnalisadorFrases())
    return _UNICO[0]


NOMES_LIGACAO = {
    "nsubj": "sujeito", "nsubj:pass": "sujeito (passiva)", "obj": "objeto", "iobj": "objeto indireto",
    "obl": "complemento (lugar, tempo, modo…)", "obl:agent": "agente da passiva", "root": "núcleo da frase",
    "det": "artigo/determinante", "case": "preposição", "amod": "adjetivo", "nmod": "complemento do nome",
    "advmod": "advérbio", "mark": "conectivo da oração", "advcl": "oração adverbial (causa, tempo…)",
    "xcomp": "complemento verbal", "ccomp": "oração objeto", "conj": "coordenação", "cc": "conjunção",
    "cop": "verbo de ligação", "aux": "auxiliar", "aux:pass": "auxiliar da passiva", "punct": "pontuação",
    "acl": "oração que modifica o nome", "acl:relcl": "oração relativa", "nummod": "número",
    "appos": "aposto", "flat:name": "parte do nome", "expl": "pronome se", "fixed": "expressão fixa",
}
NOMES_CLASSE = {
    "NOUN": "substantivo", "VERB": "verbo", "AUX": "verbo auxiliar", "DET": "artigo/determinante",
    "ADP": "preposição", "ADJ": "adjetivo", "ADV": "advérbio", "PRON": "pronome", "PROPN": "nome próprio",
    "SCONJ": "conjunção subordinativa", "CCONJ": "conjunção coordenativa", "NUM": "número",
    "PUNCT": "pontuação", "SYM": "símbolo", "INTJ": "interjeição", "X": "outro", "PART": "partícula",
}


def explicar(texto, analisador_=None):
    """Texto legível: cada palavra, sua classe e de quem depende."""
    a = analisador_ or analisador()
    if not a.disponivel:
        return "Analisador desligado (%s)." % a.motivo
    palavras = a.analisar(texto)
    linhas = []
    for p in palavras:
        if p.ligacao == "punct":
            continue
        papel = NOMES_LIGACAO.get(p.ligacao, p.ligacao)
        if p.pai == 0:
            papel = "núcleo da frase"
        else:
            papel += " de “%s”" % palavras[p.pai - 1].forma
        linhas.append("%s — %s (lema “%s”): %s" % (p.forma, NOMES_CLASSE.get(p.classe, p.classe), p.lema, papel))
    return "\n".join(linhas)


if __name__ == "__main__":
    import sys
    print(explicar(" ".join(sys.argv[1:]) or "A menina abriu o guarda-chuva porque começou a chover."))
