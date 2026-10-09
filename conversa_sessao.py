"""Atos pessoais limitados sobre a memória existente, sem coletar declarações.

Seleção e sugestões são estruturais. O Transformer próprio realiza os fatos
selecionados. Não aprende preferências com suas próprias respostas.
"""
import re

from composicao_textual import normalizar


def ato(texto):
    """Operadores explícitos; texto desconhecido conserva as outras rotas."""
    n = normalizar(texto)
    if re.search(r'\b(?:historia|poema|codigo|python|javascript|dna|fonte|fontes|formula|algoritmo|'
                 r'escrev\w*|escrever|crie|invente|mensagem|conto|personagem|simule|traduza|corrija)\b', n):
        return None
    if re.search(r'\b(?:falta (?:saber|perguntar|descobrir)|precisa saber|preciso informar|ainda falta|'
                 r'informacoes precisamos|dados.*faltando|o que ja sabemos)\b', n):
        return 'perguntar'
    if re.search(r'\b(?:onde|localizacao|de quem|preferencia de quem|limites?|restricao|'
                 r'quanto tempo|gosto verdadeiro|preferencia real)\b', n) or re.match(
                     r'^(?:e )?o que (?:eu )?(?:disse|contei)\b', n):
        return 'consultar'
    if re.search(r'\b(?:por que|motivo|justificar|justifico|explico|explicar|razao)\b', n):
        return 'explicar'
    if re.search(r'\b(?:resum\w*|resumo|junt\w*|reun\w*|descrev\w*|descrever|condens\w*|'
                 r'uma frase|reformul\w*)\b', n):
        return 'resumir'
    if re.search(r'\b(?:sugir\w*|suger\w*|sugest\w*|recomend\w*|escolh\w*|opcao|'
                 r'oferec\w*|levar|proximo passo|gosto real)\b', n):
        return 'sugerir'
    return None


def responder(texto, bot):
    if (not isinstance(texto, str) or not texto.strip() or len(texto) > 1200
            or bot.dialogo_situado.ficcao or any(c in texto for c in ('`', '"', '“', '”'))):
        return None
    n = normalizar(texto)
    if re.search(r'\b(?:se|caso|suponha|imagine|hipoteticamente)\b', n):
        return None
    acao = ato(texto)
    if acao is None:
        return None
    memoria = bot.memoria_sessao
    anterior = bot.historico[-1].get('conversa_sessao', {}) if bot.historico else {}
    pessoas = [e for e in memoria.entidades.values()
               if e['tipo'] == 'pessoa' and e['id'] != 'pessoa:usuario']
    informar = re.search(r'\b(?:precisa saber|preciso informar)\b', n)
    sujeitos = [e['id'] for e in pessoas if re.search(
        r'(?<!\w)' + re.escape(normalizar(e['nome'])) + r'(?!\w)', n)]
    pr = re.search(r'\b(ele|ela|dele|dela)\b', n)
    nominal = re.search(r'\b(?:para|de|visitar|que)\s+[A-ZÀ-Ý][\wÀ-ÿ-]+', texto)
    # Uma menção factual não basta: é preciso um referente pessoal ou uma
    # continuação imediata. Não toma as conversas antigas sobre o usuário.
    if not (sujeitos or pr or anterior or informar or nominal):
        return None
    if not (sujeitos or pr or anterior or informar):
        factual = bot.compositor.responder(texto, None)
        if factual is not None and factual[0] != 'fora':
            return None
    quadro = dict(acao=acao, afirmacoes=[], sujeitos=[],
                  selecao='estrutural', redacao_do_ato='estrutural')

    def emitir(resposta, fatos=(), sujeitos=()):
        quadro.update(afirmacoes=[f['id'] for f in fatos], sujeitos=list(sujeitos))
        return ('conversa:sessao_' + acao, resposta), quadro

    if not sujeitos:
        if pr:
            p = memoria._pessoa(pr[1])
            sujeitos = [p] if p else []
            if not p:
                return emitir('De qual pessoa você está falando? Preciso esclarecer o referente.')
        elif anterior and not nominal:
            sujeitos = [s for s in anterior.get('sujeitos', [])
                        if memoria.entidades.get(s, {}).get('tipo') == 'pessoa']
    if len(sujeitos) > 1:
        return emitir('Qual pessoa você quer considerar nesta escolha?')
    if not sujeitos:
        return emitir('Você não informou de quem se trata ou esse dado não está disponível. '
                      'Preciso saber as preferências, o objetivo da escolha e quais limites devemos respeitar.')
    p = sujeitos[0]
    objetos = [e['id'] for e in memoria.entidades.values() if e.get('dono') == p
               and re.search(r'(?<!\w)' + re.escape(normalizar(e['nome'])) + r'(?!\w)', n)]
    objetos_anteriores = [s for s in anterior.get('sujeitos', [])
                         if memoria.entidades.get(s, {}).get('dono') == p]
    alvos = objetos or objetos_anteriores or [p]
    fatos = [f for f in memoria.afirmacoes if f['status'] == 'ativo'
             and f['sujeito'] in alvos and f['relacao'] != 'vínculo']
    if acao in ('sugerir', 'explicar'):
        preferencias = [f for f in fatos if f['relacao'].startswith('preferência')]
        limites = [f for f in fatos if f['relacao'] == 'tempo disponível' or f['relacao'].startswith('permissão:')]
        fatos = preferencias + limites if preferencias else [f for f in fatos if f['relacao'] == 'objetivo'] + limites
    elif acao == 'consultar':
        if re.search(r'\b(?:onde|localizacao|achar|encontro|procurar)\b', n):
            fatos = [f for f in fatos if f['relacao'] == 'localização']
        elif re.search(r'\b(?:limite|restricao|tempo|limites)\b', n):
            fatos = [f for f in fatos if f['relacao'] == 'tempo disponível' or f['relacao'].startswith('permissão:')]
        else:
            fatos = [f for f in fatos if f['relacao'].startswith('preferência')]
    if not fatos:
        return emitir('Não sei esse dado: você não informou isso na sessão. '
                      'Qual preferência, objetivo ou localização devemos considerar para '
                      + memoria.entidades[p]['nome'] + '?', sujeitos=[p] + objetos)
    if len(fatos) > 4:
        return emitir('Há mais de quatro informações ativas. Qual aspecto você quer discutir primeiro?', sujeitos=[p])
    base = 'Segundo o que você contou, ' + '; '.join(memoria._frase(f) for f in fatos) + '.'
    resultado = base
    if acao == 'sugerir':
        pref = next((f for f in fatos if f['relacao'].startswith('preferência')), None)
        negadas = [f for f in fatos if f['relacao'].startswith('permissão:')
                   and re.search(r'\bnao\b', normalizar(f['valor']))]
        if negadas:
            resultado += ' Antes de escolher uma opção, precisamos conferir se ela respeita essa restrição. '
            resultado += 'Como essa restrição se aplica à escolha?'
        elif pref:
            resultado += ' Uma opção é oferecer ' + pref['valor'] + ', porque corresponde à preferência relatada. '
            resultado += 'Você quer levar isso ou precisa considerar alguma restrição?'
        elif any(f['relacao'] == 'objetivo' for f in fatos):
            resultado += ' Como próximo passo, escolha uma parte pequena desse objetivo que caiba no tempo '
            resultado += 'disponível, respeitando as restrições informadas. Qual parte você consegue começar?'
        else:
            resultado += 'Qual objetivo devemos considerar antes de sugerir um próximo passo?'
    elif acao == 'explicar':
        if any(f['relacao'].startswith('preferência') for f in fatos):
            resultado += ' Essa é a razão da escolha: usar a preferência que você relatou, sem supor um gosto diferente.'
        else:
            resultado += ' A razão é usar o objetivo e os limites informados para escolher um passo pequeno, '
            resultado += 'sem inventar condições que você não contou.'
    elif acao == 'perguntar':
        resultado += ' Ainda falta perguntar qual parte precisa de ajuda e quais materiais ou condições estão disponíveis.'
    quadro['complemento'] = resultado[len(base):]
    return emitir(resultado, fatos, [p] + objetos)


def realizar(texto, bot, resposta):
    from realizacao_memoria import realizar_fatos
    quadro = bot.historico[-1].get('conversa_sessao', {}) if bot.historico else {}
    escrita, trace = realizar_fatos(texto, bot.memoria_sessao, quadro.get('afirmacoes', []))
    trace.update(ato=quadro.get('acao'), selecao='estrutural', redacao_do_ato='estrutural')
    if escrita:
        resposta = escrita + quadro.get('complemento', '')
    return resposta, trace
