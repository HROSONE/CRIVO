"""Leitura da ficha: qual fato da ficha responde à pergunta, e com que evidência.

Quando a pergunta cita um conceito com ficha, a resposta muitas vezes está lá,
mas com outras palavras: "Chove em Titã?" tem resposta num fato com "chuva";
"Quem criou o fato social?" num fato que cita Durkheim. A busca factual exige
que todas as pistas apareçam literalmente no mesmo fato, então recusa.

Esta espécie lê os fatos da ficha e mede, para cada um, evidências de que ele
responde: pistas iguais, sinônimos do léxico curado, relações pergunta→fato
(dados/relacoes_pergunta_fato.json), proximidade nos vetores próprios e
compatibilidade com o tipo de pergunta (quem → nome próprio, quando → data,
quanto → número, por que → linguagem causal). Um modelo logístico, treinado
com perguntas do tutor (scripts/treinar_leitura_ficha.py), combina tudo numa
probabilidade. Sem modelo aprovado, vale uma regra: todas as pistas cobertas.

A resposta é sempre um fato cadastrado, inteiro e com fonte; a leitura só
escolhe qual. Quem decide se ela fala é o árbitro (estado_interno.py).
"""
import json
import math
import re
from collections import namedtuple
from pathlib import Path

from composicao_textual import normalizar

RAIZ = Path(__file__).resolve().parent
CAMINHO_RELACOES = RAIZ / "dados" / "relacoes_pergunta_fato.json"
CAMINHO_MODELO = RAIZ / "artefatos" / "leitura_ficha" / "meta.json"

Leitura = namedtuple("Leitura", "assunto indice prob margem cobertura tipo tracos")

TRACOS = ("vies", "exata", "lexico", "relacao", "vetor", "todas", "nenhuma", "uma_pista",
          "falta_uma", "faltam_duas",
          "quem_nome", "quando_data", "quanto_numero", "onde_lugar", "porque_causa",
          "como_funcionamento", "simnao_negacao", "definicao", "tipo_sem_par")

_TIPOS = (
    ("quem", r"(?:quem|por quem)\b"),
    ("quando", r"(?:quando|em que (?:ano|seculo|epoca|data))\b"),
    ("quanto", r"(?:quant[oa]s?|qual (?:e )?(?:a |o )?(?:tamanho|temperatura|distancia|massa|idade|"
               r"populacao|altura|duracao|velocidade))\b"),
    ("onde", r"(?:onde|em que (?:pais|paises|lugar|regiao|cidade|parte))\b"),
    ("porque", r"(?:por que|porque|pq|qual (?:e )?(?:a )?(?:causa|razao|motivo))\b"),
    ("como", r"(?:como|de que (?:forma|maneira|modo))\b"),
    ("qual", r"(?:qual|quais|que|o que)\b"),
)
# Palavras de moldura que não pedem conteúdo: "o CONCEITO de fato social",
# "a IDEIA de luta de classes", "DÁ pra ver".
GENERICAS = frozenset("""conceito ideia nome coisa coisas gente algo mesmo mesma existe existem tem ter
faz fazer feito pode podem da pra para ainda hoje so tudo isso isto aqui la sobre chama chamado
chamada significa quer dizer acontece aconteceu realmente mesmo verdade""".split())
_NEGACAO = re.compile(r"\b(?:nao|nem|nunca|jamais)\b")
_DATA = re.compile(r"\b(?:\d{3,4}|seculos?|decadas?|anos? \d)\b|\b(?:janeiro|fevereiro|marco|abril|maio|junho|"
                   r"julho|agosto|setembro|outubro|novembro|dezembro)\b|a\.c\.")
_LUGAR = re.compile(r"\b(?:em|no|na|nos|nas|do|da|de)\s+[A-ZÁÉÍÓÚÂÊÔÃÕ]")
_CAUSAL = re.compile(
    r"\b(?:produz\w*|caus\w*|provoc\w*|resulta\w*|explic\w*|contribu\w*|gera|geram|eleva\w*|devido|"
    r"por causa|porque|por isso|por|leva a|levam a|faz com que|torna\w*|mant[eé]m|permit\w*|"
    r"ampli\w*|reduz\w*)\b")


_CACHE = {}


def _vetores():
    """Carregados uma vez por processo: o site cria um Crivo por mensagem."""
    if "vetores" not in _CACHE:
        from vetores_palavras import VetoresPalavras
        _CACHE["vetores"] = VetoresPalavras(exigir_controle=False)
    return _CACHE["vetores"]


def pode_aproximar(tracos, parcial=False):
    """Aproximar também exige todas as pistas cobertas. Uma palavra de conteúdo
    sem apoio na ficha muda o que se pede ("memória INFINITA", "cor de ferrugem
    QUÂNTICA", "dê um EXEMPLO"): ali a recusa é a resposta honesta.

    Com parcial=True (desligado por padrão; docs/estado_interno_20261005.md),
    aproxima com no máximo uma pista sem apoio, desde que outra esteja coberta.
    Entrega muito mais fatos certos, mas também aproxima perguntas com premissa
    falsa, o que quatro testes do projeto proíbem."""
    if parcial:
        return not tracos.get("faltam_duas") and not (tracos.get("falta_uma") and tracos.get("nenhuma"))
    return bool(tracos.get("todas"))


def tipo_pergunta(n):
    """Forma da pergunta: quem, quando, quanto, onde, porque, como, qual ou simnao."""
    for nome, padrao in _TIPOS:
        if re.match(padrao, n) or re.search(r"(?:^|[,.] )" + padrao, n):
            return nome
    return "simnao"


class LeituraFicha:
    def __init__(self, compositor, caminho_modelo=CAMINHO_MODELO):
        self.c = compositor
        try:
            self.relacoes = json.loads(CAMINHO_RELACOES.read_text(encoding="utf-8"))["relacoes"]
        except (OSError, ValueError, KeyError):
            self.relacoes = {}
        # Os vetores próprios não passam no controle de equivalência (aproximam
        # antônimos); aqui são só um traço fraco, com peso aprendido e medido.
        self.vetores = _vetores()
        self.aproximar_parcial = False
        self.pesos = None
        self.limiar = self.limiar_aproximar = None
        try:
            meta = json.loads(Path(caminho_modelo).read_text(encoding="utf-8"))
            if meta.get("controle", {}).get("aprovado") and list(meta["tracos"]) == list(TRACOS):
                self.pesos = [float(p) for p in meta["pesos"]]
                self.limiar = float(meta["limiar"])
                self.limiar_aproximar = float(meta.get("limiar_aproximar", meta["limiar"]))
        except (OSError, ValueError, KeyError, TypeError):
            pass

    @property
    def aprendida(self):
        return self.pesos is not None

    # ------------------------------------------------------------ evidência ---

    def pistas(self, quadro):
        """Pistas de conteúdo: sem as palavras de moldura da pergunta."""
        return [(r, p) for r, p in quadro.pistas if p not in GENERICAS and r not in GENERICAS]

    def _relacao(self, raiz, palavra, raizes_fato):
        alvos = self.relacoes.get(raiz) or self.relacoes.get(palavra)
        if alvos is None:
            for k in (raiz[:5], raiz[:4]):
                if len(k) >= 4 and k in self.relacoes:
                    alvos = self.relacoes[k]
                    break
        return bool(alvos) and any(r.startswith(a) for a in alvos for r in raizes_fato)

    def _vetor(self, palavra, palavras_fato):
        vet = self.vetores
        if vet is None or not vet.disponivel or len(palavra) < 4:
            return 0.0
        return max((vet.similaridade(palavra, w) for w in palavras_fato), default=0.0)

    def tracos(self, quadro, assunto, indice):
        fato = self.c.itens[assunto]["fatos"][indice]
        texto = fato["texto"]
        n_fato = normalizar(texto)
        raizes = self.c._raizes(texto)
        palavras = [w for w in re.findall(r"[a-z]+", n_fato) if len(w) >= 4]
        exata = lexico = relacao = 0
        vetor = 0.0
        cobertas = 0
        pistas = self.pistas(quadro)
        for raiz, palavra in pistas:
            e = self.c._pista_no_fato(raiz, raizes)
            lx = e or any(self.c.lexico.sinonimo(palavra, w) for w in palavras)
            rl = lx or self._relacao(raiz, palavra, raizes)
            exata += e
            lexico += lx
            relacao += rl
            cobertas += rl
            vetor += max(0.0, self._vetor(palavra, palavras))
        k = max(1, len(pistas))
        faltam = len(pistas) - cobertas
        tipo = tipo_pergunta(normalizar(quadro.texto).strip())
        nome = normalizar(self.c.itens[assunto]["nome"])
        # Nome próprio no fato que não seja o próprio assunto nem início de frase.
        nomes = [m.group(0) for m in re.finditer(r"(?<![.!?]\s)(?<!^)\b[A-ZÁÉÍÓÚÂÊÔÃÕ][\wÀ-ú]+", texto)
                 if normalizar(m.group(0)) not in nome]
        compat = {
            "quem": bool(nomes),
            "quando": bool(_DATA.search(n_fato)),
            "quanto": bool(re.search(r"\d", texto)) or bool(re.search(
                r"\b(?:metade|terco|quinto|dobro|milh|bilh|dezenas|centenas)\w*", n_fato)),
            "onde": bool(_LUGAR.search(texto)),
            "porque": bool(_CAUSAL.search(n_fato)),
            "como": fato.get("aspecto") == "funcionamento" or bool(_CAUSAL.search(n_fato)),
        }
        valores = {
            "vies": 1.0,
            "exata": exata / k,
            "lexico": lexico / k,
            "relacao": relacao / k,
            "vetor": vetor / k,
            "todas": 1.0 if pistas and faltam == 0 else 0.0,
            "nenhuma": 1.0 if pistas and cobertas == 0 else 0.0,
            "uma_pista": 1.0 if len(pistas) <= 1 else 0.0,
            "falta_uma": 1.0 if faltam == 1 else 0.0,
            "faltam_duas": 1.0 if faltam >= 2 else 0.0,
            "quem_nome": 1.0 if tipo == "quem" and compat["quem"] else 0.0,
            "quando_data": 1.0 if tipo == "quando" and compat["quando"] else 0.0,
            "quanto_numero": 1.0 if tipo == "quanto" and compat["quanto"] else 0.0,
            "onde_lugar": 1.0 if tipo == "onde" and compat["onde"] else 0.0,
            "porque_causa": 1.0 if tipo == "porque" and compat["porque"] else 0.0,
            "como_funcionamento": 1.0 if tipo == "como" and compat["como"] else 0.0,
            "simnao_negacao": 1.0 if tipo == "simnao" and _NEGACAO.search(n_fato) else 0.0,
            "definicao": 1.0 if indice == 0 else 0.0,
            "tipo_sem_par": 1.0 if tipo in compat and not compat[tipo] else 0.0,
        }
        return [valores[t] for t in TRACOS], cobertas, tipo

    # --------------------------------------------------------------- decisão ---

    def _prob(self, x):
        z = sum(w * v for w, v in zip(self.pesos, x))
        return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))

    def candidatos(self, quadro, assunto=None):
        """[(prob, índice, cobertura, tipo, traços)] para os fatos da ficha."""
        assunto = assunto or quadro.assunto
        saida = []
        for i, _ in enumerate(self.c.itens[assunto]["fatos"]):
            x, cobertas, tipo = self.tracos(quadro, assunto, i)
            if self.aprendida:
                p = self._prob(x)
            else:
                # Regra: todas as pistas cobertas e, havendo tipo, o fato compatível.
                p = 1.0 if x[TRACOS.index("todas")] and not x[TRACOS.index("tipo_sem_par")] else 0.0
            saida.append((p, i, cobertas, tipo, x))
        saida.sort(key=lambda s: (-s[0], s[1]))
        return saida

    def ler(self, quadro, assunto=None):
        """Melhor fato da ficha com a margem para o segundo, ou None."""
        if quadro is None or quadro.recusa:
            return None
        assunto = assunto or quadro.assunto
        if assunto not in self.c.itens:
            return None
        cands = self.candidatos(quadro, assunto)
        if not cands or not self.pistas(quadro) and cands[0][3] not in ("quem", "quando", "onde", "quanto"):
            return None
        p, i, cobertas, tipo, x = cands[0]
        segundo = cands[1][0] if len(cands) > 1 else 0.0
        return Leitura(assunto, i, round(p, 4), round(p - segundo, 4), cobertas, tipo,
                       dict(zip(TRACOS, x)))

    def decisao(self, leitura):
        """'afirmar', 'aproximar' ou None, pela probabilidade da leitura."""
        if leitura is None:
            return None
        # "Qual a temperatura de Netuno?" sem número no fato não é resposta:
        # quem/quando/quanto/onde exigem nome, data, número ou lugar.
        incompativel = leitura.tracos.get("tipo_sem_par")
        # Afirmar exige todas as pistas cobertas: com cobertura parcial, a
        # validação do tutor tinha 78% de acerto (98% com cobertura total).
        if self.afirma(leitura) and not incompativel and leitura.tracos.get("todas"):
            return "afirmar"
        if self.aprendida and leitura.prob >= self.limiar_aproximar and pode_aproximar(leitura.tracos, self.aproximar_parcial):
            return "aproximar"
        return None

    def afirma(self, leitura):
        """A leitura é forte o bastante para responder sem ressalva?"""
        if leitura is None:
            return False
        limiar = self.limiar if self.aprendida else 1.0
        return leitura.prob >= limiar
