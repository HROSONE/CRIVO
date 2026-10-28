"""Correção de rótulos das falas do professor v7 (27/10/2026, v7e).

As 13.192 falas do professor (Qwen/Qwen3-32B-AWQ, Apache 2.0; modelo de terceiros, não são humanas) foram aprovadas
pela conferência do próprio professor. Lidas uma a uma pelo assistente de programação (Claude), junto com a resposta que
cada situação ensina, as 6.838 que sobraram no v7c depois dos filtros (treino, dev e blind_v6), 601 ficaram com rótulo
errado ou duvidoso: a pessoa conta algo dela numa situação em que a resposta é sobre o CRIVO ("Me cansa muito quando…"
em nao_gosta), pedido de assunto específico ensinado a receber resposta genérica ("você sabe falar sobre como nasce
uma montanha" em o_que_faz), memória que não existe ("Você lembra que eu te disse que tenho um cachorro chamado Ralf?"
→ "Nesta conversa eu lembro, sim"), sim falso ("Tu não é um chatbot desses do Google?" → "Sou, sim"), o texto do
pedido ao professor vazando ("…feita do zero, sem cópias…"), resposta do CRIVO como fala da pessoa, conteúdo adulto,
preconceito e falas sem sentido. Duas eram falas de risco rotuladas como insulto ("Não vejo como seguir com isso",
"não me aguento mais"); o crise.py passou a pegar a segunda.

O texto das falas do professor não entra no repositório (como o arquivo do professor): CORRECOES guarda só o sha256 de
"situação<TAB>fala" (situação sem o prefixo "cena:", como no arquivo do professor). A lista legível, com as falas,
fica ao lado do arquivo do professor (`correcoes_professor_v7_legivel.csv`).

Decisões: "fora" (sai) ou "->situação" (muda de rótulo; passa pelos mesmos filtros que as outras falas). A revisão é
do assistente, não humana nem cega; o critério foi a resposta da situação servir ou não para a fala.
"""
import hashlib
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ARQ = AQUI / "correcoes_professor_v7.json"


def chave(situacao, fala):
    situacao = situacao[5:] if situacao.startswith("cena:") else situacao
    return hashlib.sha256(f"{situacao}\t{fala}".encode("utf-8")).hexdigest()


def carregar():
    return json.loads(ARQ.read_text(encoding="utf-8"))


def aplicar(falas, correcoes=None):
    """falas: linhas do jsonl do professor ({"situacao", "fala", ...}). Devolve (falas corrigidas, relatório).
    Cada fala corrigida leva "situacao_professor" (o rótulo original) e "correcao" (o motivo)."""
    correcoes = carregar()["correcoes"] if correcoes is None else correcoes
    saida, rel, usadas = [], {"fora": 0, "rotulo_trocado": 0, "por_motivo": {}}, set()
    for x in falas:
        k = chave(x["situacao"], x["fala"])
        c = correcoes.get(k)
        if c is None:
            saida.append(x)
            continue
        usadas.add(k)
        rel["por_motivo"][c["motivo"]] = rel["por_motivo"].get(c["motivo"], 0) + 1
        if c["decisao"] == "fora":
            rel["fora"] += 1
            continue
        assert c["decisao"].startswith("->"), c
        rel["rotulo_trocado"] += 1
        saida.append({**x, "situacao": c["decisao"][2:], "situacao_professor": x["situacao"], "correcao": c["motivo"]})
    rel["correcoes_sem_fala"] = len(set(correcoes) - usadas)
    return saida, rel
