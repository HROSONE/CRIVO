#!/usr/bin/env python3
"""Escola Cognitiva v1: ajuste controlado do Transformer próprio de 17,43M."""
from __future__ import annotations
import argparse, hashlib, json, random, re, shutil, sys, time, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
import torch
from torch import nn
from torch.nn import functional as F

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path[:0] = [str(RAIZ), str(AQUI)]
from linguagem_profunda import Configuracao, LinguagemProfunda, ESPECIAIS  # noqa:E402
from curriculo import gerar_treino  # noqa:E402

SEMENTE = 20261011
BASE_SHA = "16102a72b21031b8bee2b4edfa633a359f7f08c5beab552b05f294e656b0cc67"
TOK_SHA = "6e3704ce921851122953b8ac20c05e3a131f9cf0fa3c76d6e2391c4ec3efc88f"
PARAMETROS = 17_428_224
CONFIG = {"vocabulario":8192,"dimensao":384,"camadas":8,"cabecas":8,"contexto":256,"dropout":0.1}
ACOES = ("recordar","atualizar","epistemico","compor","esclarecer")
FOCOS = ("pessoa","objeto","nenhum")
PASSOS, LOTE, LR, LAMBDA = 1200, 16, 3e-5, .08


def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20), b""): h.update(b)
    return h.hexdigest()


def sha_json(o):
    return hashlib.sha256(json.dumps(o,ensure_ascii=False,sort_keys=True,
        separators=(",",":")).encode()).hexdigest()


def carregar_base(pasta, dispositivo):
    from tokenizers import Tokenizer
    pasta=Path(pasta); pp=pasta/"pesos.pt"; tp=pasta/"tokenizer.json"
    if sha(pp)!=BASE_SHA or sha(tp)!=TOK_SHA:
        raise ValueError("base/tokenizador não correspondem ao protocolo 17M")
    e=torch.load(pp,map_location="cpu",weights_only=True)
    if e.get("config")!=CONFIG or e.get("passo")!=20000:
        raise ValueError("configuração/passo inesperados")
    x=e.get("execucao",{})
    if x.get("tokenizer_sha256")!=TOK_SHA or x.get("pesos_externos") is not False:
        raise ValueError("proveniência da base inválida")
    m=LinguagemProfunda(Configuracao(**CONFIG)); m.load_state_dict(e["modelo"],strict=True)
    if sum(p.numel() for p in m.parameters())!=PARAMETROS: raise ValueError("contagem de parâmetros inesperada")
    m.to(dispositivo); t=Tokenizer.from_file(str(tp)); t.encode_special_tokens=True
    if t.get_vocab_size()!=8192: raise ValueError("vocabulário incompatível")
    return m,t,e


def cod(t,texto): return t.encode(texto,add_special_tokens=False).ids


def fonte_compacta(t, ex, resposta, contexto):
    """Preserva primeiro par, correção de pessoa e pares mais recentes."""
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
        else: grupos.append((i,)); i+=1
    sel={0} if grupos else set(); rx=re.compile(r"[A-Za-zÀ-ÿ]+-\d+")
    for gi,g in enumerate(grupos):
        if hist[g[0]]["papel"]=="usuario" and len(set(rx.findall(hist[g[0]]["texto"])))>=2: sel.add(gi)
    gl=lambda gi:sum(len(seg[j]) for j in grupos[gi])
    total=lambda s:len(atual)+sum(gl(gi) for gi in s)
    if len(atual)>limite or total(sel)>limite: raise ValueError(ex["id"]+": estado essencial excede contexto")
    for gi in reversed(range(len(grupos))):
        if gi not in sel and total(sel)+gl(gi)<=limite: sel.add(gi)
    fonte=[]
    for gi,g in enumerate(grupos):
        if gi in sel:
            for j in g: fonte+=seg[j]
    return fonte+atual, sum(len(grupos[gi]) for gi in sel), len(hist)


def preparar(t, ex, contexto):
    fim=t.token_to_id("<fim>"); resp=cod(t,ex["resposta"])+[fim]
    fonte,usado,total=fonte_compacta(t,ex,resp,contexto); seq=fonte+resp
    if len(seq)-1>contexto: raise AssertionError("compactação falhou")
    x,y=seq[:-1],seq[1:]; ini=len(fonte)-1
    return {"id":ex["id"],"x":x,"y":[-100]*ini+y[ini:],"pos":ini,"primeiro":resp[0],"fonte":fonte,
      "acao":ACOES.index(ex["acao"]),"foco":FOCOS.index(ex["foco"]),"operacao":ex["operacao"],
      "resposta":ex["resposta"],"ex":ex,"hist_usado":usado,"hist_total":total}


def batch(xs,pad,dev):
    n=max(len(z["x"]) for z in xs); x=torch.full((len(xs),n),pad,dtype=torch.long); y=torch.full_like(x,-100)
    p=torch.empty(len(xs),dtype=torch.long); a=torch.empty_like(p); f=torch.empty_like(p)
    for i,z in enumerate(xs):
        x[i,:len(z["x"])]=torch.tensor(z["x"]); y[i,:len(z["y"])]=torch.tensor(z["y"]); p[i],a[i],f[i]=z["pos"],z["acao"],z["foco"]
    return x.to(dev),y.to(dev),p.to(dev),a.to(dev),f.to(dev)


def hidden_logits(m,ids,topo=False):
    t=ids.shape[1]
    if topo:
        with torch.no_grad():
            x=m.embedding(ids)+m.posicao(torch.arange(t,device=ids.device))
            for b in m.blocos[:4]: x=b(x)
        for b in m.blocos[4:]: x=b(x)
    else:
        x=m.embedding(ids)+m.posicao(torch.arange(t,device=ids.device))
        for b in m.blocos: x=b(x)
    h=m.norm(x); return h,F.linear(h,m.embedding.weight)


def treinar(m,t,dev):
    dados=[preparar(t,e,m.config.contexto) for e in gerar_treino()]
    if set(Counter(z["operacao"] for z in dados).values())!={512}: raise ValueError("treino desbalanceado")
    for p in m.parameters(): p.requires_grad=False
    for b in m.blocos[4:]:
        for p in b.parameters(): p.requires_grad=True
    for p in m.norm.parameters(): p.requires_grad=True
    torch.manual_seed(SEMENTE+1); ha=nn.Linear(384,len(ACOES)).to(dev); hf=nn.Linear(384,len(FOCOS)).to(dev)
    pars=[p for p in m.parameters() if p.requires_grad]+list(ha.parameters())+list(hf.parameters())
    opt=torch.optim.AdamW(pars,lr=LR,weight_decay=.01); rng=random.Random(SEMENTE); ordem=list(range(len(dados))); cur=len(ordem)
    torch.manual_seed(SEMENTE); m.train()
    for b in m.blocos[:4]: b.eval()
    inicio=time.time(); janela=defaultdict(float)
    for passo in range(1,PASSOS+1):
        if cur+LOTE>len(ordem): rng.shuffle(ordem); cur=0
        lote=[dados[i] for i in ordem[cur:cur+LOTE]]; cur+=LOTE; x,y,pos,aa,af=batch(lote,t.token_to_id("<pad>"),dev)
        h,log=hidden_logits(m,x,True); pg=F.cross_entropy(log.reshape(-1,8192),y.reshape(-1),ignore_index=-100)
        r=h[torch.arange(len(lote),device=dev),pos]; pa,pf=F.cross_entropy(ha(r),aa),F.cross_entropy(hf(r),af); loss=pg+LAMBDA*pa+LAMBDA*pf
        opt.zero_grad(set_to_none=True); loss.backward(); gn=torch.nn.utils.clip_grad_norm_(pars,1.0); opt.step()
        for k,v in (("loss",loss),("gen",pg),("acao",pa),("foco",pf),("grad",gn)): janela[k]+=float(v)
        if passo%100==0:
            print(json.dumps({"passo":passo,**{k:round(v/100,5) for k,v in janela.items()},"segundos":round(time.time()-inicio,1)},ensure_ascii=False),flush=True); janela.clear()
    return {"passos":PASSOS,"lote":LOTE,"lr":LR,"lambda_acao":LAMBDA,"lambda_foco":LAMBDA,
      "treinaveis_modelo":sum(p.numel() for p in m.parameters() if p.requires_grad),
      "aux_parametros":sum(p.numel() for p in ha.parameters())+sum(p.numel() for p in hf.parameters()),"segundos":time.time()-inicio}


def abrir_holdout():
    man=json.loads((AQUI/"manifesto_holdout.json").read_text(encoding="utf-8"))
    if sha(AQUI/"preparar_holdout.py")!=man["gerador_sha256"]: raise ValueError("gerador do holdout mudou")
    import preparar_holdout as h
    ex=h.gerar(); por={op:sum(z["operacao"]==op for z in ex) for op in h.OPERACOES}
    pacote={"versao":1,"semente":h.SEMENTE,"congelado_antes_do_treino":True,
      "auditoria":{"aprovado":True,"exemplos":120,"familias":len(h.FAMILIAS),"mensagens_exatas_repetidas":0,"por_operacao":por},"exemplos":ex}
    if sha_json(pacote)!=man["holdout_sha256_canonico"]: raise ValueError("hash do holdout mudou")
    return ex,man


def norm(s): return re.sub(r"\s+"," ",unicodedata.normalize("NFKC",s).casefold()).strip()


def valores(ex):
    op,r=ex["operacao"],ex["resposta"]
    if op in ("recordar_pessoa","corrigir_pessoa","pedir_detalhe"):
        q=re.search(r"([A-Za-zÀ-ÿ]+-\d+)",r); return {"pessoa":q.group(1) if q else ""}
    if op=="recordar_objeto":
        q=re.match(r"O objeto é (.+)\.$",r); return {"objeto":q.group(1) if q else ""}
    if op=="guardar_hipotese":
        q=re.match(r"Não\. (.+) continua apenas como possibilidade\.$",r); return {"atividade":q.group(1) if q else ""}
    if op=="mensagem_sem_horario":
        p=re.search(r"([A-Za-zÀ-ÿ]+-\d+)",r); a=re.search(r"combinar (.+) comigo\?",r); return {"pessoa":p.group(1) if p else "","atividade":a.group(1) if a else ""}
    return {}


def pontuar(ex,saida):
    n=norm(saida); v=valores(ex); slot=bool(v) and all(norm(x) in n for x in v.values() if x); op=ex["operacao"]
    if op in ("recordar_pessoa","recordar_objeto","corrigir_pessoa"): ok=slot
    elif op=="guardar_hipotese": ok=slot and any(x in n for x in ("não","possibilidade","hipótese","provis"))
    elif op=="mensagem_sem_horario": ok=slot and not re.search(r"\b\d{1,2}(?::\d{2})?\s*(?:h|hora|horas)\b",n)
    else:
        pergunta="?" in saida or any(x in n for x in ("o que","qual ","que item","que coisa")); obj=""
        for z in ex["historico"]:
            q=re.search(r"Objeto:\s*([^.;]+)",z["texto"])
            if q: obj=norm(q.group(1)); break
        ok=slot and pergunta and not (obj and obj in n)
    return slot,bool(ok)


@torch.no_grad()
def avaliar(m,t,exs,dev):
    m.eval(); prep=[preparar(t,e,m.config.contexto) for e in exs]; ce=nt=first=exact=slotn=opn=0
    por=defaultdict(lambda:{"n":0,"operacao":0,"slot":0,"exata":0}); det=[]; fim=t.token_to_id("<fim>"); proib=[t.token_to_id(x) for x in ESPECIAIS[:-1]]
    for z in prep:
        x=torch.tensor([z["x"]],device=dev); y=torch.tensor([z["y"]],device=dev); _,log=hidden_logits(m,x)
        ce+=float(F.cross_entropy(log.reshape(-1,8192),y.reshape(-1),ignore_index=-100,reduction="sum")); nt+=int((y!=-100).sum()); first+=int(int(log[0,z["pos"]].argmax())==z["primeiro"])
        ids,terminou=m.gerar(z["fonte"],fim,max_tokens=32,temperatura=0,top_k=0,semente=SEMENTE,proibidos=proib); s=t.decode(ids)
        exata=norm(s)==norm(z["resposta"]); sl,ok=pontuar(z["ex"],s); exact+=exata; slotn+=sl; opn+=ok
        q=por[z["operacao"]]; q["n"]+=1; q["operacao"]+=ok; q["slot"]+=sl; q["exata"]+=exata
        det.append({"id":z["id"],"operacao":z["operacao"],"alvo":z["resposta"],"saida":s,"terminou":terminou,"slot":sl,
          "operacao_correta":ok,"exata":exata,"historico_usado":z["hist_usado"],"historico_total":z["hist_total"]})
    n=len(prep); po={k:{**v,"operacao_taxa":v["operacao"]/v["n"],"slot_taxa":v["slot"]/v["n"],"exata_taxa":v["exata"]/v["n"]} for k,v in sorted(por.items())}
    return {"n":n,"ce":ce/nt,"primeiro_token":first/n,"exata":exact/n,"slot":slotn/n,"operacao":opn/n,"por_operacao":po,"detalhes":det}


@torch.no_grad()
def preservacao(m,t,textos,dev):
    m.eval(); d=t.token_to_id("<documento>"); f=t.token_to_id("<fim>"); soma=nt=0
    for s in textos:
        q=[d]+cod(t,s)+[f]; x=torch.tensor([q[:-1]],device=dev); y=torch.tensor([q[1:]],device=dev); _,log=hidden_logits(m,x)
        soma+=float(F.cross_entropy(log.reshape(-1,8192),y.reshape(-1),reduction="sum")); nt+=y.numel()
    return {"n":len(textos),"tokens":nt,"ce":soma/nt}


def gates(b,c,pb,pc):
    minimo=min(v["operacao_taxa"] for v in c["por_operacao"].values()); gp=c["primeiro_token"]-b["primeiro_token"]
    gc=(b["ce"]-c["ce"])/b["ce"]; rp=pc["ce"]/pb["ce"]
    g={"operacao_min_60":c["operacao"]>=.60,"cada_operacao_min_35":minimo>=.35,"slot_min_70":c["slot"]>=.70,
       "primeiro_token_ganho_10pp":gp>=.10,"ce_melhora_5pct":gc>=.05,"preservacao_ate_5pct":rp<=1.05}
    return g,{"min_operacao":minimo,"ganho_primeiro_token_pp":gp*100,"ganho_ce_relativo":gc,"preservacao_ce_relativa":rp}


def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--base",required=True); ap.add_argument("--saida",required=True)
    ap.add_argument("--dispositivo",default="cuda" if torch.cuda.is_available() else "cpu"); a=ap.parse_args(); dev=torch.device(a.dispositivo)
    random.seed(SEMENTE); torch.manual_seed(SEMENTE)
    if dev.type=="cuda": torch.cuda.manual_seed_all(SEMENTE)
    prot=json.loads((AQUI/"protocolo.json").read_text(encoding="utf-8"))
    if prot["base"]["pesos_sha256"]!=BASE_SHA: raise ValueError("protocolo/base divergentes")
    m,t,e=carregar_base(a.base,dev); treino=treinar(m,t,dev)
    print("treino fixado; abrindo holdout prospectivo...",flush=True); hold,man=abrir_holdout()
    textos=json.loads((AQUI/"preservacao_portugues.json").read_text(encoding="utf-8"))["textos"]
    base,tb,_=carregar_base(a.base,dev); ab=avaliar(base,tb,hold,dev); pb=preservacao(base,tb,textos,dev); del base
    if dev.type=="cuda": torch.cuda.empty_cache()
    ac=avaliar(m,t,hold,dev); pc=preservacao(m,t,textos,dev); g,der=gates(ab,ac,pb,pc); eleg=all(g.values()); simples=lambda x:{k:v for k,v in x.items() if k!="detalhes"}
    res={"versao":1,"base":{"pesos_sha256":BASE_SHA,"tokenizer_sha256":TOK_SHA,"parametros":PARAMETROS,"passo":20000},
         "holdout":man,"treino":treino,"avaliacao_base":simples(ab),"avaliacao_candidato":simples(ac),"preservacao_base":pb,
         "preservacao_candidato":pc,"gates":g,"derivados":der,"elegivel_promocao":eleg,"ativo_no_chat":False,"detalhes_holdout":ac["detalhes"]}
    out=Path(a.saida); out.mkdir(parents=True,exist_ok=True); shutil.copyfile(Path(a.base)/"tokenizer.json",out/"tokenizer.json")
    ck={"versao":1,"modelo":{k:v.detach().cpu() for k,v in m.state_dict().items()},"config":e["config"],"passo":e["passo"],
        "execucao":{"tokenizer_sha256":TOK_SHA,"semente":SEMENTE,"pesos_externos":False,"base_pesos_sha256":BASE_SHA,
        "escola_cognitiva":{"versao":1,"passos":PASSOS,"treino":treino,"auxiliares_serializados":False,"ativo_no_chat":False}}}
    torch.save(ck,out/"pesos.pt"); res["checkpoint_sha256"]=sha(out/"pesos.pt")
    (out/"resultados.json").write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"meta.json").write_text(json.dumps({"papel":"candidato Escola Cognitiva v1 sobre base própria 17M","base_pesos_sha256":BASE_SHA,
      "checkpoint_sha256":res["checkpoint_sha256"],"elegivel_promocao":eleg,"ativo_no_chat":False,"pesos_externos":False},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"elegivel_promocao":eleg,"gates":g,"base":simples(ab),"candidato":simples(ac),
      "preservacao_relativa":der["preservacao_ce_relativa"],"checkpoint_sha256":res["checkpoint_sha256"],"ativo_no_chat":False},ensure_ascii=False,indent=2),flush=True)

if __name__=="__main__": main()
