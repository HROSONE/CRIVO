"""Treino de respostas/sessões próprias, sem alterar o chat."""
import argparse
import gzip
import json
import os
from executar import DIR, RAIZ, gravar, sha, triagem
from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, tokenizar
from treinar_dialogo_seq2seq import treinar


def protocolo():
    p=ler_json(DIR/'protocolo_sessoes.json')
    if sha(DIR/'avaliacao_sessoes_congelada.json')!=p['avaliacao_sha256']:
        raise ValueError('Avaliação reservada alterada')
    if sha(DIR/p['checkpoint_inicial'])!=p['checkpoint_inicial_sha256']:
        raise ValueError('Pesos iniciais alterados')
    return p


def avaliar(path,modo='com_historico'):
    p=protocolo();m=DialogoSeq2Seq(ler_json(path));sessoes=[]
    for s in ler_json(DIR/'avaliacao_sessoes_congelada.json')['sessoes']:
        hist=[];turnos=[]
        for t in s['turnos']:
            entrada=[] if modo=='sem_historico' else list(reversed(hist)) if modo=='ordem_inversa' else hist.copy()
            bruto=1+len(tokenizar(t['mensagem']))+sum(1+len(tokenizar(h['texto'])) for h in entrada)
            r=m.gerar(t['mensagem'],entrada,**p['decodificacao'])
            turnos.append(dict(mensagem=t['mensagem'],historico_fornecido=entrada,saida=r,
                triagem=triagem(r,t),truncou_fonte=bruto>m.limite_fonte,tokens_fonte_sem_truncamento=bruto))
            hist.extend([dict(papel='usuario',texto=t['mensagem']),dict(papel='assistente',texto=r['texto'])])
        sessoes.append(dict(id=s['id'],turnos=turnos,passou_triagem_todos_turnos=all(t['triagem']['passou_triagem'] for t in turnos)))
    ts=[t for s in sessoes for t in s['turnos']]
    return dict(modo=modo,checkpoint_sha256=sha(path),avaliacao_sha256=p['avaliacao_sha256'],
        juiz_sha256=sha(__file__),sessoes_total=len(sessoes),turnos_total=len(ts),
        sessoes_triagem=sum(s['passou_triagem_todos_turnos'] for s in sessoes),
        turnos_triagem=sum(t['triagem']['passou_triagem'] for t in ts),
        turnos_com_proibidos=sum(bool(t['triagem']['proibidos_presentes']) for t in ts),
        fontes_truncadas=sum(t['truncou_fonte'] for t in ts),completas=sum(t['saida']['completa'] for t in ts),
        sessoes=sessoes,aprovado=False,ativo_no_chat=False,
        limite='Triagem lexical não aprova sentido/naturalidade; revisão semântica obrigatória; respostas reais no histórico.')


def antes():
    if (DIR/'sessoes_antes.json').exists():raise ValueError('Preservar baseline')
    p=protocolo();r=avaliar(DIR/p['checkpoint_inicial']);gravar('sessoes_antes.json',r)
    print({k:r[k] for k in ['sessoes_triagem','turnos_triagem','fontes_truncadas']})


def treino():
    p=protocolo();destino=DIR/'checkpoint_sessoes.json.gz'
    if destino.exists():raise ValueError('Preservar pesos anteriores')
    estat=ler_json(DIR/'corpus_sessoes_estatisticas.json');corpus=DIR/'corpus_sessoes.json.gz'
    if sha(corpus)!=estat['sha256_corpus']:raise ValueError('Corpus alterado')
    temp=DIR/'checkpoint_sessoes.tmp.json'
    r=treinar(corpus,temp,checkpoint_inicial=DIR/p['checkpoint_inicial'],**p['hiperparametros'])
    c=ler_json(temp);c.update(aprovado=False,ativo_no_chat=False,experimento='sessoes-textuais-20261010',
        sha256_corpus=estat['sha256_corpus'],sha256_avaliacao_reservada=p['avaliacao_sha256'])
    if c['treino']['parametros']!=p['parametros']:raise ValueError('Capacidade alterada')
    destino.write_bytes(gzip.compress((json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n').encode(),mtime=0));temp.unlink()
    r['manifesto']=dict(checkpoint_sha256=sha(destino),corpus_sha256=sha(corpus),
        checkpoint_inicial_sha256=p['checkpoint_inicial_sha256'],avaliacao_sha256=p['avaliacao_sha256'],
        protocolo_sha256=sha(DIR/'protocolo_sessoes.json'),script_sha256=sha(__file__),
        treinador_sha256=sha(RAIZ/'treinar_dialogo_seq2seq.py'),arquitetura_sha256=sha(RAIZ/'dialogo_seq2seq.py'),
        numpy=__import__('numpy').__version__,threads={k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']},
        aprovado=False,ativo_no_chat=False)
    gravar('treino_sessoes.json',r)
    gravar('selecao_sessoes_antes_holdout.json',dict(checkpoint=destino.name,checkpoint_sha256=sha(destino),
        epoca_selecionada=c['treino']['epoca_selecionada'],criterio=p['selecao'],
        entropia_desenvolvimento=r['validacao']['entropia_cruzada'],avaliacao_final_ainda_nao_executada=True,
        aprovado=False,ativo_no_chat=False))
    print(json.dumps(r['manifesto'],ensure_ascii=False),flush=True)


def depois():
    if (DIR/'sessoes_depois_com_historico.json').exists():raise ValueError('Preservar avaliação final')
    s=ler_json(DIR/'selecao_sessoes_antes_holdout.json');path=DIR/s['checkpoint']
    if sha(path)!=s['checkpoint_sha256']:raise ValueError('Seleção alterada')
    resumo={}
    for modo in ['com_historico','sem_historico','ordem_inversa']:
        r=avaliar(path,modo);gravar('sessoes_depois_'+modo+'.json',r)
        resumo[modo]={k:r[k] for k in ['sessoes_triagem','turnos_triagem','turnos_com_proibidos','fontes_truncadas']}
    gravar('sessoes_resumo_automatico.json',resumo)
    # Baterias anteriores são conhecidas; preservadas, fora do placar novo.
    from rodada3 import avaliar_checkpoint
    from executar import avaliar as antigo
    r=avaliar_checkpoint(path);r['limite_adicional']='Regressão conhecida da rodada 3; não inédito.'
    gravar('sessoes_regressao_rodada3.json',r)
    r=antigo(DialogoSeq2Seq(ler_json(path)));r['limite_adicional']='Regressão conhecida, incluindo pedido do dono.'
    gravar('sessoes_regressao_rodada2.json',r)
    print(json.dumps(resumo,ensure_ascii=False,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('etapa',choices=['antes','treinar','depois'])
    {'antes':antes,'treinar':treino,'depois':depois}[ap.parse_args().etapa]()
