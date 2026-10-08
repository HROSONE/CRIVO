"""Símbolos locais para nomes explícitos, sem fatos ou rótulos na entrada.

Usa somente palavras com inicial maiúscula fora de uma lista fixa de palavras
funcionais. Não é reconhecimento universal de entidades: nomes minúsculos,
compostos e mais de oito entidades não têm cobertura garantida. Mantém mapa
de caracteres para copiar a fonte original, inclusive após alteração de tamanho.
"""
import re
from comum import ANTERIOR
from modelo import codificar as codificar_original

SIMBOLOS=['Ana','Beto','Caio','Dora','Iara','Rui','Lia','Leo']
FUNCIONAIS=set(('A O As Os Um Uma Uns Umas Eu Tu Ele Ela Eles Elas Nós Vocês '
    'Para Por Pelo Pela Pelos Pelas De Do Da Dos Das Em No Na Nos Nas Ao Aos À Às '
    'E Mas Ou Se Só Não Sim Com Sem Sobre Entre Antes Depois Agora Hoje Quanto '
    'Qual Quais Quem Que Como Quando Onde Compare Diga Mostre Retome Lembre '
    'Volte Considere Calcule Corrijo Corrigindo Corrigido Corrigida Corrigidos '
    'Atualize Atualizando Atualizado Atualizada Atualizados Substitua Retifique '
    'Faça Imagine Esqueça Desconsidere Retire Mude Nada Tudo Use Vamos Saia '
    'Encerre Escolhendo Chega Acabei Quero Tenho Recapitule Conserve Recupere '
    'Organize Resuma Confira Cumpre Inventário Registro Requisitos '
    'Plano Planos Opção Opções Pessoa Pessoas Custo Custos Preço Preços Valor Valores '
    'Regra Regras Hipótese Hipóteses Situação Simulação Cenário Cenários').casefold().split())

def normalizar(turnos):
    nomes={}
    for texto in turnos:
        for m in re.finditer(r'(?<!\w)[A-ZÀ-ÖØ-Þ][^\W\d_]+(?!\w)',texto):
            n=m[0].casefold()
            if n in FUNCIONAIS or n in nomes:continue
            if len(nomes)==len(SIMBOLOS):raise ValueError('Mais de oito nomes candidatos; normalização não suportada.')
            nomes[n]=SIMBOLOS[len(nomes)]
    padrao=re.compile(r'(?<!\w)(?:'+ '|'.join(re.escape(n) for n in sorted(nomes,key=len,reverse=True))+r')(?!\w)',re.I) if nomes else None
    # A ordem explícita da última consulta de dois nomes define os slots. Sem
    # essa consulta, usa primeira menção. Não procura preços nem alvos gold.
    prioridade=[]
    if padrao:
        for texto in turnos:
            for frase in re.findall(r'[^.!?\n]+[.!?]?',texto):
                if not (frase.rstrip().endswith('?') or re.match(r'\s*(?:Compare|Calcule|Diga)\b',frase)):continue
                ns=list(dict.fromkeys(m[0].casefold() for m in padrao.finditer(frase)))
                if len(ns)>=2:prioridade=ns
        ordem=prioridade+[n for n in nomes if n not in prioridade]
        nomes={n:SIMBOLOS[i] for i,n in enumerate(ordem)}
    saida=[];mapas=[]
    for texto in turnos:
        novo=[];mapa=[];ultimo=0
        for m in padrao.finditer(texto) if padrao else []:
            novo.append(texto[ultimo:m.start()]);mapa.extend((i,i+1) for i in range(ultimo,m.start()))
            simbolo=nomes[m[0].casefold()];novo.append(simbolo);mapa.extend([(m.start(),m.end())]*len(simbolo));ultimo=m.end()
        novo.append(texto[ultimo:]);mapa.extend((i,i+1) for i in range(ultimo,len(texto)))
        saida.append(''.join(novo));mapas.append(mapa)
    return saida,mapas,nomes

def codificar(tok,exemplo):
    turnos,mapas,nomes=normalizar(exemplo['turnos'])
    item=codificar_original(tok,{'turnos':turnos,'argumentos':[None]*3,'referente':None})
    offsets=[]
    for o in item['offsets']:
        if o is None:offsets.append(None);continue
        t,a,b=o;ms=mapas[t][a:b]
        if not ms:raise ValueError('Token sem suporte de caracteres.')
        offsets.append((t,min(m[0] for m in ms),max(m[1] for m in ms)))
    item['offsets']=offsets;item['exemplo']=exemplo;item['simbolos_locais']=nomes
    pontos=[];null=len(item['ids'])-1
    for span in exemplo['argumentos']+[exemplo['referente']]:
        if span is None:pontos.extend([null,null]);continue
        inds=[i for i,o in enumerate(offsets) if o and o[0]==span['turno'] and o[2]>span['inicio'] and o[1]<span['fim']]
        if not inds:raise ValueError('Alvo sem fonte normalizada.')
        pontos.extend([inds[0],inds[-1]])
    item['pontos']=pontos
    return item
