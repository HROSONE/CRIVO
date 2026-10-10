"""Realização dialógica seletiva com a GRU própria treinada em #126.

Só usa atos explícitos de ficção e argumentos já resolvidos. Fatos, cálculos,
preferências e fontes conservam seus executores e suas guardas atuais.
"""
import gzip
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

from composicao_textual import normalizar

RAIZ = Path(__file__).resolve().parent
CHECKPOINT = RAIZ / 'rede_dialogo_conversa.json.gz'
ORIGEM_SHA256 = '823c44965cb7d9e3ec3830555b100aec373443e3b778cd719cc9804bc9e4ba47'
PESOS_SHA256 = '3b20dcdac656a93d61a958715978b7f5a1f45a7980492b8be637e60aa611b27b'
PESOS_V2_SHA256 = '05bbf93b1190c817fd7c621ed82bf4f5fd25ce33e85011a536ffcb7bb213aef0'
ORIGEM_V2_SHA256 = 'd6dec80197b3d6d000dfa97ec1bc1bc4831e058732fce3e9bb3e0b03c70f1399'
ATOS = frozenset(('historia', 'continuar', 'corrigir'))


def aprovacao_valida(dados):
    a = dados.get('aprovacao', {})
    m = a.get('metricas', {})
    origem=a.get('checkpoint_origem_sha256')
    pesos_esperados={ORIGEM_SHA256:PESOS_SHA256,ORIGEM_V2_SHA256:PESOS_V2_SHA256}.get(origem)
    if not pesos_esperados or hashlib.sha256(json.dumps(dados.get('pesos'),sort_keys=True,separators=(',',':')).encode()).hexdigest()!=pesos_esperados:
        return False
    v2=origem==ORIGEM_V2_SHA256
    return (dados.get('controle') == {'aprovado': True, 'ativo_no_chat': True} and
            set(a.get('atos', [])) == ATOS and
            all(m.get(k, 0) >= (43 if v2 else 34) for k in ('casos_motor', 'casos_http')) and
            m.get('trocas_dominio') == m.get('referentes_ausentes') == 0 and
            m.get('historias_entregues') == (4 if v2 else 2) and m.get('conversas_mantem_fio', 0) >= (8 if v2 else 6))


def status_dialogo():
    try:
        _, dados, sha = carregar(str(CHECKPOINT.resolve()), CHECKPOINT.stat().st_mtime_ns)
        return {'ativa':aprovacao_valida(dados), 'atos':sorted(ATOS), 'checkpoint_sha256':sha}
    except (OSError,ValueError,KeyError,TypeError):
        return {'ativa':False, 'atos':[]}


def rotear_escrita(texto, bot):
    """Reutiliza a gramática e a última escrita; não coleta memória nova."""
    from pedidos_gerativos import criacao, revisao
    pedido = criacao(texto)
    if pedido and pedido['acao'] == 'historia':
        slots = pedido['slots']
        return dict(peca='escrita', ato='historia', referentes=list(slots.values()),
                    personagem=slots['tema1'], slots=dict(slots), estilo=pedido.get('estilo', 'neutro'))
    escrita = bot.conversacao.geracao.ultima_escrita
    if not escrita or escrita['tipo'] != 'historia':
        return None
    if bot.conversacao.turno - escrita['turno'] > bot.conversacao.geracao.MAX_INTERVALO:
        return None
    mudanca = revisao(texto)
    if mudanca and mudanca['operacao'] == 'continuacao':
        return dict(peca='escrita', ato='continuar', referentes=list(escrita['slots'].values()),
                    personagem=escrita['slots'].get('tema1'), slots=dict(escrita['slots']))
    return None


@lru_cache(maxsize=2)
def carregar(caminho, mtime):
    from linguagem_gerativa import GeradorGRU
    raw = Path(caminho).read_bytes()
    dados = json.loads(gzip.decompress(raw))
    digest = hashlib.sha256(json.dumps(dados['pesos'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if digest not in (PESOS_SHA256,PESOS_V2_SHA256):
        raise ValueError('Pesos diferentes do checkpoint próprio avaliado')
    return GeradorGRU(dados), dados, hashlib.sha256(raw).hexdigest()


def conferir(gerada, contexto, vocabulario, frases=None):
    """Permite composição/paráfrase; dados variáveis só entram por argumentos.

    Eventos da ficção não são declarações reais. Tokens desconhecidos, novos
    nomes/números literais e alterações dos argumentos bloqueiam a saída.
    Não exige copiar uma resposta alvo nem uma ficha factual.
    """
    from linguagem_gerativa import renderizar
    motivos = []
    tokens = gerada['tokens']
    slots = contexto['slots']
    if not gerada['completa']:
        motivos.append('geração incompleta')
    if any(t not in vocabulario for t in tokens):
        motivos.append('token fora do vocabulário próprio aprovado')
    for t in tokens:
        if t.startswith('@') and not slots.get(t[1:]):
            motivos.append('argumento ausente')
    for nome in slots:
        if '@' + nome not in tokens:
            motivos.append('referente selecionado ausente: ' + nome)
    # Todos os valores específicos da sessão são copiados de slots. Os
    # padrões de ficção deste checkpoint não precisam de números literais.
    if any(re.search(r'\d', t) for t in tokens if not t.startswith('@')):
        motivos.append('número literal não fornecido')
    if tokens[:2] != ['Ficção', ':']:
        motivos.append('tipo de pedido não atendido: ficção')
    if any(normalizar(t) in ('prefere', 'gosta', 'registrado', 'confirmado') for t in tokens):
        motivos.append('ficção tentou afirmar dados da sessão')
    texto = ''
    if not motivos:
        texto = renderizar(gerada, slots)
        for valor in slots.values():
            if normalizar(valor) not in normalizar(texto):
                motivos.append('valor de argumento alterado')
        quantidade = len(re.findall(r'[^.!?]+[.!?](?:\s|$)', texto))
        if quantidade < 3 or frases and quantidade != frases:
            motivos.append('quantidade de frases não atendida')
    return texto, {'politica': 'conversa', 'aceita': not motivos, 'motivos': motivos}


class DialogoConversa:
    def __init__(self, habilitado=True, candidato=None):
        self.habilitado = habilitado
        self.candidato = candidato
        self.trace = self.iniciar_trace()

    def iniciar_trace(self):
        self.trace = {'habilitada': self.habilitado, 'usada': False, 'memoria_usada': False,
                      'recuou': False, 'motivo': 'rota_preservada', 'politica': 'rigida'}
        return self.trace

    def realizar(self, rota, texto, bot):
        self.trace.update(peca=rota['peca'], ato=rota['ato'])
        if rota['peca'] != 'escrita' or rota['ato'] not in ATOS:
            self.trace['politica'] = 'conversa' if rota['peca'] == 'esclarecimento' else 'rigida'
            self.trace['motivo'] = 'ato_preservado_no_executor_atual'
            return None
        self.trace['politica'] = 'conversa'
        if not self.habilitado:
            self.trace['motivo'] = 'desligada'
            return None
        escrita = bot.conversacao.geracao.ultima_escrita
        slots = dict(rota.get('slots') or {})
        if not slots and rota['ato'] == 'historia' and rota.get('personagem'):
            slots['tema1'] = rota['personagem']
        if not slots and rota['ato'] == 'corrigir':
            if escrita:
                slots = dict(escrita['slots'])
            elif rota.get('personagem'):
                slots['tema1'] = rota['personagem']
            detalhe = re.search(r'\b(?:ele|ela) (?:encontra|conhece|reencontra) (.+?)(?:,|[.!?]|$)', texto, re.I)
            if detalhe:
                slots['detalhe' if slots.get('tema2') else 'tema2'] = detalhe[1]
        if not slots.get('tema1'):
            self.trace.update(recuou=True, motivo='referente_ambiguo_ou_ausente', confianca_roteamento='baixa')
            return ('conversa:esclarecer', 'Qual personagem devo usar? Preciso desse referente para continuar a história.')
        if (rota.get('estilo', 'neutro') != 'neutro' or len(slots) > 3 or
                not set(slots)<= {'tema1','tema2','detalhe'}):
            self.trace.update(motivo='pedido_fora_do_escopo_validado', recuou=True)
            return None
        # Pedidos factuais e estilos/instruções fora do treino não ganham uma
        # resposta inventada só porque contêm a palavra história.
        if re.search(r'\b(?:real|veridica|historica|fontes?|comprovada)\b', normalizar(texto)):
            self.trace.update(recuou=True, motivo='pedido_factual_nao_e_ficcao')
            return ('conversa:esclarecer', 'Você quer uma ficção com essa personagem ou uma explicação factual com fontes?')
        caminho = Path(self.candidato) if self.candidato else CHECKPOINT
        try:
            modelo, dados, sha = carregar(str(caminho.resolve()), caminho.stat().st_mtime_ns)
            if not self.candidato and not aprovacao_valida(dados):
                self.trace.update(recuou=True, motivo='checkpoint_sem_aprovacao')
                return None
            v2=dados.get('corpus_sha256')=='e2e33fe41cceeb27f2839572003210af2ecc315d87e0f889cb41c9cc9701dd45'
            if v2 and rota['ato']=='continuar' and escrita and escrita['acao']=='final' and slots.get('tema2') and not slots.get('detalhe'):
                self.trace.update(recuou=True,motivo='amigo_do_final_nao_e_cenario')
                return ('conversa:esclarecer','Ainda não consigo continuar esse final preservando todos os papéis de '+', '.join(slots.values())+'. Qual deve ser a próxima ação?')
            if v2 and slots.get('tema2') and (rota['ato']!='corrigir' and not rota.get('repetir_final') or slots.get('detalhe')):
                # O treino ampliado cobre lugares, não duas personagens.
                # Temas de papel incerto conservam o executor anterior.
                lugar=re.match(r'(?:(?:um|uma|o|a) )?(?:ilha|bosque|estacao|vale|praca|torre|jardim|floresta|casa|farol|ponte|castelo)\b',normalizar(slots['tema2']))
                if not lugar:
                    self.trace.update(recuou=True,motivo='segundo_tema_sem_papel_de_cenario')
                    return None
            if not v2 and (rota['ato'] in ('historia','continuar') and set(slots)!={'tema1'} or len(slots)>2):
                self.trace.update(motivo='pedido_fora_do_escopo_validado',recuou=True)
                return None
            self.trace.update(checkpoint_sha256=sha, experimental=bool(self.candidato),
                              memoria_usada=bool(escrita or not rota.get('slots')),
                              argumentos=dict(slots), confianca_roteamento='explicita')
            # Mantém o mesmo arco durante continuação, final e reescrita. A
            # rotação só escolhe o arco de uma história nova.
            variante=(escrita.get('variante',1) if escrita and (rota['ato']!='historia' or rota.get('reescrita'))
                      else (bot.conversacao.geracao.variante+1)%8) if v2 else 0
            contexto = dict(acao='final' if rota.get('repetir_final') else {'historia':'historia', 'continuar':'continuacao', 'corrigir':'final'}[rota['ato']],
                            slots=slots, estilo=rota.get('estilo', 'neutro'), variante=variante,
                            mensagem=texto, historico=[h['pergunta'] for h in bot.historico[-3:]],
                            resposta_anterior='')
            gerada = modelo.gerar(contexto, max_tokens=96)
            resposta, guarda = conferir(gerada, contexto, set(modelo.vocabulario), rota.get('frases'))
            if v2 and not guarda['aceita']:
                # Texto residual pode sugerir o ato do turno anterior. Uma
                # segunda realização conserva ação, arco e argumentos; só
                # neutraliza esse texto. Ambas passam pela mesma guarda.
                estruturado=dict(contexto,mensagem='',historico=[],resposta_anterior='')
                gerada=modelo.gerar(estruturado,max_tokens=96)
                resposta,guarda=conferir(gerada,estruturado,set(modelo.vocabulario),rota.get('frases'))
                self.trace['contexto_textual_neutralizado']=True
            self.trace['guarda'] = guarda
            if not guarda['aceita']:
                self.trace.update(recuou=True, motivo='guarda_de_conversa_rejeitou')
                return ('conversa:esclarecer', 'Não consegui cumprir todos os detalhes da história com ' +
                        ', '.join(slots.values()) + '. Pode esclarecer quais detalhes devo priorizar?')
            self.trace.update(usada=True, motivo='realizacao_dialogica_aceita', tokens=gerada['quantidade_tokens'])
            g = bot.conversacao.geracao
            g.ultima_escrita = {'acao':contexto['acao'], 'tipo':'historia', 'slots':slots,
                                'estilo':contexto['estilo'], 'turno':bot.conversacao.turno, 'texto':resposta,
                                'variante':contexto['variante']}
            g.ultima_criacao = g.ultima_escrita
            if v2 and rota['ato']=='historia' and not rota.get('reescrita'):g.variante=contexto['variante']
            g.ultimo_quadro = {'modelo':'GRU de diálogo própria', 'acao':contexto['acao'],
                               'slots_copiados':sorted(slots), 'checkpoint_sha256':sha}
            return 'conversa:gerada_' + contexto['acao'], resposta
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.trace.update(recuou=True, motivo='checkpoint_indisponivel', erro=type(exc).__name__)
            return None
