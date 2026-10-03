"""Comparar redes próprias congeladas em casos novos e regressão conhecida."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from rede_estruturas import RedeEstruturas,dados as dados_v2
from rede_precisa import RedePrecisa,dados as dados_v3
from scripts.experimento_estados_v2 import medir_programas,medir_efeitos,paridade,medir_busca,digest

BENCH=ROOT/'dados/estados/benchmark-precisao.json'


def congelada():
    f=json.loads((ROOT/'dados/estados/v2-congelada.json').read_text())
    if any(digest(ROOT/n)!=h for n,h in f['fontes_sha256'].items()):raise ValueError('Baseline V2 mudou')
    return f


def validar_reserva(rs,programas):
    novos={tuple(c['entrada']) for p in programas for c in p['casos'] if isinstance(c['entrada'],list)}
    usados={tuple(r['a']) for r in rs if r['op'] in ('indice','comprimento') and isinstance(r['a'],list)}
    if novos&usados:raise ValueError('Array do novo benchmark apareceu nos dados de efeitos')


def executar_experimento(saida,tsc=None,passos=5000):
    out=Path(saida)
    if out.exists() and any(out.iterdir()):raise ValueError('Saída deve estar vazia')
    congelada();novo=json.loads(BENCH.read_text());antigo=json.loads((ROOT/'dados/estados/benchmark-v2.json').read_text())
    base=dados_v2();rs=dados_v3();validar_reserva(rs,novo['programas']);validar_reserva(base,novo['programas'])
    out.mkdir(parents=True,exist_ok=True)
    protocolo=dict(benchmark_sha256=digest(BENCH),fontes_sha256={n:digest(ROOT/n) for n in (
        'rede_precisa.py','rede_estruturas.py','interpretacao_estruturas.py','scripts/experimento_precisao.py','dados/estados/benchmark-precisao.json')},
        dados_sha256=hashlib.sha256(json.dumps(rs,sort_keys=True).encode()).hexdigest(),sementes=novo['sementes'],
        passos_operadores=passos,passos_igualdade=2000,pesos_externos=False,
        cobertura_indices_treino=dict(sorted(collections.Counter(r['b'] for r in rs if r['op']=='indice' and r['split']=='treino').items())),
        cobertura_indices_v2=dict(sorted(collections.Counter(r['b'] for r in base if r['op']=='indice' and r['split']=='treino').items())))
    (out/'protocolo.json').write_text(json.dumps(protocolo,indent=2)+'\n')
    if tsc:protocolo['paridade']=paridade(novo['programas'],tsc,out/'paridade.json')
    antigos={(p['corpo'],json.dumps(c['entrada'],sort_keys=True)) for p in antigo['programas'] for c in p['casos']}
    protocolo['casos_repetidos_v2']=sum((p['corpo'],json.dumps(c['entrada'],sort_keys=True)) in antigos for p in novo['programas'] for c in p['casos'])
    resultados=[]
    for seed in novo['sementes']:
        v2=RedeEstruturas(seed);v2.treinar([r for r in base if r['split']=='treino'],passos,semente=seed+100)
        v3=RedePrecisa(seed);hist=v3.treinar([r for r in rs if r['split']=='treino'],passos,semente=seed+100)
        pasta=out/('seed-'+str(seed));v3.salvar(pasta);v2.salvar(pasta/'baseline-v2')
        r=dict(seed=seed,pesos_sha256=digest(pasta/'rede.npz'),historico=hist,
            novos_v2=medir_programas(v2,novo['programas']),novos_v3=medir_programas(v3,novo['programas']),
            regressao_v2=medir_programas(v2,antigo['programas']),regressao_v3=medir_programas(v3,antigo['programas']),
            efeitos_validacao=medir_efeitos(v3,[r for r in rs if r['split']=='validacao']),
            efeitos_teste=medir_efeitos(v3,[r for r in rs if r['split']=='teste']),
            busca_guiada=medir_busca(v3,antigo['contratos'],'guiada'))
        (pasta/'relatorio.json').write_text(json.dumps(r,ensure_ascii=True,indent=2)+'\n');resultados.append(r)
        print(json.dumps(dict(seed=seed,novos_v2=sum(p['corretos'] for p in r['novos_v2']),novos_v3=sum(p['corretos'] for p in r['novos_v3']),
            novos_total=sum(p['total'] for p in r['novos_v3']),regressao_v3=sum(p['corretos'] for p in r['regressao_v3']),
            igualdade=r['efeitos_teste']['==='],indice=r['efeitos_teste']['indice'])),flush=True)
    resumo=dict(protocolo=protocolo,resultados=resultados,limites=[
        'Cabeça de igualdade usa distância absoluta da subtração prevista; estrutura da representação é manual, logits são aprendidos',
        'Desigualdade reutiliza o complemento da igualdade; não possui aprendizagem independente',
        'Novos programas não são dados de treino; pares numéricos isolados podem reaparecer como operadores conhecidos',
        'Casos novos de arrays são excluídos de todas as partições dos dois modelos comparados',
        'Mais dados e uma etapa extra de igualdade contribuem para o ganho; não é comparação com orçamento de treino idêntico',
        'Conjunto de foco inclui um caso idêntico à regressão V2; não são 228 problemas independentes',
        'Benchmark autoral, público, pequeno; não certifica programação geral ou nível sênior'])
    (out/'relatorio.json').write_text(json.dumps(resumo,ensure_ascii=True,indent=2)+'\n')
    linhas=['# Precisão própria: igualdade e índices','', '| Seed | V2 em casos novos | V3 em casos novos | Regressão V3 |','|---|---|---|---|']
    for r in resultados:
        linhas.append('| {} | {}/{} | {}/{} | {}/101 |'.format(r['seed'],sum(p['corretos'] for p in r['novos_v2']),sum(p['total'] for p in r['novos_v2']),sum(p['corretos'] for p in r['novos_v3']),sum(p['total'] for p in r['novos_v3']),sum(p['corretos'] for p in r['regressao_v3'])))
    linhas+=['','Modelos próprios, sem pesos externos. Sem ativação automática.','']+['- '+x for x in resumo['limites']]
    (out/'resumo.md').write_text('\n'.join(linhas)+'\n')
    return resumo


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--saida',required=True);p.add_argument('--tsc');p.add_argument('--passos',type=int,default=5000)
    a=p.parse_args();executar_experimento(a.saida,a.tsc,a.passos)
