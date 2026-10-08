"""Coleta pareada de motor e adaptador web; preserva falhas e texto integral.

Comparações usam valores estruturados, não palavras-chave. Os casos livres
exigem leitura humana e ficam fora do agregado automático de operações.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

PASTA=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser();p.add_argument('--raiz',type=Path,required=True);p.add_argument('--saida',type=Path,required=True);p.add_argument('--web',action='store_true');args=p.parse_args()
    if args.saida.exists():raise SystemExit('Não sobrescrever uma coleta anterior.')
    protocolo=json.loads((PASTA/'protocolo.json').read_text())
    digest=hashlib.sha256((PASTA/'controle.json').read_bytes()).hexdigest()
    assert digest==protocolo['controle_sha256']
    sys.path.insert(0,str(args.raiz.resolve()))
    from crivo import Crivo
    from web_core import responder_web
    cs=json.loads((PASTA/'controle.json').read_text())['sessoes']
    out=dict(controle_sha256=digest,commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=args.raiz,text=True).strip(),
             modo='web' if args.web else 'motor',limite='Controle autoral; não prova conversa livre ou generalização independente.',sessoes=[])
    for c in cs:
        bot=Crivo();hist=[];sess=dict(id=c['id'],turnos=[]);out['sessoes'].append(sess)
        for t in c['turnos']:
            inicio=time.monotonic()
            try:
                if args.web:
                    raw=responder_web(dict(message=t['texto'],history=hist[-10:]))
                    resposta=raw['response'];ident=raw['id'];r=raw.get('conversational_reasoning')
                    geracao=raw.get('generation')
                else:
                    ident,resposta=bot.responder(t['texto'])
                    r=bot.historico[-1].get('raciocinio_conversa') if bot.historico else None
                    geracao=bot.ultima_geracao
                s=dict(esperado=t,id=ident,resposta=resposta,raciocinio=r,geracao=geracao)
                if 'operacao' in t:
                    ok=r is not None and r.get('operacao')==t['operacao']
                    if 'resultado' in t:ok=ok and r.get('resultado')==t['resultado']
                    if 'status' in t:ok=ok and r.get('status')==t['status']
                    ok=ok and bool(r.get('hipotese'))==bool(t.get('hipotese')) if r else False
                    s['correto_estruturado']=bool(ok)
                elif t.get('preservar_factual'):
                    s['correto_estruturado']=ident!='conversa:raciocinio' and 'fotossintese' in ident
                elif t.get('memoria_apagada'):
                    s['correto_estruturado']=r is None and (args.web or not getattr(getattr(bot,'raciocinio_conversa',None),'custos',[]))
            except Exception as exc:
                s=dict(esperado=t,erro=type(exc).__name__,mensagem=str(exc),correto_estruturado=False)
            s['segundos']=round(time.monotonic()-inicio,3);sess['turnos'].append(s);hist.append(t['texto'])
            avaliados=[s for c in out['sessoes'] for s in c['turnos'] if 'correto_estruturado' in s]
            out['resumo']=dict(turnos_avaliados=len(avaliados),corretos=sum(s['correto_estruturado'] for s in avaliados),
                                erros=sum('erro' in s for c in out['sessoes'] for s in c['turnos']))
            args.saida.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
            print(c['id'],len(sess['turnos']),json.dumps(s,ensure_ascii=False),flush=True)
    print(json.dumps(out['resumo']),flush=True)


if __name__=='__main__':main()
