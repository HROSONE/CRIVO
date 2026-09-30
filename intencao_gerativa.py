"""Roteador autoral de pedidos de escrita e acompanhamento pessoal.

A rede escolhe uma operação, sem produzir argumentos nem respostas. Os
atributos usam somente o pedido e o estado declarado da sessão. A aceitação
neural é uma evidência local; o chamador ainda deve conferir o domínio, os
argumentos necessários e a prioridade das perguntas factuais.
"""
import hashlib
import inspect
import json
import math
from functools import lru_cache
from pathlib import Path

from rede_sequencial import RedeSequencial, atributos_frase, normalizar, palavras, softmax
from rede_sequencial import assinatura_atributos as assinatura_sequencial

VERSAO = "intencao-gerativa-contextual-v1"
DIMENSAO = 1168
ACOES = ("historia", "poema", "final", "escuta", "alternativa", "ajuste", "apoio", "ideia",
         "mensagem", "dialogo", "continuacao", "resumo", "reformulacao", "exploracao", "plano", "reflexao")
ESTADOS_BOOL = ("relato", "objetivo", "restricao", "criacao")
TIPOS_ESCRITA = ("", "historia", "poema", "mensagem", "dialogo")


def normalizar_estado(estado):
    """Conserva apenas o contrato explícito; rótulos não entram no estado."""
    if not isinstance(estado, dict) or set(estado) - set(ESTADOS_BOOL + ("tipo_escrita",)):
        raise ValueError("Estado de intenção inválido")
    resultado = {}
    for nome in ESTADOS_BOOL:
        valor = estado.get(nome, False)
        if not isinstance(valor, bool):
            raise ValueError("Estado de intenção exige valores booleanos")
        resultado[nome] = valor
    tipo = estado.get("tipo_escrita", "")
    if tipo not in TIPOS_ESCRITA:
        raise ValueError("Tipo de escrita inválido")
    resultado["tipo_escrita"] = tipo
    return resultado


def atributos(texto, estado, lexico):
    if not isinstance(texto, str) or len(texto) > 1200:
        raise ValueError("Pedido inválido para intenção gerativa")
    estado = normalizar_estado(estado)
    ts = [t for t, _, _ in palavras(texto)]
    # Canal lexical conserva flexões e termos novos. O canal abstrato evita
    # que os nomes dos temas ocupem todo o peso dos operadores do pedido.
    v = {i: .7 * valor for i, valor in atributos_frase(texto, 768).items()}
    abstratos = " ".join(t if t in lexico else "argumento" for t in ts)
    v.update({768 + i: valor for i, valor in atributos_frase(abstratos, 384).items()})
    for i, nome in enumerate(ESTADOS_BOOL):
        v[1152 + i] = .5 if estado[nome] else -.5
    v[1156 + TIPOS_ESCRITA.index(estado["tipo_escrita"])] = .5
    if "?" in texto:
        v[1161] = .15
    if len(ts) <= 4:
        v[1162] = .15
    return v


def assinatura_atributos():
    fonte = repr((VERSAO, DIMENSAO, ACOES, ESTADOS_BOOL, TIPOS_ESCRITA)) + assinatura_sequencial()
    fonte += "".join(inspect.getsource(f) for f in
                     (normalizar_estado, atributos, atributos_frase, normalizar, palavras))
    return hashlib.sha256(fonte.encode("utf-8")).hexdigest()


class IntencaoGerativa:
    def __init__(self, dados):
        if dados.get("versao") != 1 or dados.get("assinatura_atributos") != assinatura_atributos():
            raise ValueError("Pesos incompatíveis com os atributos de intenção")
        lexico = dados.get("lexico")
        if (not isinstance(lexico, list) or len(lexico) > 10000 or
                any(not isinstance(t, str) or not t or len(t) > 100 for t in lexico)):
            raise ValueError("Léxico de intenção inválido")
        self.lexico = frozenset(lexico)
        self.rede = RedeSequencial.de_dados(dados["rede"])
        if self.rede.dimensao != DIMENSAO or tuple(self.rede.rotulos) != ACOES:
            raise ValueError("Contrato neural de intenção incompatível")
        self.limiar = dados.get("limiar", .80)
        self.margem_minima = dados.get("margem_minima", .20)
        if (not isinstance(self.limiar, (int, float)) or not math.isfinite(self.limiar) or
                not .5 <= self.limiar <= 1 or
                not isinstance(self.margem_minima, (int, float)) or not math.isfinite(self.margem_minima) or
                not 0 <= self.margem_minima <= 1):
            raise ValueError("Limiares de intenção inválidos")

    def analisar(self, texto, estado):
        estado = normalizar_estado(estado)
        ps = softmax(self.rede.logits(atributos(texto, estado, self.lexico)), self.rede.temperatura)
        indices = sorted(range(len(ps)), key=lambda i: ps[i], reverse=True)
        primeiro, segundo = indices[:2]
        confianca, margem = ps[primeiro], ps[primeiro] - ps[segundo]
        return {"acao": self.rede.rotulos[primeiro], "confianca": confianca,
                "margem": margem, "aceita": bool(texto.strip()) and
                confianca >= self.limiar and margem >= self.margem_minima,
                "estado": estado, "distribuicao": dict(zip(self.rede.rotulos, ps))}


@lru_cache(maxsize=2)
def carregar(caminho, mtime):
    return IntencaoGerativa(json.loads(Path(caminho).read_text(encoding="utf-8")))


def caminho_padrao():
    return Path(__file__).with_name("rede_intencao_gerativa.json")
