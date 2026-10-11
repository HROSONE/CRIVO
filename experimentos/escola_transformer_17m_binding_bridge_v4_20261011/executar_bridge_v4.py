#!/usr/bin/env python3
"""Executa a V4 com localização de slots compatível com tokenização ByteLevel.

O tokenizer do Transformer usa tokens diferentes quando uma entidade aparece
após espaço. O treinador original procurava apenas a codificação isolada. Este
adaptador corrige somente a localização do span; currículo, holdout, perdas,
hiperparâmetros e gates permanecem inalterados.
"""
from __future__ import annotations

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import treinar_bridge as tb  # noqa:E402


def preparar_bytelevel(t, ex, contexto):
    fim=t.token_to_id("<fim>")
    resp=tb.cod(t,ex["resposta"])+[fim]
    fonte,usado,total=tb.fonte_compacta(t,ex,resp,contexto)
    seq=fonte+resp
    if len(seq)-1>contexto:
        raise AssertionError("compactação falhou")
    x,y=seq[:-1],seq[1:]
    pos=len(fonte)-1
    ptr={}
    for nome in tb.SLOTS:
        valor=ex.get("slots",{}).get(nome,"")
        p=-1
        for forma in (valor, " "+valor):
            alvo=tb.cod(t,forma) if valor else []
            p=tb.achar_subseq(fonte,alvo)
            if p>=0:
                break
        if p<0:
            raise ValueError(f"{ex['id']}: slot {nome}={valor!r} sumiu da fonte compactada")
        ptr[nome]=p
    return {"id":ex["id"],"x":x,"y":[-100]*pos+y[pos:],"pos":pos,
        "primeiro":resp[0],"fonte":fonte,"operacao":ex["operacao"],
        "resposta":ex["resposta"],"ex":ex,"ptr":ptr,
        "hist_usado":usado,"hist_total":total}


tb.preparar=preparar_bytelevel

if __name__=="__main__":
    tb.main()
