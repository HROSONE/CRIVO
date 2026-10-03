"""Contratos contrastivos, composições e reparos autorais; não usa o teste antigo."""
import hashlib
import itertools
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def split_familia(familia):
    n=int(hashlib.sha256(('logica-v1:'+familia).encode()).hexdigest()[:8],16)%10
    return 'validacao' if n==0 else 'teste' if n==1 else 'treino'


def aplicar(xs,ordem,filtro,mapa,agregacao,k,limiar):
    def filtrar(x):
        return {'maior':x>limiar,'maior_igual':x>=limiar,'menor':x<limiar,
                'menor_igual':x<=limiar,'par':x%2==0,'impar':x%2!=0}[filtro]
    def transformar(x):return {'somar':x+k,'subtrair':x-k,'escalar':x*k,'negar':-x}[mapa]
    ys=([transformar(x) for x in xs if filtrar(x)] if ordem=='filtrar_primeiro' else
        [y for y in map(transformar,xs) if filtrar(y)])
    return ys if agregacao=='lista' else sum(ys) if agregacao=='soma' else len(ys)


def corpo(ordem,filtro,mapa,agregacao,k,limiar,ts):
    pred={'maior':f'x > {limiar}','maior_igual':f'x >= {limiar}','menor':f'x < {limiar}',
          'menor_igual':f'x <= {limiar}','par':'x % 2 === 0','impar':'x % 2 !== 0'}[filtro]
    expr={'somar':f'x + ({k})','subtrair':f'x - ({k})','escalar':f'x * ({k})','negar':'-x'}[mapa]
    etapas=f'xs.filter(x => {pred}).map(x => {expr})' if ordem=='filtrar_primeiro' else f'xs.map(x => {expr}).filter(x => {pred})'
    fim={'lista':'ys','soma':'ys.reduce((total, x) => total + x, 0)','contagem':'ys.length'}[agregacao]
    return 'function resolver(xs'+(': number[]' if ts else '')+')'+((': number[]' if agregacao=='lista' else ': number') if ts else '')+' { const ys = '+etapas+'; return '+fim+'; }'


def contrato(ordem,filtro,mapa,agregacao,k,limiar,ts):
    pred={'maior':f'maiores que {limiar}','maior_igual':f'maiores ou iguais a {limiar}',
          'menor':f'menores que {limiar}','menor_igual':f'menores ou iguais a {limiar}',
          'par':'pares','impar':'ímpares'}[filtro]
    trans={'somar':f'somar {k} a cada item','subtrair':f'subtrair {k} de cada item',
           'escalar':f'multiplicar cada item por {k}','negar':'trocar o sinal de cada item'}[mapa]
    a=f'primeiro manter apenas os números {pred}; depois {trans}' if ordem=='filtrar_primeiro' else f'primeiro {trans}; depois manter apenas os números {pred} do resultado'
    fim={'lista':'devolver a lista resultante na mesma ordem','soma':'somar os itens da lista resultante; vazia retorna 0','contagem':'contar os itens da lista resultante; vazia retorna 0'}[agregacao]
    lang='typescript' if ts else 'javascript';assinatura='function resolver(xs: number[])' if ts else 'function resolver(xs)'
    return f'Em {lang}, implemente {assinatura} para {a}; ao final {fim}. Entradas inteiras pequenas. Não alterar xs. Retorne somente código, sem imports.'


def gerar():
    tarefas=[];entradas=[[],[-5],[-2,-1,0,1,2,5],[2,2,3,-3],[-10,7],[0,4,-4]]
    for ordem,filtro,mapa,agg in itertools.product(('filtrar_primeiro','transformar_primeiro'),
            ('maior','maior_igual','menor','menor_igual','par','impar'),('somar','subtrair','escalar','negar'),('lista','soma','contagem')):
        familia='logica_'+ '_'.join((ordem,filtro,mapa,agg));split=split_familia(familia)
        for variant,(k,limiar) in enumerate(((-3,-2),(-2,1),(2,-1),(3,2))):
            casos=[dict(entrada=[xs],saida=aplicar(xs,ordem,filtro,mapa,agg,k,limiar)) for xs in entradas]
            oposto={'maior':'menor_igual','maior_igual':'menor','menor':'maior_igual','menor_igual':'maior','par':'impar','impar':'par'}[filtro]
            contra=next(dict(entrada=c['entrada'],esperado=c['saida'],obtido=aplicar(c['entrada'][0],ordem,oposto,mapa,agg,k,limiar))
                for c in casos if c['saida']!=aplicar(c['entrada'][0],ordem,oposto,mapa,agg,k,limiar))
            for ts in (False,True):
                codigo=corpo(ordem,filtro,mapa,agg,k,limiar,ts);errado=corpo(ordem,oposto,mapa,agg,k,limiar,ts)
                msg=contrato(ordem,filtro,mapa,agg,k,limiar,ts)
                lang='typescript' if ts else 'javascript'
                base=dict(id=f'{familia}_{variant}_{lang}',familia=familia,linguagem=lang,split=split,
                    resposta=codigo,casos=casos,origem='composicao_autoral',contraprova=contra,codigo_incorreto=errado)
                # Metade mostra dois exemplos, metade pede somente pelo contrato verbal.
                exemplo=' Exemplos: '+json.dumps([dict(entrada=c['entrada'],saida=c['saida']) for c in (casos[1],casos[2])],ensure_ascii=False) if variant%2==0 else ''
                tarefas.append(dict(base,mensagem=msg+exemplo,tipo='contrato'))
                reparo=msg+'\nCorrija este código: '+errado+'\nDiagnóstico: '+json.dumps(contra,ensure_ascii=False)
                tarefas.append(dict(base,id=base['id']+'_reparo',mensagem=reparo,tipo='reparo'))
    # Alvos iguais ficam numa única partição (inclui casos de mapas irrelevantes à contagem).
    particoes={}
    for t in tarefas:particoes.setdefault(t['resposta'],set()).add(t['split'])
    return [t for t in tarefas if len(particoes[t['resposta']])==1]


if __name__=='__main__':
    dados=dict(versao=1,natureza='autoral; composições e contraexemplos, sem respostas do teste antigo',tarefas=gerar())
    (ROOT/'dados/programacao/logica.json').write_text(json.dumps(dados,ensure_ascii=False,separators=(',',':'))+'\n')
    print(len(dados['tarefas']),'exemplos',len({t['familia'] for t in dados['tarefas']}),'famílias')
