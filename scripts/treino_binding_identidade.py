#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, random, re, shutil, time, unicodedata
from dataclasses import dataclass
from pathlib import Path
import torch
from torch.nn import functional as F
from tokenizers import Tokenizer
from linguagem_profunda import Configuracao, ESPECIAIS, LinguagemProfunda, fonte_dialogo

SEED=202610120045
CFG={"vocabulario":8192,"dimensao":384,"camadas":8,"cabecas":8,"contexto":256,"dropout":0.1}
PHASES=[
 {"name":"01_copia_exata","steps":2000,"lr":3e-6},
 {"name":"02_binding_colisao","steps":2000,"lr":2.8e-6},
 {"name":"03_correcao_invariancia","steps":2000,"lr":2.5e-6},
 {"name":"04_composicao_mista","steps":2000,"lr":2.2e-6},
]
CATEGORIES=[
 ("recipiente",["armazenar líquidos","transportar líquidos","conter amostras","guardar substâncias"]),
 ("instrumento",["medir temperatura","observar objetos distantes","detectar vibrações","registrar sinais"]),
 ("ferramenta",["golpear peças","cortar materiais","fixar componentes","apertar parafusos"]),
 ("dispositivo",["processar dados","emitir alertas","controlar fluxo","registrar eventos"]),
 ("móvel",["servir de assento","apoiar objetos","guardar itens","organizar materiais"]),
 ("estrutura",["sustentar uma carga","proteger uma área","conectar duas partes","separar ambientes"]),
]
MATS=["metal","vidro","madeira","cerâmica","plástico","fibra","pedra","borracha"]
TEST_MATS=["quartzo","cobre","bambu","resina","argila"]

@dataclass(frozen=True)
class Entity:
    name:str; category:str; function:str; material_a:str; material_b:str

def norm(s):
    s=unicodedata.normalize("NFD",s.lower())
    s="".join(c for c in s if unicodedata.category(c)!="Mn")
    return re.sub(r"\s+"," ",s).strip()

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def make_entities(seed,n,prefix,mats):
    rng=random.Random(seed)
    A=["na","ze","tor","lum","fi","dra","kel","vo","ri","san","bel","tri","mo","pa","xel","gu","pri","do","var","chi"]
    B=["lo","ra","mi","to","ve","na","po","ri","sa","du","xel","go","fi","la","ne","bar","ti","cor","zen","mar"]
    C=["n","s","r","m","l","d"]
    seen=set(); out=[]
    while len(out)<n:
        stem=rng.choice(A)+rng.choice(B)+rng.choice(C)
        name=prefix+stem
        if name in seen: continue
        seen.add(name)
        cat,funcs=rng.choice(CATEGORIES); fn=rng.choice(funcs)
        m1,m2=rng.sample(mats,2)
        out.append(Entity(name,cat,fn,m1,m2))
    return out

def near_name(name):
    last=name[-1]
    repl={"n":"m","m":"n","s":"r","r":"s","l":"d","d":"l"}.get(last,"z")
    return name[:-1]+repl

def wrong_cat(cat):
    return next(c for c,_ in CATEGORIES if c!=cat)

def words(text):
    stop={"de","da","do","para","um","uma","e","a","o","os","as"}
    return [w for w in re.findall(r"[a-zA-ZÀ-ÿ]+",norm(text)) if len(w)>2 and w not in stop]

def item(q,name,rest,skill,wrong_name=None):
    return {"q":q,"name":name,"rest":rest,"skill":skill,"wrong_name":wrong_name}

def build_pool(entities,phase):
    out=[]
    for i,e in enumerate(entities):
        distract=near_name(e.name)
        if phase==0:
            intro=f"Considere um objeto inventado chamado {e.name}. Ele é um {e.category} usado para {e.function}."
            out += [
              item(f"{intro} Qual é exatamente o nome do objeto?",e.name,"esse é o nome exato do objeto.","nome",distract),
              item(f"{intro} A que categoria {e.name} pertence?",e.name,f"pertence à categoria {e.category}.","categoria",distract),
              item(f"{intro} Qual é a função de {e.name}?",e.name,f"tem como função {e.function}.","funcao",distract),
            ]
        elif phase==1:
            e2=entities[(i+17)%len(entities)]
            q=f"Há dois objetos parecidos. {e.name} é um {e.category} usado para {e.function}. {distract} é apenas um nome diferente. Qual nome corresponde ao objeto usado para {e.function}?"
            out.append(item(q,e.name,f"é o nome correto e sua função é {e.function}.","binding_colisao",distract))
            q2=f"{e.name} é um {e.category} usado para {e.function}. {e2.name} é um {e2.category} usado para {e2.function}. Qual deles serve para {e.function}?"
            out.append(item(q2,e.name,f"é o objeto usado para {e.function}.","binding_duplo",e2.name))
            q3=f"O nome atual é {e.name}. Não confunda com {distract}. Qual é o nome atual?"
            out.append(item(q3,e.name,"é o nome atual.","nome_contraste",distract))
        elif phase==2:
            q=f"O objeto atual era {distract}. Correção explícita: o objeto atual é {e.name}, não {distract}. Qual nome deve valer agora?"
            out.append(item(q,e.name,f"é o nome corrigido; {distract} deve ser descartado.","correcao",distract))
            q2=f"{e.name} é um {e.category} usado para {e.function}. Ele era de {e.material_a} e agora é de {e.material_b}. Só por isso deixa de ser {e.name}?"
            out.append(item(q2,e.name,f"não. A mudança de material não muda necessariamente sua identidade; continua sendo um {e.category} usado para {e.function}.","invariancia",distract))
            wc=wrong_cat(e.category)
            q3=f"{e.name} não é um {wc}. {e.name} é um {e.category} usado para {e.function}. {e.name} pertence à categoria {wc}?"
            out.append(item(q3,e.name,f"não. É um {e.category}, não um {wc}.","negacao",distract))
        else:
            intro=f"Considere {e.name}: ele é um {e.category} usado para {e.function}."
            out += [
              item(f"{intro} Explique em uma frase o que {e.name} é e para que serve.",e.name,f"é um {e.category} usado para {e.function}.","composicao",distract),
              item(f"{intro} Se o material mudar de {e.material_a} para {e.material_b}, responda sem perder o nome do objeto.",e.name,f"continua sendo o mesmo objeto; a mudança de material não altera por si só sua identidade de {e.category}.","composicao_invariancia",distract),
              item(f"{intro} Qual é o nome, a categoria e a função?",e.name,f"é um {e.category} e serve para {e.function}.","tripla",distract),
            ]
    return out

def enc(tok,s): return tok.encode(s,add_special_tokens=False).ids

def make_xy(tok,it,wrong=False):
    name=it["wrong_name"] if wrong and it.get("wrong_name") else it["name"]
    src=fonte_dialogo(tok,it["q"],(),CFG["contexto"])
    name_ids=enc(tok,name)
    rest_ids=enc(tok,": "+it["rest"])
    resp=name_ids+rest_ids+[tok.token_to_id("<fim>")]
    seq=src+resp
    if len(seq)>CFG["contexto"]: raise ValueError("exemplo excede contexto")
    x=seq[:-1]
    y=[-100]*(len(src)-1)+seq[len(src):]
    w=[0.0]*len(y)
    start=len(src)-1
    for j in range(len(name_ids)):
        if start+j<len(w): w[start+j]=1.0
    return x,y,w

def collate(tok,items,device="cuda",wrong=False):
    pad=tok.token_to_id("<pad>"); pairs=[make_xy(tok,it,wrong) for it in items]
    m=max(len(x) for x,_,_ in pairs); xs=[]; ys=[]; ws=[]
    for x,y,w in pairs:
        xs.append(x+[pad]*(m-len(x)))
        ys.append(y+[-100]*(m-len(y)))
        ws.append(w+[0.0]*(m-len(w)))
    return (torch.tensor(xs,dtype=torch.long,device=device),
            torch.tensor(ys,dtype=torch.long,device=device),
            torch.tensor(ws,dtype=torch.float32,device=device))

def weighted_lm(model,x,y,w,identity_weight):
    logits,_=model(x)
    b,t,v=logits.shape
    loss=F.cross_entropy(logits.reshape(-1,v),y.reshape(-1),ignore_index=-100,reduction="none").reshape(b,t)
    mask=(y!=-100).float()
    weights=mask*(1.0+w*(identity_weight-1.0))
    return (loss*weights).sum()/weights.sum().clamp_min(1.0)

def per_nll(model,x,y):
    logits,_=model(x); b,t,v=logits.shape
    loss=F.cross_entropy(logits.reshape(-1,v),y.reshape(-1),ignore_index=-100,reduction="none").reshape(b,t)
    mask=(y!=-100).float()
    return (loss*mask).sum(1)/mask.sum(1).clamp_min(1)

def set_trainable(model):
    for p in model.parameters(): p.requires_grad=False
    for block in model.blocos[-6:]:
        for p in block.parameters(): p.requires_grad=True
    for p in model.norm.parameters(): p.requires_grad=True
    return [p for p in model.parameters() if p.requires_grad]

def lr_at(base,step,total):
    warm=max(50,int(total*.05))
    if step<warm: return base*(step+1)/warm
    prog=(step-warm)/max(1,total-warm)
    return base*(.2+.8*.5*(1+math.cos(math.pi*prog)))

@torch.no_grad()
def generate(model,tok,q,max_tokens=48):
    src=fonte_dialogo(tok,q,(),CFG["contexto"])
    ids,_=model.gerar(src,tok.token_to_id("<fim>"),max_tokens=max_tokens,temperatura=0,top_k=0,semente=SEED,
                      proibidos=[tok.token_to_id(t) for t in ESPECIAIS[:-1]])
    return tok.decode(ids).strip()

def strict_cases(entities):
    cases=[]
    for e in entities:
        intro=f"Considere um objeto inventado chamado {e.name}. Ele é um {e.category} usado para {e.function}."
        cases += [
          {"skill":"categoria","name":e.name,"q":f"{intro} A que categoria {e.name} pertence?","must":words(e.category)},
          {"skill":"funcao","name":e.name,"q":f"{intro} Qual é a função de {e.name}?","must":words(e.function)},
          {"skill":"invariancia","name":e.name,"q":f"{intro} Ele era de {e.material_a} e agora é de {e.material_b}. Só por isso deixa de ser {e.name}?","must":["nao"]+words(e.category)},
          {"skill":"composicao","name":e.name,"q":f"{intro} Explique em uma frase o que {e.name} é e para que serve.","must":words(e.category)+words(e.function)},
          {"skill":"negacao","name":e.name,"q":f"{e.name} não é um {wrong_cat(e.category)}. {intro} {e.name} pertence à categoria {wrong_cat(e.category)}?","must":["nao"]+words(e.category)},
        ]
    return cases

def exact_name_present(answer,name):
    a=norm(answer); n=norm(name)
    return re.search(r"(?<![a-z0-9])"+re.escape(n)+r"(?![a-z0-9])",a) is not None

@torch.no_grad()
def evaluate(model,tok,cases,label):
    total=good=0; by={}; samples=[]
    for i,c in enumerate(cases,1):
        a=generate(model,tok,c["q"])
        ok=exact_name_present(a,c["name"]) and all(norm(x) in norm(a) for x in c["must"])
        total+=1; good+=int(ok); z=by.setdefault(c["skill"],[0,0]); z[0]+=int(ok); z[1]+=1
        if len(samples)<12: samples.append({"q":c["q"],"a":a,"ok":ok,"skill":c["skill"]})
        if i%100==0: print(f"[{label}] {i}/{len(cases)}",flush=True)
    return {"label":label,"correct":good,"total":total,"accuracy":good/max(1,total),
            "by_skill":{k:{"correct":v[0],"total":v[1],"accuracy":v[0]/v[1]} for k,v in by.items()},
            "samples":samples}

def save(out,model,tok_path,base_state,step,phase,metrics):
    out.mkdir(parents=True,exist_ok=True)
    state={"versao":base_state["versao"],"modelo":{k:v.detach().cpu() for k,v in model.state_dict().items()},
           "config":dict(CFG),"passo":step,
           "execucao":{**dict(base_state.get("execucao",{})),"tokenizer_sha256":sha(tok_path),
                       "pesos_externos":False,"treino_binding_identidade":True,"fase":phase,
                       "ativo_no_chat":False,"promovido":False,"seed":SEED}}
    torch.save(state,out/"pesos.pt"); shutil.copy2(tok_path,out/"tokenizer.json")
    (out/"metricas.json").write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding="utf-8")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--drive-root",default="/content/drive/MyDrive/CRIVO/checkpoints")
    ap.add_argument("--batch-size",type=int,default=16); args=ap.parse_args()
    assert torch.cuda.is_available()
    torch.manual_seed(SEED); random.seed(SEED); rng=random.Random(SEED)
    root=Path(args.drive_root)
    curricular=root/"escola_curricular_longa"
    runs=sorted(p for p in curricular.glob("run_*") if (p/"05_05_dialogo_estado/pesos.pt").exists())
    if not runs: raise FileNotFoundError("não encontrei a fase 5 do treino curricular")
    base=runs[-1]/"05_05_dialogo_estado"
    print("BASE:",base,flush=True)
    st=torch.load(base/"pesos.pt",map_location="cpu",weights_only=True)
    tok=Tokenizer.from_file(str(base/"tokenizer.json")); tok.encode_special_tokens=True
    model=LinguagemProfunda(Configuracao(**CFG)); model.load_state_dict(st["modelo"],strict=True); model=model.cuda()
    train=make_entities(SEED+10,3000,"t",MATS); dev=make_entities(SEED+20,40,"d",TEST_MATS); blind=make_entities(202610112348+30,100,"x",TEST_MATS)
    assert {e.name for e in train}.isdisjoint({e.name for e in dev}|{e.name for e in blind})
    dev_cases=strict_cases(dev); blind_cases=strict_cases(blind)
    outroot=root/"escola_binding_identidade"; stamp=time.strftime("%Y%m%d_%H%M%S"); run=outroot/f"run_{stamp}"; run.mkdir(parents=True,exist_ok=True)
    baseline=evaluate(model,tok,blind_cases,"blind_before")
    print("BASELINE RÍGIDO:",baseline["correct"],"/",baseline["total"],f"{baseline['accuracy']:.1%}",flush=True)
    trainable=set_trainable(model); scaler=torch.amp.GradScaler("cuda"); best=-1; best_dir=None; cumulative=0; hist=[]
    for pi,pcfg in enumerate(PHASES):
        pool=build_pool(train[pi*600:(pi+1)*600],pi); rng.shuffle(pool)
        opt=torch.optim.AdamW(trainable,lr=pcfg["lr"],weight_decay=.01); losses=[]; ranks=[]
        print("\nFASE",pcfg["name"],"pool",len(pool),flush=True)
        for step in range(pcfg["steps"]):
            lr=lr_at(pcfg["lr"],step,pcfg["steps"])
            for g in opt.param_groups:g["lr"]=lr
            batch=[rng.choice(pool) for _ in range(args.batch_size)]
            x,y,w=collate(tok,batch); opt.zero_grad(set_to_none=True)
            with torch.amp.autocast("cuda",dtype=torch.float16):
                lm=weighted_lm(model,x,y,w,identity_weight=4.0)
                ranked=[it for it in batch if it.get("wrong_name")]
                rank=torch.tensor(0.0,device="cuda")
                if ranked and step%2==0:
                    ranked=ranked[:6]
                    px,py,_=collate(tok,ranked); nx,ny,_=collate(tok,ranked,wrong=True)
                    rank=F.relu(.5+per_nll(model,px,py)-per_nll(model,nx,ny)).mean()
                loss=lm+.25*rank
            scaler.scale(loss).backward(); scaler.unscale_(opt); torch.nn.utils.clip_grad_norm_(trainable,1.0)
            scaler.step(opt); scaler.update(); losses.append(float(lm)); ranks.append(float(rank))
            if (step+1)%250==0 or step==0:
                print(f"{pcfg['name']} {step+1}/{pcfg['steps']} lm={sum(losses[-100:])/len(losses[-100:]):.4f} rank={sum(ranks[-100:])/len(ranks[-100:]):.4f} lr={lr:.2e}",flush=True)
        cumulative+=pcfg["steps"]; devr=evaluate(model,tok,dev_cases,"dev_"+pcfg["name"])
        metrics={"phase":pcfg["name"],"steps_added":cumulative,"dev":devr,"lm_last100":sum(losses[-100:])/len(losses[-100:])}
        pdir=run/f"{pi+1:02d}_{pcfg['name']}"; save(pdir,model,base/"tokenizer.json",st,int(st.get("passo",0))+cumulative,pcfg["name"],metrics)
        hist.append(metrics)
        print("DEV:",f"{devr['accuracy']:.1%}",flush=True)
        if devr["accuracy"]>best: best=devr["accuracy"]; best_dir=pdir
    bst=torch.load(best_dir/"pesos.pt",map_location="cpu",weights_only=True); model.load_state_dict(bst["modelo"],strict=True)
    final=evaluate(model,tok,blind_cases,"blind_after")
    finaldir=outroot/f"crivo_binding_identidade_{time.strftime('%Y%m%d_%H%M%S')}"; finaldir.mkdir(parents=True,exist_ok=True)
    shutil.copy2(best_dir/"pesos.pt",finaldir/"pesos.pt"); shutil.copy2(best_dir/"tokenizer.json",finaldir/"tokenizer.json")
    summary={"baseline":baseline,"final":final,"gain_pp":100*(final["accuracy"]-baseline["accuracy"]),
             "best_dev":best,"best_phase":best_dir.name,"phase_history":hist,
             "gate":{"overall_min":.60,"each_skill_min":.40,
                     "overall_pass":final["accuracy"]>=.60,
                     "each_skill_pass":all(v["accuracy"]>=.40 for v in final["by_skill"].values())},
             "ativo_no_chat":False,"promovido":False}
    summary["gate"]["pass"]=summary["gate"]["overall_pass"] and summary["gate"]["each_skill_pass"]
    (finaldir/"resultado_binding_identidade.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    (run/"resultado_binding_identidade.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    print("\nTREINO BINDING IDENTIDADE FINALIZADO",flush=True)
    print("Antes:",baseline["correct"],"/",baseline["total"],f"{baseline['accuracy']:.1%}",flush=True)
    print("Depois:",final["correct"],"/",final["total"],f"{final['accuracy']:.1%}",flush=True)
    print("Ganho:",f"{summary['gain_pp']:+.1f} p.p.",flush=True)
    print("Melhor fase:",best_dir.name,flush=True)
    print("Gate:","PASSOU" if summary["gate"]["pass"] else "NÃO PASSOU",flush=True)
    print("Checkpoint:",finaldir,flush=True)
    print("ativo_no_chat=false",flush=True)

if __name__=="__main__": main()
