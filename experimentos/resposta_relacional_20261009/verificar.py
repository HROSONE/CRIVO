"""Valida dados e perda causal antes de executar um piloto caro."""
from collections import Counter
import json
from pathlib import Path

from curriculo import ROOT, codificar, salvar, sha
from linguagem_profunda import carregar


if __name__ == '__main__':
    p = Path(__file__).resolve().parent
    _, tok, _ = carregar(ROOT / 'artefatos/linguagem_profunda')
    es = {s: json.loads((p / 'dados' / (s + '.json')).read_text())
          for s in ('treino', 'validacao')}
    chave = lambda e: json.dumps([e['historico'], e['mensagem']], sort_keys=True, ensure_ascii=False)
    assert not {chave(e) for e in es['treino']} & {chave(e) for e in es['validacao']}
    stats = {}
    for s, exemplos in es.items():
        cs = [codificar(tok, e) for e in exemplos]
        for c in cs:
            indices = [i for i, y in enumerate(c['y']) if y != -100]
            assert indices == list(range(indices[0], len(c['y'])))
            ys = [c['y'][i] for i in indices]
            assert tok.decode(ys[:-1]) == c['exemplo']['resposta']
            assert ys[-1] == tok.token_to_id('<fim>')
            assert len(c['x']) < 256
        stats[s] = {'pares': len(exemplos), 'familias': dict(Counter(e['familia'] for e in exemplos)),
                    'tokens_alvo_por_passagem': sum(sum(y != -100 for y in c['y']) for c in cs),
                    'max_tokens_sequencia': max(len(c['x']) + 1 for c in cs),
                    'historicos_6_turnos': sum(len(e['historico']) == 6 for e in exemplos)}
    trajetorias = json.loads((p / 'dados/trajetorias.json').read_text())
    for c in trajetorias:
        texto = ' '.join(t['texto'] for t in c['turnos'])
        for nome in ('Mara', 'Cora', 'Nara', 'Eva'):
            for adjetivo in ('concentrado', 'irritado', 'cansado', 'preocupado', 'atento', 'animado', 'distraído'):
                assert f'{nome} ficou {adjetivo}' not in texto
                assert f'{nome} estava {adjetivo}' not in texto
                assert f'{nome} confirmou que estava {adjetivo}' not in texto
        assert 'não foi autorizado.' not in texto
    salvar(p / 'integridade.json', {'verificado': True, 'alvos_somente_resposta': True,
           'entradas_completas': True, 'intersecao_entradas_particoes': 0,
           'concordancia_estados_e_autorizacao_verificada': True, 'estatisticas': stats,
           'limites': 'Validação procedural compartilha formas e vocabulário; não independente. Verificações formais não certificam linguagem geral.'})
    proto = json.loads((p / 'protocolo.json').read_text())
    proto.update(novo_manifesto_sha256=sha(p / 'dados/manifesto.json'),
                 codigo_curriculo_sha256=sha(p / 'curriculo.py'),
                 codigo_treinador_sha256=sha(p / 'piloto.py'),
                 versao_dados=2)
    salvar(p / 'protocolo.json', proto)
    print(stats)
