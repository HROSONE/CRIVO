"""Aprova apenas a realização de ficção avaliada, preservando o experimento."""
import gzip
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parent.parent


def main():
    congelado = H.parent/'dialogo_20261010/casos_congelados.json'
    sha = hashlib.sha256(congelado.read_bytes()).hexdigest()
    assert sha == (congelado.parent/'SHA256').read_text().split()[0]
    metrica = {}
    for modo in ('motor','http'):
        dados = json.loads((H/('candidato_'+modo+'.json')).read_text())
        assert dados['casos_sha256'] == sha
        r = dados['resumo']
        assert r['total'] == 37 and r['pecas_corretas_com_evidencia'] >= 34
        assert r['trocas_dominio'] == r['casos_com_referentes_ausentes'] == r['desvios'] == 0
        historias = [x for x in dados['resultados'] if x['caso'] in ('real-19','real-20')]
        assert len(historias)==2 and all(x['historia_entregue'] for x in historias)
        metrica['casos_'+modo] = r['pecas_corretas_com_evidencia']
    revisao_path = H/'revisao_conversas.json'
    revisao = json.loads(revisao_path.read_text())
    manual_sha = hashlib.sha256((H/'conversas_congeladas.json').read_bytes()).hexdigest()
    assert revisao['conversas_sha256'] == manual_sha
    assert revisao['total'] == 10 and revisao['candidato_mantem_fio'] >= 6
    metrica.update(trocas_dominio=0,referentes_ausentes=0,historias_entregues=2,
                   conversas_mantem_fio=revisao['candidato_mantem_fio'])
    fonte = H.parent/'dialogo_20261010/checkpoint_gru_dialogo.json.gz'
    origem_sha = hashlib.sha256(fonte.read_bytes()).hexdigest()
    assert origem_sha == '823c44965cb7d9e3ec3830555b100aec373443e3b778cd719cc9804bc9e4ba47'
    dados = json.loads(gzip.decompress(fonte.read_bytes()))
    assert dados['controle'] == {'aprovado':False,'ativo_no_chat':False}
    for nome, hash_antes in json.loads((H.parent/'dialogo_20261010/pesos_ativos_antes.json').read_text()).items():
        assert hashlib.sha256((ROOT/nome).read_bytes()).hexdigest() == hash_antes
    dados['controle'] = {'aprovado':True,'ativo_no_chat':True}
    dados['aprovacao'] = {'checkpoint_origem_sha256':origem_sha,
                          'atos':['historia','continuar','corrigir'], 'metricas':metrica,
                          'casos_sha256':sha,'conversas_sha256':manual_sha,
                          'revisao_sha256':hashlib.sha256(revisao_path.read_bytes()).hexdigest(),
                          'limite':'Aprovação seletiva após critérios pré-merge. Publicação deve ser validada depois do merge. Não aprova conversa livre, novas preferências ou fatos gerados.'}
    saida = ROOT/'rede_dialogo_conversa.json.gz'
    saida.write_bytes(gzip.compress(json.dumps(dados,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    (H/'aprovacao.json').write_text(json.dumps(dict(dados['aprovacao'],checkpoint_publicacao_sha256=hashlib.sha256(saida.read_bytes()).hexdigest()),ensure_ascii=False,indent=2)+'\n')
    print('Aprovados somente história/continuação/final. Pesos antigos e checkpoint experimental intactos.')


if __name__=='__main__':main()
