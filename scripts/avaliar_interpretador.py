"""Mede se o CRIVO entende a pergunta sobre um conceito, seja qual for o jeito
de perguntar ("oq é X", "explica X pra mim", "tenho uma dúvida sobre X"...).

Caso de conceito: a resposta precisa trazer a definição cadastrada do conceito.
Controle: a resposta NÃO pode ser uma definição (relato, conversa, lógica).

Uso: python scripts/avaliar_interpretador.py [dev|retido|todos] [--detalhes]
(--detalhes só mostra o dev; o retido fica só no agregado.)
"""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PASTA))

from linguagem_conversa import normalizar  # noqa: E402


def definicoes(bot):
    """nome normalizado do conceito -> trecho inicial da definição."""
    saida = {}
    for item in bot.compositor.itens.values():
        trecho = normalizar(item["fatos"][0]["texto"])[:40]
        for nome in [item["nome"]] + list(item.get("aliases", [])):
            saida.setdefault(normalizar(nome), trecho)
    return saida


def avaliar(conjunto, usar_interpretador=True):
    from crivo import Crivo
    arquivo = PASTA / "avaliacoes" / "interpretador_v1" / (conjunto + ".json")
    dados = json.loads(arquivo.read_text(encoding="utf-8"))
    fontes = ("interpretador_perguntas.py", "crivo.py", "linguagem_conversa.py")
    assinatura = {nome: hashlib.sha256((PASTA / nome).read_bytes()).hexdigest() for nome in fontes}
    referencia = Crivo()
    defs = definicoes(referencia)
    ok, tipos, detalhes = 0, Counter(), []
    alvos_corretos, controles_sem_definicao = 0, 0
    ids_por_nome = {}
    for ident, item in referencia.compositor.itens.items():
        for nome in [item["nome"]] + list(item.get("aliases", [])):
            ids_por_nome.setdefault(normalizar(nome), set()).add(ident)
    for caso in dados["casos"]:
        bot = Crivo(usar_interpretador_perguntas=usar_interpretador)
        ident, resposta = bot.responder(caso["fala"])
        n = normalizar(resposta)
        if caso.get("nao_e_definicao"):
            tipo = "controle"
            passou = not ident.startswith("conhecimento:")
            # Diagnóstico adicional: os IDs mundo_* também podem definir.
            controles_sem_definicao += not any(trecho in n for trecho in set(defs.values()))
        else:
            tipo = "conceito"
            trecho = defs.get(normalizar(caso["conceito"]))
            passou = bool(trecho) and trecho in n
            esperados = ids_por_nome.get(normalizar(caso["conceito"]), set())
            temas = set(bot.contexto_textual.temas) if bot.contexto_textual else set()
            alvos_corretos += bool(esperados & temas) and ident not in ("fora", "duvida", "social:nao_entendido")
        ok += passou
        tipos[tipo + (":ok" if passou else ":falha")] += 1
        detalhes.append((caso, ident, resposta, passou))
    if any(hashlib.sha256((PASTA / nome).read_bytes()).hexdigest() != assinatura[nome] for nome in fontes):
        raise RuntimeError("Código alterado durante a avaliação; execute novamente com a implementação congelada.")
    return {"conjunto": conjunto, "casos": len(dados["casos"]), "acertos": ok,
            "por_tipo": dict(sorted(tipos.items())),
            "conceitos_com_alvo_correto": alvos_corretos,
            "controles_sem_definicao": controles_sem_definicao,
            "interpretador_ativo": usar_interpretador,
            "dataset_sha256": hashlib.sha256(arquivo.read_bytes()).hexdigest(),
            "codigo_sha256": assinatura}, detalhes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("alvo", choices=("dev", "retido", "todos"), nargs="?", default="dev")
    parser.add_argument("--detalhes", action="store_true")
    parser.add_argument("--sem-interpretador", action="store_true")
    parser.add_argument("--saida", type=Path)
    args = parser.parse_args()
    alvo = args.alvo
    resumos = []
    for conjunto in (("dev", "retido") if alvo == "todos" else (alvo,)):
        resumo, detalhes = avaliar(conjunto, usar_interpretador=not args.sem_interpretador)
        resumos.append(resumo)
        print(json.dumps(resumo, ensure_ascii=False))
        if args.detalhes and conjunto == "dev":
            for caso, ident, resposta, passou in detalhes:
                if not passou:
                    print("  FALHA", caso["fala"], "->", ident, "|", resposta.replace("\n", " ")[:110])
    if args.saida:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(json.dumps(resumos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
