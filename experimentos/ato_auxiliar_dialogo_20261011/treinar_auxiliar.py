"""Treino experimental com perda auxiliar de ato no estado inicial da GRU.

A cabeça de 6 classes existe somente no treino. Nenhum rótulo de ato entra na
inferência e Waux/baux nunca são serializados no checkpoint final.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
DIR = Path(__file__).resolve().parent
OLD = RAIZ / "experimentos" / "gerador_historico_textual_20261010"
FAT = RAIZ / "experimentos" / "corpus_fatorial_20261011"
sys.path.insert(0, str(RAIZ))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, tokenizar, formas
from treinar_dialogo_seq2seq import (
    _embeddings, _grad_embeddings, _gru, _gru_grad, lote, perda_gradientes,
    avaliar_perda, avaliar_geracao, checkpoint,
)

ATOS = (
    "recordar_pessoa", "recordar_objeto", "corrigir_pessoa",
    "guardar_hipotese", "mensagem_sem_horario", "pedir_detalhe",
)
ATO_ID = {a:i for i,a in enumerate(ATOS)}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def gravar_json(path: Path, dados) -> None:
    path.write_text(json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def gravar_gz(path: Path, dados) -> None:
    bruto = (json.dumps(dados, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    path.write_bytes(gzip.compress(bruto, mtime=0))


def texto(ex):
    return {"mensagem": ex["mensagem"], "historico": ex.get("historico", []), "resposta": ex["resposta"]}


def norm(s):
    return re.sub(r"\s+", " ", str(s).casefold().strip())


def estado_inicial_com_cache(p, batch):
    mf = batch["mascara_fonte"]
    b, s = mf.shape
    h = p["I"].shape[1]
    emb = _embeddings(p, batch["fonte"], batch["chars_fonte"], batch["pesos_chars_fonte"])
    fwd = np.zeros((b, s, h), dtype=emb.dtype)
    bwd = np.zeros((b, s, h), dtype=emb.dtype)
    caches = {}
    for nome, saida, ordem in (("EF", fwd, range(s)), ("EB", bwd, range(s-1, -1, -1))):
        hc = np.zeros((b, h), dtype=emb.dtype)
        caches[nome] = []
        for j in ordem:
            hc, cache = _gru(p, emb[:, j], hc, nome, mf[:, j])
            saida[:, j] = hc
            caches[nome].append((j, cache))
    fim = np.concatenate((fwd[:, -1], bwd[:, 0]), axis=1)
    inicial = np.tanh(fim @ p["I"] + p["bi"])
    return inicial, fim, fwd, bwd, caches


def gradiente_auxiliar(p, batch, labels, waux, baux):
    """CE de 6 atos; gradiente só volta por I/bi, encoder e embeddings."""
    inicial, fim, fwd, bwd, caches = estado_inicial_com_cache(p, batch)
    labels = np.asarray(labels, dtype=np.int64)
    validos = np.flatnonzero(labels >= 0)
    grad = {k: np.zeros_like(v) for k, v in p.items()}
    if not len(validos):
        return 0.0, grad, np.zeros_like(waux), np.zeros_like(baux), 0, 0

    z = inicial[validos] @ waux + baux
    z -= z.max(axis=1, keepdims=True)
    probs = np.exp(z); probs /= probs.sum(axis=1, keepdims=True)
    y = labels[validos]
    perda = -float(np.log(np.maximum(probs[np.arange(len(y)), y], 1e-12)).mean())
    corretos = int((probs.argmax(axis=1) == y).sum())

    dz = probs
    dz[np.arange(len(y)), y] -= 1
    dz /= len(y)
    gw = inicial[validos].T @ dz
    gb = dz.sum(axis=0)
    dinicial = np.zeros_like(inicial)
    dinicial[validos] = dz @ waux.T

    di = dinicial * (1 - inicial * inicial)
    grad["I"] += fim.T @ di
    grad["bi"] += di.sum(axis=0)
    dfim = di @ p["I"].T
    h = p["I"].shape[1]
    dfwd = np.zeros_like(fwd); dbwd = np.zeros_like(bwd)
    dfwd[:, -1] += dfim[:, :h]
    dbwd[:, 0] += dfim[:, h:]
    demb = np.zeros((batch["fonte"].shape[0], batch["fonte"].shape[1], p["E"].shape[1]), dtype=p["E"].dtype)
    for nome, dsaida in (("EF", dfwd), ("EB", dbwd)):
        dh = np.zeros((batch["fonte"].shape[0], h), dtype=p["E"].dtype)
        for j, cache in reversed(caches[nome]):
            de, dh = _gru_grad(p, grad, dh + dsaida[:, j], cache, nome)
            demb[:, j] += de
    _grad_embeddings(grad, batch["fonte"], batch["chars_fonte"], batch["pesos_chars_fonte"], demb)
    return perda, grad, gw, gb, corretos, len(y)


def acuracia_auxiliar(p, exemplos_raw, indices, buckets, limite_fonte, limite_resposta, waux, baux, lote_tamanho=64):
    total = corretos = 0; perda_soma = 0.0
    rotulados = [e for e in exemplos_raw if e.get("operacao") in ATO_ID]
    for inicio in range(0, len(rotulados), lote_tamanho):
        es = rotulados[inicio:inicio+lote_tamanho]
        batch = lote([texto(e) for e in es], indices, buckets, limite_fonte, limite_resposta)
        inicial, *_ = estado_inicial_com_cache(p, batch)
        logits = inicial @ waux + baux
        logits -= logits.max(axis=1, keepdims=True)
        probs = np.exp(logits); probs /= probs.sum(axis=1, keepdims=True)
        y = np.asarray([ATO_ID[e["operacao"]] for e in es], dtype=np.int64)
        perda_soma += -float(np.log(np.maximum(probs[np.arange(len(y)), y], 1e-12)).sum())
        corretos += int((probs.argmax(axis=1) == y).sum()); total += len(y)
    return {"exemplos": total, "corretos": corretos, "acuracia": corretos/max(1,total), "entropia_cruzada": perda_soma/max(1,total)}


def treinar_auxiliar(corpus_path: Path, init_path: Path, protocolo):
    hcfg = protocolo["hiperparametros"]
    bruto = ler_json(corpus_path)
    exemplos = bruto["exemplos"] if isinstance(bruto, dict) else bruto
    treino_raw = [e for e in exemplos if e.get("split") == "treino"]
    valid_raw = [e for e in exemplos if e.get("split") == "validacao"]
    treino = [texto(e) for e in treino_raw]; validacao = [texto(e) for e in valid_raw]
    if (len(treino), len(validacao)) != (3699, 382):
        raise ValueError(f"Splits fatoriais inesperados: {(len(treino), len(validacao))}")
    if set(e.get("operacao") for e in treino_raw if e.get("operacao")) != set(ATOS):
        raise ValueError("Rótulos de ato inesperados")

    dados_ini = ler_json(init_path)
    modelo_ini = DialogoSeq2Seq(dados_ini)
    if (modelo_ini.ocultos, modelo_ini.embeddings, modelo_ini.buckets, len(modelo_ini.vocabulario)) != (
        hcfg["ocultos"], hcfg["embeddings"], hcfg["buckets"], hcfg["vocab_max"]):
        raise ValueError("Inicialização incompatível")
    vocab = list(modelo_ini.vocabulario); indices = {t:i for i,t in enumerate(vocab)}
    p = {k: np.asarray(v, dtype=np.float32).copy() for k,v in dados_ini["pesos"].items()}
    if sum(a.size for a in p.values()) != protocolo["modelo_producao"]["parametros"]:
        raise ValueError("Contagem de parâmetros base mudou")

    seed = hcfg["semente"]
    rng = np.random.default_rng(seed)
    rng_aux = np.random.default_rng(seed + 7919)
    hidden = hcfg["ocultos"]
    waux = rng_aux.normal(0, 1/math.sqrt(hidden), (hidden, len(ATOS))).astype(np.float32)
    baux = np.zeros(len(ATOS), dtype=np.float32)
    momentos = {k:np.zeros_like(v) for k,v in p.items()}; quadrados = {k:np.zeros_like(v) for k,v in p.items()}
    mw=np.zeros_like(waux); vw=np.zeros_like(waux); mb=np.zeros_like(baux); vb=np.zeros_like(baux)
    passo=0; inicio_treino=time.monotonic(); entropias=[]; aux_epocas=[]; validacoes=[]
    melhor=None; melhor_w=None; melhor_b=None; melhor_valor=float("inf"); melhor_epoca=0; sem_melhoria=0
    lam=float(protocolo["treino"]["lambda_auxiliar"])

    for epoca in range(hcfg["epocas"]):
        taxa_amostragem=min(hcfg["amostragem"], hcfg["amostragem"]*max(0, epoca-hcfg["aquecimento"]+1)/3)
        ordem=rng.permutation(len(treino)).tolist()
        grupos=[ordem[j:j+hcfg["lote_tamanho"]*8] for j in range(0,len(ordem),hcfg["lote_tamanho"]*8)]
        batches=[]
        for grupo in grupos:
            grupo.sort(key=lambda i: len(tokenizar(treino[i]["mensagem"])) + sum(len(tokenizar(x["texto"])) for x in treino[i].get("historico",[])))
            batches += [grupo[j:j+hcfg["lote_tamanho"]] for j in range(0,len(grupo),hcfg["lote_tamanho"])]
        rng.shuffle(batches)
        seq_total=aux_total=0.0; tokens_total=rot_total=aux_ok=0
        for pos in batches:
            textos=[treino[i] for i in pos]
            batch=lote(textos, indices, hcfg["buckets"], hcfg["limite_fonte"], hcfg["limite_resposta"])
            perda_seq,g=perda_gradientes(p,batch,dropout=hcfg["dropout"],dropout_tokens=hcfg["dropout_tokens"],amostragem=taxa_amostragem,rng=rng)
            labels=[ATO_ID.get(treino_raw[i].get("operacao"), -1) for i in pos]
            perda_aux,gaux,gw,gb,ac,nt=gradiente_auxiliar(p,batch,labels,waux,baux)
            for k in g:
                g[k] += lam*gaux[k]
            gw*=lam; gb*=lam
            if not math.isfinite(perda_seq+perda_aux) or any(not np.isfinite(x).all() for x in g.values()) or not np.isfinite(gw).all() or not np.isfinite(gb).all():
                raise ValueError("Gradiente auxiliar não finito")
            n=int(batch["mascara"].sum()); seq_total += perda_seq*n; tokens_total += n
            aux_total += perda_aux*nt; rot_total += nt; aux_ok += ac
            norma=math.sqrt(sum(float((x*x).sum()) for x in g.values()) + float((gw*gw).sum()) + float((gb*gb).sum()))
            escala=min(1.0,5/max(norma,1e-12)); passo += 1
            for k in p:
                dg=g[k]*escala
                momentos[k]=.9*momentos[k]+.1*dg; quadrados[k]=.999*quadrados[k]+.001*dg*dg
                p[k]-=hcfg["taxa"]*(momentos[k]/(1-.9**passo))/(np.sqrt(quadrados[k]/(1-.999**passo))+1e-8)
                if p[k].ndim==2: p[k]*=1-hcfg["taxa"]*hcfg.get("decaimento",.00001)
            dgw=gw*escala; dgb=gb*escala
            mw=.9*mw+.1*dgw; vw=.999*vw+.001*dgw*dgw
            mb=.9*mb+.1*dgb; vb=.999*vb+.001*dgb*dgb
            waux-=hcfg["taxa"]*(mw/(1-.9**passo))/(np.sqrt(vw/(1-.999**passo))+1e-8)
            baux-=hcfg["taxa"]*(mb/(1-.9**passo))/(np.sqrt(vb/(1-.999**passo))+1e-8)
        media=seq_total/max(1,tokens_total); entropias.append(media)
        aux_epocas.append({"epoca":epoca+1,"perda":aux_total/max(1,rot_total),"acuracia":aux_ok/max(1,rot_total),"rotulados":rot_total})
        print("Época",epoca+1,"CE geração",round(media,4),"aux",round(aux_epocas[-1]["perda"],4),"acc",round(aux_epocas[-1]["acuracia"],4),flush=True)
        if (epoca+1)%hcfg["validar_cada"]==0 or epoca+1==hcfg["epocas"]:
            med=avaliar_perda(p,validacao,indices,hcfg["buckets"],hcfg["limite_fonte"],hcfg["limite_resposta"],hcfg["lote_tamanho"])
            validacoes.append(dict(epoca=epoca+1,**med)); valor=med["entropia_cruzada"]
            print("Validação geração",epoca+1,round(valor,4),flush=True)
            if valor < melhor_valor-1e-5:
                melhor_valor=valor; melhor_epoca=epoca+1; sem_melhoria=0
                melhor={k:v.copy() for k,v in p.items()}; melhor_w=waux.copy(); melhor_b=baux.copy()
            else:
                sem_melhoria += hcfg["validar_cada"]
            if sem_melhoria >= hcfg["paciencia"]:
                print("Parada por validação; melhor época",melhor_epoca,flush=True); break
    if melhor is None:
        raise ValueError("Nenhuma época selecionada")
    p=melhor; waux=melhor_w; baux=melhor_b
    aux_train=acuracia_auxiliar(p,treino_raw,indices,hcfg["buckets"],hcfg["limite_fonte"],hcfg["limite_resposta"],waux,baux)
    aux_dev=acuracia_auxiliar(p,valid_raw,indices,hcfg["buckets"],hcfg["limite_fonte"],hcfg["limite_resposta"],waux,baux)
    meta={
        "arquitetura":"BiGRU encoder + GRU decoder + atenção e pointer-generator; cabeça auxiliar descartada",
        "treino":{"epocas_solicitadas":hcfg["epocas"],"epocas":len(entropias),"epoca_selecionada":melhor_epoca,"exemplos":len(treino),"parametros":sum(v.size for v in p.values()),"entropias":entropias,"validacoes":validacoes,"aux_por_epoca":aux_epocas,"lambda_auxiliar":lam,"segundos":round(time.monotonic()-inicio_treino,2)},
        "auxiliar":{"classes":list(ATOS),"cabeca_parametros_treino":int(waux.size+baux.size),"serializada":False,"treino":aux_train,"validacao_rotulada":aux_dev},
        "limites":{"fonte_tokens":hcfg["limite_fonte"],"resposta_tokens":hcfg["limite_resposta"]},
        "aprovado":False,"ativo_no_chat":False,
    }
    dados=checkpoint(p,vocab,hcfg["ocultos"],hcfg["embeddings"],hcfg["buckets"],hcfg["limite_fonte"],**meta)
    if set(dados["pesos"]) != set(formas(vocab,hcfg["ocultos"],hcfg["embeddings"],hcfg["buckets"])):
        raise ValueError("Cabeça auxiliar vazou para checkpoint")
    if sum(np.asarray(v).size for v in dados["pesos"].values()) != protocolo["modelo_producao"]["parametros"]:
        raise ValueError("Checkpoint serializado mudou de tamanho")
    return dados, {"epoca_selecionada":melhor_epoca,"validacao_ce":melhor_valor,"aux_train":aux_train,"aux_dev":aux_dev,"segundos":round(time.monotonic()-inicio_treino,2)}


def _nome_alvo(ex):
    if ex.get("esperado_nome"): return norm(ex["esperado_nome"])
    m=re.search(r"[\wÀ-ÿ]+-\d+", ex["resposta"], re.UNICODE)
    return norm(m.group(0)) if m else ""


def _objeto_alvo(ex):
    if ex.get("objeto"): return norm(ex["objeto"])
    a=norm(ex["resposta"])
    for padrao in (r"objeto é ([^\s.,!?;]+)", r"falando do ([^\s.,!?;]+)"):
        m=re.search(padrao,a)
        if m:return m.group(1)
    return ""


def _atividade_alvo(ex):
    if ex.get("atividade"): return norm(ex["atividade"])
    a=norm(ex["resposta"]);m=re.search(r"combinar ([^\s.,!?;]+)",a)
    return m.group(1) if m else ""


def score_operacao(ex, gerada):
    g=norm(gerada); op=ex["operacao"]
    nome=_nome_alvo(ex); objeto=_objeto_alvo(ex); atividade=_atividade_alvo(ex)
    if op=="recordar_pessoa": return bool(nome) and nome in g
    if op=="recordar_objeto": return bool(objeto) and objeto in g
    if op=="corrigir_pessoa":
        antigo=norm(ex.get("nome_antes", ""))
        return bool(nome) and nome in g and (not antigo or antigo==nome or antigo not in g)
    if op=="guardar_hipotese": return any(m in g for m in ("possibilidade","ainda não","não está confirmado","não é certeza","continua incerto"))
    if op=="mensagem_sem_horario":
        proibidos=("hoje","amanhã","ontem","horário"," horas","depois de amanhã")
        return bool(nome and atividade) and nome in g and atividade in g and not any(x in g for x in proibidos)
    if op=="pedir_detalhe": return bool(nome) and nome in g and "?" in gerada and ("o que" in g or "qual" in g)
    raise ValueError(op)


def avaliar_bloco(dados, exemplos, operacoes=False):
    modelo=DialogoSeq2Seq(dados); casos=[texto(e) for e in exemplos]
    perda=avaliar_perda(modelo.pesos,casos,modelo.indices,modelo.buckets,modelo.limite_fonte,64,lote_tamanho=32)
    livre=avaliar_geracao(dados,casos,limite_resposta=64,maximo=None,semente=179)
    primeiro=0
    for e in exemplos:
        alvo=tokenizar(e["resposta"])[0]; dist=modelo.probabilidades(e["mensagem"],e.get("historico",[]))
        top=max(dist.items(),key=lambda kv:(kv[1],kv[0]))[0]
        primeiro += top.casefold()==alvo.casefold()
    out={"perda":perda,"geracao":{k:v for k,v in livre.items() if k!="saidas"},"primeiro_token":{"corretos":primeiro,"total":len(exemplos),"acuracia":primeiro/max(1,len(exemplos))}}
    if operacoes:
        detalhes=[]
        for e,s in zip(exemplos,livre["saidas"]):
            ok=bool(score_operacao(e,s["gerada"]));detalhes.append({"id":e["id"],"operacao":e["operacao"],"passou":ok,"gerada":s["gerada"],"alvo":e["resposta"]})
        por={}
        for op in ATOS:
            ds=[d for d in detalhes if d["operacao"]==op]; ac=sum(d["passou"] for d in ds)
            por[op]={"acertos":ac,"total":len(ds),"taxa":ac/max(1,len(ds))}
        ac=sum(d["passou"] for d in detalhes)
        out["operacoes"]={"acertos":ac,"total":len(detalhes),"taxa":ac/max(1,len(detalhes)),"por_operacao":por,"detalhes":detalhes}
    return out


def executar():
    protocolo=ler_json(DIR/"protocolo.json"); mh=ler_json(DIR/"manifesto_holdout.json")
    holdout_path=DIR/"holdout_novo.json"; corpus_path=RAIZ/protocolo["treino"]["corpus"]; init_path=RAIZ/protocolo["treino"]["inicializacao"]
    if not mh.get("aprovado") or sha256(holdout_path)!=mh["holdout_sha256"]: raise ValueError("Holdout congelado inválido")
    if sha256(corpus_path)!=protocolo["treino"]["corpus_sha256"] or sha256(init_path)!=protocolo["treino"]["inicializacao_sha256"]: raise ValueError("Fontes de treino mudaram")
    fat_protocol=ler_json(FAT/"protocolo.json"); fat_results=ler_json(FAT/"resultados_treino.json")
    ctrl_path=OLD/"checkpoint_sessoes.json.gz"; fat_path=FAT/"checkpoint_fatorial.json.gz"; old_corpus=OLD/"corpus_sessoes.json.gz"
    if sha256(ctrl_path)!=fat_protocol["controle"]["checkpoint_sha256"]: raise ValueError("Controle mudou")
    if sha256(fat_path)!=fat_results["treino"]["checkpoint_sha256"]: raise ValueError("Fatorial mudou")

    inicio=time.monotonic(); cand,treino_info=treinar_auxiliar(corpus_path,init_path,protocolo)
    destino=DIR/"checkpoint_auxiliar.json.gz"; cand.update(experimento="ato-auxiliar-dialogo-20261011",sha256_holdout=mh["holdout_sha256"],aprovado=False,ativo_no_chat=False)
    gravar_gz(destino,cand)
    if sha256(holdout_path)!=mh["holdout_sha256"]: raise ValueError("Holdout mudou durante treino")

    novo=ler_json(holdout_path)["exemplos"]
    old=ler_json(old_corpus)["exemplos"]
    old334=[e for e in old if e.get("split")=="validacao" and e.get("grupo")!="sessao_completa"]
    known94=[e for e in old if e.get("split")=="validacao" and e.get("grupo")=="sessao_completa"]
    fat96=ler_json(FAT/"avaliacao_final_fatorial.json")["exemplos"]
    if (len(old334),len(known94),len(fat96),len(novo))!=(334,94,96,144): raise ValueError("Recortes de avaliação mudaram")

    modelos={"controle_1x":ler_json(ctrl_path),"fatorial":ler_json(fat_path),"auxiliar":cand}
    aval={nome:{"old334":avaliar_bloco(d,old334),"known94":avaliar_bloco(d,known94),"fatorial96":avaliar_bloco(d,fat96,True),"holdout144":avaliar_bloco(d,novo,True)} for nome,d in modelos.items()}
    c=aval["controle_1x"]; f=aval["fatorial"]; n=aval["auxiliar"]; g=protocolo["portao_candidato"]
    best_ce=min(c["holdout144"]["perda"]["entropia_cruzada"],f["holdout144"]["perda"]["entropia_cruzada"])
    best_first=max(c["holdout144"]["primeiro_token"]["acuracia"],f["holdout144"]["primeiro_token"]["acuracia"])
    best_ops=max(c["holdout144"]["operacoes"]["taxa"],f["holdout144"]["operacoes"]["taxa"])
    ce=n["holdout144"]["perda"]["entropia_cruzada"]; first=n["holdout144"]["primeiro_token"]["acuracia"]; ops=n["holdout144"]["operacoes"]["taxa"]
    ganho_ce=(best_ce-ce)/max(best_ce,1e-12); ganho_first=first-best_first; ganho_ops=ops-best_ops
    min_op=min(v["taxa"] for v in n["holdout144"]["operacoes"]["por_operacao"].values())
    criterio={
        "old334_exatas":n["old334"]["geracao"]["iguais_ao_alvo"]>=g["old334_exatas_min"],
        "old334_ce":n["old334"]["perda"]["entropia_cruzada"]<=g["old334_ce_max"],
        "known94_exatas":n["known94"]["geracao"]["iguais_ao_alvo"]>=g["known94_exatas_min"],
        "known94_ce":n["known94"]["perda"]["entropia_cruzada"]<=g["known94_ce_max"],
        "fatorial96_operacoes":n["fatorial96"]["operacoes"]["taxa"]>=g["fatorial96_operacoes_min"],
        "fatorial96_ce":n["fatorial96"]["perda"]["entropia_cruzada"]<=g["fatorial96_ce_max"],
        "holdout_ce":ganho_ce>=g["novo_holdout_ce_melhora_relativa_vs_melhor_baseline_min"],
        "holdout_primeiro":ganho_first>=g["novo_holdout_primeiro_token_ganho_vs_melhor_baseline_min"],
        "holdout_operacoes":ganho_ops>=g["novo_holdout_operacoes_ganho_vs_melhor_baseline_min"],
        "holdout_total":ops>=g["novo_holdout_operacoes_total_min"],
        "holdout_por_operacao":min_op>=g["novo_holdout_operacao_individual_min"],
        "ganho_ce_relativo":ganho_ce,"ganho_primeiro_pp":ganho_first,"ganho_operacoes_pp":ganho_ops,"min_operacao":min_op,
    }
    decisivos=[k for k in criterio if k not in ("ganho_ce_relativo","ganho_primeiro_pp","ganho_operacoes_pp","min_operacao")]
    criterio["sucesso_conjunto"]=all(criterio[k] for k in decisivos)
    resultado={"base_commit":protocolo["base_commit"],"holdout_sha256":mh["holdout_sha256"],"treino":treino_info,"controles":{"controle_1x":aval["controle_1x"],"fatorial":aval["fatorial"]},"candidato":aval["auxiliar"],"criterio":criterio,"checkpoint_sha256":sha256(destino),"aprovado_experimentalmente":bool(criterio["sucesso_conjunto"]),"ativo_no_chat":False,"integridade":{"parametros_serializados":cand["treino"]["parametros"],"vocabulario":len(cand["vocabulario"]),"cabeca_auxiliar_serializada":False,"holdout_aberto_pos_selecao":True,"checkpoint_publico_alterado":False}}
    gravar_json(DIR/"resultados.json",resultado)
    linhas=["# Ato auxiliar — resultado","",f"Cabeça auxiliar treino-only, λ={protocolo['treino']['lambda_auxiliar']}; checkpoint final mantém **{cand['treino']['parametros']} parâmetros** e vocabulário **{len(cand['vocabulario'])}**.","",f"- Auxiliar treino: **{100*treino_info['aux_train']['acuracia']:.1f}%**; dev rotulado: **{100*treino_info['aux_dev']['acuracia']:.1f}%**.",f"- old334: **{n['old334']['geracao']['iguais_ao_alvo']}/334**, CE **{n['old334']['perda']['entropia_cruzada']:.3f}**.",f"- known94: **{n['known94']['geracao']['iguais_ao_alvo']}/94**, CE **{n['known94']['perda']['entropia_cruzada']:.3f}**.",f"- fatorial96 operações: **{100*n['fatorial96']['operacoes']['taxa']:.1f}%**, CE **{n['fatorial96']['perda']['entropia_cruzada']:.3f}**.",f"- holdout144: CE **{ce:.3f}**, primeiro token **{100*first:.1f}%**, operações **{100*ops:.1f}%**, pior operação **{100*min_op:.1f}%**.","",f"**Sucesso conjunto: {'SIM' if criterio['sucesso_conjunto'] else 'NÃO'}**.","","Checkpoint permanece `ativo_no_chat=false`; nenhuma promoção automática."]
    (DIR/"RELATORIO.md").write_text("\n".join(linhas)+"\n",encoding="utf-8")
    print(json.dumps({"criterio":criterio,"aux":treino_info,"holdout":{"controle_ce":c["holdout144"]["perda"]["entropia_cruzada"],"fatorial_ce":f["holdout144"]["perda"]["entropia_cruzada"],"aux_ce":ce,"controle_ops":c["holdout144"]["operacoes"]["taxa"],"fatorial_ops":f["holdout144"]["operacoes"]["taxa"],"aux_ops":ops}},ensure_ascii=False,indent=2),flush=True)
    print("segundos totais",round(time.monotonic()-inicio,2),flush=True)


if __name__=="__main__":
    executar()
