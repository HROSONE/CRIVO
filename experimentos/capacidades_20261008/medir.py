"""Sondas autorais de desenvolvimento da main; não treinam nem ativam pesos."""
import argparse
import copy
import hashlib
import importlib
import json
import sys
import time
from pathlib import Path

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
sys.path[:0] = [str(RAIZ), str(RAIZ / "scripts")]
from crivo import Crivo


def medir_programacao():
    from interpretacao_estruturas import executar
    # Casos reservados aqui só são consultados após a resposta. Não alimentam
    # diagnóstico, síntese, reparo nem seleção de uma segunda tentativa.
    casos = [
        dict(id="executar_aritmetica", acao="interpretar", codigo="return entrada * 3 + 1;", entrada=4, esperado=13),
        dict(id="executar_soma", acao="interpretar", codigo="let total = 0; let i = 0; while (i < entrada.length) { total += entrada[i]; i += 1; } return total;", entrada=[2,5,-1], esperado=6),
        dict(id="executar_objeto", acao="interpretar", codigo="return entrada.preco * entrada.quantidade;", entrada={"preco":7,"quantidade":4}, esperado=28),
        dict(id="executar_string", acao="interpretar", codigo="return entrada.slice(1, 4);", entrada="abcdef", esperado="bcd"),
        dict(id="reparo_operador", acao="diagnosticar", codigo="return entrada - 4;", desenvolvimento=[dict(entrada=0,saida=4),dict(entrada=3,saida=7)], reservados=[dict(entrada=-2,saida=2),dict(entrada=19,saida=23)]),
        dict(id="reparo_incremento", acao="diagnosticar", codigo="let total = 0; let i = 0; while (i < entrada.length) { total += entrada[i]; } return total;", desenvolvimento=[dict(entrada=[1,2],saida=3),dict(entrada=[4],saida=4)], reservados=[dict(entrada=[],saida=0),dict(entrada=[3,-1,8],saida=10)]),
        dict(id="reparo_limite_laco", acao="diagnosticar", codigo="let total = 0; let i = 0; while (i < entrada.length - 1) { total += entrada[i]; i += 1; } return total;", desenvolvimento=[dict(entrada=[2,4],saida=6),dict(entrada=[8],saida=8)], reservados=[dict(entrada=[-3,4,7],saida=8),dict(entrada=[],saida=0)]),
        dict(id="sintese_soma", acao="gerar", desenvolvimento=[dict(entrada=0,saida=5),dict(entrada=3,saida=8)], reservados=[dict(entrada=-2,saida=3),dict(entrada=19,saida=24)]),
        dict(id="sintese_composicao", acao="gerar", desenvolvimento=[dict(entrada=1,saida=4),dict(entrada=3,saida=10)], reservados=[dict(entrada=0,saida=1),dict(entrada=-2,saida=-5),dict(entrada=20,saida=61)]),
        dict(id="sintese_tamanho", acao="gerar", desenvolvimento=[dict(entrada=[],saida=0),dict(entrada=[1,2],saida=2),dict(entrada=[5],saida=1)], reservados=[dict(entrada=[3,4,5,6],saida=4)]),
        dict(id="sintese_maximo", acao="gerar", desenvolvimento=[dict(entrada=[2,3],saida=3),dict(entrada=[7,1],saida=7)], reservados=[dict(entrada=[-2,-5],saida=-2),dict(entrada=[1,8,2],saida=8)]),
        dict(id="limite_host", acao="interpretar", codigo="return process.exit();", entrada=0, limite=True),
    ]
    detalhes=[]
    for caso in casos:
        bot=Crivo()
        pedido={k:copy.deepcopy(v) for k,v in caso.items() if k in ("acao","codigo","entrada","desenvolvimento")}
        ident,texto=bot.responder(json.dumps(pedido,ensure_ascii=False))
        d=copy.deepcopy(bot.motor_codigo.ultimo or {})
        correto=False; adicionais=[]
        if caso.get("limite"):
            correto=ident=="programacao:motor_limite" and not d
        elif caso["acao"]=="interpretar":
            correto="erro" not in d or not d.get("erro")
            correto=bool(d) and correto and d.get("resultado")==caso["esperado"]
        else:
            corpo=d.get("corpo_corrigido") if caso["acao"]=="diagnosticar" else d.get("corpo")
            for c in caso["reservados"]:
                try:
                    entrada=copy.deepcopy(c["entrada"])
                    r=executar(corpo,entrada) if corpo else {}
                    adicionais.append(bool(r) and not r.get("erro") and r.get("resultado")==c["saida"] and entrada==c["entrada"])
                except (ValueError,TypeError):
                    adicionais.append(False)
            correto=bool(d.get("atende_desenvolvimento")) and all(adicionais)
        detalhes.append(dict(id=caso["id"],acao=caso["acao"],passou=correto,response_id=ident,resposta=texto,
                              execucao=d,reservados_corretos=sum(adicionais),reservados_total=len(adicionais)))
    return dict(casos=len(casos),acertos=sum(d["passou"] for d in detalhes),detalhes=detalhes,
                natureza="12 problemas pequenos autorais; desenvolvimento, não benchmark externo; executor próprio, sem APIs do host; reservados só após a única resposta")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("grupo",choices=("mundo","bate_papo","geracao","pedidos","raciocinio","programacao"))
    parser.add_argument("--saida",type=Path,required=True)
    args=parser.parse_args()
    if args.saida.exists():raise SystemExit("Use uma saída nova.")
    inicio=time.monotonic()
    if args.grupo=="programacao":r=medir_programacao()
    elif args.grupo=="mundo":r=importlib.import_module("avaliar_mundo").avaliar()
    elif args.grupo=="pedidos":r=importlib.import_module("avaliar_evolucao_integrada").avaliar()
    elif args.grupo=="raciocinio":r=importlib.import_module("scripts.avaliar_raciocinio_ativo").avaliar()
    else:r=importlib.import_module("avaliar_"+args.grupo).avaliar(Crivo)
    r["tempo_segundos"]=round(time.monotonic()-inicio,3)
    r["fonte_codigo_sha256"]={p:hashlib.sha256((RAIZ/p).read_bytes()).hexdigest() for p in ("crivo.py","estado_interno.py","programacao_chat.py","raciocinio_ativo.py")}
    r["configuracao"]="Crivo padrão, geração própria habilitada; nenhum candidato experimental instalado"
    args.saida.parent.mkdir(parents=True,exist_ok=True)
    args.saida.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary={k:v for k,v in r.items() if k not in ("casos","detalhes","falhas","classificador_isolado") or isinstance(v,int)}
    print(json.dumps(summary,ensure_ascii=False),flush=True)


if __name__=="__main__":main()
