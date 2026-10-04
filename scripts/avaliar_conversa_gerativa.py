"""Registra geração livre e loss separada humano/sintético. Não promove pesos.

A triagem lexical é fraca: encontrar palavras esperadas não certifica coerência,
compreensão nem seguimento de instruções. Preservar texto integral é obrigatório.
"""
import argparse
import collections
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.treinar_linguagem_profunda import sha


def avaliar(modelo_path,saida,sonda,corpus=None,temperatura=0.):
    import numpy as np
    import torch
    from linguagem_profunda import carregar, fonte_dialogo, ESPECIAIS
    from geracao_incremental import gerar
    torch.set_num_threads(2)
    modelo,tok,estado=carregar(modelo_path)
    casos=json.loads(Path(sonda).read_text())['casos']
    alvos=set()
    if corpus:
        alvos={json.loads(l)['resposta'].strip().casefold() for l in (Path(corpus)/'dialogos_treino.jsonl').read_text().splitlines()}
    respostas=[]
    for c in casos:
        fonte=fonte_dialogo(tok,c['mensagem'],c.get('historico',[]),modelo.config.contexto)
        ids,fim=gerar(modelo,fonte,tok.token_to_id('<fim>'),max_tokens=120,temperatura=temperatura,
            proibidos=[tok.token_to_id(t) for t in ESPECIAIS[:-1]])
        texto=tok.decode(ids);baixo=texto.casefold()
        lexical=bool(fim and texto and all(any(p.casefold() in baixo for p in grupo) for grupo in c.get('exigir',[])) and not any(p.casefold() in baixo for p in c.get('proibir',[])))
        respostas.append(dict(c,gerado=texto,completa=fim,tokens=len(ids),triagem_lexical=lexical,
            copia_exata_alvo_treino=baixo.strip() in alvos))
        print(json.dumps(dict(id=c['id'],gerado=texto,completa=fim,triagem_lexical=lexical),ensure_ascii=False),flush=True)
    retido={}
    if corpus:
        from scripts.treinar_linguagem_profunda import Corpus
        cp=Corpus(corpus,modelo.config.contexto)
        if estado['execucao']['corpus']!=cp.assinatura:
            # Baseline pode ter corpus anterior: a análise não é seleção de pesos.
            retido['baseline_corpus_anterior']=True
        with torch.no_grad():
            for split in ('validacao','teste'):
                x=cp.x[split];y=cp.y[split]
                origens=np.load(Path(corpus)/f'dialogo_{split}_origem.npy')
                for origem,nome in ((1,'humano'),(0,'sintetico')):
                    soma=0.;tokens=0
                    indices=np.flatnonzero(origens==origem)
                    for inicio in range(0,len(indices),8):
                        idx=indices[inicio:inicio+8]
                        tx=torch.tensor(np.asarray(x[idx],dtype=np.int64))
                        ty=torch.tensor(np.asarray(y[idx],dtype=np.int64))
                        n=int((ty!=-100).sum());loss=modelo(tx,ty)[1]
                        soma+=float(loss)*n;tokens+=n
                    retido[f'{split}_{nome}']=dict(tokens=tokens,entropia_cruzada=soma/tokens if tokens else None,janelas=len(indices))
    report=dict(versao=1,modelo_sha256=sha(Path(modelo_path)/'pesos.pt'),sonda_sha256=sha(sonda),
        corpus_sha256=sha(Path(corpus)/'manifesto.json') if corpus else None,passo=estado['passo'],
        parametros=sum(p.numel() for p in modelo.parameters()),temperatura=temperatura,
        respostas=respostas,perda_retida=retido,
        terminadas=sum(r['completa'] for r in respostas),triagem_lexical=sum(r['triagem_lexical'] for r in respostas),
        copia_exata_alvo_treino=sum(r['copia_exata_alvo_treino'] for r in respostas),
        respostas_distintas=len({r['gerado'] for r in respostas}),total=len(respostas),
        promocao_automatica=False,
        limites=['Triagem lexical não é avaliação semântica.','Exige revisão das respostas livres e avaliação independente.','Loss baixa em exercício sintético não certifica conversa aberta.'])
    Path(saida).parent.mkdir(parents=True,exist_ok=True)
    Path(saida).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modelo',required=True);p.add_argument('--saida',required=True)
    p.add_argument('--sonda',default=str(ROOT/'avaliacoes/conversa_gerativa_v1/sonda.json'))
    p.add_argument('--corpus');p.add_argument('--temperatura',type=float,default=0.)
    a=p.parse_args();avaliar(a.modelo,a.saida,a.sonda,a.corpus,a.temperatura)
