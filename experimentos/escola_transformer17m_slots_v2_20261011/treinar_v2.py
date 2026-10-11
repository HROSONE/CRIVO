#!/usr/bin/env python3
"""Escola Transformer V2: testa currículo de slots abertos contra a V1."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, shutil, subprocess, sys
from pathlib import Path
import torch

AQUI=Path(__file__).resolve().parent
V1=AQUI.parents[0]/"escola_transformer_17m_20261011"
sys.path.insert(0,str(V1)); sys.path.insert(0,str(AQUI)); sys.path.insert(0,str(AQUI.parents[1]))

spec=importlib.util.spec_from_file_location("escola_v1_treino",V1/"treinar_escola.py")
v1=importlib.util.module_from_spec(spec); sys.modules[spec.name]=v1; spec.loader.exec_module(v1)
import curriculo_v2, preparar_holdout_v2  # noqa:E402

V1_CK_SHA="849bc4655820f8cd1f445539a1bd0f01959f03ce38145ece460c0fe27568c661"

def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for b in iter(lambda:f.read(1<<20),b""): h.update(b)
 return h.hexdigest()

def carregar_v1(pasta,dev):
 from tokenizers import Tokenizer
 pasta=Path(pasta); pp=pasta/"pesos.pt"; tp=pasta/"tokenizer.json"
 if sha(pp)!=V1_CK_SHA: raise ValueError("checkpoint V1 divergente")
 e=torch.load(pp,map_location="cpu",weights_only=True)
 if e.get("config")!=v1.CONFIG or e.get("execucao",{}).get("base_pesos_sha256")!=v1.BASE_SHA:
  raise ValueError("proveniência do candidato V1 inválida")
 tsha=sha(tp)
 if tsha!=e.get("execucao",{}).get("tokenizer_sha256"): raise ValueError("tokenizer V1 divergente")
 m=v1.LinguagemProfunda(v1.Configuracao(**e["config"])); m.load_state_dict(e["modelo"],strict=True); m.to(dev); m.eval()
 t=Tokenizer.from_file(str(tp)); t.encode_special_tokens=True
 return m,t,e

def validar_protocolo():
 p=json.loads((AQUI/"protocolo_v2.json").read_text(encoding="utf-8"))
 blob=subprocess.check_output(["git","hash-object",str(AQUI/"preparar_holdout_v2.py")],text=True).strip()
 if blob!=p["holdout"]["gerador_blob_sha"]: raise ValueError("gerador do holdout V2 mudou depois do congelamento")
 if p["baseline"]["candidato_v1_checkpoint_sha256"]!=V1_CK_SHA: raise ValueError("baseline V1 divergente")
 return p

def gates(prot,b1,c2,praw,p2):
 g=prot["gates"]; minimo=min(x["operacao_taxa"] for x in c2["por_operacao"].values())
 opganho=(c2["operacao"]-b1["operacao"])*100; slotganho=(c2["slot"]-b1["slot"])*100
 cerel=c2["ce"]/b1["ce"]; pres=p2["ce"]/praw["ce"]
 gs={
  "operacao_total":c2["operacao"]>=g["operacao_total_min"],
  "cada_operacao":minimo>=g["cada_operacao_min"],
  "slot":c2["slot"]>=g["slot_min"],
  "primeiro_token":c2["primeiro_token"]>=g["primeiro_token_min"],
  "preservacao":pres<=g["preservacao_ce_relativa_max"],
  "ganho_operacao_vs_v1":opganho>=g["v2_vs_v1_operacao_ganho_min_pp"],
  "ganho_slot_vs_v1":slotganho>=g["v2_vs_v1_slot_ganho_min_pp"],
  "ce_vs_v1":cerel<=g["v2_vs_v1_ce_relativa_max"],
 }
 return gs,{"min_operacao":minimo,"ganho_operacao_pp":opganho,"ganho_slot_pp":slotganho,"ce_relativa_vs_v1":cerel,"preservacao_ce_relativa":pres}

def simples(x): return {k:v for k,v in x.items() if k!="detalhes"}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument("--base",required=True); ap.add_argument("--baseline-v1",required=True); ap.add_argument("--saida",required=True); ap.add_argument("--dispositivo",default="cuda" if torch.cuda.is_available() else "cpu"); a=ap.parse_args(); dev=torch.device(a.dispositivo)
 prot=validar_protocolo()
 # Treino primeiro. O holdout V2 só é materializado depois dos 1200 passos.
 m,t,e=v1.carregar_base(a.base,dev); v1.gerar_treino=curriculo_v2.gerar_treino
 treino=v1.treinar(m,t,dev)
 print("treino V2 fixado; abrindo holdout prospectivo V2...",flush=True)
 hold=preparar_holdout_v2.gerar()
 if len(hold)!=180 or {op:sum(x["operacao"]==op for x in hold) for op in preparar_holdout_v2.OPERACOES}!={op:30 for op in preparar_holdout_v2.OPERACOES}: raise ValueError("holdout V2 inválido")
 b1,t1,_=carregar_v1(a.baseline_v1,dev); av1=v1.avaliar(b1,t1,hold,dev)
 av2=v1.avaliar(m,t,hold,dev)
 textos=json.loads((V1/"preservacao_portugues.json").read_text(encoding="utf-8"))["textos"]
 raw,tr,_=v1.carregar_base(a.base,dev); praw=v1.preservacao(raw,tr,textos,dev); p2=v1.preservacao(m,t,textos,dev)
 gs,der=gates(prot,av1,av2,praw,p2); eleg=all(gs.values())
 out=Path(a.saida); out.mkdir(parents=True,exist_ok=True); shutil.copyfile(Path(a.base)/"tokenizer.json",out/"tokenizer.json")
 ck={"versao":1,"modelo":{k:v.detach().cpu() for k,v in m.state_dict().items()},"config":e["config"],"passo":e["passo"],"execucao":{"tokenizer_sha256":v1.TOK_SHA,"semente":v1.SEMENTE,"pesos_externos":False,"base_pesos_sha256":v1.BASE_SHA,"escola_cognitiva":{"versao":2,"intervencao":"slots_abertos","passos":v1.PASSOS,"ativo_no_chat":False,"auxiliares_serializados":False}}}
 torch.save(ck,out/"pesos.pt"); cksha=sha(out/"pesos.pt")
 res={"versao":2,"protocolo":prot,"treino":treino,"baseline_v1":simples(av1),"candidato_v2":simples(av2),"preservacao_base":praw,"preservacao_v2":p2,"gates":gs,"derivados":der,"elegivel_promocao":eleg,"ativo_no_chat":False,"checkpoint_sha256":cksha,"detalhes_v1":av1["detalhes"],"detalhes_v2":av2["detalhes"]}
 (out/"resultados.json").write_text(json.dumps(res,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 (out/"meta.json").write_text(json.dumps({"papel":"Escola Transformer V2 - slots abertos","checkpoint_sha256":cksha,"elegivel_promocao":eleg,"ativo_no_chat":False},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"elegivel_promocao":eleg,"gates":gs,"baseline_v1":simples(av1),"candidato_v2":simples(av2),"derivados":der,"checkpoint_sha256":cksha,"ativo_no_chat":False},ensure_ascii=False,indent=2),flush=True)

if __name__=="__main__": main()
