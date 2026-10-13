"""Problemas de lógica para o pensador, com a resposta do professor (raciocinio_ativo.py).

Cada problema é o que o quadro do CRIVO teria depois de entender a conversa:
premissas já estruturadas (fatos e regras "se ... então ...", com "e"/"ou" e
negação) e uma pergunta sobre um literal. Nada de texto: os átomos são números.

O professor é o enumerador de mundos do próprio CRIVO (SistemaPremissas). Ele
dá, para cada problema:

  status       sustentado, refutado, indeterminado ou conflito;
  prova        um subconjunto mínimo de premissas que basta para a conclusão
               (ou para o conflito);
  perguntar    os átomos cuja resposta mais resolve a pergunta quando ela está
               indeterminada (vazio: nenhuma pergunta resolve);
  profundidade quantas regras a prova encadeia.

O rótulo vem sempre do professor, nunca do jeito como o problema foi montado.
No runtime o enumerador recusa mais de 10 átomos; aqui, offline, o professor
sobe esse limite para rotular o conjunto "ood_tamanho" (11 a 16 átomos), que é
justamente onde um pensador aprendido poderia ir além do que o runtime faz —
desde que a prova que ele propõe seja conferida.

Uso: python experimentos/pensador_20261012/gerar_pensador.py   (escreve os
conjuntos congelados e o manifesto ao lado deste arquivo)
"""
import hashlib
import json
import random
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[1]))

from raciocinio_ativo import Literal, Premissa, SistemaPremissas  # noqa: E402

STATUS = ("sustentado", "refutado", "indeterminado", "conflito")


class Professor(SistemaPremissas):
    """O mesmo enumerador, com limites maiores para rotular offline."""
    MAX_ATOMOS = 16
    MAX_PREMISSAS = 24
    MAX_VERIFICACOES = 10 ** 9


def literal(atomo, negativo):
    return Literal("a%d" % atomo, bool(negativo), "a%d" % atomo)


def para_premissas(problema):
    saida = []
    for p in problema["premissas"]:
        ants = tuple(literal(a, n) for a, n in p["a"])
        saida.append(Premissa(ants, literal(*p["c"]), p.get("op", "e"), ""))
    return saida


def rotular(problema):
    """Resposta do professor para o problema."""
    premissas = para_premissas(problema)
    sistema = Professor(premissas)
    alvo = literal(*problema["pergunta"])
    analise = sistema.analisar(alvo)
    status = analise["status"]
    prova = [d["indice"] for d in analise.get("provas", [])]
    rotulo = {"status": status, "prova": sorted(prova), "perguntar": [], "profundidade": 0}
    if status in ("sustentado", "refutado"):
        rotulo["profundidade"] = sum(1 for i in prova if problema["premissas"][i]["a"])
    if status == "indeterminado" and alvo.nome in sistema.bits:
        rotulo["perguntar"] = perguntas_uteis(sistema, alvo)
    return rotulo


def perguntas_uteis(sistema, alvo):
    """Átomos cuja resposta (sim ou não) mais vezes decide a pergunta."""
    melhores, nota_max = [], 0
    for nome, bit in sistema.bits.items():
        if nome == alvo.nome:
            continue
        nota = 0
        for valor in (True, False):
            mundos = [m for m in sistema.mundos if bool(m & bit) == valor]
            vals = {sistema.verdadeiro(m, alvo) for m in mundos}
            if mundos and len(vals) == 1:
                nota += 1
        if nota > nota_max:
            melhores, nota_max = [int(nome[1:])], nota
        elif nota == nota_max and nota > 0:
            melhores.append(int(nome[1:]))
    return sorted(melhores)


def conferir_prova(problema, status, prova):
    """A prova proposta basta para a conclusão e é mínima (nenhuma premissa sobra)?"""
    if status not in ("sustentado", "refutado", "conflito") or not prova:
        return False
    if any(not 0 <= i < len(problema["premissas"]) for i in prova):
        return False
    alvo = literal(*problema["pergunta"])
    todas = para_premissas(problema)

    def basta(indices):
        sub = [todas[i] for i in indices]
        if not sub:
            return False
        s = Professor(sub)
        if status == "conflito":
            return not s.mundos
        if not s.mundos or alvo.nome not in s.bits:
            return False
        objetivo = alvo if status == "sustentado" else alvo.oposto()
        return all(s.verdadeiro(m, objetivo) for m in s.mundos)

    prova = sorted(set(prova))
    return basta(prova) and not any(basta([j for j in prova if j != i]) for i in prova)


# ------------------------------------------------------------- geração --
class Gerador:
    def __init__(self, rng, atomos, premissas, profundidade, distratores):
        self.rng = rng
        self.atomos, self.max_premissas = atomos, premissas
        self.profundidade, self.distratores = profundidade, distratores

    def _novo(self):
        livres = [a for a in range(self.n) if a not in self.usados]
        a = self.rng.choice(livres) if livres else self.rng.randrange(self.n)
        self.usados.add(a)
        return a

    def _derivar(self, lit, d):
        a, neg = lit
        if d == 0:
            self.premissas.append({"a": [], "c": [a, neg]})
            return
        if self.rng.random() < 0.7:
            k = self.rng.choice((1, 1, 2, 2, 3))
            ants = [(self._novo(), self.rng.random() < 0.3) for _ in range(k)]
            self.premissas.append({"a": [list(x) for x in ants], "op": "e", "c": [a, neg]})
            self._derivar(ants[0], d - 1)
            for x in ants[1:]:
                self._derivar(x, 0 if self.rng.random() < 0.7 else min(1, d - 1))
        else:
            ants = [(self._novo(), self.rng.random() < 0.3) for _ in range(2)]
            self.premissas.append({"a": [list(x) for x in ants], "op": "ou", "c": [a, neg]})
            self._derivar(ants[0], d - 1)

    def _distrator(self):
        c = [self.rng.randrange(self.n), self.rng.random() < 0.3]
        if self.rng.random() < 0.3:
            return {"a": [], "c": c}
        k = self.rng.choice((1, 1, 2, 3))
        ants = [[self.rng.randrange(self.n), self.rng.random() < 0.3] for _ in range(k)]
        return {"a": ants, "op": "e" if k == 1 or self.rng.random() < 0.7 else "ou", "c": c}

    def problema(self, desejado):
        rng = self.rng
        self.n = rng.randint(*self.atomos)
        self.usados, self.premissas = set(), []
        alvo = rng.randrange(self.n)
        self.usados.add(alvo)
        d = rng.randint(*self.profundidade)
        pergunta_neg = rng.random() < 0.3
        neg = (not pergunta_neg) if desejado == "refutado" else pergunta_neg
        self._derivar((alvo, neg), d)
        if desejado == "indeterminado":
            fatos = [i for i, p in enumerate(self.premissas) if not p["a"]]
            del self.premissas[rng.choice(fatos)]
        elif desejado == "conflito":
            regras = [p for p in self.premissas if p["a"]] or self.premissas
            p = rng.choice(regras)
            if p["a"] and rng.random() < 0.5:
                a, n = rng.choice(p["a"])
                self.premissas.append({"a": [], "c": [a, not n]})
            else:
                self.premissas.append({"a": [], "c": [p["c"][0], not p["c"][1]]})
        for _ in range(rng.randint(*self.distratores)):
            self.premissas.append(self._distrator())
        self.premissas = self.premissas[:self.max_premissas[1]]
        rng.shuffle(self.premissas)
        # Átomos renumerados 0..n-1 na ordem em que aparecem (só a estrutura importa).
        mapa = {}
        for p in self.premissas:
            for a, _ in p["a"] + [p["c"]]:
                mapa.setdefault(a, len(mapa))
        mapa.setdefault(alvo, len(mapa))
        premissas = [dict(p, a=[[mapa[a], bool(n)] for a, n in p["a"]], c=[mapa[p["c"][0]], bool(p["c"][1])])
                     for p in self.premissas]
        for p in premissas:
            if not p["a"]:
                p.pop("op", None)
        return {"premissas": premissas, "pergunta": [mapa[alvo], pergunta_neg], "atomos": len(mapa)}


CONJUNTOS = {
    # nome: (atomos, premissas, profundidade, distratores, prof. aceita da prova, quantidade, semente)
    "dev": ((3, 8), (2, 12), (1, 3), (0, 4), (0, 3), 1000, 101),
    "blind_iid": ((3, 8), (2, 12), (1, 3), (0, 4), (0, 3), 2000, 202),
    "ood_profundidade": ((6, 10), (6, 16), (4, 6), (0, 3), (4, 6), 1000, 303),
    "ood_tamanho": ((11, 16), (12, 24), (1, 3), (4, 10), (0, 3), 500, 404),
}
PROPORCAO = {"sustentado": 0.3, "refutado": 0.2, "indeterminado": 0.35, "conflito": 0.15}
TREINO = ((3, 8), (2, 12), (1, 3), (0, 4), (0, 3))


def amostrar(rng, cfg, quantidade=None, proibidos=frozenset()):
    """Gera problemas rotulados com as proporções de status e a profundidade pedida."""
    atomos, premissas, prof, distr, prof_ok = cfg[:5]
    g = Gerador(rng, atomos, premissas, prof, distr)
    cotas = {s: round(PROPORCAO[s] * quantidade) for s in STATUS} if quantidade else None
    saida = []
    while quantidade is None or len(saida) < quantidade:
        desejado = rng.choices(STATUS, [PROPORCAO[s] for s in STATUS])[0]
        if cotas is not None and cotas[desejado] <= 0:
            continue
        p = g.problema(desejado)
        if not (atomos[0] <= p["atomos"] <= atomos[1]) or not (premissas[0] <= len(p["premissas"])):
            continue
        r = rotular(p)
        if r["status"] != desejado:
            continue
        if r["status"] in ("sustentado", "refutado") and not prof_ok[0] <= r["profundidade"] <= prof_ok[1]:
            continue
        chave = assinatura(p)
        if chave in proibidos:
            continue
        p.update(r)
        if cotas is not None:
            cotas[desejado] -= 1
        saida.append(p)
        if quantidade is None:
            yield p
    if quantidade is not None:
        yield from saida


def assinatura(p):
    return hashlib.sha256(json.dumps([p["premissas"], p["pergunta"]], sort_keys=True).encode()).hexdigest()[:16]


def principal():
    saida = {}
    for nome, cfg in CONJUNTOS.items():
        rng = random.Random(cfg[6])
        saida[nome] = list(amostrar(rng, cfg, cfg[5]))
        print(nome, len(saida[nome]), flush=True)
    caminho = AQUI / "conjuntos_pensador.json"
    texto = json.dumps(saida, ensure_ascii=False, separators=(",", ":"))
    caminho.write_text(texto, encoding="utf-8")
    proibidos = sorted({assinatura(p) for xs in saida.values() for p in xs})
    (AQUI / "proibidos_treino.json").write_text(json.dumps(proibidos), encoding="utf-8")
    manifesto = {
        "protocolo": "pensador_20261012",
        "conjuntos_sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
        "gerador_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "professor_sha256": hashlib.sha256((AQUI.parents[1] / "raciocinio_ativo.py").read_bytes()).hexdigest(),
        "contagem": {n: {s: sum(p["status"] == s for p in xs) for s in STATUS} for n, xs in saida.items()},
        "profundidade_max": {n: max(p["profundidade"] for p in xs) for n, xs in saida.items()},
        "atomos_max": {n: max(p["atomos"] for p in xs) for n, xs in saida.items()},
        "regra": "rótulos do professor (SistemaPremissas); treino gerado com semente própria e "
                 "sem nenhum problema dos conjuntos congelados",
    }
    (AQUI / "manifesto.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
    print(json.dumps(manifesto["contagem"], ensure_ascii=False))


if __name__ == "__main__":
    principal()
