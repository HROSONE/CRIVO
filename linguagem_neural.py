"""Interpretação neural limitada e auditável, com conservação de argumentos.

Uma rede escolhe a operação; outra marca spans nas posições originais.
Pesos de inferência não contêm respostas factuais. Não faz geração livre.
"""
import json
import math
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
        if set(self.tags.rotulos) != {"O", "B1", "I1", "B2", "I2"}:
            raise ValueError("Rótulos de argumentos incompatíveis")
        self.estruturais = frozenset(dados["estruturais"])
        self.limiar = dados.get("limiar", .80)
        self.assinatura_treino = dados["assinatura_treino"]

    def _decodificar(self, probabilidades, esperados, nomes, fora_obrigatorio):
        """Escolhe intervalos contínuos usando os pesos B/I/O aprendidos.

        O caminho tem exatamente um ou dois argumentos, na ordem original.
        Um I nunca abre um argumento; na comparação existe uma separação.
        O vocabulário não determina os limites dos argumentos.
        """
        if not esperados:
            return [], tuple("O" for _ in probabilidades)
        indices = {t: self.tags.rotulos.index(t) for t in self.tags.rotulos}
        transicoes = {0: ((0, "O"), (1, "B1")),
                      1: ((1, "I1"), (2, "O")),
                      2: ((2, "O"), (3, "B2")) if esperados == 2 else ((2, "O"),),
                      3: ((3, "I2"), (4, "O")), 4: ((4, "O"),)}
        caminhos = {0: (0.0, ())}
        for i, ps in enumerate(probabilidades):
            novos = {}
            for estado, (score, tags) in caminhos.items():
                for destino, tag in transicoes[estado]:
                    # A rede pode reconhecer ligações dentro do nome, mas
                    # não pode apagar termos desconhecidos do pedido.
                    if tag == "O" and nomes[i] == "<argumento>":
                        continue
                    if i in fora_obrigatorio and tag != "O":
                        continue
                    valor = score + math.log(max(ps[indices[tag]], 1e-300))
                    if destino not in novos or valor > novos[destino][0]:
                        novos[destino] = (valor, tags + (tag,))
            caminhos = novos
        finais = (1, 2) if esperados == 1 else (3, 4)
        candidatos = [caminhos[e] for e in finais if e in caminhos]
        if not candidatos:
            return [], ()
        _, tags = max(candidatos, key=lambda c: c[0])
        grupos = [[i for i, tag in enumerate(tags) if tag.endswith(str(papel))]
                  for papel in range(1, esperados + 1)]
        return grupos, tags

    @staticmethod
    def _sufixo_de_pedido(texto, ts, nomes, grupos, ato):
        """Impede que um qualificador vire um sufixo funcional descartado.

        Depois do último argumento, admite apenas cortesia, a interrogação
        invertida ou uma instrução após ':'/','. Outros trechos exigem que
        o tagger os inclua no argumento, ou a interpretação é recusada.
        """
        if not grupos:
            return True
        fim = grupos[-1][-1]
        sufixo = nomes[fim + 1:]
        if not sufixo or sufixo in (["por", "favor"], ["por", "gentileza"], ["para", "mim"]):
            return True
        if ato == "definir" and sufixo == ["e", "o", "que"]:
            return True
        if ato == "comparar" and sufixo == ["sao", "igual"]:
            return True
        separador = texto[ts[fim][2]:ts[fim + 1][1]]
        operadores = {"definicao", "significado", "explicar", "entender", "funciona",
                      "funcao", "serve", "retomar", "diferenca", "comparacao", "igual",
                      "dizer", "conte", "fale", "saber"}
        return any(c in separador for c in (":", ",")) and bool(set(sufixo) & operadores)

    @staticmethod
    def _escopo_negado(nomes, ato):
        """Marca um predicado negativo de pedido depois do argumento.

        'não é/foi ... pedido' pertence à instrução, não ao nome do
        argumento. Só se aplica ao ato negado, com conteúdo antes do
        predicado e nenhuma palavra desconhecida dentro dele. Assim,
        qualificadores como 'rede não circular' permanecem no argumento.
        """
        if ato == "negado":
            for i in range(1, len(nomes) - 1):
                sufixo = nomes[i:]
                if (sufixo[:2] in (["nao", "e"], ["nao", "foi"]) and
                        "pedido" in sufixo and "<argumento>" not in sufixo and
                        "<argumento>" in nomes[:i]):
                    return frozenset(range(i, len(nomes)))
        return frozenset()

    def analisar(self, texto):
        ts = palavras(texto)
        if not ts or len(ts) > 96 or len(texto) > 1200:
            return None
        ato, confianca, margem = self.atos.prever(atributos_frase(texto, self.atos.dimensao,
                                                               estruturais=self.estruturais))
        nomes = [token_estrutura(t, self.estruturais) for t, _, _ in ts]
        probabilidades = [softmax(self.tags.logits(atributos_token(nomes, i, self.tags.dimensao)),
                                  self.tags.temperatura) for i in range(len(ts))]
        spans, intervalos_validos, confiancas_slots = [], True, []
        esperados = 2 if ato == "comparar" else 1 if ato in (
            "definir", "funcionamento", "funcao", "retomar", "negado") else 0
        fora_obrigatorio = self._escopo_negado(nomes, ato)
        grupos, tags = self._decodificar(probabilidades, esperados, nomes, fora_obrigatorio)
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
        # Um termo desconhecido fora de um argumento bloqueia o fallback.
        # Mesmo palavras funcionais precisam da previsão O aprendida; ser
        # uma palavra conhecida não basta para apagar parte do pedido.
        o = self.tags.rotulos.index("O")
        conservado = (intervalos_validos and all(i in conteudo or
            nomes[i] != "<argumento>" and (probabilidades[i][o] >= .80 or i in fora_obrigatorio)
            for i in range(len(ts))) and
            (fora_obrigatorio or self._sufixo_de_pedido(texto, ts, nomes, grupos, ato)))
        conservado = bool(conservado)
        # Operadores e separadores técnicos fora dos intervalos também
        # fazem parte do pedido; a tokenização não pode apagá-los.
        if any(not any(inicio <= m.start() and m.end() <= fim for _, inicio, fim in spans)
               for m in re.finditer(r"[=<>*/\\|&~^]", texto)):
            conservado = False
        condicao = re.search(r"\b(?:se|caso|quando|supondo)\b", texto, re.I)
        return QuadroNeural(ato, campos.get("alvo", ""), campos.get("outro", ""),
                            ato == "negado", texto[condicao.start():] if condicao else "",
                            confianca, margem, tuple(spans), conservado,
                            min(confiancas_slots, default=1.0))


@lru_cache(maxsize=8)
def carregar(caminho, modificacao):
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    return LinguagemNeural(dados)
