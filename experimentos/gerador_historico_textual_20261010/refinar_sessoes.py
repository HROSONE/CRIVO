"""Última continuação do dia, decidida no desenvolvimento, antes do holdout."""
import gzip
import json
import os
from datetime import datetime, timezone
from executar import DIR,RAIZ,gravar,sha
from arquivos_contextuais import ler_json
from treinar_dialogo_seq2seq import treinar


def preparar():
    if (DIR/'protocolo_refino_sessoes.json').exists():raise ValueError('Preservar protocolo')
    gravar('protocolo_refino_sessoes.json',dict(preparado_em_utc=datetime.now(timezone.utc).isoformat(),
        checkpoint_inicial='checkpoint_sessoes.json.gz',checkpoint_inicial_sha256=sha(DIR/'checkpoint_sessoes.json.gz'),
        corpus_sha256=sha(DIR/'corpus_sessoes.json.gz'),avaliacao_sha256=sha(DIR/'avaliacao_sessoes_congelada.json'),
        motivo_antes_holdout='Primeira passagem: entropia treino sem regularização 1,5156, desenvolvimento 1,3877; gerações livres 48/428 contra 80/428 na inicialização. Rede ainda não ajustou respostas novas. Reduzir regularização em continuação curta, sem alteração de corpus/capacidade e sem consultar teste final.',
        hiperparametros=dict(epocas=20,lote_tamanho=32,ocultos=24,embeddings=16,vocab_max=720,buckets=128,
            limite_fonte=192,limite_resposta=64,semente=181,taxa=.0007,validar_cada=2,paciencia=4,
            dropout=.05,dropout_tokens=.05,amostragem=.05,aquecimento=3),
        selecao='Escolher entre as duas passagens pelo menor erro nos mesmos 428 casos de desenvolvimento, antes do holdout; sem critério extra ajustado ao teste final.',
        aprovado=False,ativo_no_chat=False))


def executar():
    p=ler_json(DIR/'protocolo_refino_sessoes.json');dest=DIR/'checkpoint_sessoes_refinado.json.gz'
    if dest.exists():raise ValueError('Preservar pesos')
    for nome,chave in [(p['checkpoint_inicial'],'checkpoint_inicial_sha256'),
        ('corpus_sessoes.json.gz','corpus_sha256'),('avaliacao_sessoes_congelada.json','avaliacao_sha256')]:
        if sha(DIR/nome)!=p[chave]:raise ValueError('Artefato alterado')
    temporario=DIR/'checkpoint_sessoes_refinado.tmp.json'
    r=treinar(DIR/'corpus_sessoes.json.gz',temporario,checkpoint_inicial=DIR/p['checkpoint_inicial'],**p['hiperparametros'])
    c=ler_json(temporario);c.update(aprovado=False,ativo_no_chat=False,experimento='sessoes-refino-20261010',
        sha256_corpus=p['corpus_sha256'],sha256_avaliacao_reservada=p['avaliacao_sha256'])
    if c['treino']['parametros']!=81433:raise ValueError('Parâmetros alterados')
    dest.write_bytes(gzip.compress((json.dumps(c,ensure_ascii=False,separators=(',',':'))+'\n').encode(),mtime=0));temporario.unlink()
    r['manifesto']=dict(checkpoint_sha256=sha(dest),checkpoint_inicial_sha256=p['checkpoint_inicial_sha256'],
        corpus_sha256=p['corpus_sha256'],avaliacao_sha256=p['avaliacao_sha256'],
        protocolo_sha256=sha(DIR/'protocolo_refino_sessoes.json'),script_sha256=sha(__file__),
        treinador_sha256=sha(RAIZ/'treinar_dialogo_seq2seq.py'),arquitetura_sha256=sha(RAIZ/'dialogo_seq2seq.py'),
        numpy=__import__('numpy').__version__,threads={k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']},
        aprovado=False,ativo_no_chat=False)
    gravar('treino_sessoes_refinado.json',r)
    anterior=ler_json(DIR/'treino_sessoes.json')['validacao']['entropia_cruzada']
    escolher=r['validacao']['entropia_cruzada']<anterior
    path=dest if escolher else DIR/p['checkpoint_inicial']
    gravar('selecao_final_sessoes_antes_holdout.json',dict(selecionado_em_utc=datetime.now(timezone.utc).isoformat(),
        checkpoint=path.name,checkpoint_sha256=sha(path),criterio=p['selecao'],
        entropia_primeira_passagem=anterior,entropia_refino=r['validacao']['entropia_cruzada'],
        aprovado=False,ativo_no_chat=False,avaliacao_final_ainda_nao_executada=True))
    print(json.dumps(ler_json(DIR/'selecao_final_sessoes_antes_holdout.json'),ensure_ascii=False),flush=True)


if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('etapa',choices=['preparar','treinar'])
    {'preparar':preparar,'treinar':executar}[ap.parse_args().etapa]()
