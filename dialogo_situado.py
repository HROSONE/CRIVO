"""Continuidade de diálogo apoiada em falas explícitas da sessão.

Política estrutural, sem pesos novos. Preserva objetivos, impedimentos,
alternativas ordenadas, disponibilidade real e escopo hipotético/ficcional.
Os assuntos são argumentos extraídos das falas, não um catálogo de respostas.
Consultas factuais, código, fontes e premissas formais mantêm suas rotas.
"""
import re
from collections import deque

from composicao_textual import normalizar


def ntexto(texto):
    n = normalizar(texto)
    n = ' '.join(re.sub(r'[,;:]',' ',n).split())
    n = re.sub(r'\bq q\b', 'o que', n)
    for a,b in (('vc','voce'),('hj','hoje'),('pq','por que'),('q','que'),('to','estou')):
        n = re.sub(r'\b'+a+r'\b', b, n)
    return n.strip(' .?!')


def citado(texto):
    return any(c in texto for c in ('`','"','“','”'))


def hipotetico(n):
    return bool(re.match(r'(?:e |mas )?(?:se |caso |talvez |imagine )',n) or
                re.search(r'\b(?:tivesse|hipotese)\b',n))


def pessoal(n):
    return bool(re.match(r'(?:(?:hoje|ontem|agora|mas|e|tambem|tipo|isso|o problema e que|'
                         r'minha dificuldade e que|a dificuldade e que)[:,]? )*'
                         r'(?:eu |meu |minha |meus |minhas |quero |queria |pretendo |'
                         r'ando |tenho |nao tenho |nao posso |nao consigo |nao sei |'
                         r'estou |consegui |fiquei |senti |acho |pensei |gostaria |'
                         r'seria (?:bom|legal|interessante) |e mais por |era |talvez )',n))


def abertura(texto):
    return re.fullmatch(r'(?:eu\s+)?(?:quero|queria|gostaria de)\s+(?:falar|conversar|trocar ideia)'
                        r'\s+(.+)',texto.strip().strip(' .!'),re.I)


def ordinal(n):
    for i,termo in enumerate(('primeir','segund','terceir','quart')):
        if re.search(r'\b'+termo+r'[ao]\b',n):
            return i
    return None


def extrair_opcoes(texto):
    m = re.fullmatch(r'(?:estou entre\s+|tenho\s+(?:duas|tr[eê]s|quatro|[234])\s+op[cç][oõ]es\s*:\s*)(.+)',
                     texto.strip().strip(' .!'),re.I)
    if not m or citado(texto):
        return []
    corpo = m.group(1)
    delimitador = r'\s*,\s*|\s+ou\s+' if ',' in corpo or re.search(r'\s+ou\s+',corpo) else r'\s+e\s+'
    partes = [p.strip() for p in re.split(delimitador,corpo) if p.strip()]
    return partes if 2 <= len(partes) <= 4 else []


def fonte(texto):
    return '“'+texto.strip().strip(' .?!')[:360]+'”'


class DialogoSituado:
    MAX_INTERVALO = 10

    def __init__(self):
        self.limpar()

    def limpar(self):
        self.meta = deque(maxlen=4)
        self.hipotese = None
        self.ficcao = None
        self.ultima_fala = ''
        self.ultimo = None
        self.suspenso = False

    def quadro(self, conversa):
        reais = []
        objetivo = None
        minutos = None
        opcoes = []
        referencias = {}
        for texto in conversa.relatos:
            n = ntexto(texto)
            if citado(texto) or hipotetico(n) or '?' in texto:
                continue
            reais.append(texto)
            if re.match(r'(?:eu )?(?:quero|queria|pretendo|ando querendo|gostaria de|'
                        r'seria (?:bom|legal|interessante))\b',n):
                objetivo = texto
            if re.search(r'\bnao (?:tenho|disponho de)\b.*\b(?:tempo|minutos|horas)\b',n):
                minutos = None
            else:
                m = re.search(r'\b(?:tenho|disponho de) (\d{1,4}) minutos?\b',n)
                if m and 1 <= int(m.group(1)) <= 1440:
                    minutos = m.group(1)
            novas = extrair_opcoes(texto)
            if novas:
                opcoes = novas
                referencias = {}
            idx = ordinal(n)
            if idx is not None and idx < len(opcoes):
                referencias[idx] = texto
        return dict(relatos=reais[-4:],objetivo=objetivo,minutos=minutos,
                    opcoes=opcoes,referencias=referencias)

    def observar(self, texto, ident, bot):
        if ident == 'conversa:reinicio':
            self.limpar()
            return
        if not isinstance(texto,str) or not texto.strip() or len(texto)>1200 or '`' in texto:
            return
        n = ntexto(texto)
        conversa = bot.conversacao
        if (ident.startswith(('conhecimento:','escrita:','programacao:','dyn:','logica:')) or
                ident in (getattr(bot,'_ids_editoriais',None) or ())):
            self.suspenso = True
            self.ultima_fala = texto[:600]
            return
        mudanca = bool(re.match(r'(?:mudando de assunto|(?:ta,? )?vamos comecar de novo)\b',n))
        if mudanca:
            conversa.relatos.clear()
            conversa.dialogo.iniciar_assunto()
            conversa.assunto = conversa.objetivo = None
            self.meta.clear()
            self.hipotese = self.ficcao = None
            # Só a nova declaração entra no escopo atual.
            texto = re.sub(r'^(?:Mudando de assunto|(?:T[aá],? )?vamos come[cç]ar de novo)[:,]?\s*','',texto,flags=re.I)
            n = ntexto(texto)
        if hipotetico(n) or re.match(r'sempre que ',n):
            self.hipotese = (texto[:600],conversa.turno)
        if not citado(texto) and '?' not in texto and not hipotetico(n) and (
                mudanca or pessoal(n) or extrair_opcoes(texto) or ordinal(n) is not None):
            self.suspenso = False
            if not conversa.relatos or conversa.relatos[-1] != texto:
                conversa.relatos.append(texto.strip()[:600])
            # Os slots compartilhados recebem somente declarações reais.
            # Assim a lembrança nativa e o gerador leem o mesmo objetivo.
            declaracao = re.match(r'(?:eu )?(?:quero|pretendo|queria|ando querendo|gostaria de) ([\w]+)\b',n)
            if (declaracao and declaracao.group(1).endswith(('ar','er','ir')) and
                    declaracao.group(1) not in ('falar','conversar','saber','entender','explicar','escrever') and
                    not ident.startswith('conversa:gerada_')):
                conversa.dialogo._extrair(texto)
                conversa.objetivo = conversa.dialogo.dados.get('objetivo')
            tempo = self.quadro(conversa)['minutos']
            if tempo:
                conversa.dialogo._guardar('minutos',tempo)
        if ident.startswith('conversa:situada_'):
            self.meta.append(texto[:600])
        self.ultima_fala = texto[:600]

    def _emitir(self, acao, resposta, fontes=()):
        self.ultimo = dict(acao=acao,origem='politica_estrutural_propria',
                           fontes=list(fontes),pesos_promovidos=False)
        return ('conversa:abertura' if acao=='abertura' else 'conversa:situada_'+acao),resposta

    def _contexto(self, q):
        partes = q['relatos'][-2:]
        if q['objetivo'] and q['objetivo'] not in partes:
            partes.insert(0,q['objetivo'])
        return ' e '.join(fonte(p) for p in partes),partes

    def responder(self, texto, bot, apos_recusa=False):
        self.ultimo = None
        if not isinstance(texto,str) or not texto.strip() or len(texto)>1200 or '`' in texto:
            return None
        n = ntexto(texto)
        conversa = bot.conversacao
        q = self.quadro(conversa)
        contexto,fontes = self._contexto(q)
        ativos = bool(q['relatos'] or self.meta) and not self.suspenso
        # Tokens dentro de citações não autorizam uma operação. Uma
        # explicação explícita de linguagem figurada é tratada à parte.
        metafora = bool(re.search(r'\bnao (?:e|era) sobre\b',n) and
                        re.search(r'\b(?:falo|disser|digo|dizer|exemplo)\b',n))
        if citado(texto) and not metafora:
            if re.search(r'\b(?:meu|minha) .+? disse\b',n) and re.search(
                    r'\b(?:nao (?:estou )?pedindo|essa fala era dele|essa fala era dela)\b',n):
                return self._emitir('citacao',
                    'Essa é uma fala citada de outra pessoa: '+fonte(texto)+
                    '. Ela não muda o que você está pedindo nem seu objetivo. '
                    'Você quer conversar sobre como recebeu essa fala?', [texto])
            return None
        if bot.contexto_textual is not None and re.fullmatch(
                r'(?:qual (?:e )?a fonte(?: dessa informacao)?|fontes|resuma isso|mais simples)',n):
            return None
        if re.search(r'\b(?:premissas?|posso concluir|podemos concluir|prove que|demonstr\w*)\b',n):
            return None
        if metafora:
            return self._emitir('sentido',
                'Entendi que você está usando uma expressão em sentido figurado: '+fonte(texto)+
                '. Vou considerar o contexto e como você se sente, sem transformar isso numa descrição literal. '
                'O que você quer expressar com essa imagem?',[texto])
        if re.search(r'\b(?:acompanhar|acompanha|entende|entender)\b',n) and re.search(
                r'\b(?:bagunc\w*|jeito de falar|palavras soltas|meio confuso)\b',n):
            return self._emitir('entendimento',
                'Posso tentar acompanhar pelo contexto, mesmo quando a fala vem bagunçada. '
                'Se houver duas interpretações, vou perguntar qual você quis dizer. Pode trazer a ideia do seu jeito.',[texto])
        perspectiva = re.fullmatch(r'o que (?:e|significa) (.+?),? (?:pra|para) voce',n)
        if perspectiva:
            alvo = perspectiva.group(1)
            self.meta.append(texto)
            return self._emitir('perspectiva',
                'Podemos explorar '+fonte(alvo)+' pelo sentido que isso tem para você: o que valoriza, '
                'o que vive e o que deseja construir. Não possuo vivências pessoais; posso ajudar '
                'a examinar perspectivas. O que te levou a pensar nisso?',[texto])
        m = abertura(texto)
        # Aberturas já suportadas conservam o protocolo nativo, incluindo
        # escuta neural e consultas sobre assuntos do acervo.
        if m and re.match(r'(?:eu )?(?:quero|queria|gostaria de) conversar sobre\b',n) and not apos_recusa:
            return None
        desejo = re.match(r'seria (?:bom|legal|interessante) (?:ter|fazer|criar|montar)\b',n)
        retomada = re.match(r'(?:eu )?quero (?:voltar|retomar)\b',n) and re.search(r'\btenho \d+ minutos',n)
        novo = re.match(r'(?:ta )?vamos comecar de novo\b|mudando de assunto\b',n)
        if re.fullmatch(r'(?:ta )?vamos comecar de novo',n):
            return None
        if m or desejo or retomada or novo:
            return self._emitir('abertura',
                'Você trouxe esta ideia: '+fonte(texto)+'. Podemos partir dela. '
                'O que mais importa para você agora: entender a vontade, lidar com um limite ou escolher um próximo passo?',[texto])
        foco = re.match(r'(?:isso )?e (?:sobre|da?|do) .+? (?:que )?eu (?:quero|queria) (?:falar|conversar)\b',n)
        if foco:
            return self._emitir('intencao',
                'Vamos focar no que você quer conversar: '+fonte(texto)+
                '. O que nessa ideia merece mais atenção para você?', [texto])
        if re.search(r'\bnao (?:escrev\w*|envie|manda\w*|quero (?:roteiro|mensagem|texto|lista))\b',n) and re.search(
                r'\b(?:pens\w*|sint\w*|receio|intencao|convers\w*|trocar ideia)\b',n):
            return self._emitir('intencao',
                'Vamos conversar sobre a decisão, sem preparar ou enviar nada. Você esclareceu: '+fonte(texto)+
                '. O que gostaria de entender antes de escolher o que fazer?',[texto])
        if re.search(r'\b(?:equilibrar|conciliar|combinando|tentando juntar)\b',n) and ativos:
            partes = q['relatos'][-4:]
            return self._emitir('sintese',
                'Você está tentando conciliar o que deseja com as condições que contou: '+
                '; '.join(fonte(p) for p in partes)+'. Qual desses limites pesa mais? '
                'Podemos escolher um passo que caiba nele sem perder o objetivo.',partes)
        idx = ordinal(n)
        if idx is not None and q['opcoes'] and re.match(r'(?:mas )?(?:a|o) (?:primeir|segund|terceir|quart)[ao]\b',n):
            if idx >= len(q['opcoes']):
                return self._emitir('referencia_incerta','Você mencionou uma opção que não está entre as alternativas guardadas. Qual delas quer considerar?')
            return self._emitir('referencia',
                'A opção a que você se refere é '+fonte(q['opcoes'][idx])+'. Você está avaliando: '+fonte(texto)+
                '. Qual parte dela quer comparar ou tornar mais fácil?',q['opcoes']+[texto])
        if q['opcoes'] and re.search(r'\b(?:qual|quais)\b',n) and re.search(r'\b(?:opcao|opcoes|duas|tres|medo|receio)\b',n):
            if re.search(r'qual era .*?(?:medo|receio)',n):
                candidatas = [q['opcoes'][i] for i,t in q['referencias'].items()
                              if re.search(r'\b(?:medo|receio)\b',ntexto(t))]
                if len(candidatas)==1:
                    return self._emitir('referencia','Você relacionou esse receio à opção '+fonte(candidatas[0])+'.',candidatas)
            partes = [fonte(p) for p in q['opcoes']]
            detalhes = '; '.join(fonte(t) for t in q['referencias'].values())
            return self._emitir('comparacao',
                'As alternativas são '+', '.join(partes)+'. '+('Você contou: '+detalhes+'. ' if detalhes else '')+
                'Esse receio pode orientar um teste pequeno, sem decidir tudo agora. Qual critério quer usar para comparar as opções?',q['opcoes']+list(q['referencias'].values()))
        if re.search(r'\b(?:quanto tempo|quantos minutos)\b',n) and re.search(r'\b(?:eu|tenho|disse|realmente|verdade)\b',n) and ativos:
            return self._emitir('disponibilidade',
                ('Você declarou '+q['minutos']+' minutos disponíveis. As hipóteses e falas citadas não substituem essa disponibilidade.'
                 if q['minutos'] else 'Não tenho uma disponibilidade real definida para você nesta conversa. Quanto tempo tem agora?'),q['relatos'])
        resumo = bool(re.search(r'\b(?:com suas palavras|reformular|reformule|resumir|resuma|'
                                r'o que .*?(?:entendeu|quis dizer|estava pedindo|falei|estou pedindo))\b',n))
        if resumo and (ativos or self.meta):
            partes = fontes or list(self.meta)[-2:]
            return self._emitir('reformulacao',
                'Entendi seu pedido como uma conversa para compreender a situação e a sua perspectiva. '
                'O contexto que estou considerando é '+ ' e '.join(fonte(p) for p in partes)+
                '. Quer que eu explore uma escolha, uma dificuldade ou o sentido disso para você?',partes)
        if re.search(r'\b(?:nao sabe|ainda nao sabe|nao sabemos|quais detalhes)\b',n) and ativos:
            return self._emitir('limites',
                'Sobre o que você contou, só tenho estas informações: '+contexto+
                '. Não sei os detalhes que você não contou e não vou completar sua história por suposição. '
                'Qual informação quer acrescentar?',fontes)
        if re.search(r'\b(?:nao sei .*?por que|mexeu comigo|mexeu .*?comigo)\b',n) and ativos:
            return self._emitir('exploracao',
                'Você contou '+contexto+'. Podemos explorar o que essa situação mexeu em você, '
                'sem assumir uma causa ou diagnóstico. O que mudou no momento: como se sentiu, '
                'o que esperava de si ou a presença de outra pessoa?',fontes)
        if re.search(r'^(?:entao |agora |por favor )?(?:me (?:pergunte|pergunta|fa[cç]a uma pergunta))\b|'
                     r'\b(?:pergunta|pergunte) algo\b',n) and ativos:
            return self._emitir('exploracao',
                'Pensando em '+contexto+', qual parte você quer entender antes de decidir: '
                'o receio, a intenção ou a reação que imagina? Podemos começar pela que mais pesa agora.',fontes)
        if re.search(r'\b(?:concorda|outro jeito|outra perspectiva)\b',n) and ativos:
            return self._emitir('perspectiva',
                'Uma perspectiva possível para '+contexto+' é comparar o que você valoriza com o que '
                'acontece na prática. Não precisamos encontrar uma resposta única para o sentido disso. '
                'Qual experiência apoia sua ideia, e qual faria você reconsiderar?',fontes)
        if re.search(r'\b(?:distinguir|diferenciar)\b',n) and ativos and re.match(r'como (?:eu )?posso ',n):
            return self._emitir('criterios',
                'Para '+fonte(texto)+', eu examinaria a intenção, o pedido feito e a resposta esperada. '
                'No que você contou — '+contexto+' — vale perguntar se há espaço para a outra pessoa escolher '
                'e responder no próprio tempo. Qual expectativa sua poderia virar pressão?',fontes+[texto])
        if re.search(r'\b(?:eu inventei|inventei (?:esse|essa|o|a|um|uma)|nao e real)\b',n):
            nome = self._nome(texto) or self._nome(self.ultima_fala)
            if nome:
                self.ficcao = (nome,conversa.turno)
            return self._emitir('ficcao_limite',
                'Você esclareceu que '+(fonte(nome) if nome else 'esse nome')+' é uma invenção. '
                'Não vou apresentar isso como fato confirmado. Podemos imaginar uma ficção e manter essa distinção.',[texto])
        if self.ficcao and conversa.turno-self.ficcao[1]<=self.MAX_INTERVALO:
            nome = self.ficcao[0]
            if re.search(r'\b(?:existe|verdade|real|confirmad\w*)\b',n) and not re.search(r'\b(?:imaginar|ficcao)\b',n):
                return self._emitir('ficcao_limite',
                    'Nesta conversa, '+fonte(nome)+' foi apresentado como invenção. Não tenho evidência de que exista de verdade.',[nome])
            if re.search(r'\b(?:imaginar|ficcao)\b',n) or n.startswith('e se '):
                return self._emitir('ficcao',
                    'Ficção: no cenário imaginado de '+fonte(nome)+', podemos explorar esta possibilidade: '+fonte(texto)+
                    '. Isso pertence à história, não a uma descoberta confirmada. Que consequência você gostaria de imaginar?',[nome,texto])
        h = self.hipotese if self.hipotese and conversa.turno-self.hipotese[1]<=self.MAX_INTERVALO else None
        condicao = hipotetico(n) and (ativos or re.search(r'\b(?:diferente|diferenca|por dia|domingo|sabado|faria sentido)\b',n))
        causal = h and (re.search(r'\b(?:pode ser|em vez|nao a|nao o|verific\w*|sem assumir|possibilidades)\b',n))
        adaptar = ativos and re.search(r'\b(?:adapt\w*|desist\w*|abandon\w*)\b',n) and '?' in texto
        if condicao or causal or adaptar:
            partes = ([h[0]] if h else [])+fontes+[texto]
            if adaptar:
                resposta = ('Adaptar é mudar a forma de seguir o objetivo; abandonar é deixar esse objetivo. '
                            'Na possibilidade '+fonte(h[0] if h else texto)+', vale verificar se a mudança ainda '
                            'preserva o que você queria alcançar. Qual seria um sinal de que ela ajuda?')
            elif causal:
                resposta = ('É uma hipótese, não uma conclusão: '+fonte(texto)+'. Você trouxe '+
                            '; '.join(fonte(p) for p in partes[:-1])+'. Para comparar as possibilidades, observe '
                            'o resultado e varie um fator de cada vez, mantendo os outros tão parecidos quanto puder. '
                            'O que conseguiria registrar para não depender só da impressão?')
            else:
                resposta = ('Na hipótese '+fonte(texto)+', podemos comparar a frequência, as condições e '
                            'o resultado que você quer observar. Isso pode mudar a continuidade, mas não garante '
                            'um resultado. Qual diferença seria importante para você?')
            return self._emitir('hipotese',resposta,partes)
        if ativos and re.match(r'isso me (?:deixou|fez|trouxe)\b',n):
            return self._emitir('sentimento',
                'Você ligou esse sentimento à situação '+contexto+'. Agora acrescentou: '+fonte(texto)+
                '. O que foi mais importante para você nessa experiência?',fontes+[texto])
        if apos_recusa and pessoal(n) and not re.search(r'\b(?:o que e|como funciona|codigo|programa|script|defina|explique)\b',n):
            return self._emitir('relato',
                'Você trouxe '+fonte(texto)+'. Posso conversar a partir disso. '
                'O que gostaria de explorar: o que aconteceu, como se sentiu ou uma escolha que está considerando?',[texto])
        return None

    @staticmethod
    def _nome(texto):
        nomes = re.findall(r'\b[A-ZÀ-Ý][\wÀ-ÿ]*(?:-\d+)?\b',texto)
        nomes = [s for s in nomes if ntexto(s) not in ('eu','meu','minha','o','a','que','como','onde','podemos')]
        return nomes[-1] if nomes else None
