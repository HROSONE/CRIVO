#!/usr/bin/env python3
"""V6: cabeça neural de cópia por span na saída; V4 inteira permanece congelada."""
from __future__ import annotations
import argparse, hashlib, json, math, random, re, shutil, sys, time, unicodedata
from collections import defaultdict
from pathlib import Path
import torch
from torch import nn
from torch.nn import functional as F
AQUI=Path(__file__).resolve().parent;RAIZ=AQUI.parents[1];sys.path[:0]=[str(RAIZ),str(AQUI)]
from linguagem_profunda import Configuracao,LinguagemProfunda,ESPECIAIS
from curriculo_copy import gerar_treino
import preparar_holdout as hold
V4_COMP='c53981fda15f31fcc22b3355a8eb75551ce85907926960c1776774db0d9f2cda';PESOS_SHA='b152e95776919f7f1bcf522f927a0239c869fccc6b385a0af2b52cf2b77db8fb';PONTE_SHA='1e13a8fd68143f465de510addddb19a6b441a208a80ec3a7b182a3afc5335808';TOK_SHA='6e37a7508def06d31f648a1fb816a67df99e806d450051b611a2406f044dbe7e';HOLD_SHA='e1ab43ecac8133aebaef8491ef45e3d7eb681c18776cdc5650b5eb96f2f198ce'
CONFIG={"vocabulario":8192,"dimensao":384,"camadas":8,"cabecas":8,"contexto":256,"dropout":0.1};SLOTS=('pessoa','objeto','atividade');PASSOS=500;LOTE=8;LR=8e-4;LAMBDA_GATE=.20;LAMBDA_SPAN=.25
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def sha_json(o):return hashlib.sha256(json.dumps(o,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def norm(s):return ' '.join(unicodedata.normalize('NFKC',s).casefold().split())
def cod(t,s):return t.encode(s,add_special_tokens=False).ids
def _nomes(s):return set(re.findall(r'[A-Za-zÀ-ÿ]+-\d+',s))
def fonte_compacta(t,ex,resposta,contexto):
 fim=t.token_to_id('<fim>');papel={'usuario':t.token_to_id('<usuario>'),'assistente':t.token_to_id('<assistente>')};atual=[papel['usuario']]+cod(t,ex['mensagem'])+[fim,papel['assistente']];lim=contexto+1-len(resposta);hist=[z for z in ex['historico'] if z['papel'] in papel];seg=[[papel[z['papel']]]+cod(t,z['texto'])+[fim] for z in hist];gr=[];i=0
 while i<len(hist):
  if i+1<len(hist) and hist[i]['papel']=='usuario' and hist[i+1]['papel']=='assistente':gr.append((i,i+1));i+=2
  else:gr.append((i,));i+=1
 sel={0} if gr else set()
 for gi,g in enumerate(gr):
  if len(_nomes(' '.join(hist[j]['texto'] for j in g)))>=2:sel.add(gi)
 gl=lambda gi:sum(len(seg[j]) for j in gr[gi]);total=lambda s:len(atual)+sum(gl(gi) for gi in s)
 if len(atual)>lim or total(sel)>lim:raise ValueError(ex['id']+': estado essencial excede contexto')
 for gi in reversed(range(len(gr))):
  if gi not in sel and total(sel)+gl(gi)<=lim:sel.add(gi)
 fonte=[]
 for gi,g in enumerate(gr):
  if gi in sel:
   for j in g:fonte+=seg[j]
 return fonte+atual
def achar_subseq(seq,alvo):
 for i in range(len(seq)-len(alvo),-1,-1):
  if seq[i:i+len(alvo)]==alvo:return i
 return -1
def achar_span(t,seq,valor):
 cand=[]
 for forma in (valor,' '+valor):
  ids=cod(t,forma);p=achar_subseq(seq,ids)
  if p>=0:cand.append((p,p+len(ids)))
 return max(cand,key=lambda z:z[0]) if cand else None
def slots_relevantes(op):return {'recordar_pessoa':('pessoa',),'recordar_objeto':('objeto',),'corrigir_pessoa':('pessoa',),'guardar_hipotese':('atividade',),'mensagem_sem_horario':('pessoa','atividade'),'pedir_detalhe':('pessoa',)}[op]
def preparar(t,ex,contexto):
 fim=t.token_to_id('<fim>');resp0=cod(t,ex['resposta']);resp=resp0+[fim];fonte=fonte_compacta(t,ex,resp,contexto);seq=fonte+resp
 if len(seq)-1>contexto:raise AssertionError('contexto')
 x=seq[:-1];pos=len(fonte)-1;spans={}
 for s in SLOTS:
  sp=achar_span(t,fonte,ex['slots'][s])
  if sp is None:raise ValueError(f"{ex['id']}: slot {s} ausente")
  spans[s]=sp
 etiquetas=[None]*len(resp);entidade=[False]*len(resp)
 for s in slots_relevantes(ex['operacao']):
  rr=achar_span(t,resp0,ex['slots'][s])
  if rr is None:continue
  ss,se=spans[s]
  for r in range(rr[0],rr[1]):entidade[r]=True;etiquetas[r]=(ss,se)
 return {'id':ex['id'],'x':x,'fonte':fonte,'pos':pos,'alvos':resp,'resposta_ids':resp0,'resposta':ex['resposta'],'ex':ex,'entidade':entidade,'span_label':etiquetas,'operacao':ex['operacao'],'primeiro':resp[0]}
class PonteBinding(nn.Module):
 def __init__(self,dim=384):super().__init__();self.q=nn.ModuleDict({s:nn.Linear(dim,dim,bias=False) for s in SLOTS});self.gate=nn.Linear(dim,3);self.proj=nn.Linear(dim,dim,bias=False);self.alpha=nn.Parameter(torch.tensor(-1.5))
 def contexto(self,h,pos):
  B,T,D=h.shape;idx=torch.arange(B,device=h.device);base=h[idx,pos];mask=torch.arange(T,device=h.device)[None,:]<=pos[:,None];sums=[]
  for s in SLOTS:
   q=self.q[s](base);sc=(h*q[:,None,:]).sum(-1)/math.sqrt(D);sc=sc.masked_fill(~mask,-1e9);pr=sc.softmax(-1);sums.append(torch.einsum('bt,btd->bd',pr,h))
  gates=torch.sigmoid(self.gate(base));emp=torch.stack(sums,1);mix=(emp*gates[:,:,None]).sum(1)/(gates.sum(1,keepdim=True)+1e-6);return self.proj(mix)*torch.tanh(self.alpha)
 def forward_residual(self,raw,m,pos):
  h=m.norm(raw);delta=self.contexto(h,pos);out=raw.clone()
  for i,p in enumerate(pos.tolist()):out[i,p:]+=delta[i]
  return out
def residuais(m,ids):
 T=ids.shape[1];x=m.embedding(ids)+m.posicao(torch.arange(T,device=ids.device))
 for bl in m.blocos:x=bl(x)
 return x
def forward_v4(m,p,ids,pos):
 raw=residuais(m,ids);raw2=p.forward_residual(raw,m,pos);h=m.norm(raw2);return h,F.linear(h,m.embedding.weight)
class CabecaCopia(nn.Module):
 def __init__(self,dim=384,att=128):
  super().__init__();self.q=nn.Linear(dim,att,bias=False);self.k=nn.Linear(dim,att,bias=False);self.fusao=nn.Sequential(nn.Linear(2*dim,dim),nn.GELU(),nn.LayerNorm(dim));self.porta=nn.Linear(2*dim,1);nn.init.constant_(self.porta.bias,-1.5)
 def passo(self,q,src,src_ids,emb,especiais):
  score=self.q(q)@self.k(src).T/math.sqrt(self.q.out_features);mask=torch.zeros(src_ids.shape[0],dtype=torch.bool,device=src_ids.device)
  for e in especiais:mask|=(src_ids==e)
  score=score.masked_fill(mask[None,:],-1e9);logatt=F.log_softmax(score,-1);ctx=logatt.exp()@src;par=torch.cat([q,ctx],-1);copy_logits=F.linear(self.fusao(par),emb);gate_logit=self.porta(par).squeeze(-1);return copy_logits,gate_logit,logatt
def carregar_v4(pasta,dev):
 from tokenizers import Tokenizer
 p=Path(pasta);assert sha(p/'pesos.pt')==PESOS_SHA;assert sha(p/'ponte_binding.pt')==PONTE_SHA;assert sha(p/'tokenizer.json')==TOK_SHA;e=torch.load(p/'pesos.pt',map_location='cpu',weights_only=True);m=LinguagemProfunda(Configuracao(**CONFIG));m.load_state_dict(e['modelo'],strict=True);m.to(dev).eval();pe=torch.load(p/'ponte_binding.pt',map_location='cpu',weights_only=True);ponte=PonteBinding(384);ponte.load_state_dict(pe['estado'],strict=True);ponte.to(dev).eval();t=Tokenizer.from_file(str(p/'tokenizer.json'));t.encode_special_tokens=True
 for z in list(m.parameters())+list(ponte.parameters()):z.requires_grad=False
 return m,t,ponte
def batch_h(m,p,t,zs,dev):
 pad=t.token_to_id('<pad>');mx=max(len(z['x']) for z in zs);ids=torch.full((len(zs),mx),pad,dtype=torch.long,device=dev);pos=[]
 for i,z in enumerate(zs):ids[i,:len(z['x'])]=torch.tensor(z['x'],device=dev);pos.append(z['pos'])
 pos=torch.tensor(pos,device=dev)
 with torch.no_grad():h,lm=forward_v4(m,p,ids,pos)
 return ids,pos,h,lm
def perdas_batch(head,m,p,t,zs,dev):
 ids,pos,h,lm=batch_h(m,p,t,zs,dev);special=[t.token_to_id(x) for x in ESPECIAIS];nlls=[];glog=[];gtgt=[];spanloss=[]
 for i,z in enumerate(zs):
  n=len(z['alvos']);pp=z['pos'];q=h[i,pp:pp+n];src=h[i,:pp];src_ids=ids[i,:pp];cp,gate,la=head.passo(q,src,src_ids,m.embedding.weight,special);lplm=F.log_softmax(lm[i,pp:pp+n],-1);lpcp=F.log_softmax(cp,-1);pg=torch.sigmoid(gate).clamp(1e-5,1-1e-5);mix=torch.logaddexp(lplm+torch.log1p(-pg)[:,None],lpcp+torch.log(pg)[:,None]);target=torch.tensor(z['alvos'],device=dev);nlls.append(F.nll_loss(mix,target));glog.append(gate);gtgt.append(torch.tensor(z['entidade'],dtype=torch.float32,device=dev))
  for r,sp in enumerate(z['span_label']):
   if sp is not None:a,b=sp;spanloss.append(-torch.logsumexp(la[r,a:b],0))
 nll=torch.stack(nlls).mean();gate_loss=F.binary_cross_entropy_with_logits(torch.cat(glog),torch.cat(gtgt));spl=torch.stack(spanloss).mean() if spanloss else torch.tensor(0.,device=dev);return nll+LAMBDA_GATE*gate_loss+LAMBDA_SPAN*spl,nll,gate_loss,spl
def _errados_nomes(ex,saida,alvo):
 todos=set()
 for h in ex['historico']:todos|=_nomes(h['texto'])
 todos|=_nomes(ex['mensagem']);return any(norm(n) in norm(saida) for n in todos if norm(n)!=norm(alvo))
def pontuar(ex,saida,terminou):
 if not terminou:return False,False
 n=norm(saida);op=ex['operacao'];s=ex['slots'];p,o,a=s['pessoa'],s['objeto'],s['atividade']
 if op=='recordar_pessoa':slot=norm(p) in n;ok=slot and not _errados_nomes(ex,saida,p)
 elif op=='recordar_objeto':slot=norm(o) in n;ok=slot
 elif op=='corrigir_pessoa':slot=norm(p) in n;ok=slot and not _errados_nomes(ex,saida,p)
 elif op=='guardar_hipotese':slot=norm(a) in n;ok=slot and any(q in n for q in ('hipótese','possibilidade','provis','não como confirmação','sem confirmação'))
 elif op=='mensagem_sem_horario':slot=norm(p) in n and norm(a) in n;ok=slot and not _errados_nomes(ex,saida,p) and '?' in saida and not re.search(r'\b\d{1,2}(?::\d{2})?\s*(?:h|hora|horas)\b',n)
 else:slot=norm(p) in n;perg='?' in saida or any(q in n for q in ('qual item','o que','que coisa','que item'));ok=slot and perg and norm(o) not in n and not _errados_nomes(ex,saida,p)
 return bool(slot),bool(ok)
def mix_ultimo(head,m,t,p,ids):
 assist=t.token_to_id('<assistente>');pos=[i for i,v in enumerate(ids) if v==assist][-1];x=torch.tensor([ids],dtype=torch.long,device=m.embedding.weight.device);pt=torch.tensor([pos],device=x.device);h,lm=forward_v4(m,p,x,pt);q=h[:,-1];src=h[0,:pos];src_ids=x[0,:pos];special=[t.token_to_id(z) for z in ESPECIAIS];cp,g,_=head.passo(q,src,src_ids,m.embedding.weight,special);lplm=F.log_softmax(lm[0,-1],-1);lpcp=F.log_softmax(cp[0],-1);pg=torch.sigmoid(g[0]).clamp(1e-5,1-1e-5);return torch.logaddexp(lplm+torch.log1p(-pg),lpcp+torch.log(pg))
@torch.no_grad()
def gerar(m,t,p,head,fonte,max_tokens=48):
 fim=t.token_to_id('<fim>');proib={t.token_to_id(x) for x in ESPECIAIS[:-1]};ids=list(fonte);out=[];ended=False
 for _ in range(max_tokens):
  log=mix_ultimo(head,m,t,p,ids[-m.config.contexto:]).clone()
  for x in proib:log[x]=-float('inf')
  nxt=int(log.argmax())
  if nxt==fim:ended=True;break
  out.append(nxt);ids.append(nxt)
 return out,ended
@torch.no_grad()
def gerar_base(m,t,p,fonte,max_tokens=48):
 fim=t.token_to_id('<fim>');assist=t.token_to_id('<assistente>');proib={t.token_to_id(x) for x in ESPECIAIS[:-1]};ids=list(fonte);out=[];ended=False
 for _ in range(max_tokens):
  win=ids[-m.config.contexto:];x=torch.tensor([win],device=m.embedding.weight.device);pos=torch.tensor([[i for i,v in enumerate(win) if v==assist][-1]],device=x.device);_,lm=forward_v4(m,p,x,pos);log=lm[0,-1].clone()
  for z in proib:log[z]=-float('inf')
  nxt=int(log.argmax())
  if nxt==fim:ended=True;break
  out.append(nxt);ids.append(nxt)
 return out,ended
def avaliar(m,t,p,head,exs,dev):
 zs=[preparar(t,e,m.config.contexto) for e in exs];ce0=ce1=ne0=ne1=0.;n=nn=first=slot=opok=0;por=defaultdict(lambda:[0,0])
 for z in zs:
  ids,pos,h,lm=batch_h(m,p,t,[z],dev);pp=z['pos'];nr=len(z['alvos']);q=h[0,pp:pp+nr];src=h[0,:pp];srcids=ids[0,:pp];special=[t.token_to_id(x) for x in ESPECIAIS];cp,g,_=head.passo(q,src,srcids,m.embedding.weight,special);lplm=F.log_softmax(lm[0,pp:pp+nr],-1);lpcp=F.log_softmax(cp,-1);pg=torch.sigmoid(g).clamp(1e-5,1-1e-5);mix=torch.logaddexp(lplm+torch.log1p(-pg)[:,None],lpcp+torch.log(pg)[:,None]);y=torch.tensor(z['alvos'],device=dev);ix=torch.arange(nr,device=dev);ce0+=float((-lplm[ix,y]).sum());ce1+=float((-mix[ix,y]).sum());n+=nr;non=torch.tensor([not x for x in z['entidade']],device=dev);ne0+=float((-lplm[ix,y])[non].sum());ne1+=float((-mix[ix,y])[non].sum());nn+=int(non.sum());first+=int(int(mix[0].argmax())==z['primeiro']);out,ended=gerar(m,t,p,head,z['fonte']);sl,ok=pontuar(z['ex'],t.decode(out),ended);slot+=sl;opok+=ok;por[z['operacao']][0]+=1;por[z['operacao']][1]+=ok
 baseop=baseslot=0
 for z in zs:
  out,ended=gerar_base(m,t,p,z['fonte']);sl,ok=pontuar(z['ex'],t.decode(out),ended);baseslot+=sl;baseop+=ok
 per={k:v[1]/v[0] for k,v in por.items()};return {'baseline_ce':ce0/n,'ce':ce1/n,'ce_rel':(ce1/n)/(ce0/n),'preservacao':(ne1/nn)/(ne0/nn),'primeiro_token':first/len(zs),'slot':slot/len(zs),'operacao':opok/len(zs),'por_operacao':per,'min_operacao':min(per.values()),'baseline_operacao':baseop/len(zs),'baseline_slot':baseslot/len(zs)}
def validar_holdout():
 xs=hold.gerar();pac={'versao':6,'semente':hold.SEMENTE,'congelado_antes_do_treino':True,'auditoria':{'exemplos':120,'familias':len(hold.FAMILIAS),'mensagens_exatas_repetidas':0,'por_operacao':{op:20 for op in hold.OPERACOES},'templates_por_operacao':{op:{str(i):5 for i in range(4)} for op in hold.OPERACOES}},'exemplos':xs};assert sha_json(pac)==HOLD_SHA;return xs
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--entrada',required=True);ap.add_argument('--saida',required=True);ap.add_argument('--dispositivo',default='cpu');a=ap.parse_args();torch.set_num_threads(2);random.seed(20261011197);torch.manual_seed(20261011197);dev=a.dispositivo;m,t,ponte=carregar_v4(a.entrada,dev);head=CabecaCopia().to(dev);train=[preparar(t,e,m.config.contexto) for e in gerar_treino()];holdex=validar_holdout();opt=torch.optim.AdamW(head.parameters(),lr=LR,weight_decay=1e-3);rng=random.Random(20261011197);start=time.time()
 for step in range(1,PASSOS+1):
  batch=rng.sample(train,LOTE);loss,nll,gl,sp=perdas_batch(head,m,ponte,t,batch,dev);opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(head.parameters(),1.0);opt.step()
  if step==1 or step%50==0:print(json.dumps({'step':step,'loss':float(loss.detach()),'nll':float(nll.detach()),'gate':float(gl.detach()),'span':float(sp.detach()),'elapsed':round(time.time()-start,1)}),flush=True)
 res=avaliar(m,t,ponte,head,holdex,dev);g={'operacao':res['operacao']>=.60,'cada_operacao':res['min_operacao']>=.35,'slot':res['slot']>=.70,'primeiro_token':res['primeiro_token']>=.55,'ce_relativa':res['ce_rel']<=.90,'preservacao':res['preservacao']<=1.05};g['todos']=all(g.values());out=Path(a.saida);out.mkdir(parents=True,exist_ok=True);shutil.copy2(Path(a.entrada)/'pesos.pt',out/'pesos.pt');shutil.copy2(Path(a.entrada)/'ponte_binding.pt',out/'ponte_binding.pt');shutil.copy2(Path(a.entrada)/'tokenizer.json',out/'tokenizer.json');torch.save({'versao':6,'estado':head.state_dict(),'parametros':sum(x.numel() for x in head.parameters())},out/'copy_head.pt');meta={'versao':6,'modelo':'transformer_crivo_17m_span_attentive_copy_v6','origem_v4':V4_COMP,'holdout_sha256':HOLD_SHA,'parametros_copy':sum(x.numel() for x in head.parameters()),'ativo_no_chat':False,'elegivel_promocao':bool(g['todos']),'gates':g};(out/'resultados.json').write_text(json.dumps(res|{'gates':g},ensure_ascii=False,indent=2));(out/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps({'resultado':res,'gates':g,'meta':meta},ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
