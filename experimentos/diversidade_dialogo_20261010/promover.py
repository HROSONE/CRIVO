"""Aprova uma cópia somente depois de todos os gates; original continua falso."""
import gzip
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

H = Path(__file__).resolve().parent; ROOT = H.parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(H))
from avaliar import pontuar
from verificar_114 import verificar, SHA
from conversa_dialogo import aprovacao_valida, ORIGEM_V6_SHA256, CORPUS_V6_SHA256, ATOS


def carregar(nome):
    return json.loads((H / nome).read_text())


def main():
    spec = importlib.util.spec_from_file_location('juiz_pratico', H.parent / 'contexto_pratico_20261010/avaliar.py')
    pratico = importlib.util.module_from_spec(spec); spec.loader.exec_module(pratico)
    div = {}; antigo = {}; util = {}
    for modo in ('motor', 'http'):
        div[modo] = pontuar(carregar('piloto_'+modo+'.json'))
        assert div[modo]['sessoes_aprovadas'] == 8 and div[modo]['problemas_fidelidade'] == 0
        antigo[modo] = verificar(carregar('piloto_114_'+modo+'.json'))
        util[modo] = pratico.pontuar(carregar('piloto_40_'+modo+'.json'))
        assert util[modo]['corretos'] == 40 and util[modo]['desvios'] == 0
    revisao = carregar('revisao_sessoes.json')
    assert revisao['motor_escrita_minima'] >= 6 and revisao['http_escrita_minima'] >= 6
    for modo in ('motor', 'http'):
        sessoes = carregar('piloto_sessoes_'+modo+'.json')['sessoes']
        assert len(sessoes) == 10 and sum(len(s['resultados']) for s in sessoes) == 104
    reproducao = carregar('reproducibilidade.json')
    assert reproducao['identico_byte_a_byte'] is True and reproducao['sha256'] == ORIGEM_V6_SHA256
    raw = (H / 'checkpoint_gru_dialogo.json.gz').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == ORIGEM_V6_SHA256
    candidato = json.loads(gzip.decompress(raw))
    assert candidato['controle'] == {'aprovado': False, 'ativo_no_chat': False}
    assert hashlib.sha256((H / 'corpus_gru.json').read_bytes()).hexdigest() == CORPUS_V6_SHA256
    a = dict(checkpoint_origem_sha256=ORIGEM_V6_SHA256, corpus_sha256=CORPUS_V6_SHA256,
             casos_sha256=SHA, atos=sorted(ATOS),
             diversidade_sha256=hashlib.sha256((H / 'sondas.json').read_bytes()).hexdigest(),
             praticos_sha256=hashlib.sha256((H.parent / 'contexto_pratico_20261010/sondas.json').read_bytes()).hexdigest(),
             treino_reproduzido_byte_a_byte=True,
             metricas=dict(casos_total=114, casos_motor=antigo['motor']['casos'], casos_http=antigo['http']['casos'],
                           casos_antigos_motor=79, casos_antigos_http=79, historias_entregues=52,
                           trocas_dominio=0, referentes_ausentes=0, desvios_proibidos=0,
                           conversas_mantem_fio=min(revisao['motor_escrita_minima'], revisao['http_escrita_minima']),
                           diversidade_turnos=48, diversidade_motor=8, diversidade_http=8,
                           diversidade_problemas_fidelidade=0, praticos_motor=40, praticos_http=40),
             limites='Quatro padrões autorais por classe conhecida. Escolha estrutural da variante, reação lexical; relatos repetidos, transições genéricas e planejamento de enredo ainda limitado. Não conversa livre geral.')
    candidato.update(controle={'aprovado': True, 'ativo_no_chat': True}, aprovacao=a, limite=a['limites'])
    assert aprovacao_valida(candidato)
    base = (H / 'checkpoint_base_133.json.gz').read_bytes()
    assert (ROOT / 'rede_dialogo_conversa.json.gz').read_bytes() == base, 'Não sobrescrever outra promoção'
    novo = gzip.compress(json.dumps(candidato, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode(), mtime=0)
    a['checkpoint_producao_sha256'] = hashlib.sha256(novo).hexdigest()
    (H / 'aprovacao.json').write_text(json.dumps(a, ensure_ascii=False, indent=2)+'\n')
    (ROOT / 'rede_dialogo_conversa.json.gz').write_bytes(novo)
    print('Cópia aprovada:', a['checkpoint_producao_sha256'])


if __name__ == '__main__':
    main()
