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
