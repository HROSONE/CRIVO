"""Diagnóstico da rodada 1: para cada frase que a v4 acertava e a v6 errou, a fala de treino do v6 mais parecida
(n-gramas). Precisa de linhas_v4_base.json e linhas_rodada1.json (do Drive) na pasta atual. Saída: lista por situação."""
import json,sys,re,unicodedata,zlib,gzip
from collections import defaultdict,Counter
import numpy as np
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import comparar_v6 as C
b=json.load(open("linhas_v4_base.json")); r=json.load(open("linhas_rodada1.json"))
d=json.load(gzip.open(Path(__file__).resolve().parent / "dados_v6.json.gz"))
def norm(s):
    s=unicodedata.normalize("NFKD",s.lower()); s="".join(c for c in s if not unicodedata.combining(c))
    return " "+re.sub(r"\s+"," ",re.sub(r"[^\w\s]"," ",s)).strip()+" "
D=1<<14
def vec(s):
    s=norm(s); v=np.zeros(D,np.float32)
    for n in (3,4):
        for i in range(len(s)-n+1): v[zlib.crc32(s[i:i+n].encode())%D]+=1
    for w in s.split(): v[zlib.crc32(("w:"+w).encode())%D]+=2
    return v/(np.linalg.norm(v)+1e-9)
nuc={}
for c in d["treino"]: nuc[c["fala_nucleo"]]=c["situacao"][5:]
F=list(nuc); M=np.stack([vec(x) for x in F])
perdas=defaultdict(list)
for k in ("v3","v1","parafrases","grok","v4"):
    for a,bl in zip(r["linhas"][k],b["linhas"][k]):
        if C.certo(bl) and not C.certo(a):
            sit,msg,hist=a["chave"].split("|",2)
            perdas[sit[5:]].append((msg,hist))
for s,L in sorted(perdas.items(),key=lambda x:-len(x[1]))[:16]:
    puxa=Counter(); ex=[]
    for msg,hist in L:
        sims=M@vec(msg); i=int(sims.argmax())
        if sims[i]>0.35: puxa[nuc[F[i]]]+=1; ex.append((msg,F[i],nuc[F[i]],round(float(sims[i]),2)))
    print(f"\n== {s}: {len(L)} frases que a v4 acertava e a v6 errou | vizinha v6 mais parecida: {puxa.most_common(4)}")
    for e in ex[:5]: print("   ",e)
    if not ex: print("    exemplos:", [m for m,_ in L[:5]])
