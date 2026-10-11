#!/usr/bin/env python3
"""Escola Cognitiva V3: binding por apontamento treino-only no Transformer 17,43M.

Parte exatamente do checkpoint V1. Durante o treino, três professores
transitórios (pessoa/objeto/atividade) obrigam o estado do fim do prompt a
apontar para a posição do valor vigente no próprio contexto. As cabeças de
apontamento nunca são serializadas e não existem na inferência.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import shutil
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path[:0] = [str(RAIZ), str(AQUI)]

from linguagem_profunda import Configuracao, LinguagemProfunda, ESPECIAIS  # noqa:E402
from curriculo_pointer import gerar_treino  # noqa:E402

SEMENTE = 20261011153
V1_SHA = "849bc4655820f8cd1f445539a1bd0f01959f03ce38145ece460c0fe27568c661"
TOK_SHA = "6e37a7508def06d31f648a1fb816a67df99e806d450051b611a2406f044dbe7e"
PARAMETROS = 17_428_224
CONFIG = {"vocabulario":8192,"dimensao":384,"camadas":8,"cabecas":8,"contexto":256,"dropout":0.1}
WARMUP, PASSOS, LOTE = 100, 900, 16
LR_MODELO, LR_POINTER, LAMBDA_POINTER = 1.5e-5, 1e-4, .12
SLOTS = ("pessoa", "objeto", "atividade")


def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()


def sha_json(o):
    return hashlib.sha256(json.dumps(o,ensure_ascii=False,sort_keys=True,
        separators=(",",":")).encode()).hexdigest()


def carregar_checkpoint(pasta, dispositivo="cpu", exigir_sha=True):
    from tokenizers import Tokenizer
    pasta=Path(pasta); pp=pasta/"pesos.pt"; tp=pasta/"tokenizer.json"
    if exigir_sha and sha(pp)!=V1_SHA: raise ValueError("checkpoint V1 diferente do pré-compromisso")
    if sha(tp)!=TOK_SHA: raise ValueError("tokenizador diferente do pré-compromisso")
    e=torch.load(pp,map_location="cpu",weights_only=True)
    if e.get("config")!=CONFIG: raise ValueError("configuração 17M inesperada")
    m=LinguagemProfunda(Configuracao(**CONFIG)); m.load_state_dict(e["modelo"],strict=True)
    if sum(p.numel() for p in m.parameters())!=PARAMETROS: raise ValueError("contagem de parâmetros inesperada")
    t=Tokenizer.from_file(str(tp)); t.encode_special_tokens=True
    if t.get_vocab_size()!=8192: raise ValueError("vocabulário incompatível")
    return m.to(dispositivo),t,e


def cod(t,texto): return t.encode(texto,add_special_tokens=False).ids


def _nomes(texto):
    return set(re.findall(r"[A-Za-zÀ-ÿ]+-\d+",texto))


def fonte_compacta(t,ex,resposta,contexto):
    """Preserva início, correções e turnos recentes, sem cortar um par ao meio."""
    fim=t.token_to_id("<fim>")
    papel={"usuario":t.token_to_id("<usuario>"),"assistente":t.token_to_id("<assistente>")}
    atual=[papel["usuario"]]+cod(t,ex["mensagem"])+[fim,papel["assistente"]]
    limite=contexto+1-len(resposta)
    hist=[z for z in ex["historico"] if z["papel"] in papel]
    seg=[[papel[z["papel"]]]+cod(t,z["texto"])+[fim] for z in hist]
    grupos=[]; i=0
    while i<len(hist):
        if i+1<len(hist) and hist[i]["papel"]=="usuario" and hist[i+1]["papel"]=="assistente":
            grupos.append((i,i+1)); i+=2
        else:
            grupos.append((i,)); i+=1
    sel={0} if grupos else set()
    for gi,g in enumerate(grupos):
        texto=" ".join(hist[j]["texto"] for j in g)
        if len(_nomes(texto))>=2: sel.add(gi)
    gl=lambda gi:sum(len(seg[j]) for j in grupos[gi])
    total=lambda s:len(atual)+sum(gl(gi) for gi in s)
    if len(atual)>limite or total(sel)>limite:
        raise ValueError(ex["id"]+": estado essencial excede contexto")
    for gi in reversed(range(len(grupos))):
        if gi not in sel and total(sel)+gl(gi)<=limite: sel.add(gi)
    fonte=[]
    for gi,g in enumerate(grupos):
        if gi in sel:
            for j in g: fonte+=seg[j]
    return fonte+atual, sum(len(grupos[gi]) for gi in sel), len(hist)


def achar_subseq(seq,alvo):
    if not alvo or len(alvo)>len(seq): return -1
    for i in range(len(seq)-len(alvo),-1,-1):
        if seq[i:i+len(alvo)]==alvo: return i
    return -1


def preparar(t,ex,contexto):
    fim=t.token_to_id("<fim>"); resp=cod(t,ex["resposta"])+[fim]
    fonte,usado,total=fonte_compacta(t,ex,resp,contexto)
    seq=fonte+resp
    if len(seq)-1>contexto: raise AssertionError("compactação falhou")
    x,y=seq[:-1],seq[1:]; pos=len(fonte)-1
    ptr={}
    for nome in SLOTS:
        valor=ex.get("slots",{}).get(nome,"")
        alvo=cod(t,valor) if valor else []
        p=achar_subseq(fonte,alvo)
        if p<0:
            raise ValueError(f"{ex['id']}: slot {nome}={valor!r} sumiu da fonte compactada")
        ptr[nome]=p
    return {"id":ex["id"],"x":x,"y":[-100]*pos+y[pos:],"pos":pos,"primeiro":resp[0],
      "fonte":fonte,"operacao":ex["operacao"],"resposta":ex["resposta"],"ex":ex,
      "ptr":ptr,"hist_usado":usado,"hist_total":total}


def batch(xs,pad,dev):
    n=max(len(z["x"]) for z in xs); b=len(xs)
    x=torch.full((b,n),pad,dtype=torch.long); y=torch.full_like(x,-100)
    pos=torch.empty(b,dtype=torch.long); ptr={s:torch.empty(b,dtype=torch.long) for s in SLOTS}
    for i,z in enumerate(xs):
        x[i,:len(z["x"])]=torch.tensor(z["x"]); y[i,:len(z["y"])]=torch.tensor(z["y"]); pos[i]=z["pos"]
        for s in SLOTS: ptr[s][i]=z["ptr"][s]
    return x.to(dev),y.to(dev),pos.to(dev),{s:v.to(dev) for s,v in ptr.items()}


def hidden_logits(m,ids,treino_topo=False):
    t=ids.shape[1]
    if treino_topo:
        with torch.no_grad():
            x=m.embedding(ids)+m.posicao(torch.arange(t,device=ids.device))
            for b in m.blocos[:4]: x=b(x)
        for b in m.blocos[4:]: x=b(x)
    else:
        x=m.embedding(ids)+m.posicao(torch.arange(t,device=ids.device))
        for b in m.blocos: x=b(x)
    h=m.norm(x)
    return h,F.linear(h,m.embedding.weight)


class ProfessoresPointer(nn.Module):
    def __init__(self,dim=384):
        super().__init__()
        self.q=nn.ModuleDict({s:nn.Linear(dim,dim,bias=False) for s in SLOTS})

    def perdas(self,h,pos,alvos):
        b,t,d=h.shape
        idx=torch.arange(b,device=h.device)
        base=h[idx,pos]
        mascara=torch.arange(t,device=h.device)[None,:] <= pos[:,None]
        perdas={}; acertos={}
        for s in SLOTS:
            q=self.q[s](base)
            esc=(h*q[:,None,:]).sum(-1)/math.sqrt(d)
            esc=esc.masked_fill(~mascara,-1e9)
            perdas[s]=F.cross_entropy(esc,alvos[s])
            acertos[s]=(esc.argmax(-1)==alvos[s]).float().mean()
        return perdas,acertos


def configurar_modelo(m,treinavel):
    for p in m.parameters(): p.requires_grad=False
    if treinavel:
        for bloco in m.blocos[4:]:
            for p in bloco.parameters(): p.requires_grad=True
        for p in m.norm.parameters(): p.requires_grad=True
        m.train()
        for bloco in m.blocos[:4]: bloco.eval()
    else:
        m.eval()


def _proximo_lote(dados,ordem,cur,rng):
    if cur+LOTE>len(ordem): rng.shuffle(ordem); cur=0
    lote=[dados[i] for i in ordem[cur:cur+LOTE]]
    return lote,cur+LOTE


def treinar(m,t,dev):
    dados=[preparar(t,e,m.config.contexto) for e in gerar_treino()]
    if len(dados)!=3072 or set(Counter(z["operacao"] for z in dados).values())!={512}:
        raise ValueError("currículo V3 desbalanceado")
    torch.manual_seed(SEMENTE+1); prof=ProfessoresPointer().to(dev)
    rng=random.Random(SEMENTE); ordem=list(range(len(dados))); cur=len(ordem)

    configurar_modelo(m,False)
    optp=torch.optim.AdamW(prof.parameters(),lr=LR_POINTER,weight_decay=.01)
    warm=defaultdict(float)
    for passo in range(1,WARMUP+1):
        lote,cur=_proximo_lote(dados,ordem,cur,rng)
        x,_,pos,ptr=batch(lote,t.token_to_id("<pad>"),dev)
        with torch.no_grad(): h,_=hidden_logits(m,x,False)
        perdas,acc=prof.perdas(h,pos,ptr); loss=sum(perdas.values())/len(SLOTS)
        optp.zero_grad(set_to_none=True); loss.backward(); optp.step()
        warm["loss"]+=float(loss)
        for s in SLOTS: warm["acc_"+s]+=float(acc[s])
    print(json.dumps({"fase":"warmup_pointer","passos":WARMUP,
          **{k:round(v/WARMUP,5) for k,v in warm.items()}},ensure_ascii=False),flush=True)

    configurar_modelo(m,True)
    pars_modelo=[p for p in m.parameters() if p.requires_grad]
    opt=torch.optim.AdamW([
        {"params":pars_modelo,"lr":LR_MODELO},
        {"params":list(prof.parameters()),"lr":LR_POINTER},
    ],weight_decay=.01)
    torch.manual_seed(SEMENTE); inicio=time.time(); janela=defaultdict(float)
    for passo in range(1,PASSOS+1):
        lote,cur=_proximo_lote(dados,ordem,cur,rng)
        x,y,pos,ptr=batch(lote,t.token_to_id("<pad>"),dev)
        h,log=hidden_logits(m,x,True)
        lm=F.cross_entropy(log.reshape(-1,8192),y.reshape(-1),ignore_index=-100)
        perdas,acc=prof.perdas(h,pos,ptr); pp=sum(perdas.values())/len(SLOTS)
        loss=lm+LAMBDA_POINTER*pp
        opt.zero_grad(set_to_none=True); loss.backward()
        gn=torch.nn.utils.clip_grad_norm_(pars_modelo+list(prof.parameters()),1.0); opt.step()
        janela["loss"]+=float(loss); janela["lm"]+=float(lm); janela["pointer"]+=float(pp); janela["grad"]+=float(gn)
        for s in SLOTS: janela["acc_"+s]+=float(acc[s])
        if passo%100==0:
            print(json.dumps({"fase":"conjunto","passo":passo,
              **{k:round(v/100,5) for k,v in janela.items()},"segundos":round(time.time()-inicio,1)},ensure_ascii=False),flush=True)
            janela.clear()
    return prof,{"warmup_pointer":WARMUP,"passos_conjuntos":PASSOS,"lote":LOTE,
      "lr_modelo":LR_MODELO,"lr_pointer":LR_POINTER,"lambda_pointer":LAMBDA_POINTER,
      "treinaveis_modelo":sum(p.numel() for p in m.parameters() if p.requires_grad),
      "aux_parametros":sum(p.numel() for p in prof.parameters()),"segundos":time.time()-inicio}


def abrir_holdout():
    man=json.loads((AQUI/"manifesto_holdout.json").read_text(encoding="utf-8"))
    if sha(AQUI/"preparar_holdout.py")!=man["gerador_sha256"]: raise ValueError("gerador do holdout V3 mudou")
    import preparar_holdout as h
    ex=h.gerar(); por={op:sum(z["operacao"]==op for z in ex) for op in h.OPERACOES}
    repetidas=len(ex)-len({z["mensagem"] for z in ex})
    pacote={"versao":3,"semente":h.SEMENTE,"congelado_antes_do_treino":True,
      "auditoria":{"aprovado":True,"exemplos":120,"familias":len(h.FAMILIAS),
                   "mensagens_exatas_repetidas":repetidas,"por_operacao":por},"exemplos":ex}
    if sha_json(pacote)!=man["holdout_sha256_canonico"]: raise ValueError("hash do holdout V3 mudou")
    return ex,man


def norm(s): return re.sub(r"\s+"," ",unicodedata.normalize("NFKC",s).casefold()).strip()


def _errados_nomes(ex,saida,alvo):
    todos=set()
    for h in ex["historico"]: todos|=_nomes(h["texto"])
    todos|=_nomes(ex["mensagem"])
    return any(norm(n) in norm(saida) for n in todos if norm(n)!=norm(alvo))


def pontuar(ex,saida,terminou):
    if not terminou: return False,False
    n=norm(saida); op=ex["operacao"]; s=ex["slots"]
    pessoa=s["pessoa"]; objeto=s["objeto"]; atividade=s["atividade"]
    if op=="recordar_pessoa":
        slot=norm(pessoa) in n; ok=slot and not _errados_nomes(ex,saida,pessoa)
    elif op=="recordar_objeto":
        slot=norm(objeto) in n; ok=slot
    elif op=="corrigir_pessoa":
        slot=norm(pessoa) in n; ok=slot and not _errados_nomes(ex,saida,pessoa)
    elif op=="guardar_hipotese":
        slot=norm(atividade) in n
        ok=slot and any(q in n for q in ("hipótese","possibilidade","provis","não como confirmação","sem confirmação"))
    elif op=="mensagem_sem_horario":
        slot=norm(pessoa) in n and norm(atividade) in n
        ok=slot and not _errados_nomes(ex,saida,pessoa) and "?" in saida and not re.search(r"\b\d{1,2}(?::\d{2})?\s*(?:h|hora|horas)\b",n)
    else:
        slot=norm(pessoa) in n
        pergunta="?" in saida or any(q in n for q in ("qual item","o que","que coisa","que item"))
        ok=slot and pergunta and norm(objeto) not in n and not _errados_nomes(ex,saida,pessoa)
    return bool(slot),bool(ok)


@torch.no_grad()
def avaliar(m,t,exs,dev,prof=None):
    m.eval(); prep=[preparar(t,e,m.config.contexto) for e in exs]
    ce=nt=first=exact=slotn=opn=0
    por=defaultdict(lambda:{"n":0,"operacao":0,"slot":0,"exata":0})
    pdiag={s:{"n":0,"acertos":0} for s in SLOTS}; det=[]
    fim=t.token_to_id("<fim>"); proib=[t.token_to_id(x) for x in ESPECIAIS[:-1]]
    for z in prep:
        x=torch.tensor([z["x"]],device=dev); y=torch.tensor([z["y"]],device=dev)
        h,log=hidden_logits(m,x,False)
        ce+=float(F.cross_entropy(log.reshape(-1,8192),y.reshape(-1),ignore_index=-100,reduction="sum")); nt+=int((y!=-100).sum())
        first+=int(int(log[0,z["pos"]].argmax())==z["primeiro"])
        if prof is not None:
            pos=torch.tensor([z["pos"]],device=dev); alvos={s:torch.tensor([z["ptr"][s]],device=dev) for s in SLOTS}
            _,acc=prof.perdas(h,pos,alvos)
            for s in SLOTS: pdiag[s]["n"]+=1; pdiag[s]["acertos"]+=int(float(acc[s])>.5)
        ids,terminou=m.gerar(z["fonte"],fim,max_tokens=48,temperatura=0,top_k=0,semente=SEMENTE,proibidos=proib)
        saida=t.decode(ids); exata=norm(saida)==norm(z["resposta"]); sl,ok=pontuar(z["ex"],saida,terminou)
        exact+=exata; slotn+=sl; opn+=ok
        q=por[z["operacao"]]; q["n"]+=1; q["operacao"]+=ok; q["slot"]+=sl; q["exata"]+=exata
        det.append({"id":z["id"],"operacao":z["operacao"],"alvo":z["resposta"],"saida":saida,
          "terminou":terminou,"slot":sl,"operacao_correta":ok,"exata":exata,
          "historico_usado":z["hist_usado"],"historico_total":z["hist_total"]})
    n=len(prep)
    po={k:{**v,"operacao_taxa":v["operacao"]/v["n"],"slot_taxa":v["slot"]/v["n"],"exata_taxa":v["exata"]/v["n"]} for k,v in sorted(por.items())}
    pd={s:{**v,"taxa":v["acertos"]/v["n"] if v["n"] else None} for s,v in pdiag.items()} if prof is not None else None
    return {"n":n,"ce":ce/nt,"primeiro_token":first/n,"exata":exact/n,"slot":slotn/n,"operacao":opn/n,
      "por_operacao":po,"pointer":pd,"detalhes":det}


@torch.no_grad()
def preservacao(m,t,textos,dev):
    m.eval(); doc=t.token_to_id("<documento>"); fim=t.token_to_id("<fim>")
    perda=nt=0
    for texto in textos:
        ids=[doc]+cod(t,texto)+[fim]
        if len(ids)>m.config.contexto: raise ValueError("texto de preservação excede contexto")
        x=torch.tensor([ids[:-1]],device=dev); y=torch.tensor([ids[1:]],device=dev)
        _,log=hidden_logits(m,x,False)
        perda+=float(F.cross_entropy(log.reshape(-1,8192),y.reshape(-1),reduction="sum")); nt+=y.numel()
    return perda/nt


def salvar(m,t,entrada,saida,treino,resultados):
    saida=Path(saida); saida.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(Path(entrada)/"tokenizer.json",saida/"tokenizer.json")
    estado={"versao":1,"modelo":{k:v.detach().cpu() for k,v in m.state_dict().items()},"config":CONFIG,
      "passo":int(torch.load(Path(entrada)/"pesos.pt",map_location="cpu",weights_only=True).get("passo",0))+PASSOS,
      "execucao":{"tokenizer_sha256":TOK_SHA,"semente":SEMENTE,"pesos_externos":False,
        "escola_cognitiva":{"versao":3,"origem_sha256":V1_SHA,"warmup_pointer":WARMUP,"passos":PASSOS,
          "lambda_pointer":LAMBDA_POINTER,"auxiliares_serializados":False,"ativo_no_chat":False}}}
    torch.save(estado,saida/"pesos.pt")
    ck=sha(saida/"pesos.pt")
    meta={"versao":3,"modelo":"transformer_crivo_17m_pointer_v3","checkpoint_sha256":ck,
      "tokenizer_sha256":TOK_SHA,"parametros":PARAMETROS,"ativo_no_chat":False,
      "elegivel_promocao":bool(resultados["gates"]["todos"]),"auxiliares_serializados":False,
      "treino":treino,"resultado_resumo":{k:v for k,v in resultados["candidato"].items() if k!="detalhes"}}
    (saida/"meta.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    (saida/"resultados.json").write_text(json.dumps(resultados,ensure_ascii=False,indent=2),encoding="utf-8")
    return ck


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--entrada",required=True); ap.add_argument("--saida",required=True); ap.add_argument("--dispositivo",default="cpu")
    a=ap.parse_args(); dev=a.dispositivo
    random.seed(SEMENTE); torch.manual_seed(SEMENTE); torch.set_num_threads(2)
    candidato,tok,_=carregar_checkpoint(a.entrada,dev,True)
    prof,info=treinar(candidato,tok,dev)
    hold,man=abrir_holdout()
    base,tokb,_=carregar_checkpoint(a.entrada,dev,True)
    entrada=avaliar(base,tokb,hold,dev,None)
    cand=avaliar(candidato,tok,hold,dev,prof)
    preservados=json.loads((AQUI/"preservacao_portugues.json").read_text(encoding="utf-8"))
    if not preservados.get("congelado_antes_do_treino"): raise ValueError("preservação não congelada")
    p0=preservacao(base,tokb,preservados["textos"],dev); p1=preservacao(candidato,tok,preservados["textos"],dev)
    protocolo=json.loads((AQUI/"protocolo.json").read_text(encoding="utf-8")); g=protocolo["avaliacao"]["promocao"]
    cada=min(v["operacao_taxa"] for v in cand["por_operacao"].values())
    gs={
      "operacao":cand["operacao"]>=g["operacao_min"],
      "cada_operacao":cada>=g["cada_operacao_min"],
      "slot":cand["slot"]>=g["slot_min"],
      "primeiro_token":cand["primeiro_token"]>=g["primeiro_token_min"],
      "ce_relativa":cand["ce"]<=entrada["ce"]*g["ce_relativa_max"],
      "preservacao":p1<=p0*g["preservacao_ce_relativa_max"],
    }
    resultados={"versao":3,"holdout_sha256":man["holdout_sha256_canonico"],"treino":info,
      "entrada_v1":entrada,"candidato":cand,
      "preservacao":{"entrada_ce":p0,"candidato_ce":p1,"relativa":p1/p0},
      "gates":{**gs,"todos":all(gs.values()),"min_operacao":cada},"ativo_no_chat":False}
    ck=salvar(candidato,tok,a.entrada,a.saida,info,resultados)
    resultados["checkpoint_sha256"]=ck
    Path(a.saida,"resultados.json").write_text(json.dumps(resultados,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"checkpoint_sha256":ck,"entrada":{"ce":entrada["ce"],"operacao":entrada["operacao"],"slot":entrada["slot"],"primeiro":entrada["primeiro_token"]},
      "candidato":{"ce":cand["ce"],"operacao":cand["operacao"],"slot":cand["slot"],"primeiro":cand["primeiro_token"],"por_operacao":{k:v["operacao_taxa"] for k,v in cand["por_operacao"].items()},"pointer":cand["pointer"]},
      "preservacao_relativa":p1/p0,"gates":resultados["gates"],"ativo_no_chat":False},ensure_ascii=False,indent=2),flush=True)

if __name__=="__main__": main()
