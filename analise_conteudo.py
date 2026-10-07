"""Análise extrativa de conteúdo do usuário, sem consultar o acervo.

Offsets e citações referem-se sempre ao documento original. Recorrência
lexical não é interpretação semântica; conectores não comprovam causalidade.
"""
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

LIMITE_CONTEUDO = 12000
IGNORAR = set("a o as os um uma uns umas de do da dos das e ou em no na nos nas por para com sem que se eu tu ele ela eles elas voce voces nos meu minha seu sua seus suas isso isto esse essa este esta ao aos pelo pela mais muito muito pouco como sobre entre porque mas portanto assim tambem ainda ja nao nem sao foi ser tem era ha neste nesta desse dessa texto ideia ideias conteudo".split())


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.casefold())
                   if unicodedata.category(c) != 'Mn')


@dataclass(frozen=True)
class Pedido:
    modo: str
    fonte: object = None
    quantidade: int = 3
    explicito: bool = False


def pedido(texto):
    if not isinstance(texto, str):
        return None
    t = texto.strip()
    # O cabeçalho é separado do documento antes de reconhecer a intenção.
    corte = re.search(r':|\n', t)
    if corte is None:
        citado = re.search(r'["“](.+)["”]\s*$', t, re.S)
        if citado:
            return pedido(t[:citado.start()] + ': ' + citado.group(1))
    cab = t[:corte.start()] if corte else t
    fonte = t[corte.end():].strip() if corte else None
    if len(cab) > 200:
        return None
    n = normalizar(cab).strip(' .!?')
    n = re.sub(r'^(?:por favor[, ]+|voce pode |pode |me )', '', n)
    if re.search(r'\brelato\b', n) and not re.search(r'\b(?:texto|conteudo|sequencia)\b', n):
        return None  # Relatos pessoais conservam a operação de conversa.
    if n in ('mais curto', 'mais curta') or re.match(r'^(?:resuma|resumir|faca um resumo|resume)\b', n):
        modo = 'resumo'
    elif re.match(r'^(?:analise|analisar|faca uma analise)\b', n):
        modo = 'analise'
    elif n in ('padroes', 'e os padroes') or re.match(r'^(?:identifique|encontre|mostre|quais sao|extraia)\b', n) and re.search(r'\bpadroes\b', n):
        modo = 'padroes'
    elif re.match(r'^(?:identifique|extraia|liste|mostre|quais sao)\b', n) and re.search(r'ideias (?:centrais|principais)|pontos principais', n):
        modo = 'ideias'
    elif n in ('texto', 'conteudo', 'sequencia de ideias') and corte:
        modo = 'recebido'
    elif n in ('qual a fonte', 'qual e a fonte', 'mostre as evidencias', 'evidencias'):
        modo = 'evidencias'
    else:
        return None
    if modo == 'resumo' and 'padroes' in n:
        modo = 'analise'
    # Citação também serve como entrada, sem exigir dois-pontos.
    if corte is None:
        citado = re.search(r'["“](.+)["”]\s*$', t, re.S)
        if citado:
            return pedido(t[:citado.start()] + ': ' + citado.group(1))
    qtd = re.search(r'\b([1-8]) (?:frases?|ideias?|pontos?)\b', n)
    explicito = bool(corte or re.search(r'\b(?:texto|conteudo|sequencia|enviado|enviei)\b', n))
    if not corte and modo in ('resumo', 'analise') and not explicito and not qtd and n not in (
            'resuma', 'resume', 'resumir', 'mais curto', 'mais curta', 'resuma isso', 'faca um resumo', 'analise', 'analise isso'):
        return None
    return Pedido(modo, fonte, int(qtd.group(1)) if qtd else 3,
                  explicito)


def unidades(fonte):
    limites = [0] + [m.end() for m in re.finditer(r'\n+|(?<=[.!?])\s+', fonte)] + [len(fonte)]
    saida = []
    for a, b in zip(limites, limites[1:]):
        trecho = fonte[a:b]
        # Numeração e marcadores da lista não pertencem à afirmação.
        inicio = re.match(r'\s*(?:(?:[-*•]|\d+[.)])\s+)?', trecho).end()
        fim = len(trecho.rstrip())
        if inicio < fim:
            if re.fullmatch(r'\d+[.)]', trecho[inicio:fim]):
                continue
            saida.append({'id': len(saida) + 1, 'inicio': a + inicio,
                          'fim': a + fim, 'texto': trecho[inicio:fim]})
    return saida


def termos(t):
    return set(w for w in re.findall(r'\b[^\W\d_]{3,}\b', normalizar(t)) if w not in IGNORAR)


def selecionar(us, quantidade):
    palavras = [termos(u['texto']) for u in us]
    frequencias = Counter(w for ws in palavras for w in ws)
    escolhidos = []
    for _ in range(min(quantidade, len(us))):
        def pontuar(i):
            ws = palavras[i]
            score = sum(math.log1p(frequencias[w]) for w in ws) / math.sqrt(max(1, len(ws)))
            redundancia = max((len(ws & palavras[j]) / max(1, len(ws | palavras[j]))
                              for j in escolhidos), default=0)
            return score * (1 - .85 * redundancia), -i
        textos = {normalizar(us[j]['texto']) for j in escolhidos}
        candidatos = [i for i in range(len(us)) if normalizar(us[i]['texto']) not in textos]
        if not candidatos:
            break
        escolhidos.append(max(candidatos, key=pontuar))
    protegidos = set()
    for a, b in oposicoes(us):
        if a - 1 in escolhidos or b - 1 in escolhidos:
            protegidos.update((a - 1, b - 1))
    for i in sorted(protegidos):
        if i not in escolhidos:
            escolhidos.append(i)
    while len(escolhidos) > quantidade and any(i not in protegidos for i in escolhidos):
        escolhidos.remove(next(i for i in reversed(escolhidos) if i not in protegidos))
    return [us[i] for i in sorted(escolhidos)]


def oposicoes(us):
    afirmacoes, pares = {}, []
    for u in us:
        n = normalizar(u['texto']).strip(' .!?')
        negacao = bool(re.search(r'\bnao\b', n))
        chave = re.sub(r'\s+', ' ', re.sub(r'\bnao\s+', '', n)).strip()
        anterior = afirmacoes.get(chave)
        if anterior and anterior[0] != negacao:
            pares.append((anterior[1], u['id']))
        afirmacoes[chave] = (negacao, u['id'])
    return pares


def padroes(us):
    resultados = []
    indices = {}
    for u in us:
        for w in termos(u['texto']):
            indices.setdefault(w, []).append(u['id'])
    for w, refs in sorted(indices.items(), key=lambda p: (-len(p[1]), p[0])):
        if len(refs) >= 2:
            resultados.append({'tipo': 'recorrencia_lexical', 'descricao': 'O termo «%s» reaparece em %d unidades.' % (w, len(refs)),
                               'evidencias': refs, 'estatuto': 'observacao'})
        if len(resultados) >= 5:
            break
    conectores = (('contraste', r'\b(?:mas|porem|entretanto|embora)\b'),
                  ('causa_apresentada', r'\b(?:porque|por isso|devido a)\b'),
                  ('condicao', r'^(?:se|caso)\b|\bdesde que\b'),
                  ('ordem_explicita', r'\b(?:primeiro|depois|em seguida|por fim)\b'),
                  ('conclusao_apresentada', r'\b(?:portanto|assim sendo)\b|^logo,'))
    for tipo, regex in conectores:
        for i, u in enumerate(us):
            m = re.search(regex, normalizar(u['texto']))
            if m:
                refs = [u['id']]
                if i and m.start() == 0:
                    refs.insert(0, us[i - 1]['id'])
                resultados.append({'tipo': tipo, 'descricao': 'O conector «%s» marca %s no texto.' % (m.group(), tipo.replace('_', ' ')),
                                   'evidencias': refs, 'estatuto': 'observacao'})
                break
    for a, b in oposicoes(us):
        resultados.insert(0, {'tipo': 'oposicao_literal', 'descricao': 'Há afirmações literalmente opostas. Podem depender de condições não explicitadas; isso exige confirmação.',
                             'evidencias': [a, b], 'estatuto': 'hipotese'})
    return resultados[:12]


class AnaliseConteudo:
    def __init__(self):
        self.fonte = None
        self.ultima = None

    def responder(self, texto):
        self.ultima = None
        p = pedido(texto)
        if p is None:
            self.fonte = None
            return None
        if p.fonte is not None:
            if not p.fonte or len(p.fonte) > LIMITE_CONTEUDO:
                self.fonte = None
                return 'texto:conteudo_invalido', 'Envie um conteúdo não vazio, com até 12 mil caracteres.'
            us = unidades(p.fonte)
            if len(us) > 200:
                self.fonte = None
                return 'texto:conteudo_invalido', 'Divida o conteúdo em partes com até 200 frases ou itens.'
            self.fonte = p.fonte
        elif self.fonte is None:
            if not p.explicito:
                return None  # Resumo do acervo permanece no compositor.
            return 'texto:pedir_conteudo', 'Cole o conteúdo depois de «Resuma este texto:» ou «Analise este conteúdo:».'
        us = unidades(self.fonte)
        if not us:
            return 'texto:conteudo_invalido', 'Não encontrei frases ou itens no conteúdo enviado.'
        qtd = min(p.quantidade, max(1, len(us) - 1)) if p.modo == 'resumo' else p.quantidade
        selecionadas = selecionar(us, qtd)
        ps = padroes(us) if p.modo in ('padroes', 'analise') else []
        refs = ([u['id'] for u in us] if p.modo == 'evidencias' else
                sorted(set([u['id'] for u in selecionadas] + [i for item in ps for i in item['evidencias']])))
        self.ultima = {'origem': 'conteudo_enviado', 'metodo': 'extrativo', 'modo': p.modo,
                       'conteudo': self.fonte,
                       'unidades': len(us), 'selecionadas': [u['id'] for u in selecionadas],
                       'padroes': ps, 'evidencias': [u for u in us if u['id'] in refs],
                       'limites': 'Recorrência lexical e conectores não comprovam relações semânticas ou causalidade.'}
        cita = lambda u: '[%d] %s' % (u['id'], u['texto'])
        if p.modo == 'recebido':
            return 'texto:conteudo_recebido', 'Conteúdo recebido (%d unidades). Você pode pedir um resumo, ideias centrais ou padrões.' % len(us)
        if p.modo == 'evidencias':
            resposta = 'Fonte: conteúdo enviado por você.\n\n' + '\n'.join(cita(u) for u in us)
        elif p.modo in ('resumo', 'ideias'):
            resposta = ('Resumo extrativo' if p.modo == 'resumo' else 'Ideias centrais — trechos selecionados') + ':\n' + '\n'.join('- ' + cita(u) for u in selecionadas)
            if oposicoes(us):
                resposta += '\n\nO conteúdo contém afirmações opostas. Conservo ambos os lados quando selecionados, mesmo que isso exceda o número de frases pedido.'
        else:
            partes = []
            if p.modo == 'analise':
                partes.append('Ideias centrais — trechos selecionados:\n' + '\n'.join('- ' + cita(u) for u in selecionadas))
            partes.append('Padrões observados:\n' + ('\n'.join('- ' + item['descricao'] + ' ' + ' '.join('[%d]' % i for i in item['evidencias']) for item in ps)
                                                   if ps else 'Não encontrei recorrências lexicais ou conectores suficientes para apontar um padrão.'))
            partes.append('Trechos de apoio:\n' + '\n'.join(cita(u) for u in us if u['id'] in refs))
            partes.append(self.ultima['limites'])
            resposta = '\n\n'.join(partes)
        return 'texto:' + p.modo, resposta
