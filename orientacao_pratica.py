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
    return re.fullmatch(r'(?:(?:agora|na verdade),? )?(?:eu )?(?:quero|gostaria de) (?!saber\b|conversar\b|falar\b)(.+?)[.!]?', texto.strip(), re.I)


def _declaracoes(texto):
    if not _literal(texto):return []
    from dialogo_situado import hipotetico
    return [t for t in re.split(r'(?<=[.!?])\s+',texto) if '?' not in t and not hipotetico(normalizar(t))
            and not re.match(r'(?:acho|acredito|talvez)\b',normalizar(t))]


def _ato(texto, dominio):
    n=normalizar(texto)
    if re.search(r'\bnao (?:quero|desenhe|escreva|estude|continue|faca|me ajude)\b',n):
        return None
    if re.search(r'\bo que (?:eu )?queria desenhar|qual (?:era|e) (?:o )?meu objetivo\b',n):
        return 'lembrar'
    if re.fullmatch(r'qual (?:e )?a fonte[?!.]?|de onde (?:veio|tirou) essa orientacao[?!.]?',n):
        return 'fonte'
    if dominio=='horta' and re.search(r'\be se\b.*\b(?:sol|luz|sombra)\b',n):
        return 'hipotese'
    if dominio=='estudo' and _resposta_fracao(texto):
        return 'conferir'
    if re.search(r'\berrei\b|\bcomo (?:eu )?corrijo\b|\bficou errad',n):
        return 'corrigir'
    if re.search(r'\bnao entendi\b|\b(?:explique|explica) (?:de )?outro jeito\b|\bmais simples\b|\bexplique sem usar palavras dificeis\b',n):
        return 'reformular'
    if re.search(r'\b(?:exemplo|exemplifique)\b',n) and '?' in texto or re.fullmatch(r'(?:me )?(?:de|mostre) um exemplo[.!]?',n):
        return 'exemplo'
    if dominio=='estudo' and re.search(r'\b(?:outro|novo) exercicio\b',n):
        return 'outro'
    if re.search(r'\bquanto tempo\b|\bqual foi minha dificuldade\b|\bo que voce ja sabe\b',n):
        return 'resumir'
    if re.search(r'\bamanha\b',n) and re.search(r'\bfazer\b|\bfaco\b|\bpasso\b',n):
        return 'amanha'
    if re.search(r'\b(?:depois|proximo passo|proximo traco|passo seguinte)\b',n) or re.fullmatch(r'e agora[?!.]?',n) or re.search(r'\b(?:fiz|desenhei|tracei|terminei)\b.*(?:agora|depois|\?)',n):
        return 'proximo'
    if re.search(r'\b(?:so isso|precisa saber.*orientar|falta.*orientar|informacao.*faltando)\b',n):
        return 'esclarecer'
    if re.search(r'\b(?:como|por onde) (?:eu )?comeco\b|\bprimeiro traco\b|\batividade para comecar\b|\bacao concreta\b',n):
        return 'iniciar'
    return None


def _resposta_fracao(texto):
    # A normalização de intenção remove pontuação, inclusive a barra da fração.
    return re.search(r'\b(?:deu|obtive|(?:minha|a) resposta [eé])\s+(\d+\s*/\s*\d+)', texto, re.I)


def _dominio(objetivo):
    n=normalizar(objetivo)
    return ('desenho' if re.search(r'\bdesenh\w*\b',n) else
            'horta' if re.search(r'\bhorta\b',n) else
            'estudo' if re.search(r'\b(?:estud\w*|aprender)\b',n) and re.search(r'\b(?:matematica|fracoes)\b',n) else None)


def rotear(texto, bot):
    if not _literal(texto) or re.search(r'\bmudando de assunto\b',normalizar(texto)):
        return None
    historico=bot.historico[-20:]
    objetivo=None;inicio=None;ativo=None;anteriores=[];retomada=False
    for i,pergunta in enumerate([h['pergunta'] for h in historico]+[texto]):
        for t in _declaracoes(pergunta):
            m=_objetivo(t)
            if not m:continue
            novo=m[1].rstrip('.!');nn=normalizar(novo)
            voltar=re.match(r'voltar (?:as|a|aos|ao) (.+)',nn)
            if voltar:
                encontrado=next(((o,j) for o,j in reversed(anteriores) if voltar[1] in normalizar(o)
                                or voltar[1]=='fracoes' and _dominio(o)=='estudo' and any('fracoes' in normalizar(t)
                                    for h in historico[j:i] for t in _declaracoes(h['pergunta']))),None)
                if not encontrado:return None
                objetivo,inicio=encontrado;ativo=i;retomada=i==len(historico)
            elif objetivo and _dominio(objetivo)=='horta' and re.match(r'cultivar\b',nn):
                continue  # Refinamento do que plantar, não nova tarefa.
            else:
                # Disponibilidade é uma restrição, não parte do nome da tarefa.
                novo=re.split(r'\s+(?:e|mas)\s+(?:(?:so|apenas)\s+)?tenho\s+',novo,flags=re.I)[0]
                objetivo=novo;inicio=ativo=i;anteriores.append((novo,i))
    if objetivo is None:return None
    dominio=_dominio(objetivo)
    if not dominio:return None
    for h in historico[ativo+1:]:
        pergunta=normalizar(h['pergunta'])
        if h['id'].startswith(('conhecimento:','logica:','calculo:','programacao:','escrita:','conversa:gerada_','conversa:raciocinio','conversa:memoria_sessao','conversa:sessao_','conversa:abertura','conversa:reinicio')) or re.search(r'\bmudando de assunto\b|\bnao (?:quero|desenhe|escreva|estude|continue|faca|me ajude)\b',pergunta):
            return None
        if re.match(r'(?:o que e|quanto e)\b',pergunta) and not h['id'].startswith('conversa:orientacao_'):
            return None
    if re.match(r'(?:o que (?:e|é)|quanto (?:e|é))\b',texto.strip(),re.I):return None
    fontes=[t for h in historico[inicio:] for t in _declaracoes(h['pergunta'])]+_declaracoes(texto)
    ato='retomar' if retomada else _ato(texto,dominio)
    declaracoes=_declaracoes(texto)
    if not ato and (ativo==len(historico) or any(re.search(
            r'\b(?:tenho (?:dificuldade|(?:\d+|um|dois|tres|quatro|cinco|dez|quinze|vinte|trinta) (?:minutos?|vasos?)|(?:uma )?borracha)|observei.*(?:sol|luz|sombra)|recebe sol|quero cultivar|nao tenho dinheiro)\b',normalizar(t)) for t in declaracoes)):
        ato='registrar'
    if not ato:return None
    tempo=None;vasos=None;borracha=None;forma=None;rodas=False;corpo=False;luz=None;erva=None;sem_comprar=False;dificuldade=None
    from dialogo_situado import minutos_declarados
    # Disponibilidade pessoal permanece entre tarefas; fatos do exercício não.
    for t in [t for h in historico for t in _declaracoes(h['pergunta'])]+declaracoes:
        valor=minutos_declarados(t)
        if valor:
            m=re.search(r'((?:\d+|um|dois|tres|quatro|cinco|dez|quinze|vinte|trinta) minutos?(?: por dia)?)',t,re.I)
            tempo=m[1] if m else valor+' minutos'
        elif re.search(r'\bnao tenho (?:mais )?tempo\b',normalizar(t)):tempo=None
    for t in fontes:
        nt=normalizar(t)
        m=re.search(r'\b((?:\d+|um|dois|três|tres|quatro|cinco) vasos?)\b',t,re.I)
        if m:vasos=None if re.search(r'\bnao tenho\b',nt) else m[1]
        if re.search(r'\b(?:sem borracha|nao tenho (?:uma )?borracha|sem apagar|so tenho (?:uma )?caneta)\b',nt):borracha=False
        elif re.search(r'\btenho (?:uma )?borracha\b',nt):borracha=True
        m=re.search(r'\b(?:fiz|desenhei|tracei) (?:um|uma|dois|duas) (círculos?|circulos?|oval)\b',t,re.I)
        if m:forma=m[1] if not m[1].endswith('s') else re.sub(r'^(?:fiz|desenhei|tracei)\s+', '',m[0],flags=re.I)
        if re.search(r'\b(?:circulos sao as rodas|desenhei (?:as |duas )?rodas|fiz (?:as |duas )?rodas)\b',nt):rodas=True
        if re.search(r'\b(?:desenhei|fiz) (?:o )?corpo\b',nt):corpo=True
        if not re.search(r'\b(?:se|talvez|acho|caso|quando)\b',nt):
            m=re.search(r'(?:recebe|tem) (sol (?:de|pela) manh[ãa]|sombra|luz[^.!?]*)',t,re.I)
            if m:luz=None if re.search(r'\b(?:nao|nunca)\b.*\b(?:recebe|tem) (?:sol|luz|sombra)\b',nt) else m[1]
        if re.search(r'\bquero cultivar\b',nt):erva=t.rstrip('.!')
        if re.search(r'\bnao tenho dinheiro para comprar vasos\b',nt):sem_comprar=True
        if re.search(r'\btenho dificuldade\b',nt):dificuldade=t.rstrip('.!')
    tema_fracoes=any(re.search(r'\bfracoes\b',normalizar(t)) for t in fontes)
    anterior=next((h.get('natural_routing',{}).get('quadro_pratico',{}).get('calculo') for h in reversed(historico[inicio:])
                   if h.get('natural_routing',{}).get('quadro_pratico',{}).get('dominio')=='estudo'
                   and h.get('natural_routing',{}).get('quadro_pratico',{}).get('calculo')),None)
    ajuste=next((h['pergunta'] for h in reversed(historico[inicio:]) if re.search(r'\berrei\b',normalizar(h['pergunta']))),None)
    return {'peca':'orientacao','ato':ato,'referentes':[objetivo],'dominio':dominio,'objetivo':objetivo,'forma':forma,
            'fontes_contexto':fontes,'pedido':texto,'tempo':tempo,'vasos':vasos,'borracha':borracha,
            'tema_fracoes':tema_fracoes,'calculo_anterior':anterior,'hipotese':ato=='hipotese',
            'fontes_disponibilidade':[t for h in historico for t in _declaracoes(h['pergunta']) if minutos_declarados(t)]+[t for t in declaracoes if minutos_declarados(t)],
            'rodas':rodas,'corpo':corpo,'luz':luz,'cultivo':erva,'sem_comprar':sem_comprar,'dificuldade':dificuldade,'ajuste':ajuste,
            'pediu_simplificacao':any(re.search(r'\bexplique sem usar palavras dificeis\b',normalizar(h['pergunta'])) for h in historico[inicio:])}


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
            'hipotese':rota['hipotese'],'gerador_neural_usado':False,'condicoes_declaradas':{k:rota.get(k) for k in ('tempo','vasos','borracha','rodas','corpo','luz','cultivo','sem_comprar','dificuldade')},
            'fontes_disponibilidade':rota['fontes_disponibilidade'],'limite':'orientação autoral limitada; não consulta factual nem planejamento geral'}
    if ato=='lembrar':
        resposta='Você queria '+rota['objetivo']+'. Isso veio do objetivo que você declarou nesta conversa.'
    elif ato=='fonte':
        resposta=base+'esta orientação é uma proposta autoral do CRIVO, baseada no que você contou. Não é uma informação retirada de uma ficha do acervo nem uma garantia de resultado.'
        if rota['calculo_anterior']:
            resposta+=' O exemplo de frações foi conferido por cálculo exato: '+rota['calculo_anterior']['expressao']+' = '+rota['calculo_anterior']['resultado']+'.'
    elif d=='desenho':
        obj=normalizar(rota['objetivo']);peixe=bool(re.search(r'\bpeixe\b',obj));bicicleta='bicicleta' in obj;ave='passarinho' in obj
        sem_apagar=rota['borracha'] is False
        if ato in ('registrar','retomar','resumir'):
            resposta=base+('vamos retomar esse rascunho.' if ato=='retomar' else 'registrei essa tarefa e as condições que você contou.')
            if sem_apagar:resposta+=' Você está desenhando sem borracha; vamos trabalhar sem apagar.'
        elif ato=='esclarecer':
            resposta=base+'não vejo o desenho. Descreva como ficou a linha, em que ponto ela começa e onde termina, e o que você quer mudar. Assim posso sugerir o próximo traço sem inventar o que está no papel.'
        elif bicicleta:
            ajuste=normalizar(texto if ato=='corrigir' else rota.get('ajuste') or '')
            if (ato=='corrigir' or ato=='reformular' and ajuste) and 'linha entre as rodas' not in ajuste:
                resposta=base+'qual parte da bicicleta você quer ajustar? Descreva a linha que saiu diferente e onde ela fica; não vejo o desenho para adivinhar esse traço.'
            elif ato=='corrigir' or ato=='reformular' and ajuste:
                resposta=base+'para ajustar a linha entre as rodas, deixe a linha anterior como marca do rascunho. Trace uma linha nova, curta e leve, ligando os pontos que você deseja, '+('sem apagar.' if sem_apagar else 'apagando apenas o trecho errado se tiver borracha.')
                if ato=='reformular':resposta+=' Pense só em um traço de cada vez: escolha um ponto perto de uma roda e ligue-o ao ponto perto da outra.'
            elif 'terminar' in n:
                resposta=base+'para terminar este rascunho, acrescente um pequeno traço para o selim e outro para o guidão. Pare aí e confira se as rodas e o quadro ficam reconhecíveis; é uma proposta de desenho, não uma avaliação visual do seu papel.'
            elif rota['rodas']:
                resposta=base+'como você disse que os círculos são as rodas, uma opção de próximo traço é esboçar dois triângulos ligados entre as rodas para representar o quadro. Faça uma linha de cada vez, com traços leves.'
            elif rota['forma'] and not rota['forma'].startswith('dois '):
                resposta=base+'você fez um '+rota['forma']+'. Se essa forma representa uma roda, uma opção é acrescentar outra roda ao lado. Se representa outra parte da bicicleta, me diga qual antes de avançarmos.'
            elif rota['forma']:
                resposta=base+'você fez '+rota['forma']+'. Se esses dois círculos serão as rodas, o próximo passo pode ser ligar as rodas com linhas leves para esboçar o quadro. Se representam outra parte, me diga qual antes de avançarmos.'
            else:resposta=base+'uma opção de começo é traçar dois círculos para as rodas, deixando espaço entre eles para o quadro. Use a caneta com traços leves; se você estiver sem borracha, continue sem apagar e trate a primeira versão como rascunho.'
        elif ave:
            if rota['corpo'] and ato=='proximo':resposta=base+'como você já desenhou o corpo, uma opção é acrescentar um pequeno triângulo para o bico e uma curva para a asa. Escolha um desses traços primeiro e continue o rascunho.'
            else:resposta=base+'comece com um oval leve para o corpo e um círculo menor para a cabeça do passarinho. Depois escolha um detalhe para acrescentar com o lápis.'
        elif ato=='corrigir':
            parte=next((p for p in ('cauda','olho','corpo') if re.search(r'\b'+p+r'\b',n)),None)
            if not parte:resposta=base+'qual parte do desenho saiu diferente do que você queria? Descreva o traço para eu sugerir um ajuste.'
            elif sem_apagar:resposta=base+'para ajustar a '+parte+' sem apagar, aproveite o traço existente e faça uma nova linha leve ao lado. Se não couber, deixe essa tentativa como rascunho e tente outro contorno no espaço livre do mesmo papel.'
            else:resposta=base+'tente ajustar a '+parte+' com duas linhas leves que saiam do corpo. Se tiver borracha, apague apenas o trecho que deseja refazer; conserve o resto do desenho.'
        elif peixe and ato=='proximo':
            if rota['forma']:resposta=base+'se o '+rota['forma']+' que você fez será o corpo do peixe, acrescente um triângulo para a cauda de um lado e um ponto para o olho do outro. Se essa forma era outra parte, me diga qual antes de avançarmos.'
            else:resposta=base+'qual parte do peixe você já desenhou? Se o corpo estiver pronto, uma opção é acrescentar uma cauda triangular e um ponto para o olho.'
        elif peixe:resposta=base+'uma opção simples é começar com um oval leve para o corpo do peixe. Depois acrescente uma cauda triangular e um ponto para o olho. Faça um rascunho, sem exigir que fique perfeito.'
        else:resposta=base+'esboce primeiro o contorno principal com traços leves; depois escolha um detalhe para acrescentar. Qual parte você quer representar primeiro?'
        if sem_apagar and 'sem apagar' not in resposta:resposta+=' Vamos fazer esses traços sem apagar.'
        if rota['tempo']:resposta+=' Você informou '+rota['tempo']+'; use esse limite para fazer apenas o rascunho inicial.'
    elif d=='horta':
        conhecidos=[]
        if rota['vasos']:conhecidos.append(rota['vasos'])
        if rota['luz']:conhecidos.append(rota['luz'])
        if rota['cultivo']:conhecidos.append(rota['cultivo'])
        dados=' Você contou: '+ '; '.join(conhecidos)+'.' if conhecidos else ''
        if ato=='hipotese':
            resposta=base+'nessa hipótese de haver apenas sombra ou não haver sol direto, observe a claridade e por quanto tempo entra luz antes de escolher uma erva. A hipótese não substitui o que você observou: '+(rota['luz'] or 'ainda não há luz observada registrada')+'. Não vou garantir que uma planta cresça nessas condições.'
        elif ato in ('esclarecer','exemplo','reformular'):
            resposta=base+'ainda preciso saber o tamanho dos vasos, se têm furos, quantas horas de luz chegam ao local e qual erva você deseja. '+('Você já observou '+rota['luz']+'; falta medir a duração, não observar isso do zero.' if rota['luz'] else 'Comece observando a luz e descrevendo o espaço disponível.')
        elif ato=='resumir':resposta=base+'isso é o que você declarou sobre a sua horta; não acrescentei condições que você não informou.'
        elif ato=='registrar':resposta=base+'registrei essa condição para orientar os próximos passos da horta.'
        elif ato=='amanha':resposta=base+'amanhã, observe por quanto tempo o sol ou a luz chegam ao local da sua horta e me conte a duração. Confira também o tamanho e os furos dos vasos que já tem; vamos decidir a escolha da erva depois dessas informações.'
        elif rota['luz']:resposta=base+'uma ação concreta é conferir o tamanho e os furos dos vasos que você já tem. Como você observou '+rota['luz']+', anote quanto tempo isso dura antes de escolher a erva.'
        else:resposta=base+'uma ação concreta para hoje é observar a luz no local da horta e anotar quando ele recebe claridade ou sol direto. Verifique também o espaço disponível e descreva os vasos antes de comprar ou escolher plantas.'
        resposta+=dados
        if rota['sem_comprar']:resposta+=' Vamos trabalhar sem comprar vasos novos e usar os vasos que você declarou.'
    else:
        if ato in ('registrar','retomar','resumir'):
            resposta=base+('vamos voltar às frações e retomar a atividade anterior.' if ato=='retomar' else 'registrei o que você contou para continuar sua atividade.')
            if rota['tema_fracoes']:resposta+=' O tópico ativo é frações.'
            if rota['dificuldade']:resposta+=' Você declarou: '+rota['dificuldade']+'.'
            elif ato=='resumir':
                resposta+=(' Você pediu uma explicação sem palavras difíceis; isso é o que observei, não um diagnóstico da sua dificuldade.'
                           if rota['pediu_simplificacao'] else ' Você ainda não declarou uma dificuldade específica.')
            if rota['tempo']:resposta+=' Você informou '+rota['tempo']+'.'
            else:resposta+=' Ainda não informou quanto tempo tem.'
        elif not rota['tema_fracoes']:
            resposta=base+'qual tópico de matemática você quer praticar e qual é a dificuldade? Preciso desse assunto para propor um exercício adequado.'
        else:
            m=re.search(r'\d{1,4}\s*/\s*\d{1,4}\s*[+-]\s*\d{1,4}\s*/\s*\d{1,4}',texto)
            expr=m[0] if m else (rota['calculo_anterior'] or {}).get('expressao','1/2 + 1/4')
            if ato in ('amanha','outro'):
                expr='1/3 + 1/6' if ato=='amanha' else next(e for e in ('1/3 + 1/6','3/4 - 1/8','2/5 + 1/10') if e!=(rota['calculo_anterior'] or {}).get('expressao'))
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
            else:resposta=base+('amanhã, proponho' if ato=='amanha' else 'proponho')+' um exercício autoral de frações: tente '+calc['expressao']+'. Desenhe figuras iguais, divida-as em partes iguais e procure um denominador comum. Depois me diga o resultado para conferirmos.'
            if rota['tempo']:resposta+=' Você informou '+rota['tempo']+'; faça uma tentativa curta e anote a dúvida que sobrar.'
    rota['quadro_pratico']=quadro
    return ('conversa:orientacao_'+ato,resposta),quadro


def conferir(rota,resposta):
    """A orientação não pode inventar dados pessoais ou perder o objetivo."""
    motivos=[];n=normalizar(resposta)
    if normalizar(rota['objetivo']) not in n:motivos.append('objetivo declarado ausente')
    if not any(normalizar(rota['objetivo']) in normalizar(t) for t in rota['fontes_contexto']):motivos.append('objetivo sem fonte do usuário')
    # Quantidades pessoais não são sugestões criativas. Não aceitar uma
    # resposta com tempo/vasos diferentes do que o usuário declarou.
    from dialogo_situado import minutos_declarados
    minutos=re.findall(r'\b(?:\d+|um|dois|tres|quatro|cinco|dez|quinze|vinte|trinta) minutos?\b',n)
    esperado=minutos_declarados('Tenho '+rota['tempo']) if rota['tempo'] else None
    if any(minutos_declarados('Tenho '+m)!=esperado for m in minutos):motivos.append('tempo disponível inventado ou alterado')
    vasos=re.findall(r'\b(?:\d+|um|dois|tres|quatro|cinco) vasos?\b',n)
    quantidade={'um':1,'dois':2,'tres':3,'quatro':4,'cinco':5}
    def numero(v):
        t=v.split()[0];return quantidade.get(t,int(t) if t.isdigit() else None)
    if vasos and (not rota['vasos'] or any(numero(v)!=numero(normalizar(rota['vasos'])) for v in vasos)):
        motivos.append('quantidade de vasos inventada ou alterada')
    if rota['dominio']=='horta' and rota['luz'] and normalizar(rota['luz']) not in n:
        motivos.append('observação de luz declarada ausente')
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
