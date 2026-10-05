"""Respostas livres em cenários de validação; usa o próprio histórico gerado.

Os alvos aparecem no relatório para revisão, nunca no contexto do gerador.
Esta sonda não seleciona dados de treino e não certifica fatos por palavras-chave.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def cenarios(corpus, quantidade=8):
    grupos={}
    for linha in (Path(corpus)/'dialogos_validacao.jsonl').read_text().splitlines():
        e=json.loads(linha)
        if e['grupo'].startswith('autoral:'):
            grupos.setdefault(e['grupo'],[]).append(e)
    selecionados=[]
    for grupo in sorted(grupos,key=lambda x:hashlib.sha256(('painel-integro-v1:'+x).encode()).hexdigest()):
        # O último par contém os turnos anteriores completos da mesma árvore.
        e=max(grupos[grupo],key=lambda x:len(x.get('historico',[])))
        turnos=e.get('historico',[])+[dict(papel='usuario',texto=e['mensagem']),dict(papel='assistente',texto=e['resposta'])]
        selecionados.append(dict(grupo=grupo,familia=e['familia'],turnos=turnos))
        if len(selecionados)==quantidade:break
    if len(selecionados)!=quantidade:raise ValueError('Validação não contém cenários suficientes')
    return selecionados


def repeticao(texto):
    palavras=re.findall(r'\w+',texto.casefold())
    seq=[tuple(palavras[i:i+4]) for i in range(len(palavras)-3)]
    return len(seq)!=len(set(seq))


def avaliar(modelo_path,corpus,quantidade=8,temperatura=0.,max_tokens=128):
    import torch
    from linguagem_profunda import carregar,fonte_dialogo,ESPECIAIS
    from geracao_incremental import gerar
    torch.set_num_threads(2)
    modelo,t,estado=carregar(modelo_path)
    itens=cenarios(corpus,quantidade)
    respostas=[]
    for c in itens:
        historico=[]
        for i in range(0,len(c['turnos']),2):
            mensagem=c['turnos'][i]['texto'];referencia=c['turnos'][i+1]['texto']
            fonte=fonte_dialogo(t,mensagem,historico,modelo.config.contexto)
            ids,fim=gerar(modelo,fonte,t.token_to_id('<fim>'),max_tokens=max_tokens,
                          temperatura=temperatura,semente=42,
                          proibidos=[t.token_to_id(x) for x in ESPECIAIS[:-1]])
            texto=t.decode(ids)
            respostas.append(dict(grupo=c['grupo'],turno=i//2,mensagem=mensagem,
                referencia=referencia,resposta=texto,terminou=fim,repeticao=repeticao(texto)))
            historico.extend([dict(papel='usuario',texto=mensagem),dict(papel='assistente',texto=texto)])
    return dict(particao='validacao',historico='respostas_do_proprio_modelo',
        criterio='termino e repeticao sao diagnosticos; coerencia e correcoes exigem revisao',
        passo=estado['passo'],pesos_sha256=hashlib.sha256((Path(modelo_path)/'pesos.pt').read_bytes()).hexdigest(),
        cenarios_sha256=hashlib.sha256(json.dumps(itens,sort_keys=True).encode()).hexdigest(),
        temperatura=temperatura,max_tokens=max_tokens,turnos=len(respostas),
        terminadas=sum(r['terminou'] for r in respostas),repetitivas=sum(r['repeticao'] for r in respostas),respostas=respostas)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modelo',required=True);p.add_argument('--corpus',required=True);p.add_argument('--saida',required=True)
    p.add_argument('--cenarios',type=int,default=8);p.add_argument('--temperatura',type=float,default=0.)
    a=p.parse_args();r=avaliar(a.modelo,a.corpus,a.cenarios,a.temperatura)
    Path(a.saida).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k!='respostas'},ensure_ascii=False))
