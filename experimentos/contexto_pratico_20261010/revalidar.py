"""Revalida apenas saídas afetadas pela revisão final, sem mudar entradas/juiz."""
import copy
import hashlib
import json
import sys
import threading
import urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent.parent
sys.path.insert(0,str(ROOT))
from web_local import criar_servidor
from avaliar import pontuar
s=json.loads((H/'sondas.json').read_text())['sessoes']
f=H/'final_http.json';original=json.loads(f.read_text());(H/'antes_revalidacao_final_http.json').write_bytes(f.read_bytes())
servidor=criar_servidor(port=0);threading.Thread(target=servidor.serve_forever,daemon=True).start()
url='http://127.0.0.1:%s/api/chat'%servidor.server_address[1]
prova={'motivo':'Após a última revisão, amanhã usa local da sua horta em vez de assumir terraço. A forma singular só afeta contraexemplo novo dos contratos. Entradas, critérios e pesos inalterados.',
       'runtime_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('orientacao_pratica.py','dialogo_situado.py')},'resultados':[]}
try:
    for sid,i in [('pratica_horta_condicoes',7),('pratica_horta_condicoes',9)]:
        sessao=next(x for x in s if x['id']==sid);texto=sessao['turnos'][i]
        req=urllib.request.Request(url,data=json.dumps({'message':texto,'history':sessao['turnos'][:i]}).encode(),headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req,timeout=90) as r:resp=json.load(r)
        row={'usuario':texto,'resposta':resp};next(x for x in original['sessoes'] if x['id']==sid)['resultados'][i]=row
        prova['resultados'].append({'sessao':sid,'turno':i+1,**row})
    original['revalidacao_final']=copy.deepcopy(prova)
    metricas=pontuar(original);assert metricas['corretos']==40 and metricas['desvios']==0
    f.write_text(json.dumps(original,ensure_ascii=False,indent=2)+'\n')
    (H/'final_http_metricas.json').write_text(json.dumps(metricas,ensure_ascii=False,indent=2)+'\n')
    (H/'revalidacao_final_http.json').write_text(json.dumps(prova,ensure_ascii=False,indent=2)+'\n')
    print('40/40 HTTP, duas saídas finais revalidadas; entradas e critérios preservados.')
finally:servidor.shutdown();servidor.server_close()
