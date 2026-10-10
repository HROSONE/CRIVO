"""Realização dialógica seletiva com a GRU própria e aprovação medida.

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
PESOS_V3_SHA256 = '26832d836402cc431b033519df7d31efb8e59e599a85b821b94a4fddea813285'
ORIGEM_V3_SHA256 = 'f8977db9bb3dadc8094eef18af20e4a24d8fc6f357d55198beab2a375ca1fc60'
CORPUS_V3_SHA256 = '26a843db812568221660d104c48a9735eff6e74a82ba14d31fad7281cc3da350'
PESOS_V5_SHA256 = 'e7ac2eea6846e439765e0ec5f51c146fab0d0141482798123bb026eb79cdd764'
CORPUS_V5_SHA256 = '4076b7af8b4e3ec651de87d8f0a72b40924244142c566330118cc79931552ba2'
ORIGEM_V5_SHA256 = 'a042a2713f3cabac4d528b7ada365890fafe2bfcbf844de84e1f9e53533f4c12'
CASOS_V5_SHA256 = '9f5164f9aefbec71ec9e36aafebd7711cb95c2ab88c31b5b01975b67128645f8'
ESTRUTURA_V5_SHA256 = '260bccc8ad50de8cd2150f3078fd4b0bbc97e802de464be6115badc33fbed531'
PESOS_V6_SHA256 = '27e193681480092afef0aacfc25fed6e4da64f473da3d145c3a016af07ed529a'
CORPUS_V6_SHA256 = '68edd570bb60630bca0888935e89081d25b7044615c1628e97ab0d18a0da74e8'
ORIGEM_V6_SHA256 = '4b871b3008542803544404e82042ab0a9dc6e8a0364de294a7f79870130a5b6d'
ESTRUTURA_V6_SHA256 = '0399ed5b8052643f6a9b4514daf2ec277c1f2ce5dc62bed180c89a64a6350d28'
DIVERSIDADE_V6_SHA256 = 'd16b084bce8c754e4ea3f5ec6e29e8621abee3fb69e89ef46f4638bcdd1b0aa7'
PRATICOS_V6_SHA256 = '799559f45a9f5b22ced00351a5a3f670b7240f1f76ac9b94ccab67f7f1c6ced0'
CORPUS_V7_SHA256 = '65f4ac8ad04474fbe3d43e8affd05981b7ce473e5659297f46646a96f1975da9'
PESOS_V7_SHA256 = 'f9305b6653a511d24b3285fcc0b05506b398e2cbac993d985b4a1d6352eb3f35'
ORIGEM_V7_SHA256 = 'adf0fa8c297eab6cf9122c8da6a1bbd5796416f406e86e0b096ed2a23f7c5d0a'
ESTRUTURA_V7_SHA256 = '10ccdc3f851b5f2c61f1ea5e3d1ce75d66c37afb95728a8af7e97884793696c9'
CAUSAL_V7_SHA256 = '15164100b1a852a7559daae49b9e7c1cb9eaaf03e29807cf4145e9071589b8ac'
FOLEGO_V7_SHA256 = 'f0fe9b014056595b383601299603e33c773270b30a4885dff15e3b5877eea7a6'
ALIASES_V7_SHA256 = '0269dde6f1b810638412b129be7e092a2bc2638d4c5423588dbd182d3137d37d'
ATOS = frozenset(('historia', 'continuar', 'corrigir'))


def classe_acontecimento(texto):
    n = normalizar(texto)
    if re.search(r'\b(?:recuper\w*|ja .*encontrad\w*)\b', n):
        return 'recuperacao'
    for padrao, classe in (
            (r'\bvazi[ao]\b', 'caixa_vazia'), (r'\bdevolv\w*\b', 'devolucao'),
            (r'\b(?:volt\w*|retorn\w*)\b', 'retorno'),
            (r'\b(?:perde|perdeu|perdido|perdida)\b', 'perda'),
            (r'\b(?:linha|fio)\b', 'costura'),
            (r'\b(?:consert\w*|rasgad\w*|costur\w*)\b', 'conserto'),
            (r'\b(?:pede|pediu) ajuda\b', 'ajuda'),
            (r'\b(?:encontra|encontrou|contem|aparece)\b', 'encontro')):
        if re.search(padrao, n):
            return classe
    return None


def reacao_adequada(tokens, classe):
    """Verifica ação realizada, sem contar a declaração copiada em @relato.

    Critério limitado às classes autorais deste experimento, não um juiz
    geral de significado nem comparação com a resposta alvo.
    """
    sinais = {
        'perda': r'\b(?:procur\w*|busc\w*)\b',
        'recuperacao': r'\b(?:guard\w*|segur\w*)\b',
        'caixa_vazia': r'\b(?:surpresa|confer\w*)\b',
        'ajuda': r'\b(?:respondeu|responderam)\b',
        'retorno': r'\b(?:voltou|retorno)\b',
        'devolucao': r'\b(?:deixou|entrega)\b',
        'conserto': r'\b(?:rasgo|unir)\b',
        'costura': r'\b(?:costurou|fio)\b',
        'companhia': r'\b(?:juntos|ajuda)\b',
        'encontro': r'\b(?:observou|examinar)\b',
    }
    return classe not in sinais or bool(re.search(sinais[classe], normalizar(' '.join(t for t in tokens if not t.startswith('@')))))


def resolver_objeto_escrita(texto, escrita, ativo):
    """Resolve pronomes e substituições literais só no objeto ficcional ativo.

    Não infere gênero de nomes, não escolhe entre objetos coordenados e não
    muda o estado em uma negação. A resolução conserva a fonte do usuário.
    """
    trecho = re.split(r'[.!]\s*(?=Continue\b)', texto.strip(), maxsplit=1, flags=re.I)[0].strip('.! ')
    pronome = re.fullmatch(r'(?:Ela|Ele|[AO] personagem)\s+(?:(não)\s+)?([oa])\s+'
                          r'(recuperou|encontrou(?: novamente)?|achou)', trecho, re.I)
    clitico = re.fullmatch(r'(?:Ela|Ele|[AO] personagem)\s+tenta\s+consert[áa]-(la|lo)', trecho, re.I)
    correcao = re.fullmatch(r'(?:(?:Corrigindo|Na verdade)[:,]?\s*)?não era\s+(.+?)'
                           r'(?:,\s*era|\.\s*Era)\s+(.+)', trecho, re.I)
    if not (pronome or clitico or correcao):
        return None
    if correcao and not ativo:
        return None  # Correções fora da escrita permanecem com a memória real.
    slots = dict((escrita or {}).get('slots', {}))
    refs = [slots[k] for k in ('tema1', 'tema2', 'detalhe') if slots.get(k)]
    def esclarecer():
        return dict(peca='esclarecimento', ato='objeto_historia_incerto', referentes=refs)
    if not ativo:
        return esclarecer()
    classe = escrita.get('classe_escrita')
    anterior = escrita.get('evento_escrita') or slots.get('relato', '')
    objeto = referente_acontecimento(anterior, classe)
    if (not objeto or not re.match(r'^(?:um|uma|o|a)\s+\S', objeto, re.I)
            or re.search(r'\b(?:e|ou|com|que|mas|enquanto|porque)\b|[,;.!?]', objeto, re.I)):
        return esclarecer()
    if pronome:
        feminino = bool(re.match(r'^(?:uma|a)\s', objeto, re.I))
        if pronome[1] or (pronome[2].casefold() == 'a') != feminino:
            return esclarecer()
        classe = 'recuperacao'
        evento = objeto + (' já foi recuperada' if feminino else ' já foi recuperado')
        novo = objeto
    elif clitico:
        feminino = bool(re.match(r'^(?:uma|a)\s', objeto, re.I))
        if clitico[1].casefold().endswith('a') != feminino:
            return esclarecer()
        classe = 'conserto'
        evento = 'A personagem tenta consertar ' + objeto
        novo = objeto
    else:
        velho, novo = (p.strip() for p in correcao.groups())
        # A correção precisa identificar o trecho inteiro. “Era azul” pode
        # designar personagem, lugar ou outro objeto; não escolher por cor.
        if (normalizar(velho) != normalizar(objeto) or not re.fullmatch(r'(?:um|uma|o|a)\s+[\wÀ-ÿ -]{1,120}', novo, re.I)
                or re.search(r'\b(?:e|ou|não)\b', novo, re.I)):
            return esclarecer()
        evento = anterior.replace(objeto, novo, 1)
    slots['relato'] = evento
    return dict(peca='escrita', ato='continuar', slots=slots, personagem=slots.get('tema1'),
                referentes=list(slots.values()), classe_escrita=classe, evento_escrita=evento,
                resolucao_objeto=dict(fonte=texto, objeto_anterior=objeto, objeto=novo,
                                     operacao='correcao' if correcao else 'pronome'))


def contexto_escrita(texto, bot):
    """Resolve apenas operadores de uma ficção ativa; não registra fatos reais."""
    escrita = bot.conversacao.geracao.ultima_escrita
    ativo = bool(escrita and escrita['tipo'] == 'historia'
                 and bot.conversacao.turno - escrita['turno'] <= bot.conversacao.geracao.MAX_INTERVALO
                 and bot.historico and bot.historico[-1].get('id', '').startswith('conversa:gerada_'))
    resolvida = resolver_objeto_escrita(texto, escrita, ativo)
    if resolvida:
        return resolvida
    if not escrita or escrita['tipo'] != 'historia':
        return None
    if bot.conversacao.turno - escrita['turno'] > bot.conversacao.geracao.MAX_INTERVALO:
        return None
    n = normalizar(texto)
    if re.search(r'\b(?:eu|meu|minha|vida real|veridic\w*|comprovad\w*)\b', n) and n.strip('.!?') != 'avance sem repetir o que eu disse':
        return None
    slots = dict(escrita['slots'])
    pessoas_cenario = [slots[k] for k in ('tema1', 'tema2', 'detalhe') if slots.get(k)]
    def rota(ato, **dados):
        return dict(peca='escrita', ato=ato, slots=slots, personagem=slots.get('tema1'),
                    referentes=list(slots.values()), **dados)
    # Operadores elípticos usam a tarefa mais recente, não apenas uma história
    # antiga ainda guardada. A extração conserva trechos literais do usuário.
    causal = re.fullmatch(r'(?:e (?:depois|agora)|o que (?:a personagem|ela|ele) faz em seguida|'
                          r'avance sem repetir o que eu disse|mais um passo|'
                          r'continue a cena,? sem recontar o acontecimento|'
                          r'o que acontece depois disso|prossiga sem repetir)[?!.]?', n)
    comum = re.fullmatch(r'(?:continue|continua|prossiga)(?: a historia| mais um pouco| de onde parou)?[.!]?|'
                         r'(?:nao repita a cena anterior|o que acontece em seguida)[?!.]?', n)
    evento_atual = escrita.get('evento_escrita') or escrita['slots'].get('relato', '')
    if comum and escrita.get('classe_escrita') in CLASSES_CAUSAIS and referente_acontecimento(evento_atual, escrita['classe_escrita']):
        causal = comum
    final_causal = escrita.get('continuidade_causal') and re.fullmatch(
        r'(?:conclua|termine) (?:a|essa) historia[.!]?|faca um final tranquilo[.!]?', n)
    if causal or final_causal:
        anterior = bot.historico[-1] if bot.historico else {}
        if not final_causal and not anterior.get('id', '').startswith('conversa:gerada_'):
            return dict(peca='esclarecimento', ato='continuidade_incerta', referentes=pessoas_cenario)
        classe = escrita.get('classe_escrita')
        evento = escrita.get('evento_escrita') or escrita['slots'].get('relato', '')
        objeto = referente_acontecimento(evento, classe)
        if not objeto or classe not in CLASSES_CAUSAIS or (not final_causal and escrita.get('passo_causal', 0) >= 4):
            return dict(peca='esclarecimento', ato='continuidade_incerta', referentes=pessoas_cenario)
        slots['relato'] = objeto
        return rota('corrigir' if final_causal else 'continuar', classe_escrita=classe,
                    continuidade_causal=True, evento_escrita=evento,
                    passo_causal=min(3, escrita.get('passo_causal', 0)))
    if re.fullmatch(r'nao (?:invente|crie|coloque|adicione) (?:um )?nome (?:para|na|no) (.+?)[.!]?', n):
        alvo = re.sub(r'^nao .+? nome (?:para|na|no) ', '', n).strip('.!')
        palavras = set(re.findall(r'\w+', normalizar(slots.get('tema1', '')))) - {'o','a','um','uma'}
        if 'personagem' in alvo or palavras.intersection(alvo.split()):
            return dict(peca='esclarecimento', ato='restricao', referentes=list(slots.values()))
    if re.fullmatch(r'(?:quem (?:estava|participou) (?:nessa|nesta|na) historia)[?!.]?', n):
        return dict(peca='esclarecimento', ato='participantes_historia', referentes=pessoas_cenario)
    if re.fullmatch(r'resuma (?:a|essa) historia(?: que voce escreveu)?[.!]?', n):
        return dict(peca='esclarecimento', ato='resumo_historia', referentes=pessoas_cenario)
    if re.fullmatch(r'o que mudou entre o comeco e o final[?!.]?', n):
        return dict(peca='esclarecimento', ato='comparar_historia', referentes=pessoas_cenario)
    if re.fullmatch(r'(?:quero|faca|escreva) (?:uma|a) historia sem (.+?)[.!]?', n):
        proibidos = re.split(r'\s+e\s+(?:sem\s+)?', re.split(r'\s+sem\s+', texto, maxsplit=1, flags=re.I)[1].strip('.! '), flags=re.I)
        if all(re.fullmatch(r'[\wÀ-ÿ -]{1,40}', p) for p in proibidos):
            return rota('continuar', classe_escrita='cotidiano', restricoes_escrita=proibidos)
    if re.fullmatch(r'nao mude a cor (?:da|do) .+[.!]?', n):
        return dict(peca='esclarecimento', ato='preservar_historia', referentes=list(slots.values()))
    if re.fullmatch(r'(?:deixe|faca) (?:a|essa) historia mais simples[.!]?', n):
        return dict(peca='esclarecimento', ato='limite_simplificacao_historia', referentes=pessoas_cenario)
    if re.fullmatch(r'mostre (?:uma )?situacao engracada com (?:a )?mesma personagem[.!]?', n):
        return rota('continuar', classe_escrita='divertido')
    if re.fullmatch(r'(?:conclua|termine) (?:a|essa) historia[.!]?|faca um final tranquilo[.!]?', n):
        return rota('corrigir', classe_escrita=escrita.get('classe_escrita') or 'cotidiano')
    aliases = (r'nao repita a cena anterior|o que acontece em seguida|continue mais um pouco|'
               r'continue de onde parou|continue a partir (?:disso|dessa situacao|da resposta)|continue sem separar os dois|'
               r'continue mostrando como (?:elas|eles) tentam resolver o problema')
    if re.fullmatch(r'(?:' + aliases + r')[?!.]?', n):
        return rota('continuar', classe_escrita=('cotidiano' if slots.get('relato') else escrita.get('classe_escrita')))
    final_evento = re.fullmatch(r'(?:Agora )?(?:muda|mude) o final:\s*((?:elas|eles|os dois) encontram .+?)[.!]?', texto.strip(), re.I)
    aparecimento = re.fullmatch(r'faça aparecer (.+?)[.!]?', texto.strip(), re.I)
    evento = None
    if final_evento:
        evento = final_evento[1].strip('.! ')
        # Recuperação substitui a perda, sem transformar o objeto em pessoa.
        slots['relato'] = evento
        return rota('corrigir', classe_escrita='recuperacao', evento_escrita=evento)
    if aparecimento:
        slots['detalhe'] = aparecimento[1].strip('.! ')
        evento = 'A personagem encontra ' + slots['detalhe']
    elif re.match(r'continue com (?:ela|ele) tentando\b', n):
        evento = re.sub(r'^Continue com (?:ela|ele) tentando\s+', 'A personagem tenta ', texto.strip(), flags=re.I).strip('.! ')
    elif re.match(r'faca (?:a|o) personagem\b', n):
        evento = re.sub(r'^Faça (?:a|o) personagem\s+', 'A personagem deve ', texto.strip(), flags=re.I).strip('.! ')
    else:
        partes = re.split(r'[.!]\s*(?=(?:Continue\b|Mostre\b|Use isso\b|Faça\b))', texto.strip(), maxsplit=1, flags=re.I)
        candidato = re.sub(r'^Agora\s+', '', partes[0], flags=re.I).strip('.! ')
        explicito = bool(re.match(r'(?:A|O) personagem\b|(?:Ela|Ele|Os dois)\b', candidato, re.I))
        vinculado = bool(len(partes) == 2 and classe_acontecimento(candidato))
        recuperacao = bool(re.search(r'\bja foi recuperad\w*\b', normalizar(candidato)))
        if explicito or vinculado or recuperacao:
            evento = candidato
    if evento and (classe := classe_acontecimento(evento)):
        if aparecimento:
            classe = 'companhia'  # O argumento detalhe tem papel de participante.
        # Guarda fontes recentes de ficção sem criar memória geral nova.
        anteriores = [escrita['slots']['relato']] if escrita['slots'].get('relato') else []
        if classe == 'recuperacao':
            anteriores = []  # Correção não repete a perda anterior como fato atual.
        declaracoes = anteriores + [evento]
        while len('. '.join(declaracoes)) > 600 and len(declaracoes) > 1:
            declaracoes.pop(0)
        if len(evento) > 600:
            return None
        slots['relato'] = '. '.join(dict.fromkeys(declaracoes))
        ajuda = re.search(r'\bpede ajuda a (uma? [^.!]+)', evento, re.I)
        if ajuda:
            slots['detalhe'] = ajuda[1].strip()
            # Pedir ajuda à companhia pede ajuda recebida; um bilhete
            # pedindo ajuda continua pedindo resposta da personagem.
            classe = 'companhia'
        return rota('continuar', classe_escrita=classe, evento_escrita=evento)
    return None


CLASSES_CAUSAIS = frozenset(('perda', 'recuperacao', 'encontro', 'caixa_vazia',
                           'retorno', 'devolucao', 'ajuda', 'conserto', 'costura', 'companhia'))


def referente_acontecimento(evento, classe):
    """Seleciona um trecho declarado; não adivinha objetos ou participantes."""
    padroes = {
        'perda': r'\b(?:perde|perdeu)\s+(.+)',
        'recuperacao': r'^(.+?)\s+j[aá] foi recuperad[oa]',
        'encontro': r'\bencontr(?:a|ou)\s+(.+)',
        'caixa_vazia': r'\bencontr(?:a|ou)\s+(.+?)\s+que está vazi[oa]',
        'retorno': r'\b(?:volta|voltou|retorna|retornou)\s+para\s+(.+)',
        'devolucao': r'\bdevolv(?:e|eu)\s+(.+)',
        'ajuda': r'\bencontr(?:a|ou)\s+(.+?)\s+que pede ajuda',
        'conserto': r'\bconsertar\s+(.+)',
        'costura': r'\b(?:recebe|recebeu|traz|trouxe)\s+(.+)',
        'companhia': r'\bpede ajuda a\s+(.+)',
    }
    m = re.search(padroes.get(classe, r'(?!)'), evento, re.I)
    return m[1].strip('.! ') if m and len(m[1]) <= 160 else None


def aprovacao_valida(dados):
    a = dados.get('aprovacao', {})
    m = a.get('metricas', {})
    origem=a.get('checkpoint_origem_sha256')
    pesos_esperados={ORIGEM_SHA256:PESOS_SHA256,ORIGEM_V2_SHA256:PESOS_V2_SHA256,ORIGEM_V3_SHA256:PESOS_V3_SHA256,ORIGEM_V5_SHA256:PESOS_V5_SHA256,ORIGEM_V6_SHA256:PESOS_V6_SHA256,ORIGEM_V7_SHA256:PESOS_V7_SHA256}.get(origem)
    if not pesos_esperados or hashlib.sha256(json.dumps(dados.get('pesos'),sort_keys=True,separators=(',',':')).encode()).hexdigest()!=pesos_esperados:
        return False
    if origem in (ORIGEM_V5_SHA256, ORIGEM_V6_SHA256, ORIGEM_V7_SHA256):
        v7 = origem == ORIGEM_V7_SHA256
        v6 = origem in (ORIGEM_V6_SHA256, ORIGEM_V7_SHA256)
        estrutura = {k:v for k,v in dados.items() if k not in ('pesos','controle','aprovacao','limite')}
        return (dados.get('controle') == {'aprovado':True,'ativo_no_chat':True} and
                hashlib.sha256(json.dumps(estrutura,sort_keys=True,separators=(',',':')).encode()).hexdigest()==(ESTRUTURA_V7_SHA256 if v7 else ESTRUTURA_V6_SHA256 if v6 else ESTRUTURA_V5_SHA256) and
                a.get('casos_sha256')==CASOS_V5_SHA256 and a.get('corpus_sha256')==(CORPUS_V7_SHA256 if v7 else CORPUS_V6_SHA256 if v6 else CORPUS_V5_SHA256) and
                set(a.get('atos',[]))==ATOS and m.get('casos_total')==114 and
                all((110 if v6 else 103)<=m.get(k,0)<=114 for k in ('casos_motor','casos_http')) and
                all(m.get(k)==79 for k in ('casos_antigos_motor','casos_antigos_http')) and
                all(m.get(k)==0 for k in ('trocas_dominio','referentes_ausentes','desvios_proibidos')) and
                m.get('historias_entregues')==52 and m.get('conversas_mantem_fio',0)>=6 and
                (not v6 or (
                    a.get('diversidade_sha256') == DIVERSIDADE_V6_SHA256 and
                    a.get('praticos_sha256') == PRATICOS_V6_SHA256 and
                    m.get('diversidade_turnos') == 48 and
                    all(m.get(k) == 8 for k in ('diversidade_motor','diversidade_http')) and
                    m.get('diversidade_problemas_fidelidade') == 0 and
                    all(m.get(k) == 40 for k in ('praticos_motor','praticos_http')) and
                    a.get('treino_reproduzido_byte_a_byte') is True)) and
                (not v7 or (
                    a.get('continuidade_sha256') == CAUSAL_V7_SHA256 and
                    a.get('folego_sha256') == FOLEGO_V7_SHA256 and
                    a.get('aliases_sha256') == ALIASES_V7_SHA256 and
                    m.get('continuidade_turnos') == 88 and
                    all(6 <= m.get(k, 0) <= 10 for k in ('continuidade_motor', 'continuidade_http')) and
                    all(m.get(k) == 2 for k in ('esclarecimentos_motor', 'esclarecimentos_http')) and
                    m.get('contradicoes_estado') == 0 and
                    all(m.get(k) == 2 for k in ('folego_motor', 'folego_http')) and
                    all(m.get(k) == 3 for k in ('aliases_motor', 'aliases_http')))))
    v2=origem==ORIGEM_V2_SHA256
    v3=origem==ORIGEM_V3_SHA256
    return (dados.get('controle') == {'aprovado': True, 'ativo_no_chat': True} and
            set(a.get('atos', [])) == ATOS and
            all(m.get(k, 0) >= (61 if v3 else 43 if v2 else 34) for k in ('casos_motor', 'casos_http')) and
            m.get('trocas_dominio') == m.get('referentes_ausentes') == 0 and
            m.get('historias_entregues') == (21 if v3 else 4 if v2 else 2) and m.get('conversas_mantem_fio', 0) >= (10 if v3 else 8 if v2 else 6))


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
    if not pedido:
        # “Uma aventura” é um pedido explícito de ficção, não um fato.
        alternativa = re.sub(r'\b(uma?) aventura\b', r'\1 história', texto, count=1, flags=re.I)
        if alternativa != texto:
            pedido = criacao(alternativa)
    if pedido and pedido['acao'] == 'historia':
        slots = dict(pedido['slots'])
        # Separa o lugar reconhecido, preservando os valores literais. Um
        # segundo participante ou descrição ambígua não vira cenário.
        if set(slots) == {'tema1'}:
            partes = re.fullmatch(r'(.+?) (?:em|numa?|na|no) ((?:(?:um|uma|o|a) )?(?:ilha|bosque|estação|vale|praça|torre|jardim|floresta|casa|farol|ponte|castelo|oficina)\b.+)', slots['tema1'], re.I)
            if partes:
                slots = {'tema1': partes[1], 'tema2': partes[2]}
        return dict(peca='escrita', ato='historia', referentes=list(slots.values()),
                    personagem=slots['tema1'], slots=dict(slots), estilo=pedido.get('estilo', 'neutro'),
                    classe_escrita='divertido' if pedido.get('estilo')=='divertido' else None)
    escrita = bot.conversacao.geracao.ultima_escrita
    if not escrita or escrita['tipo'] != 'historia':
        return None
    if bot.conversacao.turno - escrita['turno'] > bot.conversacao.geracao.MAX_INTERVALO:
        return None
    mudanca = revisao(texto)
    if not mudanca and re.fullmatch(r'(?:continue|continua|prossiga) (?:depois (?:desse|deste|do) final|a historia mais uma vez)[.!]?', normalizar(texto)):
        mudanca = {'operacao':'continuacao'}
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
    if digest not in (PESOS_SHA256,PESOS_V2_SHA256,PESOS_V3_SHA256,PESOS_V5_SHA256,PESOS_V6_SHA256,PESOS_V7_SHA256):
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


def conferir_estado_causal(tokens, classe):
    """Bloqueia inversões conhecidas de estado; não é um juiz semântico geral."""
    n = normalizar(' '.join(t for t in tokens if not t.startswith('@')))
    proibidos = {
        'recuperacao': r'\b(?:perdido|perdeu|procurou)\b|busca continuou',
        'perda': r'\brecuperado\b|guardou\s+(?:em|com)|problema (?:ficou|estava) resolvido',
        'caixa_vazia': r'\bencontrou\b|objeto (?:aberto|recuperado)',
    }
    return not re.search(proibidos.get(classe, r'(?!)'), n)


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
        detalhe_final = None
        if not slots and rota['ato'] == 'historia' and rota.get('personagem'):
            slots['tema1'] = rota['personagem']
        if not slots and rota['ato'] == 'corrigir':
            if escrita:
                slots = dict(escrita['slots'])
            elif rota.get('personagem'):
                slots['tema1'] = rota['personagem']
            detalhe = re.search(r'\b(?:ele|ela) (?:encontra|conhece|reencontra) (.+?)(?:,|[.!?]|$)', texto, re.I)
            if detalhe:
                detalhe_final = detalhe[1]
                slots['detalhe' if slots.get('tema2') else 'tema2'] = detalhe[1]
        if not slots.get('tema1'):
            self.trace.update(recuou=True, motivo='referente_ambiguo_ou_ausente', confianca_roteamento='baixa')
            return ('conversa:esclarecer', 'Qual personagem devo usar? Preciso desse referente para continuar a história.')
        if (rota.get('estilo', 'neutro') not in ('neutro','simples','divertido') or len(slots) > 4 or
                not set(slots)<= {'tema1','tema2','detalhe','relato'}):
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
            v5=dados.get('corpus_sha256') in (CORPUS_V5_SHA256, CORPUS_V6_SHA256)
            v7=dados.get('corpus_sha256') == CORPUS_V7_SHA256
            v5=v5 or v7
            v3=v5 or dados.get('corpus_sha256')==CORPUS_V3_SHA256
            v2=v3 or dados.get('corpus_sha256')=='e2e33fe41cceeb27f2839572003210af2ecc315d87e0f889cb41c9cc9701dd45'
            if v3 and detalhe_final:
                if not escrita or not escrita['slots'].get('tema2'):
                    slots.pop('tema2',None)
                slots['detalhe']=detalhe_final
            if v2 and not v3 and rota['ato']=='continuar' and escrita and escrita['acao']=='final' and slots.get('tema2') and not slots.get('detalhe'):
                self.trace.update(recuou=True,motivo='amigo_do_final_nao_e_cenario')
                return ('conversa:esclarecer','Ainda não consigo continuar esse final preservando todos os papéis de '+', '.join(slots.values())+'. Qual deve ser a próxima ação?')
            if v2 and slots.get('tema2') and (rota['ato']!='corrigir' and not rota.get('repetir_final') or slots.get('detalhe')):
                # O treino ampliado cobre lugares, não duas personagens.
                # Temas de papel incerto conservam o executor anterior.
                lugar=re.match(r'(?:(?:um|uma|o|a) )?(?:ilha|bosque|estacao|vale|praca|torre|jardim|floresta|casa|farol|ponte|castelo|oficina)\b',normalizar(slots['tema2']))
                if not lugar:
                    self.trace.update(recuou=True,motivo='segundo_tema_sem_papel_de_cenario')
                    return None
            if not v2 and (rota['ato'] in ('historia','continuar') and set(slots)!={'tema1'} or len(slots)>2):
                self.trace.update(motivo='pedido_fora_do_escopo_validado',recuou=True)
                return None
            self.trace.update(checkpoint_sha256=sha, experimental=bool(self.candidato),
                              memoria_usada=bool(escrita or not rota.get('slots')),
                              argumentos=dict(slots), confianca_roteamento='explicita')
            if rota.get('resolucao_objeto'):
                self.trace['resolucao_objeto'] = dict(rota['resolucao_objeto'])
            # Mantém o mesmo arco durante continuação, final e reescrita. A
            # nova cena com companhia pode avançar no checkpoint de continuidade.
            variante=(escrita.get('variante',1) if escrita and (rota['ato']!='historia' or rota.get('reescrita'))
                      else (bot.conversacao.geracao.variante+1)%8) if v2 else 0
            if v3 and not v5 and rota['ato']=='continuar' and slots.get('detalhe') and escrita and escrita['acao']=='continuacao':
                # Uma nova cena da mesma viagem, com os mesmos participantes.
                # A reescrita conserva esta cena; não reinicia o enredo.
                variante=(variante+1)%8
            contexto = dict(acao=rota['repetir_acao'] if v3 and rota.get('reescrita') else 'final' if rota.get('repetir_final') else {'historia':'historia', 'continuar':'continuacao', 'corrigir':'final'}[rota['ato']],
                            slots=slots, estilo=rota.get('estilo', 'neutro'), variante=variante,
                            mensagem=texto, historico=[h['pergunta'] for h in bot.historico[-3:]],
                            resposta_anterior='')
            if v3:
                # Ato, cena e todos os referentes já vêm do contexto resolvido.
                # O hash residual do texto não representa compreensão de
                # diálogo e produziu mistura de cenas na revisão experimental.
                contexto.update(mensagem='',historico=[])
                self.trace['contexto_textual_neutralizado']=True
                self.trace['contexto_selecionado']={'acao':contexto['acao'],'cena':variante,'slots':dict(slots)}
            if v5:
                classe = rota.get('classe_escrita') or (escrita or {}).get('classe_escrita')
                if detalhe_final:
                    # O final clássico já tem supervisão própria; só seleciona
                    # acontecimento quando existe uma declaração ficcional.
                    classe = 'companhia' if slots.get('relato') else None
                elif rota['ato']=='historia' and re.search(r'\boficina\b',normalizar(slots.get('tema2',''))):
                    classe = 'cotidiano'
                elif rota['ato']=='continuar' and (slots.get('relato') or classe=='companhia') and not rota.get('classe_escrita'):
                    classe = 'cotidiano'
                if rota.get('reescrita') and not slots.get('relato'):
                    # Conserva a realização clássica com cinco frases.
                    classe = None
                if classe:
                    contexto.update(mensagem='acontecimento '+classe+' estado_'+classe, resposta_anterior='')
                    if contexto['estilo']=='divertido': contexto['estilo']='neutro'
                    if escrita and rota['ato']=='continuar': contexto['variante']=(variante+1)%8
                    self.trace['classe_escrita']=classe
                elif escrita and rota['ato']=='continuar' and escrita['acao']=='continuacao':
                    contexto['resposta_anterior']=escrita['texto']
                    self.trace.update(usa_trecho_anterior=True,trecho_anterior=escrita['texto'])
                self.trace['contexto_selecionado']=dict(acao=contexto['acao'],cena=contexto['variante'],slots=dict(slots),classe=classe)
                if rota.get('continuidade_causal'):
                    if not v7:
                        self.trace.update(recuou=True, motivo='continuidade_sem_checkpoint_aprovado')
                        return ('conversa:esclarecer', 'Qual deve ser o próximo acontecimento da história?')
                    contexto.update(mensagem='continuidade_causal '+classe+' estado_'+classe,
                                    resposta_anterior='estado anterior '+classe,
                                    variante=rota['passo_causal'])
                    self.trace.update(continuidade_causal=True, passo_causal=rota['passo_causal'],
                                      usa_estado_anterior=True, evento_anterior=rota['evento_escrita'])
                    self.trace['contexto_selecionado'].update(cena=contexto['variante'],evento=rota['evento_escrita'])
            gerada = modelo.gerar(contexto, max_tokens=96)
            resposta, guarda = conferir(gerada, contexto, set(modelo.vocabulario), rota.get('frases'))
            if v2 and not v5 and not guarda['aceita']:
                # Texto residual pode sugerir o ato do turno anterior. Uma
                # segunda realização conserva ação, arco e argumentos; só
                # neutraliza esse texto. Ambas passam pela mesma guarda.
                estruturado=dict(contexto,mensagem='',historico=[],resposta_anterior='')
                gerada=modelo.gerar(estruturado,max_tokens=96)
                resposta,guarda=conferir(gerada,estruturado,set(modelo.vocabulario),rota.get('frases'))
                self.trace['contexto_textual_neutralizado']=True
            restricoes = rota.get('restricoes_escrita', (escrita or {}).get('restricoes_escrita', []))
            if v5 and guarda['aceita'] and not rota.get('continuidade_causal') and not reacao_adequada(gerada['tokens'], classe):
                guarda=dict(politica='conversa',aceita=False,motivos=['acontecimento sem reação compatível'])
            if rota.get('continuidade_causal') and guarda['aceita'] and not conferir_estado_causal(gerada['tokens'], classe):
                guarda=dict(politica='conversa',aceita=False,motivos=['continuação contradiz estado selecionado'])
            if guarda['aceita'] and any(re.search(r'(?<!\w)'+re.escape(normalizar(p))+r'(?!\w)',normalizar(resposta)) for p in restricoes):
                guarda=dict(politica='conversa',aceita=False,motivos=['restrição de escrita violada'])
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
            if v5:
                g.ultima_escrita.update(classe_escrita=classe, restricoes_escrita=restricoes,
                    inicio=(escrita or {}).get('inicio', (escrita or {}).get('texto', resposta)) if rota['ato']!='historia' else resposta)
                g.ultima_escrita.update(evento_escrita=rota.get('evento_escrita') or ((escrita or {}).get('evento_escrita', '') if rota['ato']!='historia' else ''),
                                       continuidade_causal=bool(rota.get('continuidade_causal')),
                                       passo_causal=rota['passo_causal']+1 if rota.get('continuidade_causal') else 0)
            g.ultima_criacao = g.ultima_escrita
            if v2 and rota['ato']=='historia' and not rota.get('reescrita'):g.variante=contexto['variante']
            g.ultimo_quadro = {'modelo':'GRU de diálogo própria', 'acao':contexto['acao'],
                               'slots_copiados':sorted(slots), 'checkpoint_sha256':sha}
            return 'conversa:gerada_' + contexto['acao'], resposta
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.trace.update(recuou=True, motivo='checkpoint_indisponivel', erro=type(exc).__name__)
            return None
