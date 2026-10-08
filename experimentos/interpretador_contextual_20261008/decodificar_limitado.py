"""Ablacão de cópia limitada, escolhida pela validação antes do teste.

Enumera argumentos de gramática declarada nas falas brutas; a rede escolhe
fontes entre eles. Não lê alvos/família/etapa. Essa gramática é parte da ajuda
determinística, logo o resultado não pode ser atribuído apenas ao transformer.
"""
import re
import torch
from modelo import recuperar
from corpus import OPERACOES

PADROES = {
 'numero': r'(?<!\w)-?\d+(?:[.,]\d+)?(?!\w)',
 'pessoa': r'(?<!\w)[A-ZÀ-ÖØ-Þ][^\W\d_]+(?!\w)',
 'regra': r'\b(?:exigidos|exigidas|requeridos|requeridas)\s+([^.!?;\n]+)',
 'posse': r'\b(?:não\s+)?tem\s+[^\W\d_]+(?:\s+e\s+(?:não\s+tem\s+)?[^\W\d_]+)*',
 'objetivo': r'\b(?:quero|pretendo|objetivo\s+(?:fosse|é))\s+([^,.!?;\n]+)',
 'restricao': r'\bmas\s+(?:eu\s+)?tenho\s+([^.!?;\n]+)',
}
EXCLUIR = set('Sobre Mudei Para Num Se Volte Desconsidere Retire Resuma Agora Quero Quanto Qual Quem Retome Lembre Calcule Tenho Corrijo Confira Os No Depois Ao Diga Compare Mostre Tudo Há Falta Entre Organize Não Quando Considerando Com Sem Ainda Só A O E'.split())
TIPOS = {'comparar_custos':['numero','numero',None,None],
         'tempo_restante':['numero','numero','numero',None],
         'consultar_valor':['numero',None,None,'pessoa'],
         'verificar_requisitos':['regra','posse',None,'pessoa'],
         'resumir_objetivos':['objetivo','restricao',None,'pessoa'],
         'esclarecer':[None,None,None,None]}


def candidatos(item, tipo):
    out=[]
    for t,texto in enumerate(item['exemplo']['turnos']):
        for m in re.finditer(PADROES[tipo],texto):
            a,b=m.span(1) if m.lastindex else m.span()
            literal=texto[a:b].strip()
            if tipo=='pessoa' and literal in EXCLUIR:continue
            inds=[i for i,o in enumerate(item['offsets']) if o and o[0]==t and o[2]>a and o[1]<b]
            if inds:
                # Usar o intervalo de caracteres do detector, preservando toda
                # palavra mesmo que o BPE tenha várias partes. Sem completar
                # texto por geração nem inventar fonte.
                out.append((inds, {'turno':t,'inicio':a,'fim':b,'texto':texto[a:b]}))
    return out


def proposta_limitada(item, logits, idx):
    prob=logits['operacao'][idx].softmax(-1);op=OPERACOES[int(prob.argmax())]
    pontos=logits['pontos'][idx];null=len(item['ids'])-1;trechos=[]
    for slot,tipo in enumerate(TIPOS[op]):
        if tipo is None:trechos.append(None);continue
        poss=[([null],None)]+candidatos(item,tipo)
        scores=[]
        for inds,trecho in poss:
            # Média de massa por token evita preferência por trechos longos.
            k=torch.tensor(inds);s=pontos[2*slot,k];e=pontos[2*slot+1,k]
            scores.append(float(torch.logsumexp(s,0)+torch.logsumexp(e,0)-2*torch.log(torch.tensor(float(len(inds))))))
        escolhido=max(range(len(scores)),key=scores.__getitem__)
        trechos.append(poss[escolhido][1])
    return {'operacao':op,'confianca_operacao':float(prob.max()),'argumentos':trechos[:3],
            'referente':trechos[3],'hipotese':bool(logits['escopo'][idx].argmax()),
            'fontes':sorted({s['turno'] for s in trechos if s}),
            'decodificacao':'candidatos_da_gramatica_propria_com_escolha_neural',
            'limite':'Ajuda determinística limitada à gramática declarada. Não extrai toda linguagem natural.'}
