"""Entidades e relações literais da sessão, sem rede ou fatos globais.

Só mensagens do usuário são evidência. A gramática é deliberadamente pequena:
declarações nominais, preferências, objetivos, permissões, tempo e atributos
de objetos. Uma relação não reconhecida continua nas rotas anteriores.
"""
import copy
import re

from composicao_textual import normalizar

CORES = ('verde', 'azul', 'amarelo', 'amarela', 'roxo', 'roxa', 'laranja',
         'preto', 'preta', 'branco', 'branca', 'rosa', 'vermelho', 'vermelha',
         'bege', 'cinza', 'marrom')

def chave(texto):
    return normalizar(texto).strip(' .!?')


def combinar(padrao, texto):
    return re.fullmatch(padrao, texto, re.I)


class MemoriaSessao:
    def __init__(self):
        self.limpar()

    def limpar(self):
        self.turno = 0
        self.entidades = {}
        self.afirmacoes = []
        self.indices = {}
        self.correcoes = []
        self.temas = []
        self.ultimo = None

    def exportar(self):
        return copy.deepcopy(dict(entidades=list(self.entidades.values()),
                                  afirmacoes=self.afirmacoes, correcoes=self.correcoes,
                                  temas=self.temas, turno=self.turno))

    def _pessoa(self, nome, criar=False):
        n = chave(nome)
        if n in ('eu', 'meu', 'minha', 'usuario'):
            nome, n = 'você', 'usuario'
        if n in ('ele', 'ela', 'dele', 'dela'):
            genero = 'f' if n.endswith('la') else 'm'
            pessoas = [e['id'] for e in self.entidades.values()
                       if e['tipo'] == 'pessoa' and e.get('genero') == genero]
            return pessoas[0] if len(pessoas) == 1 else None
        if n in ('voce', 'crivo') or not n or len(nome) > 80:
            return None
        ident = 'pessoa:' + n
        if ident not in self.entidades:
            # Não transforma uma oração ou um nome comum em pessoa.
            palavras = nome.split()
            nominal = (1 <= len(palavras) <= 4 and
                       all(p[:1].isupper() or p in ('de', 'da', 'do', 'das', 'dos')
                           for p in palavras) and
                       n.split()[0] not in ('nao', 'o', 'a', 'meu', 'minha', 'agora'))
            if not criar or not (n == 'usuario' or nominal):
                return None
            self.entidades[ident] = dict(id=ident, nome=nome, tipo='pessoa')
        return ident

    def _objeto(self, nome, pessoa=None, criar=False):
        nome = re.sub(r'^(?:o|a|um|uma)\s+', '', nome.strip(), flags=re.I)
        ident = 'objeto:' + chave(nome) + (':' + pessoa if pessoa else '')
        if criar and ident not in self.entidades:
            self.entidades[ident] = dict(id=ident, nome=nome, tipo='objeto', dono=pessoa)
        return ident

    def _guardar(self, sujeito, relacao, valor, texto, escopo='declarado'):
        anterior = self.indices.get((sujeito, relacao))
        if anterior is not None:
            self.afirmacoes[anterior]['status'] = 'substituido'
        idx = len(self.afirmacoes)
        self.afirmacoes.append(dict(id=idx, sujeito=sujeito, relacao=relacao, valor=valor,
                                   status='ativo', escopo=escopo,
                                   fonte=dict(origem='usuario', turno=self.turno, texto=texto)))
        self.indices[sujeito, relacao] = idx
        if anterior is not None:
            self.correcoes.append(dict(turno=self.turno, antes=anterior, depois=idx, texto=texto))

    def _retirar(self, sujeito, relacao, texto, valor=None):
        idx = self.indices.get((sujeito, relacao))
        if idx is not None and (valor is None or chave(self.afirmacoes[idx]['valor']) == chave(valor)):
            self.afirmacoes[idx]['status'] = 'retirado'
            self.correcoes.append(dict(turno=self.turno, antes=idx, depois=None, texto=texto))

    def _atual(self, sujeito, relacao):
        idx = self.indices.get((sujeito, relacao))
        return (self.afirmacoes[idx] if idx is not None and
                self.afirmacoes[idx]['status'] == 'ativo' else None)

    def _emitir(self, resposta, fatos=(), acao='consulta'):
        self.ultimo = dict(acao=acao, origem='memoria_estruturada_da_sessao',
                           fontes=[copy.deepcopy(f['fonte']) for f in fatos],
                           afirmacoes=[f['id'] for f in fatos], pesos_promovidos=False)
        return 'conversa:memoria_sessao', resposta

    def _nome(self, sujeito, fallback):
        e = self.entidades.get(sujeito)
        if e is None:
            return fallback
        dono = e.get('dono')
        return e['nome'] + (' de ' + self.entidades[dono]['nome'] if dono else '')

    def _frase(self, fato):
        nome = self._nome(fato['sujeito'], '')
        rel, valor = fato['relacao'], fato['valor']
        if rel.startswith('permissão:'):
            return nome + ' ' + valor
        if rel == 'preferência':
            return nome + ' prefere ' + valor
        if rel == 'preferência relatada':
            return nome + ' disse que prefere ' + valor
        if rel == 'objetivo':
            return 'o objetivo de ' + nome + ' é ' + valor
        if rel == 'tempo disponível':
            return nome + ' tem ' + valor + ' disponíveis'
        if rel == 'dono':
            return nome + ' pertence a ' + valor
        if rel == 'localização':
            return nome + ' está ' + valor
        if rel == 'vínculo':
            valor = re.sub(r'^minha\b', 'sua', valor, flags=re.I)
            valor = re.sub(r'^meu\b', 'seu', valor, flags=re.I)
        return nome + ' é ' + valor

    def _resposta_campo(self, sujeito, relacao, nome):
        fato = self._atual(sujeito, relacao)
        rotulo = self._nome(sujeito, nome)
        if fato is None:
            if relacao.startswith('permissão:'):
                return self._emitir('Não sei se ' + rotulo + ' pode ' + relacao.split(':', 1)[1] +
                                    '; você não informou isso na sessão.')
            return self._emitir('Não tenho ' + relacao + ' de ' + rotulo + ' informada na sessão.')
        # O valor sai literalmente da fala de origem, nunca do corpus de treino.
        return self._emitir('Segundo o que você contou, ' + self._frase(fato) + '.', [fato])

    def _observar(self, texto):
        s = texto.strip().rstrip('.!').strip()
        n = chave(s)
        if ('?' in s or any(c in s for c in ('`', '"', '“', '”', '‘', '’')) or
                re.search(r'\b(?:se|caso|talvez|suponha|imagine|hipoteticamente)\b', n)):
            return
        if n.startswith('mudando de assunto'):
            self.temas.append(dict(texto=texto, turno=self.turno))
            return  # Uma troca de tema não apaga entidades.
        corpo = re.sub(r'^(?:corrigindo|na verdade|quer dizer)[:,]?\s*', '', s, flags=re.I)
        corpo = re.sub(r'^agora\s+', '', corpo, flags=re.I)
        m = combinar(r'Não era (.+?);\s*era (.+?) que prefere (.+)', corpo)
        if m:
            antes = self._pessoa(m[1]); depois = self._pessoa(m[2])
            if antes and depois:
                self._retirar(antes, 'preferência', texto, m[3])
                self._guardar(depois, 'preferência', m[3], texto)
            return
        m = combinar(r'(?:não sei|não sabemos) a cor d[oa] (.+?) de (.+)', corpo)
        if m:
            p = self._pessoa(m[2])
            if p:
                self._retirar(self._objeto(m[1], p), 'cor', texto)
            return
        m = combinar(r'(.+?) é (meu|minha) (.+)', corpo)
        if m:
            p = self._pessoa(m[1], criar=True)
            if p:
                self._guardar(p, 'vínculo', m[2] + ' ' + m[3], texto)
                self.entidades[p]['genero'] = 'f' if m[2].lower() == 'minha' else 'm'
            return
        m = combinar(r'(?:o|a) (.+?) pertence a (.+)', corpo)
        if m:
            p = self._pessoa(m[2], criar=True)
            if p:
                self._guardar(self._objeto(m[1], criar=True), 'dono',
                              self.entidades[p]['nome'], texto)
            return
        m = combinar(r'(?:o|a) (.+?) (?:de|da|do) (.+?) (é|está) (.+)', corpo)
        if m:
            p = self._pessoa(m[2], criar=True)
            if p:
                o = self._objeto(m[1], p, criar=True)
                rel = 'localização' if chave(m[3]) == 'esta' else 'cor'
                # "É" só licencia cores conhecidas; outros atributos exigem
                # um rótulo explícito, evitando chamar profissão de cor.
                if rel == 'localização' or chave(m[4]) in CORES:
                    self._guardar(o, rel, m[4], texto)
            return
        m = combinar(r'(.+?) tem (?:um|uma) (.+?) (' + '|'.join(CORES) + r')', corpo)
        if m:
            p = self._pessoa(m[1], criar=True)
            if p:
                self._guardar(self._objeto(m[2], p, criar=True), 'cor', m[3], texto)
            return
        m = combinar(r'(?:(eu|.+?) )?(tenho|tem|disponho de) (\d{1,4}) minutos(?: disponíveis)?', corpo)
        if m:
            p = self._pessoa(m[1] or 'eu', criar=True)
            if p:
                self._guardar(p, 'tempo disponível', m[3] + ' minutos', texto)
            return
        m = combinar(r'(.+?) disse que prefere (.+)', corpo)
        if m:
            p = self._pessoa(m[1], criar=True)
            if p:
                self._guardar(p, 'preferência relatada', m[2], texto, 'fala_reportada')
            return
        # Sem sujeito explícito, a negação pertence ao verbo, não a uma
        # suposta pessoa chamada "Não".
        if re.match(r'(?:não )?(?:prefiro|quero|pretendo|posso)\b', corpo, re.I):
            corpo = 'Eu ' + corpo
        m = combinar(r'(?:(eu|.+?) )?(prefiro|prefere|não prefiro|não prefere|quero|quer|não quero|não quer|pretendo|pretende|'
                     r'não posso|não pode|posso|pode) (.+)', corpo)
        if m:
            p = self._pessoa(m[1] or 'eu', criar=True)
            if not p:
                return
            verbo, valor = chave(m[2]), m[3]
            if verbo in ('nao prefere', 'nao prefiro'):
                self._retirar(p, 'preferência', texto, valor)
            elif verbo in ('nao quero', 'nao quer'):
                self._retirar(p, 'objetivo', texto, valor)
            elif verbo in ('prefiro', 'prefere'):
                self._guardar(p, 'preferência', valor, texto)
            elif verbo in ('quero', 'quer', 'pretendo', 'pretende'):
                self._guardar(p, 'objetivo', valor, texto)
            else:
                if not re.match(r'^(?:ir|[\wÀ-ÿ]+(?:ar|er|ir))\b', valor, re.I):
                    return  # Dias/listas de agenda pertencem ao calculador.
                acao = chave(valor)
                self._guardar(p, 'permissão:' + acao,
                              ('não pode ' if verbo.startswith('nao') else 'pode ') + valor, texto)

    def _consultar(self, texto):
        s = texto.strip().rstrip('?.!').strip()
        # As consultas de objetos citam proprietário e objeto explicitamente.
        for padrao, rel in ((r'De que cor é (?:o|a) (.+?) (?:de|da|do) (.+)', 'cor'),
                            (r'Qual é a cor d[oa] (.+?) (?:de|da|do) (.+)', 'cor'),
                            (r'Onde está (?:o|a) (.+?) (?:de|da|do) (.+)', 'localização')):
            m = combinar(padrao, s)
            if m:
                p = self._pessoa(m[2])
                if chave(m[2]) in ('ele', 'ela', 'dele', 'dela') and p is None:
                    return self._emitir('A qual pessoa você se refere?', acao='esclarecer')
                if p is None:
                    return None  # "núcleo do Átomo" e "solo de Marte" são consultas factuais.
                o = self._objeto(m[1], p)
                return self._resposta_campo(o, rel, m[1] + ' de ' + m[2])
        m = combinar(r'A quem pertence (?:o|a) (.+)', s)
        if m:
            o = self._objeto(m[1])
            return self._resposta_campo(o, 'dono', m[1]) if o in self.entidades else None
        consultas = (
            (r'O que (.+?) disse que prefere', 'preferência relatada'),
            (r'O que (.+?) (?:prefere|prefiro)', 'preferência'),
            (r'Qual é o objetivo (?:de |d)(.+)', 'objetivo'),
            (r'Qual é a restrição (?:de |d)(.+)', 'restrição'),
            (r'Quantos minutos (.+?) (?:tenho|tem) disponíveis', 'tempo disponível'),
            (r'Resuma o que eu disse sobre (.+)', 'resumo'),
            (r'(.+?) pode (.+)', 'permissão'),
        )
        for padrao, rel in consultas:
            m = combinar(padrao, s)
            if not m:
                continue
            nome = m[1]
            if chave(nome) in ('voce', 'crivo'):
                return None
            p = self._pessoa(nome)
            if chave(nome) in ('ele', 'ela', 'dele', 'dela') and p is None:
                return self._emitir('A qual pessoa você se refere?', acao='esclarecer')
            if p is None and not nome[:1].isupper():
                return None
            if rel == 'permissão':
                if ('?' not in texto or p is None or
                        not re.match(r'^(?:ir|[\wÀ-ÿ]+(?:ar|er|ir))\b', m[2], re.I) or
                        re.search(r'[.!?;]', m[2])):
                    return None
                return self._resposta_campo(p, 'permissão:' + chave(m[2]), nome)
            if rel in ('restrição', 'resumo'):
                fatos = [f for f in self.afirmacoes if f['sujeito'] == p and f['status'] == 'ativo'
                         and (rel == 'resumo' or f['relacao'].startswith('permissão:')
                              and f['valor'].startswith('não pode '))]
                if not fatos:
                    return self._resposta_campo(p, rel, nome)
                return self._emitir('Segundo o que você contou, ' +
                                    '; '.join(self._frase(f) for f in fatos) + '.', fatos)
            return self._resposta_campo(p, rel, nome)
        return None

    def processar(self, texto, ficcao=False):
        self.ultimo = None
        if not isinstance(texto, str) or not texto.strip() or len(texto) > 1200:
            return None
        from correcao_relatos import pedido_reinicio
        n = chave(texto)
        if pedido_reinicio(texto) or n in ('vamos comecar de novo', 'ta vamos comecar de novo'):
            self.limpar()
            return None  # A rota nativa também limpa as outras memórias.
        if ficcao or re.match(r'(?:na historia|na ficcao|no conto)\b', n):
            return None
        if any(c in texto for c in ('`', '"', '“', '”', '‘', '’')):
            return None
        self.turno += 1
        antes = len(self.afirmacoes)
        self._observar(texto)
        # Fala hipotética nunca vira uma consulta real só por conter um nome.
        if re.search(r'\b(?:se|caso|talvez|imagine|suponha|hipoteticamente)\b', n):
            return None
        consulta = self._consultar(texto)
        if consulta is not None:
            return consulta
        novos = self.afirmacoes[antes:]
        # Uma confirmação literal impede a grafia automática de transformar
        # nomes inéditos. Declarações pessoais mantêm a conversa nativa.
        nomeados = [f for f in novos if f['sujeito'] != 'pessoa:usuario']
        if nomeados:
            return self._emitir('Registrei seu relato: ' + '; '.join(
                self._frase(f) for f in nomeados) + '.', nomeados, acao='registro')
        return None
