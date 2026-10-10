"""Carrega candidato próprio apenas para medição local, sem aprovação."""
import argparse,gzip,hashlib,importlib.util,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent.parent;sys.path.insert(0,str(ROOT))
def habilitar_candidato():
 import conversa_dialogo as cd
 p=H/'checkpoint_gru_dialogo.json.gz';d=json.loads(gzip.decompress(p.read_bytes()));b=H/'checkpoint_base_134.json.gz';base=json.loads(gzip.decompress(b.read_bytes()))
 assert d['controle']=={'aprovado':False,'ativo_no_chat':False}
 assert d['base_sha256']==hashlib.sha256(b.read_bytes()).hexdigest()
 assert d['corpus_sha256']==hashlib.sha256((H/'corpus_gru.json').read_bytes()).hexdigest()
 assert d['vocabulario']==base['vocabulario'] and d['treino']['parametros']==85130
 cd.PESOS_V7_SHA256=hashlib.sha256(json.dumps(d['pesos'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
 cd.CORPUS_V7_SHA256=d['corpus_sha256'];cd.carregar.cache_clear();return str(p)
def main():
 p=argparse.ArgumentParser();p.add_argument('--modo',choices=['motor','http'],required=True);p.add_argument('--saida',required=True);p.add_argument('--bateria',choices=['causal','114','40','diversidade','sessoes-antigas','folego','aliases'],default='causal');a=p.parse_args();c=habilitar_candidato()
 paths={'causal':H/'sondar.py','114':H.parent/'escrita_acontecimentos_20261010/avaliar.py','40':H.parent/'contexto_pratico_20261010/sondar.py','diversidade':H.parent/'diversidade_dialogo_20261010/sondar.py','sessoes-antigas':H.parent/'escrita_acontecimentos_20261010/sondar.py','folego':H/'sondar.py','aliases':H/'sondar.py'}
 s=importlib.util.spec_from_file_location('sonda_candidata',paths[a.bateria]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 if a.bateria=='114':m.avaliar(a.modo,a.saida,candidato=c,exigir=True,so_congelado=True)
 elif a.bateria=='folego':m.executar(a.modo,a.saida,candidato=c,novas=True)
 elif a.bateria=='aliases':m.executar(a.modo,a.saida,candidato=c,aliases=True)
 else:m.executar(a.modo,a.saida,candidato=c)
if __name__=='__main__':main()
