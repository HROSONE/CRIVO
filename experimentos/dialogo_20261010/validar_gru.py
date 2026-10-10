"""A mesma amostra interna pré-fixada, usando os argumentos do corpus autoral."""
import json
import re
from pathlib import Path

from avaliar import ler_modelo, juiz
from linguagem_gerativa import GeradorGRU, renderizar
from preparar import nome

H = Path(__file__).resolve().parent


def main():
    modelo = GeradorGRU(ler_modelo(H / 'checkpoint_gru_dialogo.json.gz'))
    originais = {e['id']: e for e in json.loads((H / 'corpus.json').read_text())['exemplos']}
    derivados = {e['id']: e for e in json.loads((H / 'corpus_gru.json').read_text())['exemplos']}
    amostra = json.loads((H / 'amostra_validacao.json').read_text())
    nomes = [nome(i) for i in range(960)]
    rows = []
    for ident in amostra['ids']:
        ex = originais[ident]
        ctx = derivados[ident]['contexto']
        assert ex['split'] == 'validacao'
        g = modelo.gerar(ctx)
        g['texto'] = renderizar(g, ctx['slots'])
        fonte = ' '.join([ex['contexto']['mensagem']] + [h['texto'] for h in ex['contexto']['historico']])
        obrigatorios = [n for n in nomes if juiz.contem(ex['resposta'], n)]
        obrigatorios += re.findall(r'\b\d+\b', ex['resposta'])
        personagem = re.search(r'personagem: ([^;]+)', ex['fatos_sessao'])
        if personagem and juiz.contem(ex['resposta'], personagem[1]):
            obrigatorios.append(personagem[1])
        for pessoa, valor in re.findall(r'(\w+) prefere ([^;]+)', ex['fatos_sessao']):
            if juiz.contem(ex['resposta'], valor):
                obrigatorios.append(valor)
        faltam = [t for t in obrigatorios if not juiz.contem(g['texto'], t)]
        inventados = [n for n in nomes if juiz.contem(g['texto'], n) and not juiz.contem(fonte, n)]
        numeros = sorted(set(re.findall(r'\b\d+\b', g['texto'])) - set(re.findall(r'\b\d+\b', fonte)))
        rows.append({'id': ident, 'entrada': ctx, 'alvo_para_revisao': ex['resposta'], 'gerada': g,
                     'faltam': faltam, 'nomes_inventados': inventados, 'numeros_inventados': numeros,
                     'minimo_preservado': bool(g['completa'] and not faltam and not inventados and not numeros)})
        print(ident, 'PASS' if rows[-1]['minimo_preservado'] else 'FAIL', g['texto'], flush=True)
    out = {'amostra': amostra, 'resumo': {'total': len(rows), 'minimo_preservado': sum(r['minimo_preservado'] for r in rows),
            'completas': sum(r['gerada']['completa'] for r in rows),
            'casos_com_inventados': sum(bool(r['nomes_inventados'] or r['numeros_inventados']) for r in rows)},
           'limite': 'Mesmos seis tipos e padrões de treino. Ato e argumentos anotados; não mede interpretação livre, qualidade humana ou as dez conversas manuais da Fase 2.',
           'resultados': rows}
    (H / 'validacao_gru.json').write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(out['resumo'], ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
