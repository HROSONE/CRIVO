"""Composição factual e continuidade sem modelo externo.

Planeja tópicos, seleciona unidades editoriais e realiza parágrafos/listas.
Não gera fatos, causas ou citações por probabilidade. Não é uma LLM nem
escrita irrestrita: cada sentença factual tem uma unidade de origem.
"""
import json
import re
import unicodedata
from pathlib import Path
from typing import NamedTuple, Tuple


def normalizar(texto):
    n = unicodedata.normalize("NFD", texto.lower())
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9+#_,\s-]", " ", n).split()).strip(" ,")


def tema(texto):
    return re.sub(r"^(?:o|a|os|as|um|uma|uns|umas) ", "", normalizar(texto))


class ContextoTexto(NamedTuple):
    temas: Tuple[str, ...]
    exibidos: Tuple[Tuple[str, int], ...]
    usados: Tuple[Tuple[str, int], ...]
    formato: str
    texto: str
    origem: str


class CompositorTextual:
    def __init__(self, base, caminho, extrair_definicao, curriculo_mundo=None):
        self.itens = {}
        self.aliases = {}
        self.fontes = {}
        self.expandidos = set()
        self.referencias = []
        self.mundo_ids = set()
        self.ligacoes_mundo = []
        self.comparacoes_mundo = []
        for e in base:
            if e.get("origem_curriculo") == "mundo":
                continue
            aliases = [a for p in e["perguntas"]
                       for a in [extrair_definicao(p)] if a]
            aliases += e.get("definicoes", [])
            if not aliases:
                continue
            nome = aliases[0]
            for q in e["perguntas"]:
                m = re.fullmatch(r"o que (?:é|e|são|sao) (.+?)[?!.]*", q, re.I)
                if m:
                    nome = re.sub(r"^(?:o|a|um|uma|os|as) ", "", m.group(1), flags=re.I)
                    break
            resposta = e.get("resposta_definicao") or e["resposta"]
            partes = re.split(r"(?<=[.!?])\s+", resposta.strip())
            fatos = [{"texto": p, "papel": "definicao" if i == 0 else "detalhe"}
                     for i, p in enumerate(partes) if p.strip()]
            fontes_editoriais = []
            for i, url in enumerate(e.get("fontes", [])):
                if isinstance(url, str) and re.fullmatch(r"https://[^\s<>]+", url):
                    chave = "editorial:" + e["id"] + ":" + str(i)
                    self.fontes[chave] = {"titulo": "Referência editorial de " + nome, "url": url}
                    fontes_editoriais.append(chave)
            for fato in fatos:
                if fontes_editoriais:
                    fato["fontes"] = list(fontes_editoriais)
            self._adicionar({"id": e["id"], "nome": nome,
                            "aliases": aliases, "fatos": fatos})
        if Path(caminho).is_file():
            self._carregar(json.loads(Path(caminho).read_text(encoding="utf-8")),
                           {e["id"] for e in base})
        if curriculo_mundo is not None:
            self._carregar(curriculo_mundo, {e["id"] for e in base})
            self.mundo_ids = {i["id"] for i in curriculo_mundo["itens"]}
            self.ligacoes_mundo = curriculo_mundo.get("ligacoes", [])
            self.comparacoes_mundo = curriculo_mundo.get("comparacoes", [])

    def _adicionar(self, item):
        self.itens[item["id"]] = item
        for alias in [item["nome"]] + item.get("aliases", []):
            self.aliases.setdefault(tema(alias), set()).add(item["id"])

    def _carregar(self, dados, ids_base):
        if (not isinstance(dados, dict) or dados.get("versao") != 1 or
                not isinstance(dados.get("fontes"), dict) or
                not isinstance(dados.get("itens"), list) or len(dados["itens"]) > 1000):
            raise ValueError("Currículo textual inválido")
        for ident, fonte in dados["fontes"].items():
            if (not isinstance(fonte, dict) or not isinstance(fonte.get("titulo"), str)
                    or not isinstance(fonte.get("url"), str)
                    or not re.fullmatch(r"https://[^\s<>]+", fonte["url"])):
                raise ValueError("Fonte textual inválida")
            self.fontes[ident] = dict(fonte)
        for item in dados["itens"]:
            if (not isinstance(item, dict) or not isinstance(item.get("id"), str)
                    or not re.fullmatch(r"[a-z][a-z0-9_]{1,63}", item["id"])
                    or item["id"] in self.itens or item["id"] in self.expandidos
                    or not isinstance(item.get("nome"), str) or not tema(item["nome"])
                    or ("id_resposta" in item and item["id_resposta"] not in ids_base)
                    or ("area" in item and (not isinstance(item["area"], str)
                                           or not item["area"].strip()))
                    or not isinstance(item.get("aliases", []), list)
                    or not all(isinstance(a, str) and tema(a) for a in item.get("aliases", []))
                    or not isinstance(item.get("fatos"), list) or not 1 <= len(item["fatos"]) <= 12):
                raise ValueError("Conceito textual inválido ou duplicado")
            aspectos = set()
            for fato in item["fatos"]:
                if (not isinstance(fato, dict) or not isinstance(fato.get("texto"), str)
                        or not 1 <= len(fato["texto"].strip()) <= 1000
                        or fato.get("fonte") not in self.fontes
                        or fato.get("papel") not in ("definicao", "detalhe", "exemplo", "causa", "limite")):
                    raise ValueError("Fato sem texto, papel ou fonte válida")
                if "aspecto" in fato:
                    aspecto = fato["aspecto"]
                    if (not isinstance(aspecto, str) or not re.fullmatch(r"[a-z_]+", aspecto)
                            or aspecto in aspectos):
                        raise ValueError("Aspecto inválido ou ambíguo")
                    aspectos.add(aspecto)
            if item["fatos"][0]["papel"] != "definicao":
                raise ValueError("O primeiro fato deve definir o conceito")
            self.expandidos.add(item["id"])
            self._adicionar(item)
        # Uma decisão editorial explícita pode substituir um apelido
        # genérico antigo (galáxia -> Via Láctea), sem escolher por ordem.
        preferencias = dados.get("aliases_preferidos", [])
        if not isinstance(preferencias, list):
            raise ValueError("Preferências de nomes inválidas")
        vistos = set()
        for pref in preferencias:
            if not isinstance(pref, dict) or not isinstance(pref.get("alias"), str):
                raise ValueError("Preferência de nome inválida")
            alias = tema(pref["alias"])
            destino, substitui = pref.get("destino"), pref.get("substitui")
            if (not alias or alias in vistos or destino not in self.expandidos
                    or substitui not in ids_base or destino == substitui
                    or self.aliases.get(alias) != {destino, substitui}):
                raise ValueError("Preferência sem correspondência editorial única")
            vistos.add(alias)
            self.aliases[alias] = {destino}
        refs = dados.get("referencias", [])
        if not isinstance(refs, list):
            raise ValueError("Referências textuais inválidas")
        vistas = set()
        for ref in refs:
            if (not isinstance(ref, dict) or ref.get("origem") not in ids_base | self.expandidos
                    or ref.get("destino") not in self.itens
                    or not isinstance(ref.get("termo"), str) or not tema(ref["termo"])):
                raise ValueError("Referência textual sem origem ou destino válido")
            chave = (ref["origem"], tema(ref["termo"]))
            if chave in vistas:
                raise ValueError("Referência textual ambígua")
            vistas.add(chave)
            self.referencias.append(dict(ref))

    def resolver(self, texto):
        ids = self.aliases.get(tema(texto), set())
        return next(iter(ids)) if len(ids) == 1 else None

    def _temas(self, texto):
        # Um nome composto inteiro tem prioridade sobre separar em 'e'.
        inteiro = self.resolver(texto)
        if inteiro:
            return (inteiro,), []
        partes = re.split(r"\s*,\s*|\s+e\s+", texto, flags=re.I)
        if not 1 <= len(partes) <= 3:
            return (), [texto]
        ids, faltam = [], []
        for parte in partes:
            ident = self.resolver(parte)
            if ident is None:
                faltam.append(parte)
            elif ident not in ids:
                ids.append(ident)
        return tuple(ids), faltam

    def contexto_editorial(self, identificador, resposta):
        if identificador not in self.itens:
            return None
        mostrados = tuple((identificador, i) for i, f in enumerate(self.itens[identificador]["fatos"])
                          if f["texto"] in resposta)
        if not mostrados:
            return None
        return ContextoTexto((identificador,), mostrados, mostrados, "texto", resposta, "base")

    def _selecionar(self, ids, limite, usados=()):
        escolhidos = []
        # Rodadas por tópico impedem que o primeiro consuma todo o espaço.
        for i in range(max(len(self.itens[e]["fatos"]) for e in ids)):
            for ident in ids:
                par = (ident, i)
                if i < len(self.itens[ident]["fatos"]) and par not in usados:
                    escolhidos.append(par)
                    if len(escolhidos) >= limite:
                        return tuple(escolhidos)
        return tuple(escolhidos)

    def _minuscula_inicial(self, frase):
        primeira = frase.split()[0].strip(",:;")
        if len(primeira) > 1 and primeira.isupper():
            return frase
        if any(item["nome"][0].isupper() and frase.startswith(item["nome"] + " ")
               for item in self.itens.values()):
            return frase
        return frase[0].lower() + frase[1:]

    def _ligar(self, frases):
        if len(frases) < 2:
            return " ".join(frases)
        # Conectivo aditivo não cria causalidade, equivalência ou contraste.
        segunda = self._minuscula_inicial(frases[1])
        return frases[0] + " Além disso, " + segunda + (" " + " ".join(frases[2:]) if len(frases) > 2 else "")

    def compor(self, ids, formato="texto", limite=None, anterior=None,
               selecionados=None, origem="escrita"):
        limite = limite or (len(ids) if formato in ("resumo", "simples") else
                            min(8, max(3, len(ids) * 2)))
        escolhidos = selecionados if selecionados is not None else self._selecionar(ids, limite)
        if not escolhidos:
            return "escrita:fim", "Já apresentei os fatos disponíveis sobre esse assunto. Não tenho outro detalhe cadastrado para acrescentar.", None
        from curriculo_mundo import texto_fato
        frases = [texto_fato(self.itens[e]["fatos"][i]) for e, i in escolhidos]
        if formato == "topicos":
            texto = "\n".join("- " + f for f in frases)
        elif formato == "roteiro":
            nomes = ", ".join(self.itens[e]["nome"] for e in ids)
            corpo = self._ligar(frases[:-1]) if len(frases) > 1 else frases[0]
            if len(frases) > 1:
                final = self._minuscula_inicial(frases[-1])
                corpo += "\n\nPara fechar, " + final
            texto = "Roteiro sobre " + nomes + "\n\n" + corpo
        elif formato == "simples":
            texto = "Em poucas palavras:\n" + " ".join(frases)
        else:
            paragrafos = []
            for ident in ids:
                grupo = [texto_fato(self.itens[e]["fatos"][i]) for e, i in escolhidos if e == ident]
                if grupo:
                    paragrafos.append(self._ligar(grupo))
            texto = "\n\n".join(paragrafos)
        usados = tuple(dict.fromkeys((anterior.usados if anterior else ()) + tuple(escolhidos)))
        contexto = ContextoTexto(tuple(ids), tuple(escolhidos), usados, formato, texto, origem)
        return "escrita:" + formato, texto, contexto

    def _conceito(self, ident, aspecto=None):
        indices = [i for i, f in enumerate(self.itens[ident]["fatos"])
                   if aspecto is None or f.get("aspecto") == aspecto]
        if not indices:
            return "fora", "Reconheci o assunto, mas não tenho esse detalhe cadastrado.", None
        escolhidos = tuple((ident, i) for i in indices[:2])
        _, texto, ctx = self.compor((ident,), selecionados=escolhidos, origem="conhecimento")
        # A definição ampliada pode preservar o ID público de uma
        # intenção editorial anterior, sem perder sua origem factual.
        publico = self.itens[ident].get("id_resposta")
        if publico and ident in self.mundo_ids:
            ctx = ctx._replace(origem="base")
        return publico or "conhecimento:" + ident, texto, ctx

    def _fontes(self, contexto):
        fontes = set()
        for e, i in contexto.exibidos:
            fato = self.itens[e]["fatos"][i]
            fontes.update(fato.get("fontes", []))
            if fato.get("fonte"):
                fontes.add(fato["fonte"])
        fontes = sorted(fontes)
        if not fontes:
            texto = "O texto veio da base editorial do CRIVO. Essa entrada não tem uma fonte externa cadastrada."
        else:
            texto = "Fontes dos fatos usados:\n" + "\n".join(
                "- " + (self.fontes[f]["credito"] + ": " if self.fontes[f].get("credito") else "") +
                self.fontes[f]["titulo"] +
                (" (" + ("consulta " if self.fontes[f].get("ano_tipo") == "consulta" else "") +
                 str(self.fontes[f]["ano"]) + ")" if "ano" in self.fontes[f] else "") +
                ": " + self.fontes[f]["url"] for f in fontes)
        # Perguntar pelas fontes não autoriza usar a lista de URLs como fatos.
        return "escrita:fontes", texto, contexto

    def _menciona_mundo(self, texto):
        return any(ids & self.mundo_ids and re.search(
            r"(?<!\w)" + re.escape(alias) + r"(?!\w)", texto)
            for alias, ids in self.aliases.items())

    def _consulta_mundo(self, n, contexto):
        """Seleciona evidências de funções, diferenças e relações completas.

        Não apaga modificadores, negações nem inverte argumentos. Os mesmos
        moldes gramaticais servem para qualquer conceito de um currículo.
        """
        if not self.mundo_ids:
            return None
        falta = ("fora", "Reconheci o assunto, mas não tenho evidência cadastrada "
                 "para essa pergunta completa.", None)
        if self._menciona_mundo(n) and re.search(
                r"\b(diagnostico|diagnostique|dose|remedio|medicamento)\b", n):
            return ("fora", "Posso explicar os conceitos cadastrados, mas não "
                    "determinar diagnóstico, medicamento ou dose para uma pessoa.", None)
        fontes = re.fullmatch(r"(?:qual (?:e )?a fonte|quais (?:sao )?as fontes) (?:de|do|da|sobre) (.+)", n)
        if fontes:
            ident = self.resolver(fontes.group(1))
            if ident in self.mundo_ids:
                return self._fontes(self._conceito(ident)[2])
        comparacao = re.fullmatch(
            r"(?:qual (?:e )?a diferenca entre|diferenca entre|compare) (.+?) (?:e|com) (.+)", n)
        if comparacao is None:
            comparacao = re.fullmatch(r"o que diferencia (.+?) (?:de|do|da) (.+)", n)
        if comparacao:
            a, b = (self.resolver(x) for x in comparacao.groups())
            if a in self.mundo_ids or b in self.mundo_ids or self._menciona_mundo(n):
                for ref in self.comparacoes_mundo:
                    if {a, b} == {ref["origem"], ref["destino"]}:
                        return self.compor((ref["origem"],), "comparacao", selecionados=(
                            (ref["origem"], ref["indice_fato"]),), origem="conhecimento")
                return falta
        padroes = (
            (r"como (?:funciona|funcionam|age|agem) (.+)", "funcionamento"),
            (r"para que (?:serve|servem) (.+)", "funcao"),
            (r"qual (?:e )?(?:a|o) (?:funcao|papel) (?:de|do|da|dos|das) (.+)", "funcao"),
            (r"(?:me )?de (?:um )?exemplo (?:de|do|da) (.+)", "exemplo"),
        )
        for padrao, aspecto in padroes:
            m = re.fullmatch(padrao, n)
            if m is None:
                continue
            alvo = m.group(1)
            if alvo in ("ele", "ela", "isso", "dele", "dela", "disso"):
                ident = contexto.temas[0] if contexto and len(contexto.temas) == 1 else None
            else:
                ident = self.resolver(alvo)
            if ident in self.mundo_ids:
                fatos = self.itens[ident]["fatos"]
                escolhidos = tuple((ident, i) for i, f in enumerate(fatos)
                                   if f.get("aspecto") == aspecto or
                                   aspecto == "exemplo" and f.get("papel") == "exemplo")
                if escolhidos:
                    resultado = self.compor((ident,), "explicacao", selecionados=escolhidos[:3],
                                            origem="conhecimento")
                    publico = self.itens[ident].get("id_resposta")
                    if publico:
                        return publico, resultado[1], resultado[2]._replace(origem="base")
                    return resultado
                return falta
            if self._menciona_mundo(n):
                return falta
        # Verbos cadastrados não são regras causais: cada ligação aponta
        # diretamente para um fato editorial e sua fonte verificável.
        corpo = re.sub(r"^(?:por que|porque|como) ", "", n)
        for ref in self.ligacoes_mundo:
            for verbo in sorted(ref["verbos"], key=len, reverse=True):
                m = re.fullmatch(r"(.+?) " + re.escape(verbo) + r" (.+)", corpo)
                if m and (self.resolver(m.group(1)), self.resolver(m.group(2))) == (
                        ref["origem"], ref["destino"]):
                    return self.compor((ref["origem"],), "relacao", selecionados=(
                        (ref["origem"], ref["indice_fato"]),), origem="conhecimento")
        if re.match(r"(?:por que|porque|como) ", n) and self._menciona_mundo(n):
            return falta
        return None

    def _referencia(self, n, contexto):
        m = re.fullmatch(
            r"(qual (?:e )?o nome|como se chama|onde fica) (?:d?esse|d?essa) "
            r"([a-z-]+)(?: (?:de )?que (?:voce )?(?:falou|citou|mencionou))?", n)
        if not m or contexto is None:
            return None
        operacao, termo = m.groups()
        # O referente precisa estar efetivamente no texto mostrado e ter
        # um vínculo editorial explícito. Nome parecido não cria o vínculo.
        if not any(p.rstrip("s") == termo.rstrip("s") for p in normalizar(contexto.texto).split()):
            return None
        destinos = {r["destino"] for r in self.referencias
                    if r["origem"] in contexto.temas and tema(r["termo"]) == termo}
        if len(destinos) == 1:
            return self._conceito(next(iter(destinos)), "localizacao" if operacao == "onde fica" else None)
        return None

    def responder(self, texto, contexto=None):
        if not isinstance(texto, str) or len(texto) > 1200:
            return None
        n = normalizar(texto)
        n = re.sub(r"^(?:voce )?(?:pode|poderia|consegue) (?:me )?"
                   r"(?=(?:escrever|criar|fazer|produzir|montar|resumir|explicar|falar)\b)", "", n)
        comandos = {
            "mais curto": "resumo", "mais curta": "resumo", "resuma": "resumo",
            "resuma isso": "resumo", "pode resumir": "resumo", "em uma frase": "resumo",
            "em topicos": "topicos", "coloque em topicos": "topicos",
            "transforme em topicos": "topicos", "em palavras simples": "simples",
            "mais simples": "simples", "nao entendi": "simples",
            "explique melhor": "explicacao", "explica melhor": "explicacao",
            "me explique melhor": "explicacao",
        }
        if n in comandos or n in ("qual e a fonte", "qual a fonte", "quais sao as fontes", "fontes"):
            if contexto is None:
                return "duvida", "Preciso de uma resposta anterior sobre um assunto para fazer isso. Qual tema você quer?", None
            if n not in comandos:
                return self._fontes(contexto)
            modo = comandos[n]
            exibidos = contexto.exibidos
            if modo in ("resumo", "simples"):
                exibidos = tuple(next(p for p in contexto.exibidos if p[0] == e)
                                 for e in contexto.temas if any(p[0] == e for p in contexto.exibidos))
            elif modo == "explicacao":
                extras = self._selecionar(contexto.temas, 3, contexto.usados)
                if not extras:
                    return "escrita:fim", "Já apresentei os detalhes disponíveis. Posso resumir ou organizar o que sabemos em tópicos.", None
                exibidos = extras
            return self.compor(contexto.temas, modo, anterior=contexto, selecionados=exibidos)
        if n in ("continue", "continua", "mais", "conte mais") and contexto and contexto.origem != "base":
            extras = self._selecionar(contexto.temas, 2, contexto.usados)
            return self.compor(contexto.temas, "continuacao", anterior=contexto, selecionados=extras)
        if n in ("por que", "porque") and contexto:
            causas = tuple((e, i) for e in contexto.temas for i, f in enumerate(self.itens[e]["fatos"])
                           if f.get("papel") == "causa")
            if causas:
                return self.compor(contexto.temas, "explicacao", anterior=contexto, selecionados=causas)
            return "fora", "Não tenho uma explicação causal cadastrada para essa resposta. Pode especificar o que quer explicar?", None
        consulta_mundo = self._consulta_mundo(n, contexto)
        if consulta_mundo is not None:
            return consulta_mundo
        referencia = self._referencia(n, contexto)
        if referencia:
            return referencia
        m = re.fullmatch(r"e (.+)", n)
        if m and contexto:
            ident = self.resolver(m.group(1))
            if ident in self.expandidos and contexto.origem == "base":
                return self._conceito(ident)
            if ident and contexto.origem != "base":
                return self.compor((ident,), contexto.formato)
        aspecto = None
        m = re.fullmatch(r"qual (?:e )?a distancia (?:(?:de|do|da) )?(.+)", n)
        if m:
            aspecto = "distancia"
        else:
            m = re.fullmatch(r"onde (?:fica|esta) (.+)", n)
            if m:
                aspecto = "localizacao"
        if aspecto:
            alvo = m.group(1)
            if alvo in ("dela", "dele", "disso", "disto", "ela", "ele"):
                if contexto is None or len(contexto.temas) != 1:
                    return "duvida", "De qual assunto você está falando? Preciso de uma referência única na resposta anterior.", None
                ident = contexto.temas[0]
            else:
                ident = self.resolver(alvo)
            if ident in self.expandidos:
                return self._conceito(ident, aspecto)
            return None
        m = re.fullmatch(r"(?:o que (?:e|eh|sao)|o que significa|defina) (.+)", n)
        if m:
            ident = self.resolver(m.group(1))
            if ident in self.expandidos:
                return self._conceito(ident)
            from interpretacao_geral import esclarecer_coordenacao_ou_classificacao
            ids, faltam = self._temas(m.group(1))
            if (len(ids) > 1 and not faltam and any(
                    e in self.expandidos and not (e in self.mundo_ids and
                        self.itens[e].get("id_resposta")) for e in ids)
                    and esclarecer_coordenacao_ou_classificacao(texto) is None):
                return self.compor(ids, "explicacao", limite=len(ids))
            return None
        # Pedidos de composição são explícitos; termos/modificadores que
        # não pertençam ao catálogo não podem ser simplesmente descartados.
        m = re.fullmatch(
            r"(?:(?:escreva|escrever|crie|criar|faca|fazer|produza|produzir|monte|montar) (?:um |uma )?)?"
            r"(texto|resumo|explicacao|roteiro|lista)(?: (curto|curta|breve|simples))? "
            r"(?:sobre|de|a respeito de) (.+)", n)
        if m:
            modo, tamanho, alvo = m.groups()
            limite = None
            frases = re.search(r" em (uma|duas|tres|[1-6]) frases?$", alvo)
            if frases:
                numeral = frases.group(1)
                limite = {"uma": 1, "duas": 2, "tres": 3}.get(numeral)
                limite = limite or int(numeral)
                alvo = alvo[:frases.start()]
            ids, faltam = self._temas(alvo)
            if faltam:
                # Preservar a grafia do pedido original na indicação do
                # trecho faltante ajuda a distinguir termos com acentos.
                return "fora", "Ainda não tenho conhecimento suficiente para atender a todo o pedido: " + texto.strip() + ". Posso compor textos sobre conceitos cadastrados.", None
            if limite and limite < len(ids):
                return "duvida", "Esse limite de frases não cobre todos os temas pedidos. Peça pelo menos uma frase por tema.", None
            if tamanho in ("curto", "curta", "breve") and limite is None:
                limite = max(2, len(ids))
            modo = {"lista": "topicos"}.get(modo, modo)
            if tamanho == "simples":
                modo = "simples"
            return self.compor(ids, modo, limite=limite)
        m = re.fullmatch(r"(?:me )?(fale|falar|conte|explique|explicar|resuma|resumir)(?: sobre)? (.+)", n)
        if m:
            ids, faltam = self._temas(m.group(2))
            if ids and not faltam:
                return self.compor(ids, "resumo" if m.group(1) in ("resuma", "resumir") else "explicacao")
        ident = self.resolver(n)
        if ident in self.expandidos:
            return self._conceito(ident)
        if self._menciona_mundo(n):
            return ("fora", "Reconheci o assunto, mas não tenho evidência cadastrada "
                    "para essa pergunta completa.", None)
        return None
