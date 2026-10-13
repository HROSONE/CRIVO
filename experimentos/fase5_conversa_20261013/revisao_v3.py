"""Revisão completa das falas e respostas, antes da v3 (13/10/2026).

O criador pediu uma revisão de todas as situações antes de gastar GPU. Cada situação foi lida
inteira: todas as falas de todas as fontes (v1, Grok, GPT, contraexemplos e amostras das compostas
da v2) e todas as respostas. As decisões estão em revisao/decisoes_*.json, cada uma com o motivo, e
foram conferidas pelo assistente antes de entrar:

- mover: a fala é de outra situação, cujas respostas servem;
- tirar: ambígua entre situações com respostas incompatíveis, sentido errado, quebrada, ou
  nenhuma resposta serve;
- so_treino: aceitável para treinar, estranha demais para teste;
- corrigir: erro de digitação que muda o sentido.
- evitar_no_treino (respostas): a resposta continua valendo como "da situação" na medida de
  sentido, mas não é usada como alvo de treino, porque não serve para boa parte das falas
  (por exemplo, "qual o nome dele?" para quem disse "tenho duas gatas");
- novas_respostas: respostas que entram na situação. Elas são acrescentadas aqui e também em
  sentido.py, para a medida reconhecer.

Falas de testes congelados (v1, v2, Grok) não mudam; os problemas delas ficam registrados no
relatório (`congelada: true`).
"""
import json
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PASTA = AQUI / "revisao"


def _norm(t):
    return " ".join(unicodedata.normalize("NFC", t).strip().casefold().split())


def carregar():
    falas, evitar, novas, padroes = [], [], [], []
    for p in sorted(PASTA.glob("decisoes_*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        falas += d.get("falas", [])
        evitar += d.get("respostas", [])
        novas += d.get("novas_respostas", [])
        padroes += d.get("padroes_v2", [])
    return falas, evitar, novas, padroes


FALAS, EVITAR, NOVAS, PADROES = carregar()


def acoes_por_fala(chave):
    """→ {(situação, chave da fala): decisão}."""
    return {(d["situacao"], chave(d["fala"])): d for d in FALAS}


def acrescentar_respostas(S):
    """Novas respostas aprovadas na revisão (usado no gerador e na medida de sentido)."""
    for d in NOVAS:
        if d["situacao"] in S and d["resposta"] not in S[d["situacao"]]["c"]:
            S[d["situacao"]]["c"].append(d["resposta"])


def respostas_para_treino(S):
    """Cópia das respostas sem as marcadas para evitar no treino (só no gerador)."""
    tirar = {(d["situacao"], _norm(d["resposta"])) for d in EVITAR}
    saida = {}
    for nome, c in S.items():
        boas = [r for r in c["c"] if (nome, _norm(r)) not in tirar]
        saida[nome] = boas or list(c["c"])
    return saida


def aplicar(formas, chave, situacoes_validas, congeladas=False):
    """formas: {situação: {"treino": [...], "blind": [...]}} → nova estrutura revisada.

    Com congeladas=True, o blind não muda (teste antigo) e só o treino recebe as decisões.
    """
    acoes = acoes_por_fala(chave)
    out = {}
    def por(nome):
        return out.setdefault(nome, {"treino": [], "blind": []})
    for nome, d in formas.items():
        for parte in ("treino", "blind"):
            for f in d.get(parte, []):
                a = acoes.get((nome, chave(f)))
                if a is None or (congeladas and parte == "blind"):
                    por(nome)[parte].append(f)
                    continue
                acao = a["acao"]
                if acao == "tirar":
                    continue
                if acao == "corrigir":
                    por(nome)[parte].append(a.get("correcao") or f)
                elif acao == "mover" and a.get("para") in situacoes_validas:
                    por(a["para"])[parte].append(f)
                elif acao == "so_treino":
                    por(nome)["treino"].append(f)
                else:
                    por(nome)[parte].append(f)
    return out


# Padrões das frases compostas da v2 (formas_v2.py) que montam frase quebrada ou de outro
# sentido. Saem do TREINO; o blind da v2 é congelado e fica como está.
import re as _re

FILTROS_V2 = {
    "insulto": [r"\bruim\b(?<!você é ruim)(?<!vc é ruim)", r"^(?!.*\b(você|vc|seu)\b)"],
    "voce_confunde": [r"se perde (as coisas|tudo|o que eu falo)",
                      r"entende tudo errado (as coisas|tudo|muito|demais|o que eu falo)",
                      r"viaja (tudo|as coisas|o que eu falo)"],
    "despedida": [r"\b(ir|indo) aí\b", r"^valeu, até\b"],
    "despedida_rude": [r"^fui (?!.*\btchau\b)"],
    "nunca_ensinaram": [r" nada\?$"],
    "fale_palavra": [r"\bme me\b"],
    "jogo_conta": [r"\btoc(o|ar)\b"],
    "dificil_falar": [r"(com você|contigo) demais", r"tá difícil te entender", r"falar com você é chato"],
    "de_outro_jeito": [r"^ainda (?!não)", r"(explica|fala|como assim|cinco anos)\b.*\b(nada|direito)$",
                       r"(entendi|captei|ficou claro|nada|direito)\?$"],
    "quem_e": [r"^me diz: (se apresenta|fala de você)"],
    "seja_breve": [r"por favor.*por favor", r"^(por favor, )?(ser|resumir|falar|responder|ir|encurtar)\b"],
    "nao_consegue": [r"me lembrar amanhã (agora|pra mim)", r"^(por favor, )?(pesquisar|abrir|tocar|me lembrar|ligar|mandar|"
                     r"olhar|ver|pedir|ler|acessar|baixar)\b"],
    "risada": [r"\bburro\b"],
    "cansado": [r"vou (deitar|cochilar)"],
    "nao_entendeu_queixa": [r"(disse|falei) de novo$", r"disse\?$"],
    "estou_mal": [r"\b(cansad|esgotad|ansios|estressad|sozinh)"],
    "o_que_faz": [r"^me diz (você|pra que|como|quais|no que)"],
}
_FILTROS = {s: [_re.compile(p, _re.I) for p in ps] for s, ps in FILTROS_V2.items()}


def filtrar_v2(situacao, falas):
    fs = _FILTROS.get(situacao)
    if not fs:
        return list(falas), 0
    boas = [f for f in falas if not any(rx.search(f.strip()) for rx in fs)]
    return boas, len(falas) - len(boas)
