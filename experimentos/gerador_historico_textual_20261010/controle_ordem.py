"""Sonda mecanística derivada das duas sessões congeladas de correção.

Mesma bolsa de tokens e pergunta, respostas distintas exigidas. Usa texto
do usuário e uma confirmação fixa, não respostas corretas como contexto.
Não é parte adicional independente do placar de 12 sessões.
"""
import json
import sys
from collections import Counter
from pathlib import Path

DIR=Path(__file__).resolve().parent
sys.path.insert(0,str(DIR))
from executar import protocolo, gravar, RAIZ, normalizar
from dialogo_seq2seq import DialogoSeq2Seq, fonte_dialogo
from arquivos_contextuais import ler_json


def executar():
    p=protocolo()
    casos=json.loads((DIR/'avaliacao_congelada.json').read_text())['sessoes']
    selecionados=[s for s in casos if s['id'] in ['ordem_a','ordem_b']]
    fontes=[];entradas=[]
    for s in selecionados:
        historico=[]
        for t in s['turnos'][:2]:
            historico.extend([{'papel':'usuario','texto':t['mensagem']},
                              {'papel':'assistente','texto':'Entendi.'}])
        mensagem=s['turnos'][-1]['mensagem']
        fontes.append(fonte_dialogo(mensagem,historico,192))
        entradas.append({'sessao':s['id'],'mensagem':mensagem,'historico':historico,
            'exige':s['turnos'][-1]['exige_qualquer_por_grupo'][0][0],
            'proibido':s['turnos'][-1]['proibidos'][0]})
    if Counter(fontes[0])!=Counter(fontes[1]) or fontes[0]==fontes[1]:
        raise ValueError('Controle exige mesmos tokens e ordem diferente')
    resultados={}
    for nome,path in [('seq2seq_existente',RAIZ/'rede_dialogo_seq2seq.json.gz'),
                      ('rodada2',DIR/'checkpoint_rodada2.json.gz')]:
        modelo=DialogoSeq2Seq(ler_json(path));saidas=[]
        for e in entradas:
            saida=modelo.gerar(e['mensagem'],e['historico'],**p['decodificacao'])
            texto=normalizar(saida['texto'])
            saidas.append({**e,'saida':saida,
                'usou_correcao_sem_anterior':normalizar(e['exige']) in texto and normalizar(e['proibido']) not in texto})
        resultados[nome]={'casos':saidas,'acertos':sum(s['usou_correcao_sem_anterior'] for s in saidas),
            'respostas_distintas':saidas[0]['saida']['texto']!=saidas[1]['saida']['texto']}
    gravar('controle_ordem.json',{'mesma_bolsa_tokens':True,'sequencias_diferentes':True,
        'limite':'sonda mecanística derivada do holdout; não prova interpretação universal ou naturalidade',
        'resultados':resultados})
    print(json.dumps({k:{j:v[j] for j in ['acertos','respostas_distintas']} for k,v in resultados.items()},ensure_ascii=False))


if __name__=='__main__':
    executar()
