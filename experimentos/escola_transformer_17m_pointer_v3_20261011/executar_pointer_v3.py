#!/usr/bin/env python3
"""Executa a V3 corrigindo apenas a localização de spans ByteLevel.

O tokenizador BPE diferencia um valor isolado de sua ocorrência depois de um
espaço. O treinador original procurava só a primeira forma. Este wrapper
aceita ambas sem alterar currículo, holdout, hiperparâmetros ou objetivos.
"""
import treinar_pointer as base


def achar_valor(tokenizer, fonte, valor):
    candidatos=[]
    for texto in (valor, " "+valor):
        ids=base.cod(tokenizer,texto)
        p=base.achar_subseq(fonte,ids)
        if p>=0: candidatos.append(p)
    return max(candidatos) if candidatos else -1


def preparar(tokenizer, ex, contexto):
    fim=tokenizer.token_to_id("<fim>")
    resp=base.cod(tokenizer,ex["resposta"])+[fim]
    fonte,usado,total=base.fonte_compacta(tokenizer,ex,resp,contexto)
    seq=fonte+resp
    if len(seq)-1>contexto:
        raise AssertionError("compactação falhou")
    x,y=seq[:-1],seq[1:]
    pos=len(fonte)-1
    ptr={}
    for nome in base.SLOTS:
        valor=ex.get("slots",{}).get(nome,"")
        p=achar_valor(tokenizer,fonte,valor)
        if p<0:
            raise ValueError(f"{ex['id']}: slot {nome}={valor!r} sumiu da fonte compactada")
        ptr[nome]=p
    return {"id":ex["id"],"x":x,"y":[-100]*pos+y[pos:],"pos":pos,
            "primeiro":resp[0],"fonte":fonte,"operacao":ex["operacao"],
            "resposta":ex["resposta"],"ex":ex,"ptr":ptr,
            "hist_usado":usado,"hist_total":total}


base.preparar=preparar

if __name__=="__main__":
    base.main()
