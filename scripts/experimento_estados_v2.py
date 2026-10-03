"""Protocolo fixo: três seeds, baseline congelada, estruturas e reparo reservado."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from interpretacao_estruturas import executar,efeito_exato,javascript
from interpretacao_estados import executar as executar_v1
from rede_efeitos import RedeEfeitos,dados as dados_v1
from rede_estruturas import RedeEstruturas,dados,NUMERICAS,LOGICAS
from busca_estados import buscar_com_reparo,acertou
from verificacao_codigo import iguais,verificar

BENCH=ROOT/'dados/estados/benchmark-v2.json'
FONTES=('interpretacao_estruturas.py','rede_estruturas.py','busca_estados.py','scripts/experimento_estados_v2.py','dados/estados/benchmark-v2.json','verificacao_codigo.py')


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def congelada():
    f=json.loads((ROOT/'dados/estados/v1-congelada.json').read_text())
    if any(digest(ROOT/n)!=h for n,h in f['fontes_sha256'].items()):raise ValueError('Baseline V1 mudou')
    return f


def medir_efeitos(rede,rs):
    grupos={}
    for r in rs:
        m=grupos.setdefault(r['op'],dict(total=0,corretos=0,erros=0));m['total']+=1
        try:
            v=rede.prever(r['op'],r['a'],r['b']);m['corretos']+=iguais(v,r['resultado'])
        except ValueError:m['erros']+=1
    return grupos


def medir_programas(rede,programas,legado=False):
    rs=[];executor=executar_v1 if legado else executar
    for p in programas:
        casos=[]
        for c in p['casos']:
            r=dict(entrada=c['entrada'],correto=False,executor_exato_suporta=False)
            try:r['executor_exato_suporta']=iguais(executor(p['corpo'],c['entrada'])['resultado'],c['saida'])
            except ValueError:pass
            try:
                out=executor(p['corpo'],c['entrada'],rede.prever);r['obtido']=out['resultado']
                r['correto']=iguais(out['resultado'],c['saida']) and iguais(out['estado']['entrada'],c['entrada'])
            except ValueError as e:r['erro']=str(e)
            casos.append(r)
        rs.append(dict(id=p['id'],tipo=p['tipo'],total=len(casos),corretos=sum(c['correto'] for c in casos),
                       executor_exato_suporta=sum(c['executor_exato_suporta'] for c in casos),casos=casos))
    return rs


def medir_busca(rede,contratos,modo):
    rs=[]
    for t in contratos:
        r=buscar_com_reparo(t['desenvolvimento'],t['tipo'],t['contraexemplos_desenvolvimento'],
                           rede.prever if modo=='guiada' else None,campos=t['campos'])
        # Nenhuma avaliação reservada ocorre até terminar a sequência de reparos.
        for etapa in ('inicial','final'):
            s=r[etapa];cs=[]
            for c in t['reservados']:
                cs.append(bool(s['corpo'] and acertou(s['corpo'],c)))
            r[etapa]=dict(s,casos_reservados_total=len(cs),casos_reservados_corretos=sum(cs),reservados_aprovados=all(cs))
        rs.append(dict(id=t['id'],modo=modo,**r))
    return rs


def paridade(programas,tsc,saida):
    rs=[]
    for p in programas:
        casos=[dict(entrada=[c['entrada']],saida=c['saida']) for c in p['casos']]
        for lang in ('javascript','typescript'):
            r=verificar(javascript(p['corpo'],lang=='typescript',p['tipo_ts']),lang,casos,tsc)
            rs.append(dict(id=p['id'],linguagem=lang,verificacao=r))
    Path(saida).write_text(json.dumps(rs,ensure_ascii=True,indent=2)+'\n')
    if not all(r['verificacao']['funcional'] for r in rs):raise ValueError('Referência divergiu de JS/TS ou runtime indisponível')
    return dict(referencias=len(rs),casos=sum(r['verificacao']['casos_total'] for r in rs),corretos=sum(r['verificacao']['casos_corretos'] for r in rs))


def executar_experimento(saida,tsc=None,passos=5000):
    out=Path(saida)
    if out.exists() and any(out.iterdir()):raise ValueError('Saída deve estar vazia')
    f=congelada();benchmark=json.loads(BENCH.read_text());rs=dados();out.mkdir(parents=True,exist_ok=True)
    # Protocolo e procedência são gravados antes de começar qualquer treino/medição.
    protocolo=dict(benchmark_sha256=digest(BENCH),dados_sha256=hashlib.sha256(json.dumps(rs,sort_keys=True).encode()).hexdigest(),
                   fontes_sha256={n:digest(ROOT/n) for n in FONTES},sementes=benchmark['sementes'],passos=passos,
                   pesos_externos=False,particoes={s:sum(r['split']==s for r in rs) for s in ('treino','validacao','teste')})
    (out/'protocolo.json').write_text(json.dumps(protocolo,indent=2)+'\n')
    if tsc:protocolo['paridade']=paridade(benchmark['programas'],tsc,out/'paridade.json')
    registros_treino=[r for r in rs if r['split']=='treino'];resultados=[]
    velho=dados_v1()
    for seed in benchmark['sementes']:
        rede=RedeEstruturas(seed);antes=medir_programas(rede,benchmark['programas'])
        hist=rede.treinar(registros_treino,passos=passos,semente=seed+100)
        pasta=out/('seed-'+str(seed));rede.salvar(pasta)
        baseline=RedeEfeitos(semente=seed)
        baseline.treinar([r for r in velho if r['split']=='treino'],passos=4000,semente=seed+100)
        baseline.salvar(pasta/'baseline-v1')
        extrap=[dict(op=op,a=a,b=b,resultado=efeito_exato(op,a,b)) for op in ('+','-') for a in (-32,-24,24,32) for b in (-32,-1,1,32)]
        mul=[dict(op='*',a=a,b=b,resultado=efeito_exato('*',a,b)) for a in (-16,-12,-8,-4,0,1,4,8,16) for b in (-16,-12,-8,-4,0,1,4,8,16)]
        r=dict(seed=seed,pesos_sha256=digest(pasta/'rede.npz'),historico=hist,
               efeitos={s:medir_efeitos(rede,[r for r in rs if r['split']==s]) for s in ('validacao','teste')},
               multiplicacao_composta=medir_efeitos(rede,mul),aritmetica_fora_faixa_treino=medir_efeitos(rede,extrap),
               programas_antes=antes,programas=medir_programas(rede,benchmark['programas']),
               baseline_v1=medir_programas(baseline,benchmark['programas'],legado=True),
               busca_simbolica=medir_busca(rede,benchmark['contratos'],'simbolica'),busca_guiada=medir_busca(rede,benchmark['contratos'],'guiada'))
        (pasta/'relatorio.json').write_text(json.dumps(r,ensure_ascii=True,indent=2)+'\n');resultados.append(r)
        print(json.dumps(dict(seed=seed,programas_total=sum(p['total'] for p in r['programas']),programas_corretos=sum(p['corretos'] for p in r['programas']),
                             efeitos_total=sum(m['total'] for m in r['efeitos']['teste'].values()),efeitos_corretos=sum(m['corretos'] for m in r['efeitos']['teste'].values()),
                             guiada_inicial=sum(t['inicial']['reservados_aprovados'] for t in r['busca_guiada']),guiada_final=sum(t['final']['reservados_aprovados'] for t in r['busca_guiada']))),flush=True)
    resumo=dict(protocolo=protocolo,resultados=resultados,limites=[
        'Benchmark autoral, público, sem revisão independente; não certifica nível sênior',
        'Baseline V1 tem menos cobertura de sintaxe: separar suporte do executor de aprendizado da rede',
        'Objetos e métodos de texto são interpretados manualmente; rede aprende comprimento, índice numérico e operadores',
        'Multiplicação é um algoritmo manual que compõe adições previstas pela rede; não é operador novo descoberto',
        'Tabelas booleanas estão integralmente no treino; reserva mede composição, não descoberta das tabelas',
        'Conteúdos estruturais reservados podem compartilhar máscaras de ocupação de posições conhecidas',
        'Ordenação neural tem custo próprio; menos verificações exatas não comprova maior velocidade total'])
    (out/'relatorio.json').write_text(json.dumps(resumo,ensure_ascii=True,indent=2)+'\n')
    linhas=['# Experimento próprio de estados e estruturas','', '| Seed | Execuções | Efeitos reservados | Busca guiada inicial → final |','|---|---|---|---|']
    for r in resultados:
        p=r['programas'];ef=r['efeitos']['teste'];b=r['busca_guiada']
        linhas.append('| {} | {}/{} | {}/{} | {}/{} → {}/{} |'.format(r['seed'],sum(x['corretos'] for x in p),sum(x['total'] for x in p),sum(x['corretos'] for x in ef.values()),sum(x['total'] for x in ef.values()),sum(x['inicial']['reservados_aprovados'] for x in b),len(b),sum(x['final']['reservados_aprovados'] for x in b),len(b)))
    linhas+=['','Todos os pesos foram treinados do zero. Nenhuma ativação automática.','']+['- '+x for x in resumo['limites']]
    (out/'resumo.md').write_text('\n'.join(linhas)+'\n')
    return resumo


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--saida',required=True);p.add_argument('--tsc');p.add_argument('--passos',type=int,default=5000)
    a=p.parse_args();executar_experimento(a.saida,a.tsc,a.passos)
