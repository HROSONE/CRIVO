"""Promove uma cópia somente após medidas congeladas, HTTP e revisão registrada."""
import gzip
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parent.parent


def main():
    candidato = H / 'checkpoint_gru_dialogo.json.gz'
    raw = candidato.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    assert sha == 'a042a2713f3cabac4d528b7ada365890fafe2bfcbf844de84e1f9e53533f4c12'
    dados = json.loads(gzip.decompress(raw))
    assert dados['controle'] == {'aprovado':False,'ativo_no_chat':False}
    casos_sha = hashlib.sha256((H/'casos_congelados.json').read_bytes()).hexdigest()
    assert casos_sha == (H/'SHA256-casos').read_text().split()[0]
    assert (H/'casos_congelados.json').read_bytes() == (H.parent/'generalizacao_dialogo_20261010/casos_congelados.json').read_bytes()
    ids = [c['id'] for c in json.loads((H/'casos_congelados.json').read_text())['casos']]
    resultados = [json.loads((H/n).read_text()) for n in ('final_motor.json','final_http.json')]
    for r in resultados:
        assert r['experimental'] and not r.get('avaliacao_parcial_ids')
        assert r['casos_sha256'] == casos_sha
        assert [x['caso'] for x in r['resultados']] == ids
        assert r['resumo']['total'] == 114
        assert r['resumo']['pecas_corretas_com_evidencia'] >= 103
        assert all(x['peca_correta_com_evidencia'] for x in r['resultados'][:79])
        assert all(r['resumo'][k] == 0 for k in ('trocas_dominio','casos_com_referentes_ausentes','desvios'))
        historias = [x for x in r['resultados'] if 'historia_entregue' in x]
        assert len(historias) == 52 and all(x['historia_entregue'] for x in historias)
        assert all(x['resposta']['dialogue_generation']['checkpoint_sha256'] == sha for x in historias)
    revisao = json.loads((H/'revisao_sessoes.json').read_text())
    assert revisao['motor_sessoes_atendem_criterio'] >= 6 and revisao['http_sessoes_atendem_criterio'] >= 6
    assert revisao['total'] == 10 and revisao['turnos_por_modo'] == 104
    for modo in ('motor','http'):
        s = json.loads((H/('final_sessoes_'+modo+'.json')).read_text())
        assert len(s['sessoes']) == 10 and sum(len(x['resultados']) for x in s['sessoes']) == 104
    reproducao = json.loads((H/'reproducibilidade.json').read_text())
    assert reproducao['identicos_byte_a_byte'] and reproducao['checkpoint_sha256'] == sha
    assert dados['treino']['parametros'] <= 85581
    antigo = H/'checkpoint_producao_anterior.json.gz'
    assert antigo.read_bytes() == (H.parent/'generalizacao_dialogo_20261010/checkpoint_base_130.json.gz').read_bytes()
    for caminho, digest in json.loads((H.parent/'dialogo_20261010/pesos_ativos_antes.json').read_text()).items():
        assert hashlib.sha256((ROOT/caminho).read_bytes()).hexdigest() == digest, caminho
    meta = dict(checkpoint_origem_sha256=sha, atos=['historia','continuar','corrigir'],
                casos_sha256=casos_sha, corpus_sha256=dados['corpus_sha256'],
                metricas=dict(casos_total=114,casos_motor=resultados[0]['resumo']['pecas_corretas_com_evidencia'],
                              casos_http=resultados[1]['resumo']['pecas_corretas_com_evidencia'],
                              casos_antigos_motor=79,casos_antigos_http=79,trocas_dominio=0,
                              referentes_ausentes=0,desvios_proibidos=0,historias_entregues=52,conversas_mantem_fio=6),
                escopo='Realização própria de escrita condicionada a acontecimentos, correções, papéis e restrições explícitas, com histórico HTTP de até vinte mensagens.',
                limites='Doze classes e padrões autorais compartilhados; escolha estrutural, não planejamento neural. Seis sessões mínimas de escrita; quatro práticas novas falham. Transições genéricas e episódios reutilizados; simplificação sem mudar conteúdo não demonstrada. Não é conversa livre geral.')
    dados.update(controle={'aprovado':True,'ativo_no_chat':True},aprovacao=meta,limite=meta['limites'])
    destino = ROOT/'rede_dialogo_conversa.json.gz'
    destino.write_bytes(gzip.compress(json.dumps(dados,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode(),mtime=0))
    meta['checkpoint_producao_sha256'] = hashlib.sha256(destino.read_bytes()).hexdigest()
    (H/'aprovacao.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print(meta)


if __name__ == '__main__':
    main()
