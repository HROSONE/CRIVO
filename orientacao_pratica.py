"""Orientação autoral limitada, baseada nos relatos e tarefas já existentes.

Não acrescenta memória nem fatos ao acervo. Recomendações de desenho são
propostas; horta começa por observação/perguntas; frações têm cálculo exato.
"""
import re
from fractions import Fraction
from math import gcd
from composicao_textual import normalizar


def _literal(texto):
    return not any(c in texto for c in ('`', '"', '“', '”'))


def _objetivo(texto):
    return re.fullmatch(r'(?:(?:agora|na verdade),? )?(?:eu )?(?:quero|gostaria de) (?!saber\b|conversar\b)(.+?)[.!]?', texto.strip(), re.I)


def _declaracoes(texto):
    if not _literal(texto):return []
    return [t for t in re.split(r'(?<=[.!?])\s+',texto) if '?' not in t and not re.match(r'e se\b',normalizar(t))]


def _ato(texto, dominio):
    n=normalizar(texto)
    if re.search(r'\bnao (?:quero|desenhe|escreva|estude|continue|faca|me ajude)\b',n):
        return None
    if re.search(r'\bo que (?:eu )?queria desenhar|qual (?:era|e) (?:o )?meu objetivo\b',n):
        return 'lembrar'
    if re.fullmatch(r'qual (?:e )?a fonte[?!.]?|de onde (?:veio|tirou) essa orientacao[?!.]?',n):
        return 'fonte'
    if dominio=='horta' and re.search(r'\be se\b.*\b(?:sol|luz)\b',n):
        return 'hipotese'
    if dominio=='estudo' and _resposta_fracao(texto):
        return 'conferir'
    if re.search(r'\berrei\b|\bcomo (?:eu )?corrijo\b|\bficou errad',n):
        return 'corrigir'
    if re.search(r'\bnao entendi\b|\b(?:explique|explica) (?:de )?outro jeito\b|\bmais simples\b',n):
        return 'reformular'
    if re.search(r'\b(?:exemplo|exemplifique)\b',n) and '?' in texto or re.fullmatch(r'(?:me )?(?:de|mostre) um exemplo[.!]?',n):
        return 'exemplo'
    if re.search(r'\bamanha\b',n) and re.search(r'\bfazer\b|\bfaco\b|\bpasso\b',n):
        return 'amanha'
    if re.search(r'\b(?:depois|proximo passo|passo seguinte)\b',n) or re.fullmatch(r'e agora[?!.]?',n) or re.search(r'\b(?:fiz|desenhei|tracei|terminei)\b.*(?:agora|depois|\?)',n):
        return 'proximo'
    if re.search(r'\b(?:so isso|precisa saber.*orientar)\b',n):
        return 'esclarecer'
    if re.search(r'\b(?:como|por onde) (?:eu )?comeco\b|\bprimeiro traco\b|\batividade para comecar\b|\bacao concreta\b',n):
        return 'iniciar'
    return None


def _resposta_fracao(texto):
    # A normalização de intenção remove pontuação, inclusive a barra da fração.
    return re.search(r'\b(?:deu|obtive|(?:minha|a) resposta [eé])\s+(\d+\s*/\s*\d+)', texto, re.I)


def rotear(texto, bot):
    if not _literal(texto) or re.search(r'\bmudando de assunto\b',normalizar(texto)):
        return None
    historico=bot.historico[-20:]
    objetivo=None;inicio=None
    for i,h in enumerate(historico):
        for t in _declaracoes(h['pergunta']):
            m=_objetivo(t)
            if m:objetivo=m[1].rstrip('.!');inicio=i
    for t in _declaracoes(texto):
        m=_objetivo(t)
        if m:objetivo=m[1].rstrip('.!');inicio=len(historico)
    if objetivo is None:
        return None  # Uma declaração nova continua no executor de relatos.
    n=normalizar(objetivo)
    dominio=('desenho' if re.search(r'\bdesenh\w*\b',n) else
             'horta' if re.search(r'\bhorta\b',n) else
             'estudo' if re.search(r'\b(?:estud\w*|aprender)\b',n) and re.search(r'\b(?:matematica|fracoes)\b',n) else None)
    if not dominio:return None
    # Um objetivo antigo não toma perguntas soltas de uma tarefa posterior.
    for h in historico[inicio+1:]:
        pergunta=normalizar(h['pergunta'])
        if h['id'].startswith(('conhecimento:','logica:','calculo:','programacao:','escrita:','conversa:gerada_','conversa:raciocinio','conversa:memoria_sessao','conversa:sessao_')) or re.search(r'\bmudando de assunto\b|\bnao (?:quero|desenhe|escreva|estude|continue|faca|me ajude)\b',pergunta):
            return None
        if re.match(r'(?:o que e|quanto e)\b',pergunta) and not h['id'].startswith('conversa:orientacao_'):
            return None
    if re.match(r'(?:o que (?:e|é)|quanto (?:e|é))\b',texto.strip(),re.I):
        return None
    ato=_ato(texto,dominio)
    if not ato:return None
    fontes=[t for h in historico[inicio:] for t in _declaracoes(h['pergunta'])]+_declaracoes(texto)
    tempo=None;vasos=None;borracha=None
    for t in fontes:
        nt=normalizar(t)
        m=re.search(r'\b(?:tenho|disponho de) ((?:\d+|um|dois|tres|cinco|dez|vinte|trinta) minutos?(?: por dia)?)\b',t,re.I)
        if m:tempo=m[1]
        m=re.search(r'\b((?:\d+|um|dois|três|tres|quatro|cinco) vasos?)\b',t,re.I)
        if m:vasos=m[1]
        if re.search(r'\b(?:sem borracha|nao tenho (?:uma )?borracha|sem apagar|so tenho (?:uma )?caneta)\b',nt):borracha=False
        elif re.search(r'\btenho (?:uma )?borracha\b',nt):borracha=True
    tema_fracoes=any(re.search(r'\bfracoes\b',normalizar(t)) for t in fontes)
    anterior=next((h.get('natural_routing',{}).get('quadro_pratico',{}).get('calculo') for h in reversed(historico[inicio:]) if h.get('natural_routing',{}).get('quadro_pratico',{}).get('calculo')),None)
    forma=None
    for t in fontes:
        m=re.search(r'\b(?:fiz|desenhei|tracei) (?:um|uma) (círculo|circulo|oval)\b',t,re.I)
        if m:forma=m[1]
    return {'peca':'orientacao','ato':ato,'referentes':[objetivo],'dominio':dominio,'objetivo':objetivo,'forma':forma,
            'fontes_contexto':fontes,'pedido':texto,'tempo':tempo,'vasos':vasos,'borracha':borracha,
            'tema_fracoes':tema_fracoes,'calculo_anterior':anterior,'hipotese':ato=='hipotese'}


def _conta(expressao):
    m=re.fullmatch(r'\s*(\d{1,4})\s*/\s*(\d{1,4})\s*([+-])\s*(\d{1,4})\s*/\s*(\d{1,4})\s*',expressao)
    if not m:return None
    a,b,op,c,d=m.groups();a,b,c,d=map(int,(a,b,c,d))
    if b==0 or d==0:return None
    den=b*d//gcd(b,d);x=a*(den//b);y=c*(den//d)
    total=Fraction(a,b)+(Fraction(c,d) if op=='+' else -Fraction(c,d))
    resultado=str(total.numerator)+'/'+str(total.denominator)
    return {'expressao':expressao,'a':str(a)+'/'+str(b),'b':str(c)+'/'+str(d),'operador':op,
            'denominador':den,'x':x,'y':y,'resultado':resultado,'conferido':True,
            'origem':'exercicio_autoral'}


def executar(rota):
    d,ato=rota['dominio'],rota['ato'];texto=rota['pedido'];n=normalizar(texto)
    base='Para “'+rota['objetivo']+'”, '
    quadro={'dominio':d,'ato':ato,'fontes_usuario':list(rota['fontes_contexto']),
            'hipotese':rota['hipotese'],'gerador_neural_usado':False,'limite':'orientação autoral limitada; não consulta factual nem planejamento geral'}
    if ato=='lembrar':
        resposta='Você queria '+rota['objetivo']+'. Isso veio do objetivo que você declarou nesta conversa.'
    elif ato=='fonte':
        resposta=base+'esta orientação é uma proposta autoral do CRIVO, baseada no que você contou. Não é uma informação retirada de uma ficha do acervo nem uma garantia de resultado.'
        if rota['calculo_anterior']:
            resposta+=' O exemplo de frações foi conferido por cálculo exato: '+rota['calculo_anterior']['expressao']+' = '+rota['calculo_anterior']['resultado']+'.'
    elif d=='desenho':
        peixe=bool(re.search(r'\bpeixe\b',normalizar(rota['objetivo'])))
        if ato=='corrigir':
            parte=next((p for p in ('cauda','olho','corpo') if re.search(r'\b'+p+r'\b',n)),None)
            if not parte:resposta=base+'qual parte do desenho saiu diferente do que você queria? Descreva o traço para eu sugerir um ajuste.'
            elif rota['borracha'] is False:
                resposta=base+'para ajustar a '+parte+' sem apagar, aproveite o traço existente e faça uma nova linha leve ao lado. Se não couber, deixe essa tentativa como rascunho e tente outro contorno no espaço livre do mesmo papel.'
            else:resposta=base+'tente ajustar a '+parte+' com duas linhas leves que saiam do corpo. Se tiver borracha, apague apenas o trecho que deseja refazer; conserve o resto do desenho.'
        elif peixe and ato=='proximo':
            if rota['forma']:
                resposta=base+'se o '+rota['forma']+' que você fez será o corpo do peixe, acrescente um triângulo para a cauda de um lado e um ponto para o olho do outro. Se essa forma era outra parte, me diga qual antes de avançarmos.'
            else:resposta=base+'qual parte do peixe você já desenhou? Se o corpo estiver pronto, uma opção é acrescentar uma cauda triangular e um ponto para o olho.'
        elif peixe:
            resposta=base+'uma opção simples é começar com um oval leve para o corpo do peixe. Depois acrescente uma cauda triangular e um ponto para o olho. Faça um rascunho, sem exigir que fique perfeito.'
        else:resposta=base+'esboce primeiro o contorno principal com traços leves; depois escolha um detalhe para acrescentar. Qual parte você quer representar primeiro?'
        if rota['tempo'] and ato!='lembrar':resposta+=' Você informou '+rota['tempo']+'; use esse limite para fazer apenas o rascunho inicial.'
    elif d=='horta':
        if ato=='hipotese':
            resposta=base+'nessa hipótese de não haver sol direto, ainda preciso saber se entra luz no local da horta antes de escolher plantas. Observe a claridade em horários diferentes e me conte o que encontra; não vou garantir que uma planta cresça sem saber essas condições.'
        elif ato in ('esclarecer','exemplo','reformular'):
            resposta=base+'preciso saber quanta luz chega ao local da horta, o espaço que você pode usar, o tamanho dos vasos e o que pretende plantar. Comece observando a luz e descrevendo esse espaço; depois decidimos a próxima ação.'
        else:resposta=base+'uma ação concreta para hoje é observar a luz no local da horta e anotar quando ele recebe claridade ou sol direto. Verifique também o espaço disponível e descreva os vasos antes de comprar ou escolher plantas.'
        if rota['vasos']:resposta+=' Você declarou '+rota['vasos']+'; vamos considerar esses vasos no preparo da horta.'
    else:
        if not rota['tema_fracoes']:
            resposta=base+'qual tópico de matemática você quer praticar e qual é a dificuldade? Preciso desse assunto para propor um exercício adequado.'
        else:
            m=re.search(r'\d{1,4}\s*/\s*\d{1,4}\s*[+-]\s*\d{1,4}\s*/\s*\d{1,4}',texto)
            expr=m[0] if m else (rota['calculo_anterior'] or {}).get('expressao','1/2 + 1/4')
            if ato=='amanha':expr='1/3 + 1/6'
            calc=_conta(expr)
            if calc:quadro['calculo']=calc
            if ato=='conferir' and not m and not rota['calculo_anterior']:
                quadro.pop('calculo',None);resposta=base+'qual exercício de frações produziu essa resposta? Envie a conta para eu conferir, sem adivinhar os números.'
            elif not calc:resposta=base+'envie duas frações com denominadores diferentes de zero para eu conferir essa conta.'
            elif ato=='conferir':
                informado=_resposta_fracao(texto)[1]
                try:certo=Fraction(informado.replace(' ',''))==Fraction(calc['resultado'])
                except (ValueError,ZeroDivisionError):certo=False
                resposta=base+('essa resposta está correta: ' if certo else 'essa resposta não confere; o resultado é ')+calc['resultado']+'. Confira o denominador comum '+str(calc['denominador'])+' no exercício '+calc['expressao']+'.'
            elif ato=='reformular':
                resposta=base+'pense nas frações como partes iguais de uma figura. Para este exemplo, faça um desenho com '+str(calc['denominador'])+' partes iguais. '+calc['a']+' ocupa '+str(calc['x'])+' dessas partes; '+calc['b']+' ocupa '+str(calc['y'])+'. '+('Juntando' if calc['operador']=='+' else 'Retirando')+' essas partes, o resultado é '+calc['resultado']+'. Quer tentar marcar as partes no papel?'
            elif ato=='exemplo':
                resposta=base+'vamos representar frações como partes iguais de uma mesma figura. No exemplo '+calc['expressao']+', use partes com denominador '+str(calc['denominador'])+': '+calc['a']+' vira '+str(calc['x'])+'/'+str(calc['denominador'])+' e '+calc['b']+' vira '+str(calc['y'])+'/'+str(calc['denominador'])+'. Então '+str(calc['x'])+'/'+str(calc['denominador'])+' '+calc['operador']+' '+str(calc['y'])+'/'+str(calc['denominador'])+' = '+calc['resultado']+'.'
            else:resposta=base+'proponho um exercício autoral de frações: tente '+calc['expressao']+'. Desenhe figuras iguais, divida-as em partes iguais e procure um denominador comum. Depois me diga o resultado para conferirmos.'
            if rota['tempo']:resposta+=' Você informou '+rota['tempo']+'; faça uma tentativa curta e anote a dúvida que sobrar.'
    rota['quadro_pratico']=quadro
    return ('conversa:orientacao_'+ato,resposta),quadro


def conferir(rota,resposta):
    """A orientação não pode inventar dados pessoais ou perder o objetivo."""
    motivos=[];n=normalizar(resposta)
    if normalizar(rota['objetivo']) not in n:motivos.append('objetivo declarado ausente')
    if not any(normalizar(rota['objetivo']) in normalizar(t) for t in rota['fontes_contexto']):motivos.append('objetivo sem fonte do usuário')
    if rota['dominio']=='desenho' and rota['borracha'] is False and re.search(r'\b(?:apague|use a borracha)\b',n):motivos.append('restrição de material desrespeitada')
    if rota['dominio']=='horta' and re.search(r'\b(?:plante|garanto|vai crescer)\b',n):motivos.append('recomendação factual sem condições confirmadas')
    q=rota.get('quadro_pratico',{}).get('calculo')
    if q and rota['ato'] in ('exemplo','reformular','conferir'):
        prova=_conta(q['expressao'])
        if not prova or any(prova[k]!=q[k] for k in ('a','b','operador','denominador','x','y','resultado')) or q['resultado'] not in resposta:motivos.append('resultado aritmético não confere')
        for a,b in re.findall(r'(\d+/\d+) vira (\d+/\d+)',resposta):
            try:equivalente=Fraction(a)==Fraction(b)
            except (ValueError,ZeroDivisionError):equivalente=False
            if not equivalente:motivos.append('conversão de fração incorreta')
    return {'aceita':not motivos,'motivos':motivos,'politica':'orientacao_contextual'}
