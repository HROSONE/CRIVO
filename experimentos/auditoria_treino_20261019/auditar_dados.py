import json, gzip, re, unicodedata, sys
from collections import defaultdict, Counter
def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()
d = json.load(gzip.open(sys.argv[1]))
tr = d["treino"]
# 1) mesma mensagem (sem histórico) -> várias situações
sit = defaultdict(set); resp = defaultdict(set)
for c in tr:
    if c["historico"]: continue
    k = norm(c["mensagem"]); sit[k].add(c["situacao"]); resp[k].add(c["resposta"])
multi = {k: v for k, v in sit.items() if len(v) > 1}
print("msgs distintas sem historico:", len(sit))
print("msgs com >1 situacao:", len(multi), f"({len(multi)/len(sit):.1%})")
for k, v in sorted(multi.items(), key=lambda x: -len(x[1]))[:15]:
    print("  ", repr(k), sorted(v))
# 2) diversidade: formas de fala e respostas por situacao
formas = defaultdict(set); respostas = defaultdict(set); n = Counter()
for c in tr:
    s = c["situacao"]; n[s] += 1
    formas[s].add(norm(c["mensagem"])); respostas[s].add(c["resposta"])
sits = sorted(n)
import statistics as st
fv = [len(formas[s]) for s in sits]; rv = [len(respostas[s]) for s in sits if s.startswith("cena:")]
print("situacoes:", len(sits), "exemplos:", len(tr))
print("formas distintas por situacao: mediana", st.median(fv), "min", min(fv), "max", max(fv))
print("respostas distintas por situacao (cena:): mediana", st.median(rv), "min", min(rv))
print("razao exemplos/forma distinta:", round(len(tr)/sum(fv),1))
# 3) vazamento: mensagens do blind/dev que aparecem no treino (normalizado)
todas = set(norm(c["mensagem"]) for c in tr)
for nome in ("dev", "blind_v3"):
    if nome in d:
        L = d[nome]; vaz = sum(norm(c["mensagem"]) in todas for c in L)
        print(f"{nome}: {len(L)} casos, mensagem identica ao treino: {vaz} ({vaz/len(L):.1%})")
# 4) respostas: quantas respostas do treino servem a mais de uma situacao
rs = defaultdict(set)
for c in tr: rs[c["resposta"]].add(c["situacao"])
print("respostas distintas no treino:", len(rs), "| respostas usadas em >1 situacao:", sum(len(v)>1 for v in rs.values()))
