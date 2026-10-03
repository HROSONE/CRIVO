"""Treinar pesos próprios e separar previsão neural de verificação/busca exatas."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from rede_efeitos import RedeEfeitos,dados
from interpretacao_estados import executar,sintetizar

PROGRAMAS = [
 ('composicao','let x = entrada + 2; x -= 1; return x;',list(range(-4,5))),
 ('ramificacao','if (entrada < 0) { return 0 - entrada; } else { return entrada; }',list(range(-4,5))),
 ('laco','let x = entrada; while (x < 3) { x += 1; } return x;',list(range(-3,5))),
 ('acumulacao','let total = 0; let i = 0; while (i < entrada) { total += i; i += 1; } return total;',list(range(0,5))),
]
CONTRATOS = [
 dict(id='somar_constante',dev=[dict(entrada=x,saida=x+2) for x in (-2,0,3)],teste=[dict(entrada=x,saida=x+2) for x in (-4,1,4)]),
 dict(id='subtrair_constante',dev=[dict(entrada=x,saida=x-1) for x in (-2,0,3)],teste=[dict(entrada=x,saida=x-1) for x in (-4,1,4)]),
 dict(id='limiar',dev=[dict(entrada=x,saida=x<2) for x in (0,2,3)],teste=[dict(entrada=x,saida=x<2) for x in (-4,1,4)]),
 dict(id='contagem',dev=[dict(entrada=x,saida=x) for x in (0,2,3)],teste=[dict(entrada=x,saida=x) for x in (1,4,5)]),
 dict(id='acumulacao',dev=[dict(entrada=x,saida=x*(x-1)//2) for x in (0,2,3)],teste=[dict(entrada=x,saida=x*(x-1)//2) for x in (1,4,5)]),
]


def avaliar_programas(rede):
    rs=[]
    for nome,codigo,entradas in PROGRAMAS:
        casos=[]
        for entrada in entradas:
            exato=executar(codigo,entrada)
            try:
                neural=executar(codigo,entrada,rede.prever)
                a=neural['resultado'];b=exato['resultado']
                casos.append(dict(entrada=entrada,esperado=b,obtido=a,correto=type(a) is type(b) and a==b))
            except ValueError as e:casos.append(dict(entrada=entrada,correto=False,erro=str(e)))
        rs.append(dict(id=nome,total=len(casos),corretos=sum(x['correto'] for x in casos),casos=casos))
    return rs


def avaliar_busca(rede):
    rs=[]
    for t in CONTRATOS:
        r=dict(id=t['id'])
        for modo,previsor in (('simbolica',None),('guiada_rede',rede.prever)):
            s=sintetizar(t['dev'],previsor,limite=500,finalistas=32)
            acertos=0
            if s['codigo']:
                for c in t['teste']:
                    try:
                        v=executar(s['corpo'],c['entrada'])['resultado']
                        acertos+=type(v) is type(c['saida']) and v==c['saida']
                    except ValueError:pass
            r[modo]=dict(s,total=len(t['teste']),corretos=acertos)
        rs.append(r)
    return rs


def treinar(saida,passos=4000):
    out=Path(saida)
    if out.exists() and any(out.iterdir()):raise ValueError('Saída deve estar vazia')
    registros=dados();rede=RedeEfeitos();antes={s:rede.avaliar([r for r in registros if r['split']==s]) for s in ('validacao','teste')}
    programas_antes=avaliar_programas(rede)
    historico=rede.treinar([r for r in registros if r['split']=='treino'],passos=passos)
    rede.salvar(out)
    relatorio=dict(versao=2,semente_pesos=7,semente_treino=11,pesos_sha256=hashlib.sha256((out/'rede.npz').read_bytes()).hexdigest(),
        dados_sha256=hashlib.sha256(json.dumps(registros,sort_keys=True).encode()).hexdigest(),
        passos=passos,fontes_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('rede_efeitos.py','interpretacao_estados.py','scripts/treinar_efeitos.py')},pesos_externos=False,antes=antes,historico=historico,
        depois={s:rede.avaliar([r for r in registros if r['split']==s]) for s in ('treino','validacao','teste')},
        programas_antes=programas_antes,programas_depois=avaliar_programas(rede),busca=avaliar_busca(rede),
        limitacoes=['Subconjunto numérico, não JavaScript completo','Programas reservados compõem operadores conhecidos; não prova aprendizagem de operadores novos',
        'Parser, executor exato e gramática de busca foram implementados manualmente','Busca guiada usa rede para ordenar; verificação final é simbólica',
        'Resultados medidos em um único seed; benchmark autoral pequeno; não demonstra nível sênior'])
    (out/'relatorio.json').write_text(json.dumps(relatorio,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in relatorio.items() if k not in ('busca','programas_antes','programas_depois','historico')},ensure_ascii=False,indent=2))
    print(json.dumps(dict(programas=[{k:p[k] for k in ('id','total','corretos')} for p in relatorio['programas_depois']],busca=[dict(id=x['id'],**{k:x[k]['corretos'] for k in ('simbolica','guiada_rede')}) for x in relatorio['busca']]),ensure_ascii=False))
    return relatorio


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--saida',required=True);p.add_argument('--passos',type=int,default=4000)
    a=p.parse_args();treinar(a.saida,a.passos)
