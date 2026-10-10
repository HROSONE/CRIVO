"""Continuação própria com reformulações; avaliação nova reservada."""
import argparse
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

DIR=Path(__file__).resolve().parent
sys.path.insert(0,str(DIR))
from executar import RAIZ,sha,triagem,gravar
from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq,tokenizar
from treinar_dialogo_seq2seq import treinar


def protocolo():
    p=json.loads((DIR/'protocolo_rodada3.json').read_text())
    if sha(DIR/'avaliacao_rodada3_congelada.json')!=p['sha256_avaliacao']:
        raise ValueError('Avaliação da rodada 3 alterada')
    if sha(DIR/p['checkpoint_inicial'])!=p['checkpoint_inicial_sha256']:
        raise ValueError('Pesos próprios iniciais alterados')
    return p


def avaliar_checkpoint(path,modo='com_historico'):
    p=protocolo();modelo=DialogoSeq2Seq(ler_json(path))
    teste=json.loads((DIR/'avaliacao_rodada3_congelada.json').read_text());sessoes=[]
    for s in teste['sessoes']:
        historico=[];turnos=[]
        for t in s['turnos']:
            entrada=[] if modo=='sem_historico' else list(reversed(historico)) if modo=='ordem_inversa' else historico.copy()
            bruto=1+len(tokenizar(t['mensagem']))+sum(1+len(tokenizar(h['texto'])) for h in entrada)
            resposta=modelo.gerar(t['mensagem'],entrada,**p['decodificacao'])
            turnos.append({'mensagem':t['mensagem'],'historico_fornecido':entrada,'saida':resposta,
                'triagem':triagem(resposta,t),'tokens_fonte_sem_truncamento':bruto,
                'truncou_fonte':bruto>modelo.limite_fonte})
            historico.extend([{'papel':'usuario','texto':t['mensagem']},{'papel':'assistente','texto':resposta['texto']}])
        sessoes.append({'id':s['id'],'turnos':turnos,
            'passou_triagem_todos_turnos':all(t['triagem']['passou_triagem'] for t in turnos)})
    turnos=[t for s in sessoes for t in s['turnos']]
    return {'modo':modo,'checkpoint_sha256':sha(path),'avaliacao_sha256':p['sha256_avaliacao'],
        'juiz_sha256':sha(__file__),'sessoes_total':len(sessoes),
        'sessoes_triagem':sum(s['passou_triagem_todos_turnos'] for s in sessoes),
        'turnos_total':len(turnos),'turnos_triagem':sum(t['triagem']['passou_triagem'] for t in turnos),
        'turnos_com_proibidos':sum(bool(t['triagem']['proibidos_presentes']) for t in turnos),
        'fontes_truncadas':sum(t['truncou_fonte'] for t in turnos),
        'completas':sum(t['saida']['completa'] for t in turnos),'sessoes':sessoes,
        'limite':'triagem lexical não demonstra sentido, naturalidade nem ausência de toda invenção; revisão obrigatória',
        'aprovado':False,'ativo_no_chat':False}


def antes():
    p=protocolo()
    resultado=avaliar_checkpoint(DIR/p['checkpoint_inicial'])
    gravar('rodada3_antes.json',resultado)
    print(json.dumps({k:resultado[k] for k in ['sessoes_triagem','turnos_triagem','fontes_truncadas']}))


def treino():
    p=protocolo();destino=DIR/'checkpoint_rodada3.json.gz'
    if destino.exists():raise ValueError('Preservar checkpoint existente')
    corpus=DIR/'corpus_rodada3.json';corpus_sha=sha(corpus)
    estat=json.loads((DIR/'corpus_rodada3_estatisticas.json').read_text())
    if corpus_sha!=estat['sha256_corpus']:raise ValueError('Corpus alterado após preparação')
    temporario=DIR/'checkpoint_rodada3.tmp.json'
    r=treinar(corpus,temporario,checkpoint_inicial=DIR/p['checkpoint_inicial'],**p['hiperparametros'])
    dados=json.loads(temporario.read_text())
    dados.update(aprovado=False,ativo_no_chat=False,experimento='gerador-historico-textual-rodada3',
        sha256_corpus=corpus_sha,sha256_avaliacao_reservada=p['sha256_avaliacao'])
    if dados['treino']['parametros']!=p['limite_parametros'] or sha(corpus)!=corpus_sha:
        raise ValueError('Parâmetros ou corpus mudaram')
    destino.write_bytes(gzip.compress((json.dumps(dados,ensure_ascii=False,separators=(',',':'))+'\n').encode(),mtime=0))
    temporario.unlink()
    r['manifesto']={'checkpoint_sha256':sha(destino),'checkpoint_inicial_sha256':p['checkpoint_inicial_sha256'],
        'corpus_sha256':corpus_sha,'protocolo_sha256':sha(DIR/'protocolo_rodada3.json'),
        'avaliacao_sha256':p['sha256_avaliacao'],'script_sha256':sha(__file__),
        'treinador_sha256':sha(RAIZ/'treinar_dialogo_seq2seq.py'),
        'arquitetura_sha256':sha(RAIZ/'dialogo_seq2seq.py'),'numpy':__import__('numpy').__version__,
        'threads':{k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']},
        'aprovado':False,'ativo_no_chat':False}
    gravar('treino_rodada3.json',r);print(json.dumps(r['manifesto'],ensure_ascii=False),flush=True)


def depois():
    resultados={}
    for modo in ['com_historico','sem_historico','ordem_inversa']:
        r=avaliar_checkpoint(DIR/'checkpoint_rodada3.json.gz',modo)
        gravar('rodada3_depois_'+modo+'.json',r)
        resultados[modo]={k:r[k] for k in ['sessoes_triagem','turnos_triagem','turnos_com_proibidos','fontes_truncadas']}
    # Regressão conhecida: não entra no placar inédito desta rodada.
    from executar import avaliar
    regressao=avaliar(DialogoSeq2Seq(ler_json(DIR/'checkpoint_rodada3.json.gz')))
    regressao['limite_adicional']='12 casos anteriores e pergunta do dono são regressão conhecida; não são avaliação inédita nesta rodada'
    gravar('rodada3_regressao_conhecida.json',regressao)
    gravar('rodada3_resumo_automatico.json',resultados)
    print(json.dumps(resultados,ensure_ascii=False,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('etapa',choices=['antes','treinar','depois'])
    args=ap.parse_args();{'antes':antes,'treinar':treino,'depois':depois}[args.etapa]()
