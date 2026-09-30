"""Interpretação neural limitada e auditável, com conservação de argumentos.

Uma rede escolhe a operação; outra marca spans nas posições originais.
Pesos de inferência não contêm respostas factuais. Não faz geração livre.
"""
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

from rede_sequencial import (RedeSequencial, atributos_frase, atributos_token,
                            palavras, VERSAO_ATRIBUTOS, token_estrutura, softmax, assinatura_atributos)


class QuadroNeural(NamedTuple):
    ato: str
    alvo: str
    outro: str
    negacao_pedido: bool
    condicao: str
    confianca: float
    margem: float
    spans: tuple
    conservado: bool
    confianca_spans: float


class LinguagemNeural:
    def __init__(self, dados):
        if dados.get("versao") != 1 or dados.get("atributos") != VERSAO_ATRIBUTOS:
            raise ValueError("Checkpoint de linguagem incompatível")
        if dados.get("assinatura_atributos") != assinatura_atributos():
            raise ValueError("Atributos de linguagem mudaram; treine novamente")
        self.atos = RedeSequencial.de_dados(dados["atos"])
        self.tags = RedeSequencial.de_dados(dados["tags"])
        self.estruturais = frozenset(dados["estruturais"])
        self.limiar = dados.get("limiar", .80)
        self.assinatura_treino = dados["assinatura_treino"]

    def analisar(self, texto):
        ts = palavras(texto)
        if not ts or len(ts) > 96 or len(texto) > 1200:
            return None
        ato, confianca, margem = self.atos.prever(atributos_frase(texto, self.atos.dimensao,
                                                               estruturais=self.estruturais))
        nomes = [token_estrutura(t, self.estruturais) for t, _, _ in ts]
        probabilidades = [softmax(self.tags.logits(atributos_token(nomes, i, self.tags.dimensao)),
                                  self.tags.temperatura) for i in range(len(ts))]
        # Decodificação restrita: argumentos são intervalos de conteúdo;
        # artigos e ligações podem estar dentro deles. Nenhum conteúdo fica
        # de fora para forçar uma definição conhecida. O tagger estima a
        # confiança dos papéis; o decoder aplica restrições de continuidade.
        conteudos = [i for i, n in enumerate(nomes) if n == "<argumento>"]
        grupos = []
        for i in conteudos:
            ligacoes = {"de", "do", "da", "dos", "das", "em", "no", "na", "sem"}
            if ato != "comparar":
                ligacoes.update({"e", "com"})
            if grupos and all(ts[k][0] in ligacoes for k in range(grupos[-1][-1]+1, i)):
                grupos[-1].append(i)
            else:
                grupos.append([i])
        spans, intervalos_validos, confiancas_slots = [], True, []
        if ato == "outro":
            grupos = []
        esperados = 2 if ato == "comparar" else 1 if ato in (
            "definir", "funcionamento", "funcao", "retomar", "negado") else 0
        if len(grupos) != esperados:
            intervalos_validos = False
        if len(grupos) == esperados:
            for k, grupo in enumerate(grupos):
                nome = "alvo" if k == 0 else "outro"
                a, b = grupo[0], grupo[-1]
                # O primeiro/segundo argumento da comparação precisa manter
                # a direção escrita; não reordena entidades por semelhança.
                spans.append((nome, ts[a][1], ts[b][2]))
                papel = "1" if k == 0 else "2"
                posicoes = [self.tags.rotulos.index(t + papel) for t in ("B", "I")]
                confiancas_slots.append(sum(sum(probabilidades[i][p] for p in posicoes)
                                             for i in grupo) / len(grupo))
        campos = {nome: texto[a:b] for nome, a, b in spans}
        conteudo = {i for i, (_, a, b) in enumerate(ts)
                    if any(inicio <= a and b <= fim for _, inicio, fim in spans)}
        # Palavras de conteúdo fora de um span nunca são descartadas para
        # transformar um alvo desconhecido numa definição conhecida.
        conservado = intervalos_validos and all(i in conteudo or token_estrutura(t, self.estruturais) != "<argumento>"
                                               for i, (t, _, _) in enumerate(ts))
        condicao = re.search(r"\b(?:se|caso|quando|supondo)\b", texto, re.I)
        return QuadroNeural(ato, campos.get("alvo", ""), campos.get("outro", ""),
                            ato == "negado", texto[condicao.start():] if condicao else "",
                            confianca, margem, tuple(spans), conservado,
                            min(confiancas_slots, default=1.0))


@lru_cache(maxsize=8)
def carregar(caminho, modificacao):
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return LinguagemNeural(dados)
