"""Memória explícita reversível de uma gramática autoral limitada.

Não lê modelos, exemplos anotados ou arquivos. Entradas são exclusivamente as
falas brutas e a proposta neural já calculada. Esta ajuda determinística não é
aprendizado neural nem conversação livre. Em ambiguidade preserva a proposta.
"""
from copy import deepcopy
from dataclasses import dataclass, field
import re


PALAVRA = r"[^\W\d_]+"
NUMERO = r"-?\d+"
FLAGS = re.IGNORECASE | re.UNICODE
FUNCIONAIS = set("a o os as e não se sobre para por quanto qual quem com sem de do da dos das um uma agora entre compare mostre diga confira verifique imagine suponha corrigo corrigindo corrigido inventário regra preço custo plano fatos fato hipótese simulação cenário alternativa informação é estou isto isso houve acabei mude retome fora no na nenhum nenhuma ele ela eles elas este esta esse essa estes estas aquele aquela".split())


class Ambiguo(ValueError):
    pass


def _nome(texto):
    return (bool(texto) and texto[0].isupper() and texto.isalpha()
            and texto.casefold() not in FUNCIONAIS)


def _span(texto, turno, a, b):
    while a < b and texto[a].isspace(): a += 1
    while a < b and texto[b - 1].isspace(): b -= 1
    return {'turno': turno, 'inicio': a, 'fim': b, 'texto': texto[a:b]}


def _rx(pattern):
    return re.compile(pattern, FLAGS)


# Extração conjunta de entidade e preço. A unidade moeda é obrigatória: um
# número de dias/minutos não é uma cobrança. Sem inferir entidade por proximidade.
PRECOS = [_rx(p) for p in [
    rf"\b(?P<n>{PALAVRA})(?:\s+(?:agora|realmente|na\s+verdade|de\s+fato))?\s+(?:custa|custaria|custasse|vale|valeria|valesse|ficaria(?:\s+em)?|passou\s+a|passasse\s+a|sai\s+por|tem\s+preço\s+de|por|a)\s+(?P<v>{NUMERO})\s+reais\b",
    rf"\b(?:custo|preço|cobrança|despesa)(?:\s+(?:real|certo|correto))?\s+(?:de|com|do\s+plano)\s+(?P<n>{PALAVRA})\s+(?:é(?:\s+de)?|fica\s+em|para)\s+(?P<v>{NUMERO})\s+reais\b",
    rf"\b(?P<n>{PALAVRA})\s*:\s*(?:o\s+)?(?:custo|preço|valor)(?:\s+(?:real|certo|correto))?\s+(?:é|fica\s+em)\s+(?P<v>{NUMERO})\s+reais\b",
    rf"\bpor\s+(?P<n>{PALAVRA})\s*,\s*paga[- ]se\s+(?P<v>{NUMERO})\s+reais\b",
]]
POSSE = _rx(rf"\b(?P<n>{PALAVRA})\s*[:,]?\s*(?:(?:agora|é\s+que|diz\s+que)\s+)?(?P<v>(?:não\s+)?tem\s+{PALAVRA}(?:\s+e\s+(?:(?:não\s+)?tem\s+)?{PALAVRA})*)")
REGRA = _rx(rf"\b(?:exigidos|exigidas|requeridos|requeridas)\s+(?:para\s+entrar\s+)?(?:são\s+)?(?P<v>{PALAVRA}\s+e\s+{PALAVRA})(?!\w)")


def _extrair(texto, turno):
    updates = {'precos': {}, 'posses': {}}
    refs = {}
    for tipo, patterns in [('precos', PRECOS), ('posses', [POSSE])]:
        for pat in patterns:
            for m in pat.finditer(texto):
                n = m['n']
                if not _nome(n): continue
                key = n.casefold(); source = _span(texto, turno, *m.span('v'))
                old = updates[tipo].get(key)
                if old and old['texto'] != source['texto']:
                    raise Ambiguo('Duas declarações diferentes da mesma entidade na mesma fala.')
                if old is None: updates[tipo][key] = source
                refs.setdefault(key, _span(texto, turno, *m.span('n')))
    rules = [_span(texto, turno, *m.span('v')) for m in REGRA.finditer(texto)]
    if len(rules) > 1:
        raise Ambiguo('Mais de uma regra declarada na mesma fala.')
    updates['regra'] = rules[0] if rules else None
    if re.search(r'\bnão\s+(?:custa|vale|sai\s+por)\b', texto, FLAGS):
        raise Ambiguo('Negar uma cobrança não declara seu valor correto.')
    if not updates['precos'] and re.search(r'\d+\s+(?:reais|dólares|euros)\b', texto, FLAGS):
        raise Ambiguo('Cobrança sem vínculo literal suportado com uma entidade.')
    if re.search(r'\b(?:ele|ela|eles|elas)\s+(?:agora\s+)?(?:não\s+)?tem\b', texto, FLAGS):
        raise Ambiguo('Atualização pronominal sem entidade explícita.')
    for sp in updates['posses'].values():
        if any(w[0].isupper() for w in re.findall(PALAVRA, sp['texto'])):
            raise Ambiguo('Inventário contém outro nome ou item capitalizado não suportado.')
        if len(re.findall(r'\be\b', sp['texto'], FLAGS)) > 1:
            raise Ambiguo('Inventário com mais de dois itens fora do executor declarado.')
    # Uma frase negativa não transforma sua cobrança em evidência positiva.
    for tipo in ['precos', 'posses']:
        for key, sp in updates[tipo].items():
            before = texto[max(0, sp['inicio'] - 80):sp['inicio']].casefold()
            if tipo == 'precos' and re.search(r'\bnão\s+(?:custa|vale|sai\s+por)\s*$', before):
                raise Ambiguo('Preço negado não informa um preço alternativo confirmado.')
    return updates, refs


def _eventos(texto, possui_updates):
    low = texto.casefold()
    # Menções negadas não são instruções para abrir uma hipótese. Rejeitamos
    # ordens negadas de confirmar/corrigir em vez de inverter sua polaridade.
    if re.search(r'\b(?:não|nunca)\s+(?:(?:vou|quero|estou)\s+)?(?:confirm\w*|corrij\w*|corrig\w*)', low):
        raise Ambiguo('Ação de confirmação/correção negada.')
    if re.search(r'\b(?:não|nunca)\s+(?:esqueça|desconsidere|abandone|encerre|cancele|ignore|volte|retome)\b', low):
        raise Ambiguo('Ação de abandono/retorno negada.')
    neg_confirm = bool(re.search(r'\b(?:não|nunca)\s+(?:(?:foi|se|realmente)\s+){0,2}(?:confirm\w*|acontec\w*|ocorr\w*|concretiz\w*)', low))
    ret = bool(re.search(r'\b(?:esqueça|desconsidere|abandone|encerre|cancele|ignore|deixe\s+de\s+lado)\b.{0,70}\b(?:simula\w*|hipótese|alternativa|imagin\w*|fict\w*|cenário)', low)
               or re.search(r'\b(?:volte|retome|use|considere)\b.{0,50}\b(?:fatos|preços\s+reais|objetos\s+reais|caso\s+real|inventário\s+factual)', low))
    con = not neg_confirm and bool(
        re.search(r'\bconfirmo\s+(?:como\s+)?reais\b', low)
        or re.search(r'\b(?:hipótese|simulação|cenário|situação|possibilidade)\b.{0,90}\b(?:aconteceu\s+de\s+verdade|ocorreu\s+(?:realmente|de\s+verdade)|foi\s+(?:confirmad\w*|comprovad\w*|verificad\w*)|passou\s+a\s+ser\s+real|é\s+fato)', low)
        or re.search(r'\b(?:realmente\s+ocorreu|se\s+concretizou)\b', low))
    semantic = re.sub(r'\bfora\s+da\s+hipótese\b', '', low)
    semantic = re.sub(r'\b(?:não|nunca)\s+(?:(?:é|era|foi|seria|estou|estamos|se|trata|de|uma|um|o|a|apenas|propondo|dizendo|afirmando)\s+){0,6}(?:hipótese|imagin\w*|simula\w*|suposição|possibilidade)\b', '', semantic)
    hip = bool(re.search(r'\b(?:imagine|suponha|faça\s+de\s+conta|hipótese|simulação|suposição|possibilidade|hipotétic\w*|imaginári\w*|fictíci\w*)\b', semantic))
    cor = bool(re.search(r'\b(?:corrij\w*|corrig\w*|correção|retific\w*|me\s+enganei|fora\s+da\s+hipótese|na\s+verdade|na\s+realidade|de\s+fato|factual|acabei\s+de\s+conferir)\b', low)
               or re.search(r'\b(?:valor|custo|preço|cobrança|registro|dado)\s+(?:real|certo|correto)\b', low)
               or re.search(r'\bmude\b.{0,55}\b(?:real|fatos)\b', low))
    # Cancelar ou confirmar menciona a hipótese, mas não abre outra. Combiná-lo
    # a uma nova ordem de imaginar, ou a valores novos, exige interpretação maior.
    nova_ordem = bool(re.search(r'\b(?:imagine|suponha|faça\s+de\s+conta)\b', semantic))
    if con or ret:
        if (con and ret) or nova_ordem or possui_updates:
            raise Ambiguo('Mais de uma transição ou dados novos junto de confirmação/retorno.')
        return 'confirmacao' if con else 'retorno'
    if re.search(r'\b(?:confirme|confirmar|confirmando)\b', low):
        raise Ambiguo('Pedido de confirmar sem promoção explícita da alternativa a fato.')
    if hip and cor:
        raise Ambiguo('A mesma fala mistura atualização factual e hipótese.')
    if neg_confirm and not (nova_ordem or (possui_updates and hip)):
        raise Ambiguo('A hipótese foi negada sem retorno inequívoco aos fatos.')
    if hip:
        if not possui_updates and not nova_ordem:
            if re.search(r'\b(?:mantenha|continue|retome)\b', low): return 'consulta'
            raise Ambiguo('Mencionar uma hipótese não instrui abertura de um novo cenário.')
        return 'hipotese'
    if cor:
        if not possui_updates: raise Ambiguo('Correção sem novo dado literal inequívoco.')
        return 'correcao'
    return 'declaracao' if possui_updates else 'consulta'


@dataclass
class Banco:
    precos: dict = field(default_factory=dict)
    posses: dict = field(default_factory=dict)
    regra: object = None

    def atualizar(self, updates):
        self.precos.update(updates['precos']); self.posses.update(updates['posses'])
        if updates['regra'] is not None: self.regra = updates['regra']


def _consulta(texto, op, banco):
    # Só uma consulta explícita na última fala. Entidade inexistente, pronome e
    # seleção implícita não recebem resolução inventada a partir dos ponteiros.
    frases = [x.strip() for x in re.split(r'[.!?\n]', texto) if x.strip()]
    pares = []
    pairs = [_rx(p) for p in [
        rf'\bcompare\s+(?:(?:os\s+)?(?:preços|custos|gastos)\s+(?:de\s+)?)?(?P<a>{PALAVRA})\s+e\s+(?P<b>{PALAVRA})\b',
        rf'\bentre\s+(?P<a>{PALAVRA})\s+e\s+(?P<b>{PALAVRA})\b',
        rf'\bqual\s+custa\s+menos\s*:\s*(?P<a>{PALAVRA})\s+ou\s+(?P<b>{PALAVRA})\b',
        rf'\b(?:preços|custos|gastos)\s+de\s+(?P<a>{PALAVRA})\s+e\s+(?P<b>{PALAVRA})\b',
    ]]
    pessoas = []
    for frase in frases:
        if re.search(r'\b(?:compare|diferença|menor|preços|custos|gastos|separa)\b', frase, FLAGS):
            found = []
            for pat in pairs:
                for m in pat.finditer(frase):
                    if _nome(m['a']) and _nome(m['b']): found.append((m['a'].casefold(), m['b'].casefold()))
            if found:
                if len(set(found)) != 1: raise Ambiguo('Mais de um par na consulta.')
                pares.append(found[0])
        # Declarações de regra/inventário também mencionam entrada: exigimos
        # verbo de consulta e exatamente um nome explícito em sua própria frase.
        if (re.search(r'\b(?:cumpre|atende|satisfaz|pode|permite|confira|verifique|consegue)\b', frase, FLAGS)
                and re.search(r'\b(?:requisitos|regra|entrada|entrar|entre|condições|acesso|ingressar)\b', frase, FLAGS)):
            ns = [m[0].casefold() for m in re.finditer(PALAVRA, frase) if _nome(m[0])]
            ns = list(dict.fromkeys(ns))
            if len(ns) != 1: raise Ambiguo('Consulta de requisitos sem uma única pessoa explícita.')
            pessoas.append(ns[0])
    if op == 'comparar_custos':
        if pessoas or len(pares) != 1: raise Ambiguo('Consulta de custos ausente ou misturada.')
        a, b = pares[0]
        if a == b or a not in banco.precos or b not in banco.precos:
            raise Ambiguo('Os dois preços da consulta não estão declarados no banco ativo.')
        return [banco.precos[a], banco.precos[b], None], None
    if pares or len(pessoas) != 1: raise Ambiguo('Consulta de requisitos ausente ou misturada.')
    n = pessoas[0]
    if n not in banco.posses or banco.regra is None:
        raise Ambiguo('Regra ou inventário da pessoa consultada não declarado.')
    return [banco.regra, banco.posses[n], None], n


def aplicar(turnos, proposta_neural):
    """Retorna (proposta, diagnóstico); a abstenção retorna o MESMO objeto neural.

    Inventários são retratos declarados completos da informação, com mundo
    aberto: itens não mencionados são desconhecidos. Não interpreta adição/
    retirada incremental, pronomes, múltiplas regras ou cenários nomeados.
    """
    diag = {'aplicado': False, 'metodo': 'memoria_explicita', 'eventos': []}
    try:
        if not isinstance(proposta_neural, dict): raise Ambiguo('Proposta neural não é um objeto.')
        op = proposta_neural.get('operacao')
        if op not in ('comparar_custos', 'verificar_requisitos'):
            raise Ambiguo('Operação fora da gramática de memória explícita.')
        if not isinstance(turnos, (list, tuple)) or not turnos or any(not isinstance(t, str) or not t.strip() for t in turnos):
            raise Ambiguo('A entrada precisa ser uma sequência de falas brutas não vazias.')
        real = Banco(); alt = None; refs = {}; confirmations = []
        for t, texto in enumerate(turnos):
            if re.search(r'\b(?:adicion\w*|retir\w*|perdeu|ganhou|mais\s+um|também\s+tem|outro\s+cenário\s+chamado)\b', texto, FLAGS):
                raise Ambiguo('Atualização incremental ou cenário nomeado fora do contrato.')
            updates, found_refs = _extrair(texto, t)
            has = bool(updates['precos'] or updates['posses'] or updates['regra'])
            event = _eventos(texto, has)
            for sp in list(updates['precos'].values()) + list(updates['posses'].values()) + ([updates['regra']] if updates['regra'] else []):
                following = re.search(r'[.!?;\n]', texto[sp['fim']:])
                if following and following[0] == '?' and event != 'hipotese':
                    raise Ambiguo('Uma pergunta sobre um dado não é declaração factual desse dado.')
            diag['eventos'].append({'turno': t, 'evento': event})
            for n, sp in found_refs.items(): refs.setdefault(n, sp)
            if len(refs) > 8: raise Ambiguo('Mais de oito entidades declaradas.')
            if event == 'hipotese':
                alt = deepcopy(real); alt.atualizar(updates)
            elif event == 'correcao':
                real.atualizar(updates); alt = None
            elif event == 'confirmacao':
                if alt is None: raise Ambiguo('Confirmação sem uma alternativa ativa única.')
                real = deepcopy(alt); alt = None; confirmations.append(t)
            elif event == 'retorno': alt = None
            elif event == 'declaracao':
                if alt is not None: raise Ambiguo('Dado novo sem escopo explícito durante uma hipótese.')
                for field in ['precos', 'posses']:
                    for n, sp in updates[field].items():
                        prior = getattr(real, field).get(n)
                        if prior and prior['texto'] != sp['texto']:
                            raise Ambiguo('Mudança de um dado conhecido sem correção explícita.')
                if real.regra and updates['regra'] and real.regra['texto'] != updates['regra']['texto']:
                    raise Ambiguo('Troca de regra sem correção explícita.')
                real.atualizar(updates)
        banco = alt if alt is not None else real
        args, person = _consulta(turnos[-1], op, banco)
        ref = refs.get(person) if person is not None else None
        if person is not None and ref is None: raise Ambiguo('Pessoa sem fonte literal de declaração.')
        for sp in args + [ref]:
            if sp and turnos[sp['turno']][sp['inicio']:sp['fim']] != sp['texto']:
                raise Ambiguo('Fonte literal não corresponde à fala original.')
        final = deepcopy(proposta_neural)
        final.update(argumentos=deepcopy(args), referente=deepcopy(ref), hipotese=alt is not None,
                     fontes=sorted({s['turno'] for s in args + [ref] if s}),
                     decodificacao='memoria_explicita_input_only',
                     limite='Gramática e estado determinísticos próprios, com execução fechada; não aprendizado neural nem conversa livre. Inventário declarado substitui o retrato anterior; itens ausentes são desconhecidos.')
        diag.update(aplicado=True, motivo='Consulta explícita com fontes literais e transições não ambíguas.',
                    banco='alternativo' if alt is not None else 'factual', confirmacoes=confirmations,
                    fontes=final['fontes'])
        return final, diag
    except Ambiguo as exc:
        diag['motivo'] = str(exc)
        return proposta_neural, diag
