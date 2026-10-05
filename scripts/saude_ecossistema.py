"""Painel de saúde do ecossistema: quem decide, quem acerta e quem erra.

Roda os conjuntos de desenvolvimento e o teste congelado de compreensão, e
conta, por espécie (mecanismo que respondeu), quantas decisões tomou e quantas
estavam certas pelo critério do próprio conjunto. Os conjuntos retidos não
entram aqui: eles só aparecem no agregado das próprias catracas.

Uso: python scripts/saude_ecossistema.py [--saida painel.json]
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

import ecossistema  # noqa: E402


def _ler(caminho):
    return json.loads((RAIZ / caminho).read_text(encoding="utf-8"))


def _assunto_certo(bot, ident, ids):
    """Mesmo critério de scripts/avaliar_entendimento.py; para a compreensão
    neural, que confirma em vez de responder, vale o assunto sugerido."""
    from scripts.avaliar_entendimento import _sugestao, id_resposta
    sugestao = _sugestao(bot)
    if sugestao is not None:
        return sugestao in ids
    temas = getattr(bot.contexto_textual, "temas", ()) or ()
    return id_resposta(ident) in ids or any(t in ids for t in temas)


def casos():
    """(conjunto, histórico, fala, função que diz se a resposta está certa)."""
    from scripts.avaliar_assunto_tom import conferir
    from scripts.avaliar_bateria import classificar
    from scripts.avaliar_entendimento import RECUSAS
    for caso in _ler("avaliacoes/bateria_v1/dev.json")["casos"]:
        yield "bateria_dev", (), caso["p"], (lambda b, i, r, c=caso: classificar(c, i, r) == "acerto")
    for caso in _ler("avaliacoes/assunto_tom_v1/dev.json")["casos"]:
        yield "assunto_tom_dev", tuple(caso.get("historico", ())), caso["fala"], (
            lambda b, i, r, c=caso: not conferir(c, r))
    teste = _ler("avaliacoes/entendimento_v1/teste.json")
    for caso in teste["positivos"]:
        yield "entendimento_positivos", (), caso["p"], (lambda b, i, r, c=caso: _assunto_certo(b, i, c["ids"]))
    for p in teste["negativos"]:
        yield "entendimento_negativos", (), p, (
            lambda b, i, r: i in RECUSAS or i.startswith(("social:", "conversa:", "nocao:", "contexto:")))


def medir():
    from crivo import Crivo
    por_especie = defaultdict(Counter)
    por_conjunto = defaultdict(Counter)
    for conjunto, historico, fala, certo in casos():
        bot = Crivo()
        bot.conversacao.sorteio.seed(20261004)
        for anterior in historico:
            bot.responder(anterior)
        ident, resposta = bot.responder(fala)
        especie = ecossistema.mecanismo_do_turno(bot, fala, ident)
        ok = bool(certo(bot, ident, resposta))
        por_especie[especie]["decisoes"] += 1
        por_especie[especie]["acertos"] += ok
        por_conjunto[conjunto]["casos"] += 1
        por_conjunto[conjunto]["acertos"] += ok
    especies = {}
    for nome, c in sorted(por_especie.items(), key=lambda x: -x[1]["decisoes"]):
        e = ecossistema.especie(nome)
        especies[nome] = {"reino": e.reino if e else "fora_do_mapa", "decisoes": c["decisoes"],
                          "acertos": c["acertos"], "taxa": round(c["acertos"] / c["decisoes"], 3)}
    reinos = Counter()
    for nome, d in especies.items():
        reinos[d["reino"]] += d["decisoes"]
    total = sum(reinos.values())
    return {
        "especies": especies,
        "equilibrio_por_reino": {r: round(n / total, 3) for r, n in reinos.most_common()},
        "conjuntos": {k: dict(v) for k, v in por_conjunto.items()},
        "mapa_integro": not ecossistema.problemas(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida")
    args = parser.parse_args()
    painel = medir()
    print("%-34s %-13s %8s %8s %6s" % ("espécie", "reino", "decisões", "acertos", "taxa"))
    for nome, d in painel["especies"].items():
        print("%-34s %-13s %8d %8d %6.0f%%" % (nome, d["reino"], d["decisoes"], d["acertos"], 100 * d["taxa"]))
    print("\nequilíbrio por reino:", json.dumps(painel["equilibrio_por_reino"], ensure_ascii=False))
    print("conjuntos:", json.dumps(painel["conjuntos"], ensure_ascii=False))
    if args.saida:
        Path(args.saida).write_text(json.dumps(painel, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
