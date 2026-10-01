"""BPTT e Adam de um encoder-decoder com atenção/cópia, treinado do zero.

Somente texto e papéis entram na rede. Ato, spans, quadro e quaisquer
outros rótulos do currículo são ignorados. NumPy é usado no treinamento;
o checkpoint também pode ser executado com Python padrão.
"""
import argparse
from arquivos_contextuais import ler_json
import hashlib
import json
import math
import os
import time
from pathlib import Path

from dialogo_seq2seq import (VERSAO, ESPECIAIS, PAD, INICIO, FIM, DESCONHECIDO,
                            DialogoSeq2Seq, fonte_dialogo, tokenizar, subpalavras,
                            vocabulario_treino, formas)


def assinatura(dados):
    return hashlib.sha256(json.dumps(dados,ensure_ascii=False,sort_keys=True,
                                    separators=(",",":")).encode("utf-8")).hexdigest()


def inicializar(vocabulario, ocultos=96, embeddings=64, buckets=512, semente=173):
    import numpy as np
    rng = np.random.default_rng(semente)
    p = {}
    for k,forma in formas(vocabulario,ocultos,embeddings,buckets).items():
        if len(forma) == 1:
            p[k] = np.zeros(forma,dtype="float32")
        else:
            escala = .08 if k in ("E","C") else 1/math.sqrt(forma[0])
            p[k] = rng.normal(0,escala,forma).astype("float32")
    # Um gate equilibrado permite aprender cópia e geração desde o início.
    p["G"] *= .15
    return p


def lote(exemplos, indices, buckets=512, limite_fonte=192, limite_resposta=64):
    import numpy as np
    fontes = [fonte_dialogo(ex["mensagem"],ex.get("historico",[]),limite_fonte) for ex in exemplos]
    respostas = [tokenizar(ex["resposta"]) for ex in exemplos]
    if any(not s or len(s)+1 > limite_resposta for s in respostas):
        raise ValueError("Resposta vazia ou acima do limite de treino")
    b,s,t = len(exemplos),max(map(len,fontes)),max(map(len,respostas))+1
    fonte = np.zeros((b,s),dtype="int64");mf = np.zeros((b,s),dtype="float32")
    x = np.zeros((b,t),dtype="int64");y = np.zeros((b,t),dtype="int64")
    mascara = np.zeros((b,t),dtype="float32")
    cf = np.zeros((b,s,16),dtype="int64");wf = np.zeros((b,s,16),dtype="float32")
    cx = np.zeros((b,t,16),dtype="int64");wx = np.zeros((b,t,16),dtype="float32")
    iguais = np.zeros((b,t,s),dtype="float32")
    alvo_vocab = np.zeros((b,t),dtype="float32")
    alvos_copiaveis, alvos_desconhecidos = 0,0
    def preencher_chars(cs,ws,i,j,palavra):
        partes = subpalavras(palavra,buckets)
        if partes:
            cs[i,j,:len(partes)] = partes;ws[i,j,:len(partes)] = 1/len(partes)
    for i,(src,res) in enumerate(zip(fontes,respostas)):
        for j,palavra in enumerate(src):
            fonte[i,j] = indices.get(palavra,DESCONHECIDO);mf[i,j] = 1
            preencher_chars(cf,wf,i,j,palavra)
        for j,(ant,palavra) in enumerate(zip([ESPECIAIS[INICIO]]+res,res+[ESPECIAIS[FIM]])):
            x[i,j] = indices.get(ant,DESCONHECIDO)
            preencher_chars(cx,wx,i,j,ant)
            y[i,j] = indices.get(palavra,DESCONHECIDO);mascara[i,j] = 1
            alvo_vocab[i,j] = palavra in indices
            for k,tok in enumerate(src):
                iguais[i,j,k] = tok == palavra and tok not in ESPECIAIS
            if palavra not in indices:
                if iguais[i,j].sum():
                    alvos_copiaveis += 1
                else:
                    # UNK permite medir cobertura; jamais é liberado na saída.
                    alvo_vocab[i,j] = 1;alvos_desconhecidos += 1
    return {"fonte":fonte,"mascara_fonte":mf,"chars_fonte":cf,"pesos_chars_fonte":wf,
            "x":x,"y":y,"mascara":mascara,"chars_x":cx,"pesos_chars_x":wx,
            "iguais":iguais,"alvo_vocab":alvo_vocab,
            "textos_fonte":fontes,"vocabulario":[t for t,_ in sorted(indices.items(),key=lambda item:item[1])],
            "alvos_copiaveis":alvos_copiaveis,"alvos_desconhecidos":alvos_desconhecidos}


def _embeddings(p,ids,chars,pesos):
    return p["E"][ids]+(p["C"][chars]*pesos[:,:,:,None]).sum(axis=2)


def _grad_embeddings(grad,ids,chars,pesos,de):
    import numpy as np
    np.add.at(grad["E"],ids.ravel(),de.reshape(-1,de.shape[-1]))
    np.add.at(grad["C"],chars.ravel(),(de[:,:,None,:]*pesos[:,:,:,None]).reshape(-1,de.shape[-1]))


def _gru(p,x,anterior,nome,mascara=None):
    import numpy as np
    h = anterior.shape[1]
    xi = x@p[nome+"W"]+p[nome+"b"]
    hu = anterior@p[nome+"U"][:,:2*h]
    z = 1/(1+np.exp(-np.clip(xi[:,:h]+hu[:,:h],-60,60)))
    r = 1/(1+np.exp(-np.clip(xi[:,h:2*h]+hu[:,h:],-60,60)))
    n = np.tanh(xi[:,2*h:]+(r*anterior)@p[nome+"U"][:,2*h:])
    novo = (1-z)*anterior+z*n
    if mascara is not None:
        novo = mascara[:,None]*novo+(1-mascara[:,None])*anterior
    return novo,(x,anterior,z,r,n,mascara)


def _gru_grad(p,grad,dh,cache,nome):
    import numpy as np
    x,anterior,z,r,n,mask = cache;h = anterior.shape[1]
    dt = dh if mask is None else dh*mask[:,None]
    previo = dt*(1-z)+(0 if mask is None else dh*(1-mask[:,None]))
    dn = dt*z*(1-n*n)
    dz = dt*(n-anterior)*z*(1-z)
    drh = dn@p[nome+"U"][:,2*h:].T
    dr = drh*anterior*r*(1-r);previo += drh*r
    dgs = np.concatenate((dz,dr,dn),axis=1)
    grad[nome+"W"] += x.T@dgs;grad[nome+"b"] += dgs.sum(axis=0)
    grad[nome+"U"][:,:2*h] += anterior.T@dgs[:,:2*h]
    grad[nome+"U"][:,2*h:] += (r*anterior).T@dn
    previo += dgs[:,:2*h]@p[nome+"U"][:,:2*h].T
    return dgs@p[nome+"W"].T,previo


def perda_gradientes(p,batch,gradientes=True,dropout=0.0,dropout_tokens=0.0,
                     amostragem=0.0,rng=None):
    """Gradientes analíticos: ambas GRUs, atenção, gate, cópia e subpalavras."""
    import numpy as np
    mf,x,y,mask = batch["mascara_fonte"],batch["x"],batch["y"],batch["mascara"]
    b,s = mf.shape;t = x.shape[1];h = p["Q"].shape[0];e = p["E"].shape[1]
    if any(not 0<=taxa<=.5 for taxa in (dropout,dropout_tokens,amostragem)):
        raise ValueError("Regularização deve estar entre zero e 0,5")
    if (dropout or dropout_tokens or amostragem) and rng is None:
        raise ValueError("Regularização exige gerador aleatório explícito")
    def mascara_locked(forma):
        return ((rng.random(forma)>=dropout).astype(p["E"].dtype)/(1-dropout)
                if dropout else np.ones(forma,dtype=p["E"].dtype))
    fonte_ids = batch["fonte"].copy() if dropout_tokens else batch["fonte"]
    if dropout_tokens:
        # Só o embedding lexical vira UNK. Literal, chars, papéis e cópia
        # permanecem iguais; jamais misturamos histórias ou eventos.
        apagar = (rng.random(fonte_ids.shape)<dropout_tokens)&(fonte_ids>=len(ESPECIAIS))&mf.astype(bool)
        fonte_ids[apagar] = DESCONHECIDO
    mascara_emb = mascara_locked((b,1,e));mascara_x = mascara_locked((b,1,e))
    mascara_saida = mascara_locked((b,3*h))
    chars_x,pesos_chars_x = batch["chars_x"],batch["pesos_chars_x"]
    if amostragem:
        x = x.copy();chars_x = chars_x.copy();pesos_chars_x = pesos_chars_x.copy()
    emb = _embeddings(p,fonte_ids,batch["chars_fonte"],batch["pesos_chars_fonte"])*mascara_emb
    dxemb = _embeddings(p,x,chars_x,pesos_chars_x)*mascara_x
    fwd,bwd = np.zeros((b,s,h),dtype=emb.dtype),np.zeros((b,s,h),dtype=emb.dtype)
    caches_enc = {}
    for nome,saida,ordem in (("EF",fwd,range(s)),("EB",bwd,range(s-1,-1,-1))):
        hc = np.zeros((b,h),dtype=emb.dtype);caches_enc[nome] = []
        for j in ordem:
            hc,cache = _gru(p,emb[:,j],hc,nome,mf[:,j])
            saida[:,j] = hc
            caches_enc[nome].append((j,cache))
    estados = np.concatenate((fwd,bwd),axis=2)
    fim = np.concatenate((fwd[:,-1],bwd[:,0]),axis=1)
    inicial = np.tanh(fim@p["I"]+p["bi"])
    chaves = estados@p["K"]
    hc = inicial.copy();ctx = np.zeros((b,2*h),dtype=emb.dtype)
    caches = [];soma = max(1,float(mask.sum()));perda = 0.0
    for j in range(t):
        entrada = np.concatenate((dxemb[:,j],ctx),axis=1)
        hc,cache_gru = _gru(p,entrada,hc,"D")
        query = hc@p["Q"]
        energia = np.einsum("bsa,ba->bs",chaves,query)/math.sqrt(h)
        energia = np.where(mf,energia,-1e9)
        att = np.exp(energia-energia.max(axis=1,keepdims=True));att /= att.sum(axis=1,keepdims=True)
        ctx = np.einsum("bs,bsh->bh",att,estados)
        combinado = np.concatenate((hc,ctx),axis=1)
        projetado = combinado*mascara_saida
        logits = projetado@p["O"]+p["bo"]
        ps = np.exp(logits-logits.max(axis=1,keepdims=True));ps /= ps.sum(axis=1,keepdims=True)
        gate_entrada = np.concatenate((dxemb[:,j],combinado),axis=1)
        gate = 1/(1+np.exp(-np.clip((gate_entrada@p["G"])[:,0]+p["bg"][0],-60,60)))
        pv = ps[np.arange(b),y[:,j]]*batch["alvo_vocab"][:,j]
        pc = (att*batch["iguais"][:,j]).sum(axis=1)
        py = np.maximum(gate*pv+(1-gate)*pc,1e-12)
        perda -= float((np.log(py)*mask[:,j]).sum())/soma
        if gradientes:
            caches.append((cache_gru,hc,query,att,ctx,combinado,ps,gate_entrada,gate,pv,pc,py))
        if amostragem and j+1<t:
            usar_modelo = (rng.random(b)<amostragem)&mask[:,j+1].astype(bool)
            vocab = batch["vocabulario"];indices = {tok:i for i,tok in enumerate(vocab)}
            for i in np.flatnonzero(usar_modelo):
                distribuicao = {tok:float(gate[i]*pv_) for tok,pv_ in zip(vocab,ps[i])}
                for k,tok in enumerate(batch["textos_fonte"][i]):
                    distribuicao[tok] = distribuicao.get(tok,0.0)+float((1-gate[i])*att[i,k])
                # A escolha discreta recebe stop-gradient. Os alvos, a fonte
                # e as origens são preservados, inclusive palavras OOV copiadas.
                palavra = max((tok for tok in distribuicao if tok not in ESPECIAIS or tok==ESPECIAIS[FIM]),
                              key=distribuicao.get)
                indice = indices.get(palavra,DESCONHECIDO);x[i,j+1] = indice
                partes = subpalavras(palavra,len(p["C"]))
                chars_x[i,j+1] = 0;pesos_chars_x[i,j+1] = 0
                if partes:
                    chars_x[i,j+1,:len(partes)] = partes
                    pesos_chars_x[i,j+1,:len(partes)] = 1/len(partes)
                vetor = p["E"][indice].copy()
                if partes:
                    vetor += p["C"][list(partes)].mean(axis=0)
                dxemb[i,j+1] = vetor*mascara_x[i,0]
    if not gradientes:
        return perda,None
    grad = {k:np.zeros_like(a) for k,a in p.items()}
    dh = np.zeros((b,h),dtype=emb.dtype);dctx = np.zeros((b,2*h),dtype=emb.dtype)
    destados = np.zeros_like(estados);dchaves = np.zeros_like(chaves)
    dxs = np.zeros_like(dxemb)
    for j in range(t-1,-1,-1):
        cache_gru,hc,query,att,ctx,combinado,ps,gate_entrada,gate,pv,pc,py = caches[j]
        fator = mask[:,j]/soma
        # Responsabilidade do ramo de geração na probabilidade observada.
        resp = gate*pv/py*fator
        dlogits = ps*resp[:,None];dlogits[np.arange(b),y[:,j]] -= resp
        grad["O"] += (combinado*mascara_saida).T@dlogits;grad["bo"] += dlogits.sum(axis=0)
        dcombinado = (dlogits@p["O"].T)*mascara_saida
        dgate = -(pv-pc)/py*fator*gate*(1-gate)
        grad["G"] += gate_entrada.T@dgate[:,None];grad["bg"] += dgate.sum()
        dgentrada = dgate[:,None]@p["G"].T
        dxs[:,j] += dgentrada[:,:e]
        dcombinado += dgentrada[:,e:]
        dh += dcombinado[:,:h];dctx += dcombinado[:,h:]
        datt = np.einsum("bh,bsh->bs",dctx,estados)
        datt -= ((1-gate)/py*fator)[:,None]*batch["iguais"][:,j]
        destados += att[:,:,None]*dctx[:,None,:]
        denergia = att*(datt-(att*datt).sum(axis=1,keepdims=True))
        denergia *= mf
        dchaves += denergia[:,:,None]*query[:,None,:]/math.sqrt(h)
        dq = np.einsum("bs,bsa->ba",denergia,chaves)/math.sqrt(h)
        grad["Q"] += hc.T@dq;dh += dq@p["Q"].T
        de,dh = _gru_grad(p,grad,dh,cache_gru,"D")
        dxs[:,j] += de[:,:e];dctx = de[:,e:]
    di = dh*(1-inicial*inicial)
    grad["I"] += fim.T@di;grad["bi"] += di.sum(axis=0)
    dfim = di@p["I"].T
    grad["K"] += estados.reshape(-1,2*h).T@dchaves.reshape(-1,h)
    destados += dchaves@p["K"].T
    dfwd,dbwd = destados[:,:,:h].copy(),destados[:,:,h:].copy()
    dfwd[:,-1] += dfim[:,:h];dbwd[:,0] += dfim[:,h:]
    demb = np.zeros_like(emb)
    for nome,dsaida in (("EF",dfwd),("EB",dbwd)):
        dh = np.zeros((b,h),dtype=emb.dtype)
        for j,cache in reversed(caches_enc[nome]):
            de,dh = _gru_grad(p,grad,dh+dsaida[:,j],cache,nome)
            demb[:,j] += de
    _grad_embeddings(grad,fonte_ids,batch["chars_fonte"],batch["pesos_chars_fonte"],demb*mascara_emb)
    _grad_embeddings(grad,x,chars_x,pesos_chars_x,dxs*mascara_x)
    return perda,grad


def checkpoint(p,vocabulario,ocultos,embeddings,buckets=512,limite_fonte=192,**metadados):
    import numpy as np
    return dict(versao=VERSAO,vocabulario=vocabulario,ocultos=ocultos,embeddings=embeddings,
                buckets=buckets,limite_fonte=limite_fonte,
                pesos={k:np.round(a.astype("float64"),7).tolist() for k,a in p.items()},**metadados)


def salvar_checkpoint(destino,dados):
    arquivo = Path(destino)
    temporario = arquivo.with_name(arquivo.name+".tmp")
    temporario.write_text(json.dumps(dados,ensure_ascii=False,separators=(",",":"),allow_nan=False)+"\n",
                          encoding="utf-8")
    os.replace(str(temporario),str(arquivo))


def _apenas_texto(exemplo):
    contexto = exemplo.get("contexto", exemplo)
    return {"mensagem":contexto["mensagem"],"historico":contexto.get("historico",[]),
            "resposta":exemplo["resposta"]}


def selecionar_adicional(caminho,limite_fonte=192,limite_resposta=96):
    """Usa pares completos licenciados; não corta a resposta ou o histórico."""
    dados = ler_json(caminho)
    exemplos = dados["exemplos"] if isinstance(dados,dict) else dados
    aceitos = []
    for ex in exemplos:
        texto = _apenas_texto(ex)
        tamanho_fonte = 1+len(tokenizar(texto["mensagem"]))+sum(
            1+len(tokenizar(h["texto"])) for h in texto["historico"])
        tamanho_alvo = 1+len(tokenizar(texto["resposta"]))
        if tamanho_fonte<=limite_fonte and 2<=tamanho_alvo<=limite_resposta:
            aceitos.append(dict(split=ex["split"],**texto))
    return aceitos


def ler_corpus(caminho,adicional=None,limite_fonte=192,limite_resposta=96):
    dados = ler_json(caminho)
    exemplos = dados["exemplos"] if isinstance(dados,dict) else dados
    if adicional is not None:
        exemplos = exemplos+selecionar_adicional(adicional,limite_fonte,limite_resposta)
    treino = [_apenas_texto(c) for c in exemplos if c.get("split")=="treino"]
    validacao = [_apenas_texto(c) for c in exemplos if c.get("split")=="validacao"]
    if not treino or not validacao or len(treino)+len(validacao) != len(exemplos):
        raise ValueError("Corpus deve separar explicitamente treino e validação")
    # Repetir exatamente a entrada/resposta nas duas partes invalida a avaliação.
    if {assinatura(c) for c in treino}&{assinatura(c) for c in validacao}:
        raise ValueError("Exemplos duplicados entre treino e validação")
    return treino,validacao


def avaliar_perda(p,casos,indices,buckets,limite_fonte,limite_resposta,lote_tamanho=32):
    perda,tokens,desconhecidos,copiaveis = 0.0,0,0,0
    for inicio in range(0,len(casos),lote_tamanho):
        batch = lote(casos[inicio:inicio+lote_tamanho],indices,buckets,limite_fonte,limite_resposta)
        valor,_ = perda_gradientes(p,batch,gradientes=False)
        n = int(batch["mascara"].sum());perda += valor*n;tokens += n
        desconhecidos += batch["alvos_desconhecidos"];copiaveis += batch["alvos_copiaveis"]
    return {"exemplos":len(casos),"tokens":tokens,"entropia_cruzada":perda/max(1,tokens),
            "perplexidade":math.exp(min(50,perda/max(1,tokens))),
            "alvos_desconhecidos_nao_copiaveis":desconhecidos,"alvos_ineditos_copiaveis":copiaveis}


def avaliar_geracao(dados,casos,limite_resposta=96,maximo=48,semente=173):
    """Amostra fixa da validação: decodificação livre, sem resposta como entrada.

    Correspondência literal mede reprodução do alvo; não mede pertinência,
    verdade factual ou compreensão geral. As saídas permitem revisão humana.
    """
    import random
    modelo = DialogoSeq2Seq(dados)
    escolhidos = (list(range(len(casos))) if maximo is None else
                  sorted(random.Random(semente).sample(range(len(casos)),min(maximo,len(casos)))))
    saidas = [];inicio = time.monotonic()
    for i in escolhidos:
        ex = casos[i]
        gerada = modelo.gerar(ex["mensagem"],ex.get("historico",[]),max_tokens=limite_resposta)
        alvo = [t.casefold() for t in tokenizar(ex["resposta"])]
        obtido = [t.casefold() for t in gerada["tokens"]]
        saidas.append({"indice":i,"mensagem":ex["mensagem"],"historico":ex.get("historico",[]),
                       "alvo":ex["resposta"],"gerada":gerada["texto"],
                       "completa":gerada["completa"],"igual_ao_alvo":alvo == obtido,
                       "log_prob_media":gerada["log_prob_media"],
                       "proporcao_geracao":gerada["proporcao_geracao"],
                       "tokens_gerados":len(gerada["tokens"]),"fonte_tokens":gerada["fonte_tokens"]})
    n = max(1,len(saidas))
    return {"exemplos":len(saidas),"semente":semente,
            "completas":sum(s["completa"] for s in saidas),
            "iguais_ao_alvo":sum(s["igual_ao_alvo"] for s in saidas),
            "segundos":round(time.monotonic()-inicio,3),"saidas":saidas,
            "limite":"Amostra de desenvolvimento, sem avaliação automática de pertinência ou veracidade; sem calibração com diálogos externos."}


def avaliar_por_intencao(dados,caminho,adicional=None,limite_resposta=96,semente=173):
    """Todas as saídas da validação; atos servem só para agrupar o relatório."""
    import random
    corpus = ler_json(caminho)
    exemplos = corpus["exemplos"] if isinstance(corpus,dict) else corpus
    exemplos = [e for e in exemplos if e["split"] == "validacao"]
    if adicional is not None:
        exemplos += [e for e in selecionar_adicional(adicional,dados.get("limite_fonte",192),limite_resposta)
                     if e["split"] == "validacao"]
    casos = [_apenas_texto(e) for e in exemplos]
    avaliacao = avaliar_geracao(dados,casos,limite_resposta,maximo=None,semente=semente)
    grupos = {};vocab = set(dados["vocabulario"])
    for saida,ex in zip(avaliacao["saidas"],exemplos):
        ato = ex.get("ato","humano")
        saida["ato"] = ato
        fonte = set(fonte_dialogo(saida["mensagem"],saida["historico"],dados.get("limite_fonte",192)))
        oov = set(tokenizar(saida["gerada"]))-vocab
        saida["copias_literais_oov"] = sorted(oov & fonte)
        grupos.setdefault(ato,[]).append(saida)
    resumo = {}
    rng = random.Random(semente)
    for ato,saidas in sorted(grupos.items()):
        resumo[ato] = {"exemplos":len(saidas),"completas":sum(s["completa"] for s in saidas),
                       "iguais_ao_alvo":sum(s["igual_ao_alvo"] for s in saidas),
                       "media_log_prob":sum(s["log_prob_media"] for s in saidas)/len(saidas),
                       "com_copia_oov":sum(bool(s["copias_literais_oov"]) for s in saidas),
                       "amostra":sorted(rng.sample([s["indice"] for s in saidas],min(3,len(saidas))))}
    avaliacao["por_intencao"] = resumo
    avaliacao["limite"] = "Validação interna completa, sem alvos ou atos na entrada da geração. EOS, cópia, correspondência literal e probabilidade neural não demonstram pertinência, gramática, veracidade ou compreensão; textos devem ser revisados. Não há calibração com sondas externas."
    return avaliacao


def treinar(caminho,destino,epocas=25,lote_tamanho=32,ocultos=96,embeddings=64,
            vocab_max=2500,buckets=512,limite_fonte=192,limite_resposta=64,
            semente=173,taxa=.002,decaimento=.00001,validar_cada=2,paciencia=8,adicional=None,
            checkpoint_temporario=None,dropout=0.0,dropout_tokens=0.0,amostragem=0.0,aquecimento=3):
    import numpy as np
    if (not 1<=epocas<=1000 or not 1<=lote_tamanho<=128 or not 16<=ocultos<=128 or
            not 8<=embeddings<=96 or not 16<=vocab_max<=8192 or not 32<=buckets<=2048 or
            not 8<=limite_fonte<=512 or not 4<=limite_resposta<=128 or not 0<taxa<=.02 or
            not 1<=validar_cada<=1000 or not 1<=paciencia<=1000 or
            any(not 0<=prob<=.5 for prob in (dropout,dropout_tokens,amostragem)) or
            not 0<=aquecimento<=1000):
        raise ValueError("Configuração de treinamento inválida")
    treino,validacao = ler_corpus(caminho,adicional,limite_fonte,limite_resposta)
    vocabulario = vocabulario_treino(treino,vocab_max);indices = {t:i for i,t in enumerate(vocabulario)}
    p = inicializar(vocabulario,ocultos,embeddings,buckets,semente)
    momentos = {k:np.zeros_like(a) for k,a in p.items()};quadrados = {k:np.zeros_like(a) for k,a in p.items()}
    rng = np.random.default_rng(semente);passo = 0;entropias = [];inicio_treino = time.monotonic()
    validacoes = [];melhor = None;melhor_valor = float("inf");melhor_epoca = 0;sem_melhoria = 0
    print("Parâmetros",sum(a.size for a in p.values()),"vocabulário",len(vocabulario),
          "exemplos",len(treino),flush=True)
    for epoca in range(epocas):
        taxa_amostragem = min(amostragem,amostragem*max(0,epoca-aquecimento+1)/3)
        # Comprimentos próximos limitam padding sem alterar a sequência original.
        ordem = rng.permutation(len(treino)).tolist();perdas=[];tokens_total=0;perda_total=0.0
        grupos = [ordem[j:j+lote_tamanho*8] for j in range(0,len(ordem),lote_tamanho*8)]
        batches = []
        for grupo in grupos:
            grupo.sort(key=lambda i:len(tokenizar(treino[i]["mensagem"]))+
                       sum(len(tokenizar(h["texto"])) for h in treino[i].get("historico",[])))
            batches += [grupo[j:j+lote_tamanho] for j in range(0,len(grupo),lote_tamanho)]
        rng.shuffle(batches)
        for pos in batches:
            batch = lote([treino[i] for i in pos],indices,buckets,limite_fonte,limite_resposta)
            perda,g = perda_gradientes(p,batch,dropout=dropout,dropout_tokens=dropout_tokens,
                                      amostragem=taxa_amostragem,rng=rng)
            n = int(batch["mascara"].sum())
            if not math.isfinite(perda) or any(not np.isfinite(a).all() for a in g.values()):
                raise ValueError("Treinamento produziu perda ou gradiente não finito")
            perdas.append(perda);tokens_total += n;perda_total += perda*n
            norma = math.sqrt(sum(float((a*a).sum()) for a in g.values()))
            escala = min(1.0,5/max(norma,1e-12));passo += 1
            for k in p:
                dg = g[k]*escala
                momentos[k] = .9*momentos[k]+.1*dg;quadrados[k] = .999*quadrados[k]+.001*dg*dg
                p[k] -= taxa*(momentos[k]/(1-.9**passo))/(np.sqrt(quadrados[k]/(1-.999**passo))+1e-8)
                if p[k].ndim == 2:
                    p[k] *= 1-taxa*decaimento
        media = perda_total/max(1,tokens_total);entropias.append(media)
        print("Época",epoca+1,"entropia treino",round(media,4),"segundos",round(time.monotonic()-inicio_treino,1),flush=True)
        if (epoca+1)%validar_cada == 0 or epoca+1 == epocas:
            medicao = avaliar_perda(p,validacao,indices,buckets,limite_fonte,limite_resposta,lote_tamanho)
            validacoes.append(dict(epoca=epoca+1,**medicao))
            valor = medicao["entropia_cruzada"]
            print("Validação",epoca+1,"entropia",round(valor,4),"perplexidade",round(medicao["perplexidade"],3),flush=True)
            if valor < melhor_valor-1e-5:
                melhor_valor,melhor_epoca = valor,epoca+1
                melhor = {k:a.copy() for k,a in p.items()};sem_melhoria = 0
                if checkpoint_temporario is not None:
                    salvar_checkpoint(checkpoint_temporario,checkpoint(
                        p,vocabulario,ocultos,embeddings,buckets,limite_fonte,
                        treino={"epoca":epoca+1,"parametros":sum(a.size for a in p.values()),
                                "estado":"parcial; sem relatório de geração livre"},
                        limites={"fonte_tokens":limite_fonte,"resposta_tokens":limite_resposta}))
            else:
                sem_melhoria += validar_cada
            if sem_melhoria >= paciencia:
                print("Parada por validação; melhor época",melhor_epoca,flush=True)
                break
    if melhor is not None:
        p = melhor
    meta = {"arquitetura":"BiGRU encoder + GRU decoder + atenção e pointer-generator",
            "assinatura_treino":assinatura(treino),"assinatura_validacao":assinatura(validacao),
            "treino":{"epocas_solicitadas":epocas,"epocas":len(entropias),"epoca_selecionada":melhor_epoca,
                      "validar_cada":validar_cada,"paciencia":paciencia,
                      "dropout_locked":dropout,"dropout_lexical_fonte":dropout_tokens,
                      "scheduled_sampling_max":amostragem,"scheduled_sampling_aquecimento":aquecimento,
                      "regularizacao":"Máscaras locked em embeddings e projeção; dropout lexical mantém chars/literais/origens; amostragem autoregressiva recebe stop-gradient e não altera alvos.",
                      "lote":lote_tamanho,"semente":semente,"taxa":taxa,
                      "decaimento":decaimento,"exemplos":len(treino),"parametros":sum(a.size for a in p.values()),
                      "entropias":entropias,"validacoes":validacoes,
                      "segundos":round(time.monotonic()-inicio_treino,2)},
            "limites":{"fonte_tokens":limite_fonte,"resposta_tokens":limite_resposta},
            "limite":"Rede pequena treinada do zero. Validação interna não demonstra conversa universal, consciência ou aprendizado automático durante uso. O checkpoint não contém corpus nem catálogo de respostas."}
    if adicional is not None:
        selecionados = selecionar_adicional(adicional,limite_fonte,limite_resposta)
        meta["corpus_adicional"] = {"arquivo":str(adicional),
                                   "sha256_arquivo":hashlib.sha256(Path(adicional).read_bytes()).hexdigest(),
                                   "treino":sum(e["split"] == "treino" for e in selecionados),
                                   "validacao":sum(e["split"] == "validacao" for e in selecionados),
                                   "selecao":"Pares completos cuja fonte inteira e resposta com EOS cabem nos limites; sem truncamento."}
    dados = checkpoint(p,vocabulario,ocultos,embeddings,buckets,limite_fonte,**meta)
    salvar_checkpoint(destino,dados)
    resultado = {"treino":avaliar_perda(p,treino,indices,buckets,limite_fonte,limite_resposta,lote_tamanho),
                 "validacao":avaliar_perda(p,validacao,indices,buckets,limite_fonte,limite_resposta,lote_tamanho),
                 "geracao_validacao":avaliar_geracao(dados,validacao,limite_resposta,semente=semente),
                 "metadados":meta}
    resultado["geracao_desenvolvimento"] = avaliar_por_intencao(dados,caminho,adicional,limite_resposta,semente)
    if adicional is not None:
        humanos = [_apenas_texto(e) for e in selecionados if e["split"] == "validacao"]
        resultado["humanos_validacao"] = {
            "perda":avaliar_perda(p,humanos,indices,buckets,limite_fonte,limite_resposta,lote_tamanho),
            "geracao":avaliar_geracao(dados,humanos,limite_resposta,semente=semente),
            "limite":"A amostra humana é pequena e separada por árvore; não calibra aceitação nem demonstra generalização irrestrita."}
    return resultado


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus",required=True);ap.add_argument("--saida",default="rede_dialogo_seq2seq.json")
    ap.add_argument("--dialogos-humanos",default=None)
    ap.add_argument("--checkpoint-temporario",default=None)
    ap.add_argument("--relatorio",default="avaliacao_dialogo_seq2seq.json")
    ap.add_argument("--epocas",type=int,default=25);ap.add_argument("--lote",type=int,default=32)
    ap.add_argument("--ocultos",type=int,default=96);ap.add_argument("--embeddings",type=int,default=64)
    ap.add_argument("--vocab-max",type=int,default=2500);ap.add_argument("--buckets",type=int,default=512)
    ap.add_argument("--limite-fonte",type=int,default=192);ap.add_argument("--limite-resposta",type=int,default=64)
    ap.add_argument("--semente",type=int,default=173);ap.add_argument("--taxa",type=float,default=.002)
    ap.add_argument("--validar-cada",type=int,default=2);ap.add_argument("--paciencia",type=int,default=8)
    ap.add_argument("--dropout",type=float,default=0);ap.add_argument("--dropout-tokens",type=float,default=0)
    ap.add_argument("--amostragem",type=float,default=0);ap.add_argument("--aquecimento",type=int,default=3)
    args = ap.parse_args()
    resultado = treinar(args.corpus,args.saida,args.epocas,args.lote,args.ocultos,args.embeddings,
                       args.vocab_max,args.buckets,args.limite_fonte,args.limite_resposta,args.semente,args.taxa,
                       validar_cada=args.validar_cada,paciencia=args.paciencia,adicional=args.dialogos_humanos,
                       checkpoint_temporario=args.checkpoint_temporario,dropout=args.dropout,
                       dropout_tokens=args.dropout_tokens,amostragem=args.amostragem,aquecimento=args.aquecimento)
    Path(args.relatorio).write_text(json.dumps(resultado,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
