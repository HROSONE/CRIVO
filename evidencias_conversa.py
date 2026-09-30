"""Busca e seleção de unidades factuais dentro de um assunto resolvido.

Uma coincidência de ranking não resolve um nome nem comprova causalidade.
Todos os termos substantivos do detalhe precisam estar na mesma evidência.
"""
import math
import re
import unicodedata
from collections import Counter

from composicao_textual import ContextoTexto


def normalizar(texto):
    n = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in n if unicodedata.category(c) != "Mn")


FUNCIONAIS = set("a o as os um uma uns umas de do da dos das em no na nos nas por para com e que qual quais como me se sobre explique explicar explica fale falar fala conte contar diga dizer mostre mostrar desse dessa dele dela isso detalhe detalhes respeito ao aos pelo pela seus suas seu sua eu voce vc pode poderia quero saber gostaria entenda entender dos das".split())


def termos(texto):
    return [t for t in re.findall(r"[a-z0-9]+", normalizar(texto)) if len(t) > 1 and t not in FUNCIONAIS]


def equivalente(a, b):
    if a == b or a.rstrip("s") == b.rstrip("s"):
        return True
    # Flexões próximas só em palavras longas. Números, símbolos e nomes
    # resolvidos pelo catálogo nunca são alterados por esta comparação.
    return len(a) >= 6 and len(b) >= 6 and a[:6] == b[:6]


def protegido(fato):
    return fato.get("papel") == "limite" or bool(re.search(r"\d", fato["texto"])) or bool(re.search(
        r"\b(nao|nunca|jamais|se|quando|pode|podem|geralmente|aproximadamente|associacao)\b",
        normalizar(fato["texto"])))


class IndiceEvidencias:
    def __init__(self, compositor):
        self.compositor = compositor
        self.docs = {(e, i): Counter(termos(f["texto"])) for e, item in compositor.itens.items()
                     for i, f in enumerate(item["fatos"])}
        df = Counter(t for d in self.docs.values() for t in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n-f+.5)/(f+.5)) for t,f in df.items()}
        self.media = sum(sum(d.values()) for d in self.docs.values()) / max(1, n) or 1

    def buscar(self, ident, detalhe):
        consulta = termos(detalhe)
        if not consulta or len(consulta) > 30 or re.search(r"[=<>*/\\|&~^]", detalhe):
            return ()
        candidatos = []
        for par, doc in self.docs.items():
            if par[0] != ident:
                continue
            associados = []
            for termo in consulta:
                encontrados = [t for t in doc if equivalente(termo, t)]
                if len(encontrados) != 1:
                    break
                associados.append(encontrados[0])
            else:
                score = sum(self.idf[t] * doc[t] * 2.2 /
                            (doc[t] + 1.2*(.3+.7*sum(doc.values())/self.media)) for t in associados)
                candidatos.append((score, par))
        if not candidatos:
            return ()
        return tuple(par for _, par in sorted(candidatos, reverse=True)[:2])

    def selecionar(self, ids, operacao, contexto=None):
        comp = self.compositor
        if operacao in ("resumo", "reformulacao", "simples", "topicos"):
            pares = tuple(p for p in (contexto.exibidos if contexto else ()) if p[0] in ids)
            if not pares:
                pares = tuple((e, 0) for e in ids)
            if operacao == "resumo":
                centrais = [next(p for p in pares if p[0] == e) for e in ids if any(p[0] == e for p in pares)]
                pares = tuple(dict.fromkeys(centrais + [p for p in pares if protegido(comp.itens[p[0]]["fatos"][p[1]])]))
            return pares
        if operacao == "aprofundar":
            usados = contexto.usados if contexto else ()
            novos = list(comp._selecionar(ids, max(4, len(ids)*2), usados))
            # Avisos fazem parte da explicação aprofundada mesmo quando
            # aparecem depois de vários detalhes no catálogo.
            novos.extend((e, i) for e in ids for i,f in enumerate(comp.itens[e]["fatos"])
                         if protegido(f) and (e, i) not in usados)
            return tuple(dict.fromkeys(novos))
        if operacao == "definir":
            return tuple(p for e in ids for p in [(e, 0)])
        return tuple((e, i) for e in ids for i, f in enumerate(comp.itens[e]["fatos"])
                     if f.get("aspecto") == operacao or operacao == "exemplo" and f.get("papel") == "exemplo")

    def contexto(self, ids, pares, texto, anterior=None, provas=()):
        usados = tuple(dict.fromkeys((anterior.usados if anterior else ()) + tuple(pares)))
        return ContextoTexto(tuple(ids), tuple(pares), usados, "texto", texto, "plano",
                             tuple(p for p in provas if p[1] in texto))

    def fontes(self, pares):
        resultado = []
        for e, i in dict.fromkeys(pares):
            fato = self.compositor.itens[e]["fatos"][i]
            chaves = list(fato.get("fontes", [])) + ([fato["fonte"]] if fato.get("fonte") else [])
            resultado.append({"assunto": e, "indice": i, "texto": fato["texto"],
                              "fontes": [dict(self.compositor.fontes[f]) for f in dict.fromkeys(chaves)]})
        return resultado
