"""Só este currículo autoral entra no treino; nenhuma sessão da sonda."""
import hashlib,json,sys
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent))
from intencao_sessao import IntencaoSessao,ACOES,assinatura
from intencao_gerativa import atributos,DIMENSAO
from rede_sequencial import RedeSequencial,palavras,normalizar
raw=(HERE/'curriculo_roteador.json').read_bytes()
assert hashlib.sha256(raw).hexdigest()=='ab557ed14d45410c1e1fe279815d33f10c95dc42515d06ea26e214567529da00'
ex=json.loads(raw)['exemplos']
train=[e for e in ex if e['split']=='treino']
valid=[e for e in ex if e['split']=='validacao']
assert not {e['familia'] for e in train}&{e['familia'] for e in valid}
assert not {normalizar(e['texto']) for e in train}&{normalizar(e['texto']) for e in valid}
count=Counter(t for e in train for t,_,_ in palavras(e['texto']))
lexico=sorted(t for t,n in count.items() if n>=12 and t not in ('norali','tereno','vusira'))
r=RedeSequencial(ACOES,DIMENSAO,48,119)
r.treinar([(atributos(e['texto'],e['estado'],lexico),e['acao']) for e in train],epocas=110,semente=119,acelerar=True)
data=dict(assinatura=assinatura(),rede=r.dados(),lexico=lexico,aprovado=True,
          controle='aprovação condicional à validação interna abaixo; não geração livre',
          treino=dict(sha256_curriculo=hashlib.sha256(raw).hexdigest(),semente=119,epocas=110,limiar=.8,margem=.2,arquitetura='RedeSequencial autoral 1168x48x6'))
m=IntencaoSessao(data)
report={}
for label,cases in [('treino',train),('validacao',valid)]:
 qs=[(e,m.analisar(e['texto'],e['estado'])) for e in cases]
 accepted=[(e,q) for e,q in qs if q['aceita']]
 inside=[(e,q) for e,q in qs if e['acao']!='fora']
 report[label]=dict(total=len(qs),acertos=sum(e['acao']==q['acao'] for e,q in qs),
                   aceitos=len(accepted),aceitos_corretos=sum(e['acao']==q['acao'] for e,q in accepted),
                   positivos=len(inside),positivos_aceitos=sum(q['aceita'] for e,q in inside),
                   negativos=sum(e['acao']=='fora' for e,q in qs),negativos_aceitos=sum(q['aceita'] and e['acao']=='fora' for e,q in qs),
                   erros=[dict(texto=e['texto'],estado=e['estado'],esperado=e['acao'],obtido=q) for e,q in qs if e['acao']!=q['acao']])
v=report['validacao']
data['aprovado']=bool(v['aceitos'] and v['aceitos_corretos']/v['aceitos']>=.98 and v['negativos_aceitos']==0 and v['positivos_aceitos']/v['positivos']>=.65)
data['validacao']=v
report['aprovado']=data['aprovado']
(HERE/'avaliacao_roteador.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(HERE/'roteador_rejeitado'/'pesos.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
print(json.dumps({k:{a:b for a,b in v.items() if a!='erros'} for k,v in report.items() if isinstance(v,dict)},ensure_ascii=False))
print('Aprovado:',data['aprovado'])
if not data['aprovado']: raise SystemExit(1)
