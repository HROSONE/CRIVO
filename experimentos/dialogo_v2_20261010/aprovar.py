"""Promove somente a cópia de produção após os gates e a revisão registrada."""
import gzip
import hashlib
import json
from pathlib import Path

H=Path(__file__).resolve().parent;ROOT=H.parent.parent

def main():
    candidato=H/'checkpoint_gru_dialogo.json.gz';dados=json.loads(gzip.decompress(candidato.read_bytes()))
    assert dados['controle']=={'aprovado':False,'ativo_no_chat':False}
    assert hashlib.sha256(candidato.read_bytes()).hexdigest()=='d6dec80197b3d6d000dfa97ec1bc1bc4831e058732fce3e9bb3e0b03c70f1399'
    casos=H/'casos_congelados.json';sha=hashlib.sha256(casos.read_bytes()).hexdigest()
    assert sha==(H/'SHA256').read_text().split()[0]
    resultados=[json.loads((H/n).read_text()) for n in ('final_motor.json','final_http.json')]
    for r in resultados:
        assert r['experimental'] and r['casos_sha256']==sha
        assert r['resumo']['total']==r['resumo']['pecas_corretas_com_evidencia']==43
        assert r['resumo']['trocas_dominio']==r['resumo']['casos_com_referentes_ausentes']==0
        historias=[x for x in r['resultados'] if x['caso'] in ('real-19','real-20','pos127-03','pos127-05')]
        assert len(historias)==4 and all(x['historia_entregue'] and x['resposta']['dialogue_generation']['usada'] for x in historias)
        assert len(r['conversas'])==10
    revisao=json.loads((H/'revisao_conversas.json').read_text())
    assert revisao['mantem_fio_motor']>=8 and revisao['mantem_fio_http']>=8
    assert json.loads((H/'reproducibilidade.json').read_text())['checkpoint_sha256']==hashlib.sha256(candidato.read_bytes()).hexdigest()
    assert json.loads((H/'reproducibilidade.json').read_text())['identicos_byte_a_byte']
    assert dados['treino']['parametros']<=88969
    for caminho,digest in json.loads((H.parent/'dialogo_20261010/pesos_ativos_antes.json').read_text()).items():
        assert hashlib.sha256((ROOT/caminho).read_bytes()).hexdigest()==digest,caminho
    meta={'checkpoint_origem_sha256':hashlib.sha256(candidato.read_bytes()).hexdigest(),
        'atos':['historia','continuar','corrigir'],'casos_sha256':sha,'corpus_sha256':dados['corpus_sha256'],
        'metricas':{'casos_motor':43,'casos_http':43,'trocas_dominio':0,'referentes_ausentes':0,
                    'historias_entregues':4,'conversas_mantem_fio':min(revisao['mantem_fio_motor'],revisao['mantem_fio_http'])},
        'escopo':'Personagem, cenário de papel reconhecido, final com amigo, reescrita em cinco frases; capacidades/fatos/cálculos e sessão real continuam nos executores existentes.',
        'limites':'Oito arcos; não aprende conversa geral, planejamento específico ou raciocínio humano. Após final com amigo pode esclarecer em vez de continuar; temas de papel incerto mantêm o executor anterior.'}
    dados['aprovacao']=meta;dados['controle']={'aprovado':True,'ativo_no_chat':True}
    destino=ROOT/'rede_dialogo_conversa.json.gz'
    raw=json.dumps(dados,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    destino.write_bytes(gzip.compress(raw,mtime=0))
    meta['checkpoint_producao_sha256']=hashlib.sha256(destino.read_bytes()).hexdigest()
    (H/'aprovacao.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');print(meta)

if __name__=='__main__':main()
