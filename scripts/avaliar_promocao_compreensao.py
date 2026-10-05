"""Bloqueia promoção por métricas superficiais; não ativa pesos no chat.

Validação e teste comparam o mesmo painel e os mesmos pesos congelados.
Mesmo superar os limiares numéricos requer revisão semântica da conversa.
"""
import argparse
import json
from pathlib import Path


def pares_livres(relatorio):
    grupos={}
    for r in relatorio['geracao']['respostas']:
        grupos.setdefault(r['id'],[]).append(r)
    if not grupos or any(len(rs)!=2 or len({r['referencia'] for r in rs})!=2 for rs in grupos.values()):
        raise ValueError('Geração livre exige dois contextos com alvos distintos por par')
    acertos=0
    for rs in grupos.values():
        if all(r['terminou'] and r['resposta'].strip().casefold()==r['referencia'].strip().casefold() for r in rs):
            acertos+=1
    return dict(pares=len(grupos),pares_corretos=acertos,
        criterio='Ambas as gerações precisam terminar e coincidir com seus alvos; pode rejeitar paráfrases corretas.')


def comparar(anterior,candidato):
    if anterior['split'] != candidato['split']:
        raise ValueError('Partições diferentes')
    for nome in ('corpus_sha256','pares','casos'):
        if anterior['ranking'][nome] != candidato['ranking'][nome]:
            raise ValueError('Ranking sem o mesmo conjunto: '+nome)
    if anterior['painel_livre_sha256'] != candidato['painel_livre_sha256']:
        raise ValueError('Painéis livres diferentes')
    def entradas(r):
        return [(e['id'],e['mensagem'],e['historico'],e['referencia']) for e in r['geracao']['respostas']]
    if entradas(anterior)!=entradas(candidato):
        raise ValueError('Mensagens, histórico ou referências foram alterados')
    antes,depois=pares_livres(anterior),pares_livres(candidato)
    return dict(split=candidato['split'],ranking_antes=anterior['ranking']['pares_corretos'],
        ranking_depois=candidato['ranking']['pares_corretos'],ranking_total=candidato['ranking']['pares'],
        livre_antes=antes['pares_corretos'],livre_depois=depois['pares_corretos'],livre_total=depois['pares'])


def decidir(anterior_validacao,candidato_validacao,anterior_teste,candidato_teste):
    if anterior_validacao['split']!='validacao' or anterior_teste['split']!='teste':
        raise ValueError('Forneça validação e teste distintos')
    for v,t in ((anterior_validacao,anterior_teste),(candidato_validacao,candidato_teste)):
        if v['pesos_sha256']!=t['pesos_sha256']:
            raise ValueError('Os pesos mudaram entre validação e teste')
    comparacoes=[comparar(anterior_validacao,candidato_validacao),comparar(anterior_teste,candidato_teste)]
    recusas=[]
    for c in comparacoes:
        if c['ranking_depois']<c['ranking_antes']:
            recusas.append(c['split']+': regressão no ranking de pares')
        if c['livre_depois']<c['livre_antes']:
            recusas.append(c['split']+': regressão na geração livre de pares')
        if c['ranking_depois']/c['ranking_total']<.8:
            recusas.append(c['split']+': menos de 80% dos pares corretos no ranking')
        if c['livre_depois']/c['livre_total']<.8:
            recusas.append(c['split']+': menos de 80% dos pares corretos em geração livre')
    return dict(decisao='rejeitado' if recusas else 'requer_revisao_semantica',
        ativar_no_chat=False,pesos_sha256=candidato_validacao['pesos_sha256'],
        comparacoes=comparacoes,motivos=recusas,
        limiar=.8,limite='Limiar de engenharia para esta tarefa, não certificação independente. Nenhuma aprovação automática de conversa geral.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('anterior-validacao','candidato-validacao','anterior-teste','candidato-teste','saida'):
        p.add_argument('--'+n,required=True)
    a=p.parse_args()
    def ler(n):return json.loads(Path(getattr(a,n)).read_text())
    r=decidir(ler('anterior_validacao'),ler('candidato_validacao'),ler('anterior_teste'),ler('candidato_teste'))
    Path(a.saida).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(r,ensure_ascii=False))
