"""Treinar ranking próprio de reparos e comparar com buscas sem rede."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from busca_estados import variacoes
from diagnostico_estados import avaliar, diagnosticar, executar, gerar_edicoes
from rede_reparos import RedeReparos, features
from scripts.experimento_estados_v2 import paridade

BENCH = ROOT/'dados/estados/benchmark-diagnostico.json'
FONTES = ('diagnostico_estados.py', 'execucao_rastreada.py', 'rede_reparos.py',
          'scripts/diagnosticar_estados.py', 'scripts/experimento_diagnostico.py',
          'dados/estados/benchmark-diagnostico.json', 'dados/estados/v3-congelada.json')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def congelada():
    c = json.loads((ROOT/'dados/estados/v3-congelada.json').read_text())
    if any(digest(ROOT/n) != h for n, h in c['fontes_sha256'].items()):
        raise ValueError('Baseline V3 alterada')
    return c


def casos(v, particao):
    # Referência só produz saídas para a partição solicitada pelo avaliador.
    return [dict(entrada=x, saida=executar(v['referencia'], x)['resultado'])
            for x in v[particao]]


def montar_treino(benchmark):
    grupos = []
    for f in benchmark['familias']:
        if f['split'] != 'treino':
            continue
        for v in f['variantes']:
            dev = casos(v, 'desenvolvimento')
            inicial = avaliar(v['corpo'], dev)
            edicoes = gerar_edicoes(v['corpo'], dev)
            corretas = [int(all(r['correto'] for r in avaliar(e['corpo'], dev))) for e in edicoes]
            grupos.append(dict(id=v['id'], familia=f['familia'], split='treino',
                               features=[features(e, inicial).tolist() for e in edicoes], corretas=corretas))
    return grupos


def baseline_tokens(codigo, dev, verificacoes=16):
    inicio = time.perf_counter()
    edicoes = variacoes(codigo)
    corpo = None
    feitas = 0
    for c in edicoes[:verificacoes]:
        feitas += 1
        if all(x['correto'] for x in avaliar(c, dev)):
            corpo = c
            break
    return dict(corpo_corrigido=corpo, candidatos=len(edicoes), verificadas=feitas,
                segundos=time.perf_counter()-inicio, casos_reservados_consultados=False)


def medir(benchmark, ranking=None, modo='estrutural', orcamento=16):
    resultados = []
    for f in benchmark['familias']:
        if f['split'] == 'treino':
            continue
        for v in f['variantes']:
            dev = casos(v, 'desenvolvimento')
            r = (baseline_tokens(v['corpo'], dev, orcamento) if modo == 'tokens' else
                 diagnosticar(v['corpo'], dev, ranking, verificacoes=orcamento))
            # O reparo está encerrado ANTES de acessar as saídas reservadas.
            reservado = casos(v, 'reservados')
            antes = avaliar(v['corpo'], reservado)
            depois = avaliar(r['corpo_corrigido'], reservado) if r['corpo_corrigido'] else []
            resultados.append(dict(id=v['id'], familia=f['familia'], split=f['split'],
                                   modo=modo, orcamento=orcamento, diagnostico=r,
                                   reservado_inicial=antes, reservado_final=depois,
                                   reparo_generalizou=bool(depois) and all(x['correto'] for x in depois)))
    return resultados


def resumo_medidas(rs):
    testes = [r for r in rs if r['split'] == 'teste']
    return dict(programas_teste=len(testes), reparados=sum(r['reparo_generalizou'] for r in testes),
                verificacoes=sum(r['diagnostico']['verificadas'] for r in testes),
                segundos=sum(r['diagnostico']['segundos'] for r in testes),
                reservados_corretos=sum(c['correto'] for r in testes for c in r['reservado_final']),
                reservados_total=sum(len(r['reservado_inicial']) for r in testes))


def executar_experimento(saida, tsc=None, passos=1200):
    out = Path(saida)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Saída deve estar vazia')
    congelada()
    b = json.loads(BENCH.read_text())
    familias = [f['familia'] for f in b['familias']]
    if len(familias) != len(set(familias)):
        raise ValueError('Família aparece em mais de uma partição')
    out.mkdir(parents=True, exist_ok=True)
    protocolo = dict(benchmark_sha256=digest(BENCH), fontes_sha256={n: digest(ROOT/n) for n in FONTES},
                     sementes=b['sementes'], passos=passos, orcamento_primario=16, orcamento_cobertura=128,
                     pesos_externos=False, familias={s: [f['familia'] for f in b['familias'] if f['split']==s]
                                                     for s in ('treino', 'validacao', 'teste')},
                     reserva_consultada_no_reparo=False, selecao_por_teste=False)
    (out/'protocolo.json').write_text(json.dumps(protocolo, indent=2)+'\n')
    grupos = montar_treino(b)
    (out/'treino.json').write_text(json.dumps(grupos, indent=2)+'\n')
    protocolo['dados_treino_sha256'] = digest(out/'treino.json')
    # Orçamentos fixados antes de treinar. Baselines não recebem uma rede.
    tokens = medir(b, modo='tokens')
    estrutural = medir(b)
    cobertura = medir(b, orcamento=128)
    resultados = []
    for seed in b['sementes']:
        rede = RedeReparos(seed)
        antes = medir(b, rede, 'ranking_aleatorio')
        hist = rede.treinar(grupos, passos, seed+100)
        pasta = out/('seed-'+str(seed))
        rede.salvar(pasta)
        depois = medir(b, rede, 'ranking_aprendido')
        amplo = medir(b, rede, 'ranking_aprendido', 128)
        r = dict(seed=seed, historico=hist, parametros=rede.parametros,
                 pesos_sha256=digest(pasta/'rede.npz'), bytes_pesos=(pasta/'rede.npz').stat().st_size,
                 antes=antes, depois=depois, cobertura=amplo,
                 resumo_antes=resumo_medidas(antes), resumo_depois=resumo_medidas(depois),
                 resumo_cobertura=resumo_medidas(amplo))
        resultados.append(r)
        (pasta/'relatorio.json').write_text(json.dumps(r, ensure_ascii=True, indent=2)+'\n')
        print(json.dumps(dict(seed=seed, treino=hist, teste=r['resumo_depois'], cobertura=r['resumo_cobertura'])), flush=True)
    total = dict(protocolo=protocolo, tokens=tokens, estrutural=estrutural, cobertura_estrutural=cobertura,
                 resumo_tokens=resumo_medidas(tokens), resumo_estrutural=resumo_medidas(estrutural),
                 resumo_cobertura=resumo_medidas(cobertura), resultados=resultados,
                 limites=['Diagnóstico identifica hipótese pelo reparo que satisfaz desenvolvimento; não prova intenção nem causalidade.',
                          'Parser, execução, atributos de entrada e geração de edições são programados manualmente.',
                          'A rede aprende só a prioridade de edições; validação final usa o executor exato.',
                          'Benchmark autoral público com 14 famílias; seis famílias de teste não treinam a rede, mas não são avaliação externa cega.',
                          'Reservados têm a mesma tarefa que desenvolvimento; acerto não comprova equivalência para todas as entradas.',
                          'Uma edição local por tentativa, subconjunto limitado, nenhuma promoção automática.'])
    if tsc:
        programas = []
        for f in b['familias']:
            for v in f['variantes']:
                xs = casos(v, 'desenvolvimento') + casos(v, 'reservados')
                entrada = xs[0]['entrada']
                tipo_ts = 'number[]' if type(entrada) is list else 'number' if type(entrada) is int else 'string' if type(entrada) is str else '{'+ '; '.join(k+': '+('boolean' if type(val) is bool else 'number') for k,val in entrada.items()) +'}'
                programas.append(dict(id=v['id']+'-referencia', corpo=v['referencia'], tipo_ts=tipo_ts, casos=xs))
                # Paridade de cada correção, inclusive quando falha reservados, usa sua saída própria.
                corpos = {r['diagnostico']['corpo_corrigido'] for rs in (tokens, estrutural, cobertura) for r in rs
                          if r['id']==v['id'] and r['diagnostico']['corpo_corrigido']}
                corpos.update(r['diagnostico']['corpo_corrigido'] for seed in resultados
                              for etapa in ('depois', 'cobertura') for r in seed[etapa]
                              if r['id']==v['id'] and r['diagnostico']['corpo_corrigido'])
                for i, corpo in enumerate(sorted(corpos)):
                    saidas = [dict(entrada=c['entrada'], saida=executar(corpo, c['entrada'])['resultado']) for c in xs]
                    programas.append(dict(id=v['id']+'-reparo-'+str(i), corpo=corpo, tipo_ts=tipo_ts, casos=saidas))
        total['paridade'] = paridade(programas, tsc, out/'paridade.json')
    (out/'relatorio.json').write_text(json.dumps(total, ensure_ascii=True, indent=2)+'\n')
    linhas = ['# Diagnóstico e reparos próprios', '', '| Método | Orçamento | Teste reparado | Verificações | Segundos |',
              '|---|---|---|---|---|']
    for nome, n, r in [('Tokens V2',16,total['resumo_tokens']), ('AST sem rede',16,total['resumo_estrutural']),
                       ('AST sem rede',128,total['resumo_cobertura'])] + [
                       ('Ranking seed '+str(r['seed']), n, r[chave]) for r in resultados
                       for n,chave in ((16,'resumo_depois'),(128,'resumo_cobertura'))]:
        linhas.append('| {} | {} | {}/{} | {} | {:.4f} |'.format(nome,n,r['reparados'],r['programas_teste'],r['verificacoes'],r['segundos']))
    linhas += ['', 'Sem pesos externos. Sem ativação automática.', ''] + ['- '+s for s in total['limites']]
    (out/'resumo.md').write_text('\n'.join(linhas)+'\n')
    return total


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--saida', required=True)
    p.add_argument('--tsc')
    p.add_argument('--passos', type=int, default=1200)
    a = p.parse_args()
    executar_experimento(a.saida, a.tsc, a.passos)
