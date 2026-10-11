#!/usr/bin/env python3
"""Executor V7: mesma mecânica V4, mudando apenas a diversidade do currículo."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import treinar_bridge as tb

VERSAO = 7
ESPERADOS = {3072: 24576, 512: 4096, "currículo V4 desbalanceado": "currículo V7 desbalanceado"}


def _adaptar_validacao_tamanho():
    """Altera somente constantes da asserção administrativa do currículo.

    O corpo, forward, loss, hiperparâmetros e otimizadores permanecem os do
    arquivo V4 copiado byte a byte. A V7 pré-comprometeu 4096 sessões.
    """
    code = tb.treinar.__code__
    novos = tuple(ESPERADOS.get(c, c) for c in code.co_consts)
    tb.treinar.__code__ = code.replace(co_consts=novos)


def abrir_holdout_v7():
    man = json.loads((tb.AQUI / "manifesto_holdout.json").read_text(encoding="utf-8"))
    if tb.sha(tb.AQUI / "preparar_holdout.py") != man["gerador_sha256"]:
        raise ValueError("gerador do holdout V7 mudou")
    import preparar_holdout as h
    ex = h.gerar()
    por = {op: sum(z["operacao"] == op for z in ex) for op in h.OPERACOES}
    repetidas = len(ex) - len({z["mensagem"] for z in ex})
    variantes = {
        op: {v: sum(z["operacao"] == op and z["variante"] == v for z in ex) for v in range(4)}
        for op in h.OPERACOES
    }
    pacote = {
        "versao": 7,
        "semente": h.SEMENTE,
        "congelado_antes_do_treino": True,
        "auditoria": {
            "aprovado": True,
            "exemplos": 120,
            "familias": len(h.FAMILIAS),
            "mensagens_exatas_repetidas": repetidas,
            "por_operacao": por,
            "variantes_por_operacao": variantes,
        },
        "exemplos": ex,
    }
    if tb.sha_json(pacote) != man["holdout_sha256_canonico"]:
        raise ValueError("hash do holdout V7 mudou")
    if len(ex) != 120 or set(por.values()) != {20} or repetidas != 0:
        raise ValueError("holdout V7 perdeu o balanceamento")
    if any(set(v.values()) != {5} for v in variantes.values()):
        raise ValueError("paráfrases do holdout V7 perderam o balanceamento")
    return ex, man


def _rotular_resultado(saida: Path):
    meta_p = saida / "meta.json"
    res_p = saida / "resultados.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    res = json.loads(res_p.read_text(encoding="utf-8"))
    tecnico = bool(res.get("gates", {}).get("todos", False))
    meta.update({
        "versao": VERSAO,
        "modelo": "transformer_crivo_17m_generalizacao_semantica_v7",
        "ativo_no_chat": False,
        "elegivel_promocao_tecnica": tecnico,
        "elegivel_promocao": False,
        "porta_conversacional": "pendente" if tecnico else "nao_aplicavel",
        "intervencao": "diversidade_semantica_do_curriculo",
    })
    res.update({
        "versao": VERSAO,
        "ativo_no_chat": False,
        "elegivel_promocao_tecnica": tecnico,
        "elegivel_promocao": False,
        "porta_conversacional": "pendente" if tecnico else "nao_aplicavel",
        "intervencao": "diversidade_semantica_do_curriculo",
    })
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    res_p.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    if "--saida" not in sys.argv:
        raise SystemExit("--saida é obrigatório")
    saida = Path(sys.argv[sys.argv.index("--saida") + 1])
    _adaptar_validacao_tamanho()
    tb.abrir_holdout = abrir_holdout_v7
    tb.main()
    _rotular_resultado(saida)


if __name__ == "__main__":
    main()
