"""Investigação recorrente limitada; componentes procedurais, não um cérebro.

Hipóteses independentes podem coexistir. Compatibilidade depende de restrições
de um modelo declarado, não prova causalidade. Perguntas são escolhidas pelo
ganho esperado nesse modelo, com respostas equiprováveis explicitamente
assumidas. Não há probabilidades calibradas, pesos externos ou treino online.
"""
from collections import deque
from dataclasses import dataclass
import math


def _texto(valor, limite=160):
    if type(valor) is not str or not 1 <= len(valor) <= limite or '\x00' in valor:
        raise ValueError('Texto inválido ou acima do limite')


@dataclass(frozen=True)
class Episodio:
    id: int
    campo: str
    valor: str
    origem: str
    referencia: str
    substitui: int = None


class MemoriaInvestigacao:
    """Histórico por instância. Relatos não viram conhecimento global.

Correções substituem a observação ativa do campo e conservam a anterior no
histórico limitado. Saída gerada, citação e hipótese têm outra fila e nunca
substituem observações. 'instrumento' exige referência fornecida pelo backend;
o rótulo por si só não verifica se a medição ou o instrumento estão corretos.
"""
    def __init__(self, limite=64):
        if type(limite) is not int or not 1 <= limite <= 64:
            raise ValueError('Memória deve ter entre 1 e 64 episódios')
        self._observacoes = deque(maxlen=limite)
        self._propostas = deque(maxlen=16)
        self._contador = 0

    def registrar(self, campo, valor, origem, referencia):
        for t in (campo, valor, referencia): _texto(t)
        if origem not in ('usuario', 'instrumento', 'hipotese', 'gerador', 'citacao'):
            raise ValueError('Origem desconhecida')
        fila = self._observacoes if origem in ('usuario', 'instrumento') else self._propostas
        for e in fila:
            if (e.campo, e.valor, e.origem, e.referencia) == (campo, valor, origem, referencia):
                return e  # Replay da mesma evidência não cria apoio novo.
        anteriores = [e for e in fila if e.campo == campo]
        self._contador += 1
        e = Episodio(self._contador, campo, valor, origem, referencia,
                    anteriores[-1].id if anteriores else None)
        fila.append(e)
        return e

    def observacoes(self):
        return {e.campo: e for e in self._observacoes}

    def episodios(self):
        return tuple(sorted(tuple(self._observacoes) + tuple(self._propostas), key=lambda e: e.id))

    def limpar(self):
        self._observacoes.clear(); self._propostas.clear(); self._contador = 0


@dataclass(frozen=True)
class Hipotese:
    id: str
    descricao: str
    # Tuplas imutáveis: (campo, valores compatíveis segundo o modelo).
    previsoes: tuple


@dataclass(frozen=True)
class Pergunta:
    campo: str
    texto: str
    respostas: tuple
    custo: float = 1.


class Investigador:
    """Observe → recupere → simule → compare → pergunte/abstenha-se.

Um ciclo não inventa observações e termina antes de aguardar a resposta. O
próximo ciclo incorpora uma resposta nova ou uma correção. Até oito hipóteses,
doze perguntas e seis etapas por ciclo. Simulações não são eventos do mundo.
"""
    def __init__(self, hipoteses, perguntas, dominio=()):
        self.hipoteses = tuple(hipoteses); self.perguntas = tuple(perguntas)
        self.dominio = tuple(dominio)
        if not 1 <= len(self.hipoteses) <= 8 or not 1 <= len(self.perguntas) <= 12:
            raise ValueError('Quantidade de hipóteses/perguntas fora do orçamento')
        self.campos = {}
        for p in self.perguntas:
            _texto(p.campo); _texto(p.texto, 600)
            if p.campo in self.campos or type(p.respostas) is not tuple or not 2 <= len(p.respostas) <= 8:
                raise ValueError('Pergunta repetida ou respostas inválidas')
            for r in p.respostas: _texto(r)
            if len(set(p.respostas)) != len(p.respostas) or type(p.custo) not in (int, float) or not math.isfinite(p.custo) or not 1e-6 <= p.custo <= 1e6:
                raise ValueError('Custo ou respostas inválidas')
            self.campos[p.campo] = p.respostas
        ids = set()
        for h in self.hipoteses:
            _texto(h.id); _texto(h.descricao, 600)
            if h.id in ids or type(h.previsoes) is not tuple or len(h.previsoes) > 12:
                raise ValueError('Hipótese repetida ou previsões inválidas')
            ids.add(h.id); usados = set()
            for campo, valores in h.previsoes:
                if campo in usados or campo not in self.campos or type(valores) is not tuple or not valores or not set(valores) <= set(self.campos[campo]):
                    raise ValueError('Previsão fora dos campos declarados')
                usados.add(campo)
        usados = set()
        for campo, valor in self.dominio:
            if campo in usados or campo not in self.campos or valor not in self.campos[campo]:
                raise ValueError('Domínio inválido')
            usados.add(campo)
        self.memoria = MemoriaInvestigacao()
        self.ultimo = None

    def observar(self, dados, referencia, origem='usuario'):
        if type(dados) is not dict or len(dados) > len(self.campos):
            raise ValueError('Observações inválidas')
        # Validação completa antes de alterar qualquer estado.
        _texto(referencia)
        for campo, valor in dados.items():
            if campo not in self.campos or type(valor) is not str or valor not in self.campos[campo]:
                raise ValueError('Observação fora do domínio: ' + str(campo))
        if origem not in ('usuario', 'instrumento'):
            raise ValueError('Hipótese, citação e geração não são observações')
        for campo, valor in dados.items():
            self.memoria.registrar(campo, valor, origem, referencia)

    def _comparar(self, dados):
        quadro = []
        for h in self.hipoteses:
            contra = [campo for campo, valores in h.previsoes if campo in dados and dados[campo] not in valores]
            apoio = [campo for campo, valores in h.previsoes if campo in dados and dados[campo] in valores]
            faltantes = [campo for campo, _ in h.previsoes if campo not in dados]
            quadro.append(dict(id=h.id, descricao=h.descricao,
                estado='incompativel_no_modelo' if contra else 'compativel_no_modelo',
                contradicoes=contra, observacoes_compativeis=apoio, faltantes=faltantes,
                comprovada=False))
        return quadro

    def investigar(self):
        observacoes = self.memoria.observacoes()
        dados = {k: e.valor for k, e in observacoes.items()}
        passos = ['recuperar_observacoes', 'verificar_dominio']
        fora = [(c, v) for c, v in self.dominio if c in dados and dados[c] != v]
        faltam = [c for c, _ in self.dominio if c not in dados]
        quadro = self._comparar(dados) if not fora and not faltam else []
        perguntas = []
        if fora:
            acao = 'fora_de_escopo'; escolhida = None
        elif faltam:
            acao = 'esclarecer'; escolhida = next(p for p in self.perguntas if p.campo == faltam[0])
        else:
            passos += ['comparar_hipoteses', 'simular_observacoes']
            compativeis = {h['id'] for h in quadro if not h['contradicoes']}
            for p in self.perguntas:
                if p.campo in dados: continue
                simulacoes = []
                for r in p.respostas:
                    depois = self._comparar(dict(dados, **{p.campo: r}))
                    descartadas = sorted(h['id'] for h in depois if h['id'] in compativeis and h['contradicoes'])
                    simulacoes.append(dict(resposta=r, hipoteses_descartadas_no_modelo=descartadas))
                ganho = sum(len(s['hipoteses_descartadas_no_modelo']) for s in simulacoes) / len(simulacoes)
                perguntas.append(dict(campo=p.campo, texto=p.texto,
                    ganho_modelado=ganho, custo=p.custo, utilidade=ganho/p.custo, simulacoes=simulacoes))
            # Empates seguem ordem editorial estável; não expressam confiança.
            perguntas.sort(key=lambda p: -p['utilidade'])
            if not compativeis:
                acao = 'rever_modelo'; escolhida = None
            elif perguntas and perguntas[0]['ganho_modelado'] > 0:
                acao = 'perguntar'; escolhida = next(p for p in self.perguntas if p.campo == perguntas[0]['campo'])
            else:
                acao = 'investigar_fora_do_modelo'; escolhida = None
        passos.append('selecionar_acao')
        from dataclasses import asdict
        self.ultimo = dict(acao=acao, pergunta=escolhida.texto if escolhida else None,
            campo=escolhida.campo if escolhida else None, passos=passos,
            workspace=dict(observacoes={k: asdict(e) for k, e in observacoes.items()},
                hipoteses=quadro, alternativas=perguntas),
            suposicoes=['Respostas equiprováveis somente para a heurística de escolha.',
                       'Hipóteses independentes: causas podem coexistir.',
                       'Observações informadas não certificam medições nem causalidade.'],
            comprovado=False, pesos_treinados=False, memoria_persistente=False)
        import copy
        return copy.deepcopy(self.ultimo)
