"""Treino do gerador GRU autoral, com diálogos e validação separados.

NumPy é uma dependência somente do treinamento. O script não lê sondas,
bases de conhecimento, conversas do servidor ou o teste final anterior.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from linguagem_gerativa import (DIMENSAO, ESPECIAIS, GeradorGRU, atributos,
                              assinatura_atributos, tokenizar)


def assinatura(dados):
    return hashlib.sha256(json.dumps(dados,ensure_ascii=False,sort_keys=True,
                                    separators=(",",":")).encode("utf-8")).hexdigest()


def inicializar(vocabulario, ocultos=64, embeddings=32, semente=91):
    import numpy as np
    rng = np.random.default_rng(semente)
    h,e,v = ocultos,embeddings,len(vocabulario)
    p = {"E":rng.normal(0,.08,(v,e)).astype("float32"),
         "F":rng.normal(0,.12,(DIMENSAO,h)).astype("float32"), "bc":np.zeros(h,dtype="float32"),
         "O":rng.normal(0,.08,(h,v)).astype("float32"),"bo":np.zeros(v,dtype="float32")}
    for g in "zrn":
        p["W"+g] = rng.normal(0,1/math.sqrt(e+h),(e+h,h)).astype("float32")
        p["U"+g] = rng.normal(0,1/math.sqrt(h),(h,h)).astype("float32")
        p["b"+g] = np.zeros(h,dtype="float32")
    return p


def perda_gradientes(p, f, x, y, mascara):
    """Entropia cruzada e BPTT analítica de todas as matrizes da GRU."""
    import numpy as np
    c = np.tanh(f@p["F"] + p["bc"])
    h = c.copy()
    caches, soma = [], max(1,float(mascara.sum()))
    perda, e = 0.0,p["E"].shape[1]
    for t in range(x.shape[1]):
        anterior = h
        entrada = np.concatenate((p["E"][x[:,t]],c),axis=1)
        z = 1/(1+np.exp(-np.clip(entrada@p["Wz"] + h@p["Uz"] + p["bz"],-60,60)))
        r = 1/(1+np.exp(-np.clip(entrada@p["Wr"] + h@p["Ur"] + p["br"],-60,60)))
        n = np.tanh(entrada@p["Wn"] + (r*h)@p["Un"] + p["bn"])
        h = (1-z)*h + z*n
        logits = h@p["O"] + p["bo"]
        ps = np.exp(logits - logits.max(axis=1,keepdims=True))
        ps /= ps.sum(axis=1,keepdims=True)
        perda -= float((np.log(np.maximum(ps[np.arange(len(y)),y[:,t]],1e-12))*mascara[:,t]).sum())/soma
        caches.append((entrada,anterior,h,z,r,n,ps))
    grad = {k:np.zeros_like(a) for k,a in p.items()}
    dh,dc = np.zeros_like(h),np.zeros_like(c)
    for t in reversed(range(x.shape[1])):
        entrada,anterior,h,z,r,n,ps = caches[t]
        dlogits = ps.copy()
        dlogits[np.arange(len(y)),y[:,t]] -= 1
        dlogits *= (mascara[:,t]/soma)[:,None]
        grad["O"] += h.T@dlogits;grad["bo"] += dlogits.sum(axis=0)
        dh += dlogits@p["O"].T
        dn = dh*z*(1-n*n)
        dz = dh*(n-anterior)*z*(1-z)
        seguinte = dh*(1-z)
        drh = dn@p["Un"].T
        dr = drh*anterior*r*(1-r)
        seguinte += drh*r
        de = np.zeros_like(entrada)
        for g,dg,recorrencia in (("n",dn,r*anterior),("z",dz,anterior),("r",dr,anterior)):
            grad["W"+g] += entrada.T@dg
            grad["U"+g] += recorrencia.T@dg
            grad["b"+g] += dg.sum(axis=0)
            de += dg@p["W"+g].T
            if g != "n":
                seguinte += dg@p["U"+g].T
        np.add.at(grad["E"],x[:,t],de[:,:e])
        dc += de[:,e:]
        dh = seguinte
    dc = (dc+dh)*(1-c*c)
    grad["F"] += f.T@dc;grad["bc"] += dc.sum(axis=0)
    return perda,grad


def lote(casos, indices):
    import numpy as np
    sequencias = [[indices.get(t,3) for t in tokenizar(c["resposta"])] + [2] for c in casos]
    tam = max(map(len,sequencias))
    x,y = np.zeros((len(casos),tam),dtype="int64"),np.zeros((len(casos),tam),dtype="int64")
    mascara = np.zeros((len(casos),tam),dtype="float32")
    for i,s in enumerate(sequencias):
        x[i,:len(s)] = [1]+s[:-1];y[i,:len(s)]=s;mascara[i,:len(s)]=1
    return np.asarray([atributos(c["contexto"]) for c in casos],dtype="float32"),x,y,mascara


def avaliar(modelo, casos):
    perda,acertos,total,oov,concluidas = 0.0,0,0,0,0
    por_acao = {}
    for caso in casos:
        c,h = modelo.iniciar(caso["contexto"])
        anterior = 1
        alvo = tokenizar(caso["resposta"])
        for palavra in alvo + ["<fim>"]:
            h,logits = modelo.passo(anterior,h,c)
            pico = max(logits);exps=[math.exp(max(-70,z-pico)) for z in logits];soma=sum(exps)
            idx = modelo.indices.get(palavra,3)
            perda -= math.log(max(exps[idx]/soma,1e-12))
            acertos += max(range(len(logits)),key=lambda i:logits[i])==idx
            total += 1;oov += palavra not in modelo.indices
            anterior = idx
        g = modelo.gerar(caso["contexto"])
        concluidas += g["completa"]
        a = por_acao.setdefault(caso["contexto"]["acao"],{"total":0,"concluidas":0})
        a["total"] += 1;a["concluidas"] += g["completa"]
    return {"exemplos":len(casos),"tokens":total,"acertos_proximo_token":acertos,
            "entropia_cruzada":perda/max(1,total),"perplexidade":math.exp(min(50,perda/max(1,total))),
            "tokens_fora_vocabulario":oov,"geracoes_concluidas":concluidas,"por_acao":por_acao}


def treinar(caminho, destino, epocas=60, lote_tamanho=32, ocultos=64, embeddings=32, semente=91):
    import numpy as np
    if not 1<=epocas<=1000 or not 1<=lote_tamanho<=256 or not 8<=ocultos<=96 or not 8<=embeddings<=64:
        raise ValueError("Configuração de treino fora dos limites suportados")
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if dados.get("versao") != 1:
        raise ValueError("Currículo generativo inválido")
    treino = [c for c in dados["exemplos"] if c["split"]=="treino"]
    validacao = [c for c in dados["exemplos"] if c["split"]=="validacao"]
    if (not treino or not validacao or len(treino)+len(validacao)!=len(dados["exemplos"]) or
            {c["familia"] for c in treino}&{c["familia"] for c in validacao} or
            {c["dialogo"] for c in treino}&{c["dialogo"] for c in validacao}):
        raise ValueError("Partições de diálogos/famílias não conservadas")
    vocab = list(ESPECIAIS)+sorted({t for c in treino for t in tokenizar(c["resposta"])}-set(ESPECIAIS))
    indices = {t:i for i,t in enumerate(vocab)}
    p = inicializar(vocab,ocultos,embeddings,semente)
    m = {k:np.zeros_like(v) for k,v in p.items()};v = {k:np.zeros_like(a) for k,a in p.items()}
    rng = np.random.default_rng(semente)
    passo,historico = 0,[]
    for epoca in range(epocas):
        ordem = rng.permutation(len(treino));perdas=[]
        for inicio in range(0,len(treino),lote_tamanho):
            batch = [treino[i] for i in ordem[inicio:inicio+lote_tamanho]]
            perda,g = perda_gradientes(p,*lote(batch,indices));perdas.append(perda)
            norma = math.sqrt(sum(float((a*a).sum()) for a in g.values()))
            escala = min(1.0,5/max(norma,1e-9));passo+=1
            for k in p:
                grad = g[k]*escala;m[k]=.9*m[k]+.1*grad;v[k]=.999*v[k]+.001*grad*grad
                p[k] -= .003*(m[k]/(1-.9**passo))/(np.sqrt(v[k]/(1-.999**passo))+1e-8)
        media = sum(perdas)/len(perdas);historico.append(media)
        if epoca==0 or (epoca+1)%5==0:
            print("Época",epoca+1,"entropia treino",round(media,4),flush=True)
    checkpoint = {"versao":1,"arquitetura":"GRU condicional autoregressiva","assinatura_atributos":assinatura_atributos(),
                  "assinatura_treino":assinatura(treino),"vocabulario":vocab,"ocultos":ocultos,"embeddings":embeddings,
                  "pesos":{k:np.round(a.astype("float64"),7).tolist() for k,a in p.items()},
                  "treino":{"epocas":epocas,"lote":lote_tamanho,"semente":semente,"exemplos":len(treino),
                            "contextos_dialogo":len({c['dialogo'] for c in treino}),"respostas_deslexicalizadas":len({c['resposta'] for c in treino}),
                            "parametros":sum(a.size for a in p.values()),"entropias":historico}}
    modelo = GeradorGRU(checkpoint)
    relatorio = {"treino":avaliar(modelo,treino),"validacao":avaliar(modelo,validacao),
                 "assinatura_treino":checkpoint["assinatura_treino"],"arquitetura":checkpoint["arquitetura"],
                 "parametros":checkpoint["treino"]["parametros"],
                 "limite":"Corpus autoral pequeno e domínio de escrita controlado. Perplexidade e próxima palavra não demonstram inteligência geral nem conversa irrestrita. Slots copiam argumentos; o modelo não aprende fatos da sessão."}
    Path(destino).write_text(json.dumps(checkpoint,ensure_ascii=False,separators=(",",":"),allow_nan=False)+"\n",encoding="utf-8")
    return relatorio


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dados",default="curriculo_geracao.json")
    parser.add_argument("--saida",default="rede_geracao.json")
    parser.add_argument("--relatorio",default="avaliacao_geracao_neural.json")
    parser.add_argument("--epocas",type=int,default=60)
    parser.add_argument("--lote",type=int,default=32)
    parser.add_argument("--ocultos",type=int,default=64)
    parser.add_argument("--embeddings",type=int,default=32)
    parser.add_argument("--semente",type=int,default=91)
    args = parser.parse_args()
    relatorio = treinar(args.dados,args.saida,args.epocas,args.lote,args.ocultos,args.embeddings,args.semente)
    Path(args.relatorio).write_text(json.dumps(relatorio,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(relatorio,ensure_ascii=False,indent=2))
