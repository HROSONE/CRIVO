"""Replay HTTP com nomes novos; só falas do usuário reconstruem a sessão."""
import hashlib,json,sys,threading,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
sys.path.insert(0,str(ROOT))
from web_local import criar_servidor
casos=[
 ('Melorina é minha irmã.',[],[]),
 ('Renavo é meu primo.',[],[]),
 ('Melorina prefere doce de guabiroba.',[],[]),
 ('Renavo prefere torta de cagaita.',[],[]),
 ('Me sugira uma opção para Melorina.',['Melorina','doce de guabiroba','oferecer'],['torta de cagaita']),
 ('Corrigindo: Melorina prefere mingau de castanha de baru.',[],[]),
 ('Como eu justifico a escolha para Melorina?',['Melorina','mingau de castanha de baru','razão'],['doce de guabiroba','torta de cagaita']),
 ('Me sugira algo que ele goste.',['Renavo','torta de cagaita','oferecer'],['mingau de castanha de baru'])]
server=criar_servidor('127.0.0.1',0)
t=threading.Thread(target=server.serve_forever,daemon=True)
t.start()
history=[]
turnos=[]
try:
 for texto,presentes,ausentes in casos:
  payload=json.dumps(dict(message=texto,history=history),ensure_ascii=False).encode()
  request=urllib.request.Request('http://127.0.0.1:%s/api/chat'%server.server_address[1],data=payload,headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(request,timeout=120) as response:
   status=response.status
   r=json.load(response)
  erros=[v for v in presentes if v not in r['response']]+[v for v in ausentes if v in r['response']]
  turnos.append(dict(entrada=texto,status=status,avaliado=bool(presentes),erros=erros,resultado=r))
  history.append(texto)
  print(status,r['id'],erros,flush=True)
finally:
 server.shutdown();server.server_close();t.join()
avaliados=[t for t in turnos if t['avaliado']]
result=dict(total=len(avaliados),acertos=sum(not t['erros'] and t['status']==200 for t in avaliados),
            realizacoes_neurais=sum(t['resultado']['generation']['usada'] for t in avaliados),
            fontes_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('crivo.py','conversa_sessao.py','realizacao_memoria.py','memoria_sessao.py','web_core.py')},turnos=turnos,
            limite='Replay autoral complementar de oito mensagens; não teste cego de conversa livre.')
(HERE/'manual_http.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('%d/%d consultas, %d realizações neurais'%(result['acertos'],result['total'],result['realizacoes_neurais']))
if result['acertos']!=result['total']:raise SystemExit(1)
