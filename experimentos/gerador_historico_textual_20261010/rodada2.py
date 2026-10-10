"""Rodada 2: mesmas dimensões e algoritmo; somente dados revisados."""
import argparse
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR))
from executar import avaliar, gravar, protocolo, sha, RAIZ
from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq
from treinar_dialogo_seq2seq import treinar


def treinar_rodada2():
    protocolo()
    p=json.loads((DIR/'protocolo_rodada2.json').read_text())
    corpus=DIR/'corpus_rodada2.json'
    if sha(corpus)!=p['sha256_corpus'] or (DIR/'checkpoint_rodada2.json.gz').exists():
        raise ValueError('Corpus divergente ou checkpoint existente; preservar rodada')
    temporario=DIR/'checkpoint_rodada2.tmp.json'
    resultado=treinar(corpus,temporario,**p['hiperparametros'])
    dados=json.loads(temporario.read_text())
    dados.update(aprovado=False,ativo_no_chat=False,experimento='gerador_historico_textual_20261010-rodada2',
        sha256_corpus=p['sha256_corpus'],sha256_avaliacao_reservada=p['sha256_avaliacao'])
    if dados['treino']['parametros']>p['limite_parametros']:
        raise ValueError('Orçamento excedido')
    serializado=(json.dumps(dados,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode()
    destino=DIR/'checkpoint_rodada2.json.gz'
    destino.write_bytes(gzip.compress(serializado,mtime=0));temporario.unlink()
    resultado['manifesto']={'checkpoint_sha256':sha(destino),'corpus_sha256':sha(corpus),
        'protocolo_sha256':sha(DIR/'protocolo_rodada2.json'), 'avaliacao_sha256':p['sha256_avaliacao'],
        'script_sha256':sha(__file__),'avaliador_sha256':sha(DIR/'executar.py'),
        'treinador_sha256':sha(RAIZ/'treinar_dialogo_seq2seq.py'),
        'arquitetura_sha256':sha(RAIZ/'dialogo_seq2seq.py'),
        'numpy':__import__('numpy').__version__,
        'threads':{k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']},
        'aprovado':False,'ativo_no_chat':False}
    gravar('treino_rodada2.json',resultado)
    print(json.dumps(resultado['manifesto'],ensure_ascii=False),flush=True)


def avaliar_rodada2():
    modelo=DialogoSeq2Seq(ler_json(DIR/'checkpoint_rodada2.json.gz'))
    resumo={}
    for modo in ['com_historico','sem_historico','ordem_inversa']:
        resultado=avaliar(modelo,modo)
        gravar('rodada2_depois_'+modo+'.json',resultado)
        resumo[modo]={k:resultado[k] for k in ['sessoes_triagem','turnos_triagem','turnos_total','fontes_truncadas']}
    gravar('rodada2_resumo_automatico.json',resumo)
    print(json.dumps(resumo,ensure_ascii=False,indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('etapa',choices=['treinar','avaliar']);args=ap.parse_args()
    {'treinar':treinar_rodada2,'avaliar':avaliar_rodada2}[args.etapa]()
