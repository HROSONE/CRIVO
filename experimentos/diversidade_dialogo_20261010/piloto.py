"""Carregamento experimental local; não altera registry nem checkpoint do chat."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parent.parent;sys.path.insert(0,str(ROOT))

def habilitar_candidato():
    import conversa_dialogo as cd
    candidato=H/'checkpoint_gru_dialogo.json.gz';d=json.loads(gzip.decompress(candidato.read_bytes()))
    assert d['controle']=={'aprovado':False,'ativo_no_chat':False}
    assert d['base_sha256']==hashlib.sha256((H/'checkpoint_base_133.json.gz').read_bytes()).hexdigest()
    assert d['corpus_sha256']==hashlib.sha256((H/'corpus_gru.json').read_bytes()).hexdigest()
    base=json.loads(gzip.decompress((H/'checkpoint_base_133.json.gz').read_bytes()))
    assert d['vocabulario']==base['vocabulario'] and d['ocultos']==80 and d['embeddings']==9
    assert sum(np.asarray(v).size for v in d['pesos'].values())==85130
    # Registro apenas deste processo de medição; produção continua usando 4e5894e2.
    cd.PESOS_V5_SHA256=hashlib.sha256(json.dumps(d['pesos'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    cd.CORPUS_V5_SHA256=d['corpus_sha256'];cd.carregar.cache_clear()
    return str(candidato)

def main():
    p=argparse.ArgumentParser();p.add_argument('--modo',choices=['motor','http'],required=True);p.add_argument('--saida',required=True);p.add_argument('--bateria',choices=['diversidade','114','40','sessoes-antigas'],default='diversidade');a=p.parse_args()
    candidato=habilitar_candidato()
    caminhos={'diversidade':H/'sondar.py','114':H.parent/'escrita_acontecimentos_20261010/avaliar.py',
              '40':H.parent/'contexto_pratico_20261010/sondar.py','sessoes-antigas':H.parent/'escrita_acontecimentos_20261010/sondar.py'}
    caminho=caminhos[a.bateria]
    spec=importlib.util.spec_from_file_location('execucao_piloto',caminho);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    if a.bateria=='114':m.avaliar(a.modo,a.saida,candidato=candidato,exigir=True,so_congelado=True)
    else:m.executar(a.modo,a.saida,candidato=candidato)
if __name__=='__main__':main()
