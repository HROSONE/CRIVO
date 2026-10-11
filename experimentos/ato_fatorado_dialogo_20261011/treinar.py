"""Treino fatorado: modalidade + papel semântico, somente durante o treino."""
from __future__ import annotations
import gzip,hashlib,json,math,sys,time
from pathlib import Path
import numpy as np
RAIZ=Path(__file__).resolve().parents[2];DIR=Path(__file__).resolve().parent;sys.path.insert(0,str(RAIZ))
from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq,tokenizar,formas
from treinar_dialogo_seq2seq import _embeddings,_grad_embeddings,_gru,_gru_grad,lote,perda_gradientes,avaliar_perda,avaliar_geracao,checkpoint
from experimentos.ato_auxiliar_dialogo_20261011.treinar_auxiliar import texto,avaliar_bloco,ATOS
OLD=RAIZ/'experimentos/gerador_historico_textual_20261010'; FAT=RAIZ/'experimentos/corpus_fatorial_20261011'; PREV=RAIZ/'experimentos/ato_auxiliar_dialogo_20261011'
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def gz(path,d):path.write_bytes(gzip.compress((json.dumps(d,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode(),mtime=0))
def save(path,d):path.write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def estado(p,b):
 mf=b['mascara_fonte'];B,S=mf.shape;H=p['I'].shape[1];emb=_embeddings(p,b['fonte'],b['chars_fonte'],b['pesos_chars_fonte']);fw=np.zeros((B,S,H),dtype=emb.dtype);bw=np.zeros_like(fw);cs={}
 for nome,out,ordem in (('EF',fw,range(S)),('EB',bw,range(S-1,-1,-1))):
  hc=np.zeros((B,H),dtype=emb.dtype);cs[nome]=[]
  for j in ordem:hc,c=_gru(p,emb[:,j],hc,nome,mf[:,j]);out[:,j]=hc;cs[nome].append((j,c))
 fim=np.concatenate((fw[:,-1],bw[:,0]),1);ini=np.tanh(fim@p['I']+p['bi']);return ini,fim,fw,bw,cs
def softmax_grad(ini,y,W,b):
 valid=np.flatnonzero(y>=0)
 if not len(valid):return 0.,np.zeros_like(ini),np.zeros_like(W),np.zeros_like(b),0,0
 z=ini[valid]@W+b;z-=z.max(1,keepdims=True);pr=np.exp(z);pr/=pr.sum(1,keepdims=True);yy=y[valid];loss=-float(np.log(np.maximum(pr[np.arange(len(yy)),yy],1e-12)).mean());ok=int((pr.argmax(1)==yy).sum());dz=pr;dz[np.arange(len(yy)),yy]-=1;dz/=len(yy);di=np.zeros_like(ini);di[valid]=dz@W.T;return loss,di,ini[valid].T@dz,dz.sum(0),ok,len(yy)
def back_base(p,b,ini,fim,fw,bw,cs,dini):
 g={k:np.zeros_like(v) for k,v in p.items()};di=dini*(1-ini*ini);g['I']+=fim.T@di;g['bi']+=di.sum(0);df=di@p['I'].T;H=p['I'].shape[1];dfw=np.zeros_like(fw);dbw=np.zeros_like(bw);dfw[:,-1]+=df[:,:H];dbw[:,0]+=df[:,H:];demb=np.zeros((b['fonte'].shape[0],b['fonte'].shape[1],p['E'].shape[1]),dtype=p['E'].dtype)
 for nome,ds in (('EF',dfw),('EB',dbw)):
  dh=np.zeros((b['fonte'].shape[0],H),dtype=p['E'].dtype)
  for j,c in reversed(cs[nome]):de,dh=_gru_grad(p,g,dh+ds[:,j],c,nome);demb[:,j]+=de
 _grad_embeddings(g,b['fonte'],b['chars_fonte'],b['pesos_chars_fonte'],demb);return g
def aux_grad(p,b,ym,yr,Wm,bm,Wr,br):
 ini,fim,fw,bw,cs=estado(p,b);lm,dm,gwm,gbm,om,nm=softmax_grad(ini,ym,Wm,bm);lr,dr,gwr,gbr,or_,nr=softmax_grad(ini,yr,Wr,br);g=back_base(p,b,ini,fim,fw,bw,cs,.5*(dm+dr));return .5*(lm+lr),g,.5*gwm,.5*gbm,.5*gwr,.5*gbr,om,nm,or_,nr
def normgrad(g):return math.sqrt(sum(float((x*x).sum()) for x in g.values()))
def accuracy_heads(p,raw,idx,buck,lf,lr,Wm,bm,Wr,br,mapa,mods,roles):
 mi={x:i for i,x in enumerate(mods)};ri={x:i for i,x in enumerate(roles)};xs=[x for x in raw if x.get('operacao') in mapa];tm=tr=okm=okr=0
 for st in range(0,len(xs),64):
  es=xs[st:st+64];bb=lote([texto(x) for x in es],idx,buck,lf,lr);ini,*_=estado(p,bb);pm=(ini@Wm+bm).argmax(1);pr=(ini@Wr+br).argmax(1);ym=np.array([mi[mapa[x['operacao']][0]] for x in es]);yr=np.array([ri[mapa[x['operacao']][1]] for x in es]);okm+=int((pm==ym).sum());okr+=int((pr==yr).sum());tm+=len(es);tr+=len(es)
 return {'modalidade':okm/max(1,tm),'papel':okr/max(1,tr),'exemplos':tm}
def treinar(proto):
 hp=proto['hiperparametros'];corpus=ler_json(RAIZ/proto['treino']['corpus']);xs=corpus['exemplos'] if isinstance(corpus,dict) else corpus;traw=[x for x in xs if x.get('split')=='treino'];vraw=[x for x in xs if x.get('split')=='validacao'];tr=[texto(x) for x in traw];va=[texto(x) for x in vraw]
 ini=ler_json(RAIZ/proto['treino']['inicializacao']);m0=DialogoSeq2Seq(ini);vocab=list(m0.vocabulario);idx={x:i for i,x in enumerate(vocab)};p={k:np.asarray(v,dtype=np.float32).copy() for k,v in ini['pesos'].items()};mods=proto['rotulos']['modalidades'];roles=proto['rotulos']['papeis'];mapa=proto['rotulos']['mapa'];mi={x:i for i,x in enumerate(mods)};ri={x:i for i,x in enumerate(roles)}
 rng=np.random.default_rng(hp['semente']);ra=np.random.default_rng(hp['semente']+17011);H=hp['ocultos'];Wm=ra.normal(0,1/math.sqrt(H),(H,len(mods))).astype(np.float32);bm=np.zeros(len(mods),np.float32);Wr=ra.normal(0,1/math.sqrt(H),(H,len(roles))).astype(np.float32);br=np.zeros(len(roles),np.float32)
 names=['Wm','bm','Wr','br'];aux={'Wm':Wm,'bm':bm,'Wr':Wr,'br':br};mom={k:np.zeros_like(v) for k,v in p.items()};sq={k:np.zeros_like(v) for k,v in p.items()};am={k:np.zeros_like(v) for k,v in aux.items()};av={k:np.zeros_like(v) for k,v in aux.items()};step=0;best=None;bestaux=None;bestv=1e9;bestep=0;stale=0;hist=[];budget=float(proto['treino']['orcamento_gradiente_auxiliar']);ratios=[]
 for ep in range(hp['epocas']):
  order=rng.permutation(len(tr)).tolist();groups=[order[j:j+hp['lote_tamanho']*8] for j in range(0,len(order),hp['lote_tamanho']*8)];batches=[]
  for gr in groups:gr.sort(key=lambda i:len(tokenizar(tr[i]['mensagem']))+sum(len(tokenizar(z['texto'])) for z in tr[i].get('historico',[])));batches += [gr[j:j+hp['lote_tamanho']] for j in range(0,len(gr),hp['lote_tamanho'])]
  rng.shuffle(batches);seqsum=toks=auxsum=lab=okm=okr=0
  samp=min(hp['amostragem'],hp['amostragem']*max(0,ep-hp['aquecimento']+1)/3)
  for pos in batches:
   bb=lote([tr[i] for i in pos],idx,hp['buckets'],hp['limite_fonte'],hp['limite_resposta']);ls,gs=perda_gradientes(p,bb,dropout=hp['dropout'],dropout_tokens=hp['dropout_tokens'],amostragem=samp,rng=rng);ym=np.array([mi[mapa[traw[i]['operacao']][0]] if traw[i].get('operacao') in mapa else -1 for i in pos]);yr=np.array([ri[mapa[traw[i]['operacao']][1]] if traw[i].get('operacao') in mapa else -1 for i in pos]);la,ga,gwm,gbm,gwr,gbr,cm,nm,cr,nr=aux_grad(p,bb,ym,yr,Wm,bm,Wr,br)
   ns=normgrad(gs);na=normgrad(ga);scale=min(1.,budget*ns/max(na,1e-12)) if na else 0.;ratios.append((scale*na)/max(ns,1e-12));
   for k in gs:gs[k]+=scale*ga[k]
   head={'Wm':scale*gwm,'bm':scale*gbm,'Wr':scale*gwr,'br':scale*gbr};n=int(bb['mascara'].sum());seqsum+=ls*n;toks+=n;auxsum+=la*nm;lab+=nm;okm+=cm;okr+=cr;step+=1;norm=math.sqrt(normgrad(gs)**2+sum(float((x*x).sum()) for x in head.values()));clip=min(1.,5/max(norm,1e-12))
   for k in p:
    d=gs[k]*clip;mom[k]=.9*mom[k]+.1*d;sq[k]=.999*sq[k]+.001*d*d;p[k]-=hp['taxa']*(mom[k]/(1-.9**step))/(np.sqrt(sq[k]/(1-.999**step))+1e-8)
    if p[k].ndim==2:p[k]*=1-hp['taxa']*hp['decaimento']
   for k in names:
    d=head[k]*clip;am[k]=.9*am[k]+.1*d;av[k]=.999*av[k]+.001*d*d;aux[k]-=hp['taxa']*(am[k]/(1-.9**step))/(np.sqrt(av[k]/(1-.999**step))+1e-8)
  Wm,bm,Wr,br=aux['Wm'],aux['bm'],aux['Wr'],aux['br'];med=avaliar_perda(p,va,idx,hp['buckets'],hp['limite_fonte'],hp['limite_resposta'],hp['lote_tamanho']);hist.append({'epoca':ep+1,'ce':med['entropia_cruzada'],'aux':auxsum/max(1,lab),'modalidade':okm/max(1,lab),'papel':okr/max(1,lab)});print(hist[-1],flush=True)
  if med['entropia_cruzada']<bestv-1e-5:bestv=med['entropia_cruzada'];bestep=ep+1;best={k:v.copy() for k,v in p.items()};bestaux={k:v.copy() for k,v in aux.items()};stale=0
  else:stale+=1
  if stale*hp['validar_cada']>=hp['paciencia']:break
 p=best;aux=bestaux;Wm,bm,Wr,br=aux['Wm'],aux['bm'],aux['Wr'],aux['br'];acc_tr=accuracy_heads(p,traw,idx,hp['buckets'],hp['limite_fonte'],hp['limite_resposta'],Wm,bm,Wr,br,mapa,mods,roles);acc_dev=accuracy_heads(p,vraw,idx,hp['buckets'],hp['limite_fonte'],hp['limite_resposta'],Wm,bm,Wr,br,mapa,mods,roles);meta={'treino':{'parametros':sum(v.size for v in p.values()),'epoca_selecionada':bestep,'validacao_ce':bestv,'historico':hist,'orcamento_aux':budget,'razao_gradiente_aux_media':float(np.mean(ratios))},'auxiliar':{'modalidades':mods,'papeis':roles,'parametros_temporarios':sum(x.size for x in aux.values()),'serializado':False,'treino':acc_tr,'validacao':acc_dev},'limites':{'fonte_tokens':hp['limite_fonte'],'resposta_tokens':hp['limite_resposta']},'aprovado':False,'ativo_no_chat':False};d=checkpoint(p,vocab,hp['ocultos'],hp['embeddings'],hp['buckets'],hp['limite_fonte'],**meta)
 if sum(np.asarray(v).size for v in d['pesos'].values())!=81433 or set(d['pesos'])!=set(formas(vocab,hp['ocultos'],hp['embeddings'],hp['buckets'])):raise ValueError('Cabeças vazaram para checkpoint')
 return d
def main():
 proto=ler_json(DIR/'protocolo.json');man=ler_json(DIR/'manifesto_holdout.json');hold=DIR/'holdout_novo.json'
 if sha(hold)!=man['holdout_sha256'] or not man['aprovado']:raise ValueError('Holdout congelado inválido')
 start=time.monotonic();cand=treinar(proto);cp=DIR/'checkpoint_fatorado.json.gz';gz(cp,cand)
 old=ler_json(OLD/'corpus_sessoes.json.gz')['exemplos'];old334=[x for x in old if x.get('split')=='validacao' and x.get('grupo')!='sessao_completa'];known=[x for x in old if x.get('split')=='validacao' and x.get('grupo')=='sessao_completa'];fat96=ler_json(FAT/'avaliacao_final_fatorial.json')['exemplos'];prev144=ler_json(PREV/'holdout_novo.json')['exemplos'];new144=ler_json(hold)['exemplos']
 bases={'controle':ler_json(OLD/'checkpoint_sessoes.json.gz'),'fatorial':ler_json(FAT/'checkpoint_fatorial.json.gz'),'aux146':ler_json(PREV/'checkpoint_auxiliar.json.gz'),'fatorado':cand};sets={'old334':(old334,False),'known94':(known,False),'fatorial96':(fat96,True),'holdout146':(prev144,True),'novo144':(new144,True)};ev={m:{s:avaliar_bloco(d,x,o) for s,(x,o) in sets.items()} for m,d in bases.items()};n=ev['fatorado'];g=proto['portao_candidato'];best_ce=min(ev[b]['novo144']['perda']['entropia_cruzada'] for b in ('controle','fatorial','aux146'));best_first=max(ev[b]['novo144']['primeiro_token']['acuracia'] for b in ('controle','fatorial','aux146'));best_ops=max(ev[b]['novo144']['operacoes']['taxa'] for b in ('controle','fatorial','aux146'));ce=n['novo144']['perda']['entropia_cruzada'];first=n['novo144']['primeiro_token']['acuracia'];ops=n['novo144']['operacoes']['taxa'];minop=min(v['taxa'] for v in n['novo144']['operacoes']['por_operacao'].values());criteria={'old334_exatas':n['old334']['geracao']['iguais_ao_alvo']>=g['old334_exatas_min'],'old334_ce':n['old334']['perda']['entropia_cruzada']<=g['old334_ce_max'],'known94_exatas':n['known94']['geracao']['iguais_ao_alvo']>=g['known94_exatas_min'],'known94_ce':n['known94']['perda']['entropia_cruzada']<=g['known94_ce_max'],'fatorial96_ops':n['fatorial96']['operacoes']['taxa']>=g['fatorial96_operacoes_min'],'fatorial96_ce':n['fatorial96']['perda']['entropia_cruzada']<=g['fatorial96_ce_max'],'holdout146_ops':n['holdout146']['operacoes']['taxa']>=g['holdout146_operacoes_min'],'holdout146_ce':n['holdout146']['perda']['entropia_cruzada']<=g['holdout146_ce_max'],'novo_ce':(best_ce-ce)/best_ce>=g['novo_holdout_ce_melhora_relativa_vs_melhor_baseline_min'],'novo_primeiro':first-best_first>=g['novo_holdout_primeiro_token_ganho_vs_melhor_baseline_min'],'novo_ops':ops-best_ops>=g['novo_holdout_operacoes_ganho_vs_melhor_baseline_min'],'novo_total':ops>=g['novo_holdout_operacoes_total_min'],'novo_minop':minop>=g['novo_holdout_operacao_individual_min']};criteria['sucesso']=all(criteria.values());res={'checkpoint_sha256':sha(cp),'holdout_sha256':man['holdout_sha256'],'avaliacoes':ev,'criterio':criteria,'aprovado_experimentalmente':criteria['sucesso'],'ativo_no_chat':False,'segundos':round(time.monotonic()-start,2),'integridade':{'parametros':cand['treino']['parametros'],'aux_serializado':False}};save(DIR/'resultados.json',res);(DIR/'RELATORIO.md').write_text('# Supervisão fatorada — resultado\n\n'+f"- old334: **{n['old334']['geracao']['iguais_ao_alvo']}/334**, CE **{n['old334']['perda']['entropia_cruzada']:.3f}**.\n- known94: **{n['known94']['geracao']['iguais_ao_alvo']}/94**, CE **{n['known94']['perda']['entropia_cruzada']:.3f}**.\n- fatorial96 operações: **{100*n['fatorial96']['operacoes']['taxa']:.1f}%**.\n- holdout146 operações: **{100*n['holdout146']['operacoes']['taxa']:.1f}%**.\n- novo144: CE **{ce:.3f}**, primeiro **{100*first:.1f}%**, operações **{100*ops:.1f}%**, pior ato **{100*minop:.1f}%**.\n- modalidade dev: **{100*cand['auxiliar']['validacao']['modalidade']:.1f}%**; papel dev: **{100*cand['auxiliar']['validacao']['papel']:.1f}%**.\n\n**Sucesso conjunto: {'SIM' if criteria['sucesso'] else 'NÃO'}**.\n\nCheckpoint continua `ativo_no_chat=false`.\n",encoding='utf-8');print(json.dumps({'criterio':criteria,'novo':{'best_ce':best_ce,'ce':ce,'best_first':best_first,'first':first,'best_ops':best_ops,'ops':ops,'minop':minop},'aux':cand['auxiliar']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
