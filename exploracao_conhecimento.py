"""Propõe investigações a partir de unidades do acervo, com rastros e fontes.

Uma ligação editorial e uma coincidência lexical recebem tratamentos distintos.
A seleção recombina evidências; não inventa fatos, relações ou causalidade.
"""
import re
from collections import defaultdict

from composicao_textual import tema
from evidencias_conversa import normalizar


class ExploradorConhecimento:
    MAX_INTERVALO = 10
    MAX_IDEIAS = 12

    def __init__(self):
        self.limpar()

    def limpar(self):
        self.ids = ()
        self.usadas = set()
        self.turno = -100
        self.ultimo = None
        self._indice = None
        self._inverso = {}

    def _indexar(self, indice):
        if self._indice is indice:
            return
        inverso = defaultdict(set)
        for par, doc in indice.docs.items():
            for termo in doc:
                if len(termo) >= 5:
                    inverso[termo].add(par)
        self._indice, self._inverso = indice, dict(inverso)

    def _candidatos(self, ids, bot):
        comp, indice = bot.compositor, bot.planejador.indice
        self._indexar(indice)
        def com_fonte(par):
            return bool(indice.fontes((par,))[0]['fontes'])
        candidatos = []
        vistos = set()
        def adicionar(chave, tipo, pergunta, pares, apoio, prioridade, relacionados=(), palavras=()):
            if chave in vistos or any(not com_fonte(p) for p in pares):
                return
            vistos.add(chave)
            candidatos.append({'chave': chave, 'tipo': tipo, 'pergunta': pergunta,
                               'pares': tuple(pares), 'apoio': apoio, 'prioridade': prioridade,
                               'relacionados': tuple(relacionados), 'termos_compartilhados': list(palavras)})
        for origem in ids:
            nome = comp.itens[origem]['nome']
            for ligacao in comp.ligacoes_mundo + comp.comparacoes_mundo:
                a, b = ligacao['origem'], ligacao['destino']
                if origem not in (a, b) or len(ids) == 2 and set(ids) != {a, b}:
                    continue
                outro = b if origem == a else a
                if outro not in comp.itens:
                    continue
                par = (a, ligacao['indice_fato'])
                adicionar('ligacao:' + a + ':' + b + ':' + str(par[1]), 'ligacao_editorial',
                          'Que mecanismos, condições e limites ajudam a entender a ligação entre ' + nome + ' e ' + comp.itens[outro]['nome'] + '?',
                          (par,), 'O acervo registra uma ligação ou comparação explícita; a investigação deve respeitar seu alcance.',
                          100, (outro,))
            # Associações lexicalmente fortes sugerem uma comparação, nunca
            # um vínculo real. Dois trechos preservados sustentam a pergunta.
            associados = {}
            for i, fato in enumerate(comp.itens[origem]['fatos']):
                par = (origem, i)
                if not com_fonte(par):
                    continue
                doc = indice.docs[par]
                for palavra in doc:
                    destinos = self._inverso.get(palavra, ())
                    if not destinos or len(destinos) > 60:
                        continue
                    for outro_par in destinos:
                        outro = outro_par[0]
                        if outro == origem or len(ids) == 2 and outro not in ids or not com_fonte(outro_par):
                            continue
                        comuns = set(doc) & set(indice.docs[outro_par]) & set(self._inverso)
                        comuns = {p for p in comuns if len(self._inverso[p]) <= 60}
                        if not comuns:
                            continue
                        score = sum(indice.idf[p] for p in comuns)
                        anterior = associados.get(outro)
                        if anterior is None or score > anterior[0]:
                            associados[outro] = (score, par, outro_par, comuns)
            for outro, (score, par, outro_par, comuns) in sorted(associados.items(), key=lambda x: (-x[1][0], x[0]))[:6]:
                palavras = sorted(comuns, key=lambda p: (-indice.idf[p], p))[:3]
                chave = 'associacao:' + ':'.join(sorted((origem, outro)))
                adicionar(chave, 'associacao_lexical',
                          'Em que contextos ' + nome + ' e ' + comp.itens[outro]['nome'] + ' usam ' + ', '.join(palavras) + ', e onde a comparação deixa de valer?',
                          (par, outro_par), 'Os trechos compartilham termos. Isso sugere uma investigação, sem provar relação ou causalidade.',
                          20 + min(score, 30), (outro,), palavras)
            if len(ids) == 1:
                for i, fato in enumerate(comp.itens[origem]['fatos']):
                    papel = fato.get('papel', '')
                    aspecto = fato.get('aspecto', '')
                    tipo = 'limites' if papel == 'limite' else 'mecanismo' if aspecto in ('funcionamento', 'formacao', 'funcao') else 'verificacao'
                    pergunta = ('Sob quais condições esta explicação sobre ' + nome + ' deixa de valer?'
                                if tipo == 'limites' else 'Quais etapas e condições explicam este mecanismo de ' + nome + '?'
                                if tipo == 'mecanismo' else 'Que observação ou comparação ajudaria a verificar esta afirmação sobre ' + nome + '?')
                    adicionar('fato:' + origem + ':' + str(i), tipo, pergunta, ((origem, i),),
                              'O trecho abaixo é o ponto de partida; faltam critérios e evidências específicos para realizar a investigação.',
                              65 if tipo == 'limites' else 55 if tipo == 'mecanismo' else 10)
        return sorted(candidatos, key=lambda c: (-c['prioridade'], c['chave']))

    def preparar(self, texto, bot, turno):
        self.ultimo = None
        if not isinstance(texto, str) or len(texto) > 1200 or any(c in texto for c in ('`', '"', '“', '”')):
            return None
        n = texto.strip().strip('.?! ')
        pedido = re.fullmatch(r'(?:explore ideias sobre|explore possibilidades sobre|que ideias voc[eê] (?:prop[oõ]e|sugere) sobre)\s+(.+)', n, re.I)
        mais = normalizar(n) in ('mais ideias', 'outras ideias', 'mais possibilidades')
        if not pedido and not mais:
            return None
        if turno - self.turno > self.MAX_INTERVALO:
            self.ids, self.usadas = (), set()
        comp, indice = bot.compositor, bot.planejador.indice
        ids = self.ids
        if pedido:
            alvo = pedido.group(1)
            inteiro = comp.resolver(alvo)
            partes = [alvo] if inteiro else re.split(r'\s+e\s+', alvo, flags=re.I)
            resolvidos = [comp.resolver(p) for p in partes]
            if not 1 <= len(partes) <= 2 or any(i is None for i in resolvidos):
                ambiguos = [p for p in partes if len(comp.aliases.get(tema(p), ())) > 1]
                resposta = ('Esse nome tem mais de um significado no acervo. Especifique qual conceito quer explorar.'
                            if ambiguos else 'Indique um ou dois conceitos inteiros do acervo, por exemplo: “Explore ideias sobre sono”.')
                self.ultimo = {'status': 'nao_resolvido', 'propostas': [], 'comprovado_no_mundo': False}
                return 'exploracao:esclarecer', resposta, None, ''
            ids = tuple(dict.fromkeys(resolvidos))
            # Pedir explicitamente um tema novamente reinicia a seleção.
            self.ids, self.usadas = ids, set()
        if not ids:
            self.ultimo = {'status': 'sem_tema', 'propostas': [], 'comprovado_no_mundo': False}
            return 'exploracao:esclarecer', 'Sobre qual conceito do acervo você quer explorar ideias?', None, ''
        selecionadas, tipos, outros = [], set(), set()
        candidatos = self._candidatos(ids, bot)
        disponiveis = [c for c in candidatos if c['chave'] not in self.usadas]
        limite = min(3, self.MAX_IDEIAS - len(self.usadas))
        # Primeira passagem favorece perguntas de naturezas diferentes e
        # conceitos diferentes; depois completa sem repetir uma proposta.
        for diversificar in (True, False):
            for c in disponiveis:
                if len(selecionadas) >= limite:
                    break
                if c in selecionadas or diversificar and (c['tipo'] in tipos or set(c['relacionados']) & outros):
                    continue
                selecionadas.append(c)
                tipos.add(c['tipo'])
                outros.update(c['relacionados'])
        self.turno = turno
        propostas, pares, blocos = [], [], []
        for i, c in enumerate(selecionadas, 1):
            evidencias = indice.fontes(c['pares'])
            proposta = {k: c[k] for k in ('chave', 'tipo', 'pergunta', 'apoio', 'termos_compartilhados')}
            proposta.update(evidencias=evidencias, comprovada_no_mundo=False,
                            verificacao='Definir condições, procurar contraexemplos e confrontar as fontes; a proposta ainda não foi testada.')
            propostas.append(proposta)
            pares.extend(c['pares'])
            blocos.append(str(i) + '. ' + c['pergunta'] + '\n' + c['apoio'] + '\n' +
                          '\n'.join('Base (' + comp.itens[e['assunto']]['nome'] + '): ' + e['texto'] for e in evidencias))
            self.usadas.add(c['chave'])
        resposta = ('Ideias de investigação a partir do acervo, ainda não verificadas:\n\n' + '\n\n'.join(blocos) +
                    '\n\nPara avaliar cada ideia, defina as condições e procure também o que a contrariaria. Você pode pedir “Quais fontes?” ou “Mais ideias”.'
                    if propostas else 'Não encontrei novas ideias com fontes para esses conceitos dentro do limite desta exploração. Escolha outro tema ou forneça premissas explícitas para testar uma hipótese.')
        pares = tuple(dict.fromkeys(pares))
        contexto = indice.contexto(ids, pares, resposta) if pares else None
        self.ultimo = {'status': 'propostas' if propostas else 'esgotado', 'temas': list(ids),
                       'origem': 'acervo_ativo', 'comprovado_no_mundo': False,
                       'propostas': propostas, 'total_exibido': len(self.usadas)}
        return 'exploracao:ideias' if propostas else 'exploracao:fim', resposta, contexto, ''
