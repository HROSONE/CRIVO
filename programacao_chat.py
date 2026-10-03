"""Motor de código ligado ao chat: interpretação, diagnóstico e síntese limitada.

Fontes passam somente pelo parser/executor próprios. O replay HTTP reconstrói
contratos sem executar novamente cada busca. Nenhum histórico é persistido.
"""
import copy
import json
import re

from busca_estados import buscar, validar_casos
from diagnostico_estados import avaliar, diagnosticar, percorrer
from execucao_rastreada import executar_rastreado
from interpretacao_estruturas import analisar, javascript, validar_valor
from modelo_efeitos_chat import conferir_efeitos, PASTA, status_modelo

CERCA = re.compile(r'```([^\n`]*)\n([\s\S]*?)```')
AJUDA = ('Posso interpretar um corpo de função JavaScript, rastrear estados e tentar corrigir falhas usando exemplos de entrada e saída. '
         'Também posso montar funções simples a partir desses exemplos.\n\n'
         'Envie o código entre três crases, com a linguagem javascript, e depois Exemplos: '
         '[{"entrada": 0, "saida": 2}, {"entrada": 3, "saida": 5}]. '
         'Para apenas executar, envie Entrada: 3. '
         'O motor aceita um subconjunto limitado; chamadas livres, imports e APIs externas não são suportados.')


def simples(s):
    from conversa_assistente import normalizar
    return normalizar(s)


def json_texto(v):
    # Escapa unidades UTF-16 isoladas que podem surgir em slice de strings JS.
    return json.dumps(v, ensure_ascii=True)


def validar_dados(v):
    validar_valor(v)
    def contar(x):
        if type(x) is dict:
            return 1 + sum(contar(y) for y in x.values())
        if type(x) is list:
            return 1 + sum(contar(y) for y in x)
        return 1
    if contar(v) > 128:
        raise ValueError('Este chat aceita até 128 valores por entrada/saída')


def validar_exemplos(cs):
    validar_casos(cs)
    if len(cs) > 6:
        raise ValueError('Envie até seis exemplos de desenvolvimento por pedido')
    for c in cs:
        validar_dados(c['entrada'])
        validar_dados(c['saida'])


def corpo_funcao(codigo):
    if not isinstance(codigo, str):
        raise ValueError('Código deve ser texto')
    codigo = codigo.strip()
    # Somente uma função com parâmetro entrada; não interpreta JS/TS arbitrário.
    if re.match(r'^(?:export\s+)?function\b', codigo):
        m = re.fullmatch(r'(?:export\s+)?function\s+[A-Za-z_][A-Za-z_0-9]*\s*\(\s*entrada\s*'
                         r'(?::\s*(?:number(?:\[\])?|string|boolean))?\s*\)\s*'
                         r'(?::\s*(?:number(?:\[\])?|string|boolean))?\s*\{([\s\S]*)\}\s*;?', codigo)
        if not m:
            raise ValueError('Envie o corpo da função ou uma função com único parâmetro chamado entrada')
        codigo = m.group(1).strip()
    if len(codigo) > 1000:
        raise ValueError('Este chat aceita até 1.000 caracteres de código por análise')
    ast = analisar(codigo)
    if sum(1 for _ in percorrer(ast)) > 160:
        raise ValueError('Código complexo demais para este chat')
    return codigo


def extrair(texto, pendente=None):
    cercas = list(CERCA.finditer(texto))
    prefixo = texto[:cercas[0].start()] if cercas else texto
    n = simples(prefixo)
    comando = re.match(r'^(?:por favor )?(?:(?:voce|crivo) (?:pode|consegue) )?'
                       r'(corrija|corrigir|diagnostique|depure|analise|analisar|interprete|interpretar|'
                       r'execute|executar|rode|gerar|gere|crie|escreva|implemente)\b', n)
    ajuda = bool(re.fullmatch(r'(?:voce )?(?:consegue|pode|sabe) (?:analisar|interpretar|corrigir|gerar) '
                              r'(?:meu )?codigo(?: (?:js|ts|javascript|typescript))?', n))
    if ajuda and not cercas:
        return {'ajuda': True}
    modo = None
    if comando:
        verbo = comando[1]
        modo = ('interpretar' if verbo in ('interprete','interpretar','execute','executar','rode') else
                'gerar' if verbo in ('gerar','gere','crie','escreva','implemente') else 'diagnosticar')
    r = {}
    if texto.strip().startswith('{'):
        try:
            objeto = json.loads(texto)
        except ValueError:
            objeto = None
        if isinstance(objeto, dict) and set(objeto) & {'codigo','desenvolvimento','entrada','acao'}:
            if set(objeto) - {'codigo','desenvolvimento','entrada','acao','tipo'}:
                raise ValueError('Envie somente codigo, desenvolvimento, entrada, acao ou tipo; não envie referências ou reservados')
            r.update(objeto)
            modo = objeto.get('acao', modo)
    reconhecido = bool(r or cercas and (comando or not n or n in ('codigo','meu codigo','o codigo')) or
                       comando and re.search(r'\b(?:codigo|javascript|typescript|js|ts)\b', n) or
                       pendente and re.match(r'^(?:exemplos?|entrada|saida|corrija|diagnostique|rode|execute|interprete)\b', n))
    if not reconhecido:
        return None
    if not modo:
        modo = pendente.get('acao','diagnosticar') if pendente else 'diagnosticar'
    if modo not in ('interpretar','diagnosticar','gerar'):
        raise ValueError('Ação deve ser interpretar, diagnosticar ou gerar')
    r['acao'] = modo
    for c in cercas:
        lang = c[1].strip().lower()
        if lang in ('js','javascript','ts','typescript',''):
            if 'codigo' in r:
                raise ValueError('Envie apenas um trecho de código')
            r['codigo'] = c[2].strip()
        elif lang == 'json':
            if 'desenvolvimento' in r:
                raise ValueError('Envie apenas uma lista de exemplos')
            r['desenvolvimento'] = json.loads(c[2])
        else:
            raise ValueError('Este motor interpreta somente o subconjunto JavaScript/TypeScript')
    restante = CERCA.sub('', texto)
    # Rótulos de linha explícitos. raw_decode preserva tipos JSON e não adivinha saídas.
    exemplos = re.search(r'(?:^|\n)\s*(?:Exemplos?|Desenvolvimento)\s*:\s*', restante, re.I)
    if exemplos:
        valor, fim = json.JSONDecoder().raw_decode(restante[exemplos.end():].lstrip())
        if 'desenvolvimento' in r:
            raise ValueError('Exemplos duplicados')
        r['desenvolvimento'] = valor
    pares = {}
    for nome, padrao in (('entrada', 'Entrada'), ('saida', 'Sa[ií]da')):
        m = re.search(r'(?:^|\n)\s*'+padrao+r'\s*:\s*', restante, re.I)
        if m:
            pares[nome], _ = json.JSONDecoder().raw_decode(restante[m.end():].lstrip())
    if 'saida' in pares:
        if set(pares) != {'entrada','saida'} or 'desenvolvimento' in r:
            raise ValueError('Envie Entrada e Saída juntas ou uma lista de Exemplos')
        r['desenvolvimento'] = [pares]
    elif 'entrada' in pares:
        r['entrada'] = pares['entrada']
    return r


class MotorCodigoChat:
    def __init__(self, pasta_modelo=PASTA):
        self.pasta_modelo = str(pasta_modelo)
        self.pendente = None
        self.ultimo = None
        self.reconstruindo = False

    def status(self):
        return dict(ativo=True, interpretacao=True, diagnostico=True, sintese_limitada=True,
                    modelo_efeitos=status_modelo(self.pasta_modelo), ranking_neural_padrao=False)

    def responder(self, texto, gerador_experimental=False):
        self.ultimo = None
        try:
            pedido = extrair(texto, self.pendente)
            if pedido is None:
                self.pendente = None
                return None
            if pedido.get('ajuda'):
                return 'programacao:motor_ajuda', AJUDA
            if (gerador_experimental and pedido['acao']=='gerar' and
                    not set(pedido) & {'codigo','desenvolvimento'} and self.pendente is None):
                return None
            contexto = copy.deepcopy(self.pendente or {})
            contexto.update(pedido)
            if 'codigo' in pedido and self.pendente and 'codigo' in self.pendente:
                # Uma nova fonte não herda exemplos de um programa anterior.
                contexto = copy.deepcopy(pedido)
            if 'codigo' in contexto:
                contexto['codigo'] = corpo_funcao(contexto['codigo'])
            if 'desenvolvimento' in contexto:
                validar_exemplos(contexto['desenvolvimento'])
            if 'entrada' in contexto:
                validar_dados(contexto['entrada'])
            self.pendente = contexto
            if self.reconstruindo:
                return 'programacao:motor_contexto', 'Contexto de código reconstruído.'
            modo = contexto['acao']
            if modo != 'gerar' and 'codigo' not in contexto:
                return 'programacao:motor_pendente', 'Envie o código JavaScript entre três crases.\n\n'+AJUDA
            if modo == 'interpretar':
                return self._interpretar(contexto)
            if 'desenvolvimento' not in contexto:
                return 'programacao:motor_pendente', ('Preciso de exemplos de entrada e saída esperada para '+
                        ('montar a função.' if modo=='gerar' else 'avaliar a falha e testar uma correção.')+
                        '\n\nExemplos: [{"entrada": 0, "saida": 2}, {"entrada": 3, "saida": 5}]')
            return self._gerar(contexto) if modo == 'gerar' else self._diagnosticar(contexto)
        except (ValueError, TypeError, RecursionError) as exc:
            return 'programacao:motor_limite', 'Não consegui analisar este pedido: '+str(exc)[:240]+'.\n\n'+AJUDA

    def _interpretar(self, c):
        if 'entrada' not in c:
            return 'programacao:motor_pendente', 'Com qual entrada devo executar? Envie, por exemplo, Entrada: 3 ou Entrada: [1, 2].'
        r = executar_rastreado(c['codigo'], c['entrada'])
        rede = conferir_efeitos([r], self.pasta_modelo)
        self.ultimo = dict(acao='interpretar', resultado=r.get('resultado'), erro=r.get('erro'),
                           passos=r['passos'], efeitos_neurais=rede, execucao='executor_proprio_exato')
        if 'erro' in r:
            texto = 'A execução parou: '+r['erro']+'. Passos: '+str(r['passos'])+'.'
        else:
            texto = 'Resultado: '+json_texto(r['resultado'])+'. Passos: '+str(r['passos'])+'.'
        return 'programacao:motor_interpretacao', texto+self._rastro(r['tracos'])+self._nota_rede(rede)

    def _diagnosticar(self, c):
        r = diagnosticar(c['codigo'], c['desenvolvimento'], limite=256, verificacoes=128)
        rede = conferir_efeitos(r['inicial'], self.pasta_modelo)
        self.ultimo = dict(acao='diagnosticar', atende_desenvolvimento=r['atende_desenvolvimento'],
                           verificadas=r['verificadas'], candidatos=r['candidatos'], hipotese=r['hipotese'],
                           corpo_corrigido=r['corpo_corrigido'], efeitos_neurais=rede,
                           casos_reservados_consultados=False, execucao='executor_proprio_exato')
        falhas = [x for x in r['inicial'] if not x['correto']]
        if not falhas:
            return 'programacao:motor_diagnostico', ('O código passou nos '+str(len(c['desenvolvimento']))+
                    ' exemplos fornecidos. Isso não garante que esteja correto para todas as entradas.'+self._nota_rede(rede))
        primeiro = falhas[0]
        observado = primeiro.get('erro', json_texto(primeiro.get('observado')))
        texto = ('Reproduzi a falha. Entrada: '+json_texto(primeiro['entrada'])+
                 '. Esperado: '+json_texto(primeiro['esperado'])+'. Observado: '+observado+'.')
        if r['corpo_corrigido']:
            h = r['hipotese']
            texto += ('\n\nEsta edição local passou nos '+str(len(c['desenvolvimento']))+' exemplos fornecidos:'+
                      '\nAntes: '+h['antes']+'\nDepois: '+h['depois']+
                      '\n\n```javascript\n'+javascript(r['corpo_corrigido'])+'\n```'+
                      '\n\nÉ uma hipótese de correção; confira com novos exemplos antes de usar.')
        else:
            texto += '\n\nNão encontrei uma correção que passe nos exemplos dentro das '+str(r['verificadas'])+' tentativas.'
        return 'programacao:motor_diagnostico', texto+self._rastro(primeiro.get('tracos', []))+self._nota_rede(rede)

    def _gerar(self, c):
        entradas = [x['entrada'] for x in c['desenvolvimento']]
        tipos = {type(x) for x in entradas}
        mapa = {int:'numero', list:'array', str:'string', dict:'objeto'}
        if len(tipos)!=1 or next(iter(tipos)) not in mapa:
            raise ValueError('Síntese exige entradas todas do mesmo tipo: número, array, string ou objeto')
        tipo = mapa[next(iter(tipos))]
        if 'tipo' in c and c['tipo'] != tipo:
            raise ValueError('Tipo informado difere das entradas')
        campos = sorted(set.intersection(*(set(x) for x in entradas)))[:8] if tipo=='objeto' else []
        r = buscar(c['desenvolvimento'], tipo, campos=campos, limite=1000, finalistas=128)
        corpo = r['corpo']
        analises = avaliar(corpo, c['desenvolvimento'], guardar_tracos=True) if corpo else []
        rede = conferir_efeitos(analises, self.pasta_modelo)
        self.ultimo = dict(acao='gerar', corpo=corpo, verificadas=r['verificadas'],
                           atende_desenvolvimento=r['atende_desenvolvimento'], efeitos_neurais=rede,
                           casos_reservados_consultados=False, execucao='executor_proprio_exato')
        if corpo:
            return 'programacao:motor_sintese', ('Montei uma função que passou nos '+str(len(entradas))+
                    ' exemplos fornecidos:\n\n```javascript\n'+r['codigo']+'\n```'+
                    '\n\nA busca tem uma gramática limitada. Confira novos exemplos; eles podem exigir outra função.'+self._nota_rede(rede))
        return 'programacao:motor_sintese', 'Não encontrei uma função que passe nos exemplos dentro do orçamento desta busca.'

    @staticmethod
    def _rastro(tracos):
        estados = [x for x in tracos if x['tipo']=='estado']
        if not estados:
            return ''
        escolhidos = estados[:2] + (estados[-1:] if len(estados)>2 else [])
        return '\n\nEstados observados:\n'+'\n'.join(json_texto(x['depois']) for x in escolhidos)

    @staticmethod
    def _nota_rede(r):
        if not r['ativo'] or not r['comparados']:
            return ''
        texto = '\n\nRede própria de efeitos: '+str(r['concordantes'])+'/'+str(r['comparados'])+' previsões concordaram com o executor exato.'
        if r['fora_dominio']:
            texto += ' '+str(r['fora_dominio'])+' efeitos ficaram fora do domínio da rede.'
        return texto
