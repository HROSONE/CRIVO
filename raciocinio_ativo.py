"""Lógica proposicional própria, limitada e explicável, sob premissas da sessão.

Enumera mundos compatíveis com fatos, negações e implicações. A hipótese não
altera o acervo. Uma base inconsistente nunca autoriza concluir qualquer coisa.
Abdução encontra suposições suficientes; contrafactuais usam uma cópia da base.
"""
import itertools
import re
import unicodedata
from typing import NamedTuple


def normalizar(texto):
    n = unicodedata.normalize('NFD', texto.casefold())
    return ' '.join(''.join(c for c in n if unicodedata.category(c) != 'Mn').split())


class Literal(NamedTuple):
    nome: str
    negativo: bool
    rotulo: str

    def oposto(self):
        return self._replace(negativo=not self.negativo)

    def texto(self):
        return 'não é verdade que ' + self.rotulo if self.negativo else self.rotulo

    def dados(self):
        return {'nome': self.nome, 'negativo': self.negativo, 'texto': self.texto()}


class Premissa(NamedTuple):
    antecedentes: tuple
    consequente: Literal
    operador: str
    texto: str


class LimiteRaciocinio(ValueError):
    pass


def ler_literal(texto):
    texto = ' '.join(texto.strip().strip('.?! ').split())
    n = normalizar(texto)
    if n.startswith('nao e verdade que '):
        resto = texto[len('não é verdade que '):] if texto.casefold().startswith('não é verdade que ') else texto[len('nao e verdade que '):]
        l = ler_literal(resto)
        if l.negativo:
            raise ValueError('A dupla negação precisa ser reformulada.')
        return l.oposto()
    if (not 1 <= len(texto) <= 80 or not re.fullmatch(r'[\wÀ-ÿ -]+', texto)
            or len(n.split()) > 10 or re.search(r'\b(?:se|entao|ou|e|mas|talvez|geralmente|todo|toda|algum|alguma|porque|quando|exceto|nunca)\b', n)):
        # "é" vira "e" na normalização; a cópula com acento é permitida.
        sem_copula = normalizar(re.sub(r'\bé\b', '', texto, flags=re.I))
        if (not 1 <= len(texto) <= 80 or not re.fullmatch(r'[\wÀ-ÿ -]+', texto)
                or len(n.split()) > 10 or re.search(r'\b(?:se|entao|ou|e|mas|talvez|geralmente|todo|toda|algum|alguma|porque|quando|exceto|nunca)\b', sem_copula)):
            raise ValueError('Use afirmações curtas, sem quantificadores ou condições dentro do nome.')
    negativas = re.findall(r'\b(?:não|nao)\b', texto, re.I)
    if len(negativas) > 1:
        raise ValueError('A dupla negação precisa ser reformulada.')
    rotulo = ' '.join(re.sub(r'\b(?:não|nao)\b', '', texto, flags=re.I).split())
    nome = re.sub(r'^(?:o|a|os|as|um|uma) ', '', normalizar(rotulo))
    if not nome:
        raise ValueError('Falta a afirmação.')
    return Literal(nome, bool(negativas), rotulo)


def ler_premissa(texto):
    texto = texto.strip().strip('. ')
    regra = re.fullmatch(r'se\s+(.+?)(?:,\s*|\s+)ent[aã]o\s+(.+)', texto, re.I)
    if not regra:
        return Premissa((), ler_literal(texto), 'e', texto)
    condicao, consequente = regra.groups()
    tem_e = bool(re.search(r'\s+e\s+', condicao, re.I))
    tem_ou = bool(re.search(r'\s+ou\s+', condicao, re.I))
    if tem_e and tem_ou:
        raise ValueError('Separe uma condição que mistura "e" e "ou" em regras menores.')
    antecedentes = tuple(ler_literal(p) for p in re.split(r'\s+(?:e|ou)\s+', condicao, flags=re.I))
    if len(antecedentes) > 3:
        raise LimiteRaciocinio('Cada regra aceita até três condições.')
    return Premissa(antecedentes, ler_literal(consequente), 'ou' if tem_ou else 'e', texto)


class SistemaPremissas:
    MAX_ATOMOS = 10
    MAX_PREMISSAS = 16
    MAX_VERIFICACOES = 100000

    def __init__(self, premissas):
        if len(premissas) > self.MAX_PREMISSAS:
            raise LimiteRaciocinio('Use até 16 premissas por hipótese.')
        self.premissas = tuple(premissas)
        self.nomes = {}
        for p in premissas:
            for l in p.antecedentes + (p.consequente,):
                self.nomes.setdefault(l.nome, l.rotulo)
        if len(self.nomes) > self.MAX_ATOMOS:
            raise LimiteRaciocinio('Use até dez afirmações diferentes por hipótese.')
        self.bits = {n: 1 << i for i, n in enumerate(self.nomes)}
        self.verificacoes = 0
        self.compiladas = []
        for p in premissas:
            grupos = [(l,) for l in p.antecedentes] if p.operador == 'ou' else [p.antecedentes]
            regras = []
            for grupo in grupos:
                mascara = valores = 0
                contraditorio = False
                for l in grupo:
                    bit = self.bits[l.nome]
                    valor = 0 if l.negativo else bit
                    if mascara & bit and valores & bit != valor:
                        contraditorio = True
                    mascara |= bit
                    valores |= valor
                if not contraditorio:
                    regras.append((mascara, valores, self.bits[p.consequente.nome], not p.consequente.negativo))
            self.compiladas.append(tuple(regras))
        self.cache = {}
        self.mundos = self._mundos(tuple(range(len(premissas))))

    def _mundos(self, indices):
        if indices in self.cache:
            return self.cache[indices]
        regras = [r for i in indices for r in self.compiladas[i]]
        mundos = []
        for mundo in range(1 << len(self.bits)):
            self.verificacoes += 1
            if self.verificacoes > self.MAX_VERIFICACOES:
                raise LimiteRaciocinio('A busca atingiu o orçamento; reduza as premissas.')
            if all(mundo & mascara != valores or bool(mundo & bit) == positivo
                   for mascara, valores, bit, positivo in regras):
                mundos.append(mundo)
        self.cache[indices] = mundos
        return mundos

    def verdadeiro(self, mundo, literal):
        return bool(mundo & self.bits[literal.nome]) != literal.negativo

    def _reduzir(self, predicado):
        indices = list(range(len(self.premissas)))
        for indice in tuple(indices):
            candidato = tuple(i for i in indices if i != indice)
            if predicado(self._mundos(candidato)):
                indices.remove(indice)
        return [{'indice': i, 'texto': self.premissas[i].texto} for i in indices]

    def analisar(self, alvo):
        base = {'alvo': alvo.dados(), 'mundos_compativeis': len(self.mundos)}
        if not self.mundos:
            return dict(base, status='conflito', provas=self._reduzir(lambda m: not m))
        if alvo.nome not in self.bits:
            return dict(base, status='indeterminado', provas=[], contraexemplos=[])
        sim = [m for m in self.mundos if self.verdadeiro(m, alvo)]
        if len(sim) == len(self.mundos) or not sim:
            sustentado = bool(sim)
            objetivo = alvo if sustentado else alvo.oposto()
            provas = self._reduzir(lambda mundos: bool(mundos) and all(self.verdadeiro(m, objetivo) for m in mundos))
            return dict(base, status='sustentado' if sustentado else 'refutado', provas=provas)
        nao = next(m for m in self.mundos if not self.verdadeiro(m, alvo))
        def descrever(m):
            return {self.nomes[n]: bool(m & bit) for n, bit in self.bits.items()}
        return dict(base, status='indeterminado', provas=[], contraexemplos=[descrever(sim[0]), descrever(nao)])

    def conclusoes(self):
        if not self.mundos:
            return {'status': 'conflito', 'provas': self._reduzir(lambda m: not m), 'conclusoes': []}
        dados = []
        assumidos = {(p.consequente.nome, p.consequente.negativo) for p in self.premissas if not p.antecedentes}
        for nome, rotulo in self.nomes.items():
            for negativo in (False, True):
                l = Literal(nome, negativo, rotulo)
                if (nome, negativo) not in assumidos and all(self.verdadeiro(m, l) for m in self.mundos):
                    dados.append(self.analisar(l))
        return {'status': 'consistente', 'conclusoes': dados[:6], 'mundos_compativeis': len(self.mundos)}

    def abduzir(self, alvo):
        analise = self.analisar(alvo)
        propostas = []
        if analise['status'] != 'indeterminado' or alvo.nome not in self.bits:
            return dict(analise, propostas=propostas)
        candidatos = {}
        for nome, rotulo in self.nomes.items():
            if nome == alvo.nome:
                continue
            for negativo in (False, True):
                l = Literal(nome, negativo, rotulo)
                valores = [self.verdadeiro(m, l) for m in self.mundos]
                if any(valores) and not all(valores):
                    candidatos[(nome, negativo)] = l
        mascaras = {chave: sum(1 << i for i, m in enumerate(self.mundos) if self.verdadeiro(m, l))
                    for chave, l in candidatos.items()}
        objetivo = sum(1 << i for i, m in enumerate(self.mundos) if self.verdadeiro(m, alvo))
        todos = (1 << len(self.mundos)) - 1
        escolhidos = []
        for tamanho in range(1, min(3, len(candidatos)) + 1):
            for grupo in itertools.combinations(candidatos.values(), tamanho):
                chaves = {(l.nome, l.negativo) for l in grupo}
                if any(c <= chaves for c in escolhidos) or len({l.nome for l in grupo}) != len(grupo):
                    continue
                compativeis = todos
                self.verificacoes += 1
                if self.verificacoes > self.MAX_VERIFICACOES:
                    raise LimiteRaciocinio('A busca de hipóteses atingiu o orçamento.')
                for l in grupo:
                    compativeis &= mascaras[(l.nome, l.negativo)]
                if compativeis and compativeis & ~objetivo == 0:
                    escolhidos.append(chaves)
                    propostas.append({'suposicoes': [l.dados() for l in grupo],
                                      'alvo': alvo.dados(), 'mundos_compativeis': bin(compativeis).count('1'),
                                      'comprovada_no_mundo': False})
                    if len(propostas) == 3:
                        return dict(analise, propostas=propostas)
        return dict(analise, propostas=propostas)


class RaciocinioAtivo:
    MAX_INTERVALO = 10

    def __init__(self):
        self.limpar()

    def limpar(self):
        self.premissas = ()
        self.turno = -100
        self.alvo = None
        self.ultimo = None

    @staticmethod
    def _alvo(texto):
        m = re.fullmatch(r'(?:posso concluir que|pode concluir que|podemos concluir que|conclua se|ent[aã]o[, ]+)\s*(.+)', texto, re.I)
        return ler_literal(m.group(1)) if m else None

    def _registrar(self, operacao, dados, texto, premissas=None):
        self.ultimo = dict(dados, operacao=operacao, origem='premissas_da_sessao',
                           comprovado_no_mundo=False,
                           premissas=[{'indice': i, 'texto': p.texto} for i, p in enumerate(self.premissas if premissas is None else premissas)])
        return 'raciocinio:' + operacao, texto, None, ''

    @staticmethod
    def _explicar(dados):
        estado = dados['status']
        if estado == 'conflito':
            inicio = 'As premissas entram em conflito; não vou tirar uma conclusão dessa hipótese.'
        elif estado == 'sustentado':
            inicio = 'Sim, a conclusão decorre das premissas que você pediu para assumir.'
        elif estado == 'refutado':
            inicio = 'Não: as premissas sustentam a negação dessa conclusão.'
        elif estado == 'consistente':
            inicio = 'Conclusões adicionais sustentadas pelas premissas:\n' + ('\n'.join('- ' + c['alvo']['texto'] for c in dados.get('conclusoes', [])) or 'Nenhuma conclusão adicional demonstrável.')
        else:
            inicio = 'Não é possível concluir nem negar isso com as premissas atuais.'
        provas = dados.get('provas', [])
        if provas:
            inicio += '\nPremissas usadas:\n' + '\n'.join('- ' + p['texto'] for p in provas)
        if dados.get('contraexemplos'):
            inicio += '\nHá possibilidades compatíveis em que a afirmação vale e outras em que não vale.'
        return inicio + '\nEssa análise depende das premissas; não comprova que elas sejam fatos reais.'

    def preparar(self, texto, turno):
        self.ultimo = None
        if not isinstance(texto, str) or len(texto) > 1200 or any(c in texto for c in ('`', '"', '“', '”')):
            return None
        n = texto.strip().strip('.?! ')
        if turno - self.turno > self.MAX_INTERVALO:
            self.premissas, self.alvo = (), None
        introducao = re.fullmatch(r'(?:(?:considere|suponha) (?:estas|as seguintes) premissas|vamos raciocinar|hip[oó]tese)\s*:\s*(.+)', n, re.I | re.S)
        alteracao = re.fullmatch(r'(acrescente|corrija|retire) (?:a )?premissa\s*:\s*(.+)', n, re.I)
        eh_consulta = bool(re.match(r'(?:posso concluir que|pode concluir que|podemos concluir que|conclua se|ent[aã]o[, ]+)\s*', n, re.I))
        abducao = re.fullmatch(r'(?:o que falta para concluir que|que hip[oó]tese permitiria concluir que)\s+(.+)', n, re.I)
        contrafactual = re.fullmatch(r'e se\s+(.+)', n, re.I)
        geral = normalizar(n) in ('o que voce conclui', 'o que conclui', 'quais sao as conclusoes', 'que hipoteses voce sugere')
        limpar = normalizar(n) in ('limpar hipotese', 'esqueca essas premissas')
        # Continuação vaga sem esta hipótese pertence aos outros motores,
        # inclusive ao raciocínio anterior sobre relações universais.
        if not self.premissas and (contrafactual or eh_consulta and normalizar(n).startswith('entao')):
            return None
        if not any((introducao, alteracao, eh_consulta, abducao, contrafactual, geral, limpar)):
            return None
        try:
            consulta = self._alvo(n) if eh_consulta else None
            if limpar:
                self.limpar()
                return self._registrar('limpar', {'status': 'sem_premissas'}, 'Apaguei as premissas desta hipótese.')
            if introducao:
                partes = [p.strip() for p in re.split(r';|\n', introducao.group(1)) if p.strip()]
                alvo = self._alvo(partes[-1]) if partes else None
                if alvo:
                    partes.pop()
                novas = tuple(ler_premissa(p) for p in partes)
                if not novas:
                    raise ValueError('Informe pelo menos uma premissa.')
                sistema = SistemaPremissas(novas)
                self.premissas, self.turno, self.alvo = novas, turno, alvo
                if alvo:
                    dados = sistema.analisar(alvo)
                    return self._registrar('concluir', dados, self._explicar(dados))
                dados = sistema.conclusoes()
                if dados['status'] == 'conflito':
                    resposta = self._explicar(dados)
                else:
                    resposta = 'Vou tratar essas afirmações como premissas desta hipótese.'
                    resposta += '\n' + '\n'.join('- ' + c['alvo']['texto'] for c in dados['conclusoes']) if dados['conclusoes'] else '\nAinda não há uma conclusão adicional demonstrável.'
                    resposta += '\nVocê pode perguntar o que concluo, o que falta para concluir ou testar "e se…?".'
                return self._registrar('premissas', dados, resposta)
            if not self.premissas:
                return self._registrar('concluir', {'status': 'sem_premissas'}, 'Quais premissas você quer assumir? Comece com “Considere estas premissas: …”.')
            if alteracao:
                acao, conteúdo = alteracao.groups()
                p = ler_premissa(conteúdo)
                novas = list(self.premissas)
                if acao.casefold() == 'retire':
                    def assinatura(q):
                        return (tuple((l.nome, l.negativo) for l in q.antecedentes),
                                q.consequente.nome, q.consequente.negativo, q.operador)
                    removidas = [q for q in novas if assinatura(q) == assinatura(p)]
                    if not removidas:
                        raise ValueError('Não encontrei essa premissa para retirar.')
                    novas = [q for q in novas if q not in removidas]
                elif acao.casefold() == 'corrija':
                    if p.antecedentes:
                        raise ValueError('Retire a regra antiga e acrescente a nova regra.')
                    if not any(not q.antecedentes and q.consequente.nome == p.consequente.nome for q in novas):
                        raise ValueError('Não encontrei uma afirmação assumida com esse nome para corrigir.')
                    novas = [q for q in novas if q.antecedentes or q.consequente.nome != p.consequente.nome]
                    novas.append(p)
                elif p not in novas:
                    novas.append(p)
                sistema = SistemaPremissas(novas)
                self.premissas, self.turno = tuple(novas), turno
                dados = sistema.conclusoes()
                resposta = self._explicar(dados) if dados['status'] == 'conflito' else 'Atualizei as premissas e recalculei as consequências. Qual conclusão você quer verificar?'
                return self._registrar('revisar', dados, resposta)
            sistema = SistemaPremissas(self.premissas)
            self.turno = turno
            if consulta:
                dados = sistema.analisar(consulta)
                self.alvo = consulta
                return self._registrar('concluir', dados, self._explicar(dados))
            if abducao:
                alvo = ler_literal(abducao.group(1))
                self.alvo = alvo
                dados = sistema.abduzir(alvo)
                resposta = self._explicar(dados)
                if dados['propostas']:
                    resposta += '\nHipóteses suficientes para testar, sem afirmar que sejam verdadeiras:'
                    for i, p in enumerate(dados['propostas'], 1):
                        resposta += '\n' + str(i) + '. Assumir: ' + '; '.join(l['texto'] for l in p['suposicoes']) + '.'
                elif dados['status'] == 'indeterminado':
                    resposta += '\nNão encontrei uma suposição suficiente dentro das regras dadas.'
                return self._registrar('abducao', dados, resposta)
            if contrafactual:
                l = ler_literal(contrafactual.group(1))
                if l.nome not in sistema.bits:
                    raise ValueError('Essa afirmação não está nas premissas atuais.')
                novas = [p for p in self.premissas if p.antecedentes or p.consequente.nome != l.nome]
                novas.append(Premissa((), l, 'e', l.texto()))
                ramo = SistemaPremissas(novas)
                dados = ramo.analisar(self.alvo) if self.alvo else ramo.conclusoes()
                dados['alteracao_temporaria'] = l.dados()
                resposta = 'Testando temporariamente: ' + l.texto() + '.\n' + self._explicar(dados)
                resposta += '\nAs premissas originais continuam intactas.'
                return self._registrar('contrafactual', dados, resposta, novas)
            if normalizar(n) == 'que hipoteses voce sugere':
                ideias = []
                for p in self.premissas:
                    if p.antecedentes and p.consequente.nome not in {i['alvo']['nome'] for i in ideias}:
                        for proposta in sistema.abduzir(p.consequente)['propostas']:
                            ideias.append(proposta)
                            if len(ideias) == 3:
                                break
                    if len(ideias) == 3:
                        break
                if not sistema.mundos:
                    dados = dict(sistema.conclusoes(), propostas=[])
                    return self._registrar('explorar', dados, self._explicar(dados))
                resposta = 'Hipóteses para explorar dentro das regras que você forneceu:'
                for i, ideia in enumerate(ideias, 1):
                    resposta += '\n' + str(i) + '. Se assumirmos ' + '; '.join(l['texto'] for l in ideia['suposicoes']) + ', podemos concluir: ' + ideia['alvo']['texto'] + '.'
                if not ideias:
                    resposta += '\nNão encontrei novas hipóteses suficientes nas regras atuais.'
                resposta += '\nSão possibilidades para verificar, não fatos novos.'
                return self._registrar('explorar', {'status': 'conflito' if not sistema.mundos else 'consistente', 'propostas': ideias}, resposta)
            dados = sistema.conclusoes()
            resposta = self._explicar(dados) if dados['status'] == 'conflito' else 'Conclusões adicionais sustentadas pelas premissas:\n' + ('\n'.join('- ' + c['alvo']['texto'] for c in dados['conclusoes']) or 'Nenhuma conclusão adicional demonstrável.')
            return self._registrar('conclusoes', dados, resposta)
        except LimiteRaciocinio as exc:
            return self._registrar('limite', {'status': 'limite'}, str(exc))
        except ValueError as exc:
            return self._registrar('esclarecer', {'status': 'nao_interpretado'}, 'Preciso esclarecer a hipótese: ' + str(exc))
