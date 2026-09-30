"""Acrescenta exemplos revisados a um currículo; não lê sessões do chat.

Cada linha JSON deve declarar revisado=true, id_dialogo, familia, split,
contexto e resposta deslexicalizada. Contextos da mesma conversa e famílias
não podem atravessar treino/validação. A revisão é uma declaração do autor,
não uma avaliação automática da qualidade da resposta.
"""
import argparse
import json
from pathlib import Path

from linguagem_gerativa import ACOES, ESTILOS, SLOTS, ESPECIAIS, VARIANTES, atributos, tokenizar, slots_requeridos


def validar_exemplo(c):
    if not isinstance(c,dict): raise ValueError("Cada exemplo deve ser um objeto JSON")
    if c.get("revisado") is not True:
        raise ValueError("O exemplo precisa ter sido revisado: revisado=true")
    if c.get("split") not in ("treino","validacao"):
        raise ValueError("Split deve ser treino ou validacao")
    for nome in ("id_dialogo","familia"):
        if not isinstance(c.get(nome),str) or not 1<=len(c[nome])<=120:
            raise ValueError("Identificador inválido: "+nome)
    ctx=c.get("contexto",{})
    if not isinstance(ctx,dict): raise ValueError("Contexto deve ser um objeto JSON")
    if ctx.get("acao") not in ACOES or ctx.get("estilo","neutro") not in ESTILOS:
        raise ValueError("Ação/estilo desconhecido")
    if not isinstance(ctx.get("mensagem"),str) or not 1<=len(ctx["mensagem"])<=1200:
        raise ValueError("Mensagem inválida")
    hs=ctx.get("historico",[])
    if not isinstance(hs,list) or len(hs)>3 or any(not isinstance(x,str) or len(x)>1200 for x in hs):
        raise ValueError("Histórico inválido")
    anterior=ctx.get("resposta_anterior","")
    if not isinstance(anterior,str) or len(anterior)>2400:
        raise ValueError("Resposta anterior inválida")
    slots=ctx.get("slots",{})
    if not isinstance(slots,dict) or any(k not in SLOTS or not isinstance(v,str) or not 1<=len(v)<=1200 for k,v in slots.items()):
        raise ValueError("Slots inválidos")
    variante=ctx.get("variante",0)
    if isinstance(variante,bool) or not isinstance(variante,int) or not 0<=variante<VARIANTES:
        raise ValueError("Variante fora dos limites suportados")
    if not isinstance(c.get("resposta"),str): raise ValueError("Resposta inválida")
    ts=tokenizar(c["resposta"])
    if not 6<=len(ts)<128 or ts[-1] not in (".","?","!") or any(t in c["resposta"] for t in ESPECIAIS):
        raise ValueError("Resposta deve ser completa, com 6 a 127 tokens")
    if any(t.startswith("@") and (t[1:] not in slots or t[1:] not in SLOTS) for t in ts):
        raise ValueError("Marcador sem slot declarado")
    requeridos=slots_requeridos(ctx["acao"],slots)
    if any(s not in slots or "@"+s not in ts for s in requeridos):
        raise ValueError("A resposta precisa conservar os argumentos requeridos")
    atributos(ctx)
    return {"split":c["split"],"dialogo":c["id_dialogo"],"familia":c["familia"],
            "contexto":ctx,"resposta":c["resposta"],"origem":"autoral revisada"}


def combinar(curriculo, exemplos):
    if curriculo.get("versao")!=1: raise ValueError("Currículo inválido")
    novos=[validar_exemplo(c) for c in exemplos]
    if not novos: raise ValueError("Nenhum exemplo informado")
    casos=curriculo["exemplos"]+novos
    for chave in ("dialogo","familia"):
        a={c[chave] for c in casos if c["split"]=="treino"}
        b={c[chave] for c in casos if c["split"]=="validacao"}
        if a&b: raise ValueError("Vazamento entre partições por "+chave+": "+", ".join(sorted(a&b)))
    return dict(curriculo,exemplos=casos)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--curriculo",type=Path,default=Path("curriculo_geracao.json"))
    p.add_argument("--dialogos",type=Path,required=True)
    p.add_argument("--saida",type=Path,required=True)
    a=p.parse_args()
    exemplos=[json.loads(l) for l in a.dialogos.read_text(encoding="utf-8").splitlines() if l.strip()]
    r=combinar(json.loads(a.curriculo.read_text(encoding="utf-8")),exemplos)
    a.saida.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Currículo preparado:",len(r["exemplos"]),"exemplos. Nenhum peso ativo foi alterado.")
