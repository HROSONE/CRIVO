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
    provas: Tuple[Tuple[str, str], ...] = ()


class QuadroFactual(NamedTuple):
    texto: str
    forma: str            # pergunta normalizada, moldura causal apagada
    intencao: str         # propriedade, quantidade, tempo, causa, mecanismo, comparacao
    assunto: object       # conceito com ficha, ou None
    outros: tuple         # outros conceitos citados (só aceitos em comparação)
    pistas: tuple         # (raiz, palavra original) de cada palavra de conteúdo
    recusa: str           # motivo para não buscar, ou ""
    pedido_nome: bool     # "o que é/foi X", "onde fica X": busca por nome raro


class CompositorTextual:
    LIMIAR_VETOR = 0.62

    def __init__(self, base, caminho, extrair_definicao, curriculo_mundo=None):
        self.itens = {}
        self.aliases = {}
        self.fontes = {}
        self.expandidos = set()
        self.referencias = []
        self.mundo_ids = set()
        self.ultimo_quadro = None
        self.aliases_busca_extra = {}
        self.fichas_busca = set()
        from vetores_palavras import VetoresPalavras
        from lexico_pt import LexicoPT
        self.vetores = VetoresPalavras()
        self.lexico = LexicoPT()
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
        # A memoria sinaptica so coativa fatos com fontes editoriais. Ela
        # NUNCA usa perguntas de prova, feedback de chat ou pesos externos.
        # A inicializacao a partir de provas permite auditar cada resposta.
        # Tabela de nomes da busca factual: um nome leva à única ficha com
        # fontes entre seus significados; preferências explícitas valem.
        self.aliases_busca = {}
        for alias, ids in self.aliases.items():
            fichas = ids & (self.expandidos | self.fichas_busca)
            if len(fichas) == 1:
                self.aliases_busca[alias] = next(iter(fichas))
        self.aliases_busca.update(self.aliases_busca_extra)
        from cortex_associativo import CortexAssociativo
        from crivo import tokens
        self.cortex = CortexAssociativo(self.itens, self.aliases, self.fontes, tokens)

    def _resposta_associativa(self, pergunta):
        """Fallback restrito: evidencia forte de UM fato tipado, mesmo assunto."""
        ativacao = self.cortex.associar(pergunta)
        if ativacao is None:
            return None
        # O circuito so seleciona fatos: o compositor controla a redação,
        # contexto e proveniencia. Nenhum preenchimento probabilistico.
        return self.compor((ativacao.conceito,), "explicacao", selecionados=(
            (ativacao.conceito, ativacao.indice),), origem="conhecimento")

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
            if (fonte.get("reutilizacao") == "somente_referencia" and
                    fonte.get("reproducao_autorizada") is not False):
                raise ValueError("Referência bibliográfica não autoriza reprodução")
        for item in dados["itens"]:
            if (not isinstance(item, dict) or not isinstance(item.get("id"), str)
                    or not re.fullmatch(r"[a-z][a-z0-9_]{1,63}", item["id"])
                    or item["id"] in self.itens or item["id"] in self.expandidos
                    or item["id"] in self.fichas_busca
                    or not isinstance(item.get("nome"), str) or not tema(item["nome"])
                    or ("id_resposta" in item and item["id_resposta"] not in ids_base)
                    or ("area" in item and (not isinstance(item["area"], str)
                                           or not item["area"].strip()))
                    or not isinstance(item.get("aliases", []), list)
                    or not all(isinstance(a, str) and tema(a) for a in item.get("aliases", []))
                    or not isinstance(item.get("fatos"), list) or not 1 <= len(item["fatos"]) <= 12):
                raise ValueError("Conceito textual inválido ou duplicado")
            fatos_por_aspecto = set()
            for fato in item["fatos"]:
                if (not isinstance(fato, dict) or not isinstance(fato.get("texto"), str)
                        or not 1 <= len(fato["texto"].strip()) <= 1000
                        or fato.get("fonte") not in self.fontes
                        or not isinstance(fato.get("fontes", []), list)
                        or not all(isinstance(f, str) and f in self.fontes for f in fato.get("fontes", []))
                        or fato.get("papel") not in ("definicao", "detalhe", "exemplo", "causa", "limite")):
                    raise ValueError("Fato sem texto, papel ou fonte válida")
                if "aspecto" in fato:
                    aspecto = fato["aspecto"]
                    if not isinstance(aspecto, str) or not re.fullmatch(r"[a-z_]+", aspecto):
                        raise ValueError("Aspecto inválido ou ambíguo")
                    # Um aspecto tem varias evidencias, desde que nao repita
                    # literalmente a mesma unidade e sua proveniencia.
                    chave = (aspecto, fato["texto"].strip())
                    if chave in fatos_por_aspecto:
                        raise ValueError("Fato repetido no mesmo aspecto")
                    fatos_por_aspecto.add(chave)
            if item["fatos"][0]["papel"] != "definicao":
                raise ValueError("O primeiro fato deve definir o conceito")
            if item.get("somente_busca") is True:
                # Nome já usado por uma entrada anterior: a ficha atende à
                # busca factual sem tornar o nome ambíguo nas definições.
                self.itens[item["id"]] = item
                self.fichas_busca.add(item["id"])
                for nome in [item["nome"]] + item.get("aliases", []):
                    self.aliases_busca_extra.setdefault(tema(nome), item["id"])
                continue
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
            if pref.get("somente_busca") is True:
                # Só a busca factual passa a preferir a ficha; definições,
                # elipses e referências continuam com a entrada anterior.
                if (not alias or pref.get("destino") not in self.expandidos | self.fichas_busca
                        or alias not in self.aliases or alias in self.aliases_busca_extra):
                    raise ValueError("Preferência de busca sem nome existente")
                self.aliases_busca_extra[alias] = pref["destino"]
                continue
            destino, substitui = pref.get("destino"), pref.get("substitui")
            # "novo": o nome ainda não pertence ao destino (sem alterar o
            # conceito nem as perguntas da rede); só redireciona o apelido
            # que hoje leva exclusivamente à entrada antiga.
            esperado = {substitui} if pref.get("novo") is True else {destino, substitui}
            if (not alias or alias in vistos or destino not in self.expandidos
                    or substitui not in ids_base or destino == substitui
                    or self.aliases.get(alias) != esperado):
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

    def _sem_aspecto(self, ident):
        _, resposta, ctx = self._conceito(ident)
        resposta += ("\n\nEsses são os fatos disponíveis sobre " + self.itens[ident]["nome"] +
                     ". Não tenho uma explicação separada desse aspecto.")
        return "escrita:explicacao", resposta, ctx._replace(texto=resposta)

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
        # Uma ligacao positiva comprovada nao serve como prova de sua
        # negacao. Reconhecer sujeito, verbo e objeto INTEIROS antes de
        # chegar ao filtro generico de negacoes. A resposta e abstenção,
        # nunca a inversao de uma relacao editorial.
        negada = re.fullmatch(r"(?:o |a |os |as )?(.+?) nao (.+)", n)
        if negada:
            sujeito = self.resolver(negada.group(1))
            predicado = negada.group(2)
            for ligacao in self.ligacoes_mundo:
                if ligacao["origem"] != sujeito:
                    continue
                for verbo in ligacao["verbos"]:
                    prefixo = normalizar(verbo) + " "
                    if (predicado.startswith(prefixo) and
                            self.resolver(predicado[len(prefixo):]) == ligacao["destino"]):
                        return falta
        padroes = (
            (r"como (?:se form(?:a|am|ou|aram)|nasc(?:e|em|eu|eram)|surg(?:e|em|iu|iram)) (.+)", "formacao"),
            (r"como (?:foi|foram) (?:formad[oa]s?|criad[oa]s?|construid[oa]s?) (.+)", "formacao"),
            (r"qual (?:e )?(?:a|o) (?:origem|formacao) (?:de|do|da|dos|das) (.+)", "formacao"),
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

    # Palavras que formulam a pergunta, sem descrever o conteúdo procurado.
    _FORMA_PERGUNTA = frozenset("""
        o a os as um uma uns umas de do da dos das em no na nos nas ao aos
        e com que qual quais quem quanto quanta quantos quantas quando onde como
        por porque para pra me voce sabe saber diga dizer explique fale
        tem ter tenha teem possui possuem possuia existe existem existiu ha
        houve eh sao foi foram era eram esta estao fica ficam faz fazem fez
        acontece aconteceu ocorre ocorreu vale mede medem equivale corresponde
        leva levam demora demoram dar da isso isto ele ela eles elas seu sua
        algum alguma alguns algumas mesmo realmente verdade certo sim
        seus suas tao muito deixa deixam torna tornam causa causam provoca provocam
        explica explicam afeta afetam influencia influenciam continua continuam
        mecanismo maneira modo so apenas somente gente
    """.split())
    # Formas irregulares de "ver" que o radical não une ("vê" ≠ "vemos").
    _FORMAS_VER = {"ve": "vemos", "veem": "vemos", "vejo": "vemos", "vi": "vemos",
                   "enxerga": "vemos", "enxergamos": "vemos", "enxergam": "vemos"}
    # Nomes genéricos dispensáveis quando um nome próprio raro identifica
    # o assunto ("missão DART"): não são qualificadores do fato.
    _NOMES_GENERICOS = frozenset("missao sonda nave projeto experimento evento".split())
    # Pequena ponte lexical para pistas de pergunta; cada grupo só aceita
    # palavras que aparecem literalmente nos fatos.
    _EQUIVALENTES = {
        "lua": ("lua", "satelit"), "satelit": ("lua", "satelit"),
        "vida": ("vida", "vivo", "organism"),
        "idad": ("idad", "anos"), "temp": ("temp", "dura", "anos", "dias"),
        "volt": ("volt", "revoluc", "orbit", "translac"),
        "temperatur": ("temperatur", "quent", "calor"),
        "detect": ("detect", "detecc", "observ"),
        "quent": ("quent", "temperatur", "calor"),
        "maior": ("maior", "superior", "mais"), "mais": ("maior", "superior", "mais"),
        "menor": ("menor", "inferior", "menos"), "menos": ("menor", "inferior", "menos"),
        "vermelh": ("vermelh", "avermelh"), "avermelh": ("vermelh", "avermelh"),
        "estaco": ("estac", "sazon"), "estac": ("estac", "sazon"),
        "retem": ("retem", "retend", "reten", "reter", "retid"),
    }
    # Linguagem causal explícita no fato: coocorrência não basta para
    # responder "por que" ou "o que causa".
    _CAUSAL = re.compile(
        r"\b(?:produz\w*|caus\w*|provoc\w*|resulta\w*|explic\w*|contribu\w*|"
        r"gera|geram|eleva\w*|ret[eé]m|retendo|devido|por causa|porque|por isso|leva a|levam a|"
        r"faz com que|torna\w*|mant[eé]m|impulsion\w*|alimenta\w*)\b")
    _SUFIXOS = ("amento", "imento", "acoes", "acao", "icoes", "icao", "aram",
                "eram", "iram", "ados", "adas", "idos", "idas", "ando", "endo",
                "ado", "ada", "ido", "ida", "ou", "eu", "iu", "am", "em", "ar",
                "er", "ir", "es", "a", "e", "o", "s")

    def _raiz(self, palavra):
        # Plural primeiro: "extremas" e "extrema" têm a mesma raiz.
        if len(palavra) > 4 and palavra.endswith("s") and not palavra.endswith(("ss", "us", "is")):
            palavra = palavra[:-1]
        for sufixo in self._SUFIXOS:
            if palavra.endswith(sufixo) and len(palavra) - len(sufixo) >= 4:
                return palavra[:-len(sufixo)]
        return palavra

    def _raizes(self, texto):
        return [self._raiz(p) for p in normalizar(texto).replace("-", " ").replace(",", " ").split()]

    def _pista_no_fato(self, pista, raizes_fato):
        opcoes = self._EQUIVALENTES.get(pista, (pista,))
        return any(r.startswith(o) for o in opcoes for r in raizes_fato)

    def _padrao_alias(self, alias, ident):
        """Nome próprio ("Lua", "Marte") não aceita plural: "luas" é
        substantivo comum. Conceitos comuns aceitam o plural simples."""
        plural = "s?" if not self.itens[ident]["nome"][:1].isupper() else ""
        return r"(?<![a-z0-9])" + re.escape(alias) + plural + r"(?![a-z0-9])"

    def _menciona_conceito(self, ident, texto_normalizado):
        return any(destino == ident and re.search(self._padrao_alias(alias, ident), texto_normalizado)
                   for alias, destino in self.aliases_busca.items())

    def assunto_mencionado(self, texto):
        """Único conceito com ficha citado por nome inteiro no texto."""
        n = normalizar(texto)
        achados = {ident for alias, ident in self.aliases_busca.items()
                   if re.search(self._padrao_alias(alias, ident), n)}
        return next(iter(achados)) if len(achados) == 1 else None

    def _descricao(self, alvo):
        """"Descreva Vênus como um mundo do Sistema Solar": o conceito do
        início, desde que o enquadramento só use palavras dos seus fatos ou
        nomes de outros conceitos cadastrados."""
        palavras = alvo.split()
        for fim in range(len(palavras), 0, -1):
            ident = self.resolver(" ".join(palavras[:fim]))
            if ident in self.expandidos:
                break
        else:
            return None
        resto = " ".join(palavras[fim:])
        for alias, ids in self.aliases.items():
            if len(ids) == 1 and next(iter(ids)) in self.expandidos and len(alias) >= 4:
                resto = re.sub(r"(?<![a-z0-9])" + re.escape(alias) + r"s?(?![a-z0-9])", " ", resto)
        raizes = [r for f in self.itens[ident]["fatos"] for r in self._raizes(f["texto"])]
        for palavra in resto.split():
            if palavra in self._FORMA_PERGUNTA or palavra in ("como", "sendo", "enquanto"):
                continue
            if not self._pista_no_fato(self._raiz(palavra), raizes):
                return None
        return ident

    def _elo(self, par, excluidos):
        """Um único salto: a definição de UM outro conceito com ficha que o
        fato escolhido cita por nome inteiro. Nunca um conceito parecido."""
        texto = normalizar(self.itens[par[0]]["fatos"][par[1]]["texto"])
        citados = {ident for alias, ident in self.aliases_busca.items()
                   if ident not in excluidos and len(alias) >= 4
                   and re.search(self._padrao_alias(alias, ident), texto)}
        if len(citados) != 1:
            return None
        citado = next(iter(citados))
        definicao = self.itens[citado]["fatos"][0]
        if definicao.get("papel") != "definicao":
            return None
        # O elo precisa acrescentar algo ligado ao fato, não só repetir o nome.
        nomes = {r for a, ident in self.aliases_busca.items() if ident == citado for r in self._raizes(a)}
        comuns = ({r for r in self._raizes(texto) if len(r) >= 5} &
                  {r for r in self._raizes(definicao["texto"]) if len(r) >= 5}) - nomes
        if len(comuns) < 2:
            return None
        return (citado, 0)

    def interpretar(self, texto):
        """Quadro único da pergunta factual: o que se pede, sobre qual
        conceito, com quais pistas e por que (se for o caso) não buscar.

        A interpretação é feita uma vez e consumida pelo planejador da
        busca e pelas decisões do Crivo (ficha versus resposta antiga).
        """
        if not isinstance(texto, str):
            return None
        n = normalizar(texto)
        vazio = QuadroFactual(texto, n, "geral", None, (), (), "", False)
        if len(texto) > 320:
            return vazio._replace(recusa="tamanho")
        if re.search(r"\b(nao|nunca|jamais|nem|sem|exceto|supondo|imaginando|imagine|"
                     r"fictici[oa]s?|inventad[oa]s?|hipotetic[oa]s?|magic[oa]s?|dose|dosagem|"
                     r"medicamento|remedio|diagnostico)\b|(?:^|\b(?:e|mas) )se\b", n):
            return vazio._replace(recusa="negacao_ou_qualificador")
        palavras = n.replace("-", " ").replace(",", " ").split()
        if not 2 <= len(palavras) <= 16:
            return vazio._replace(recusa="tamanho")
        # "Qual planeta é o maior?" escolhe um item entre vários; não é
        # propriedade de um assunto e fica com as listas e relações.
        if re.match(r"qual (?:e )?(?:o |a )?[a-z]+ (?:e |eh |tem )(?:o |a )?(?:mais|menos|maior|menor)\b", n):
            return vazio._replace(recusa="superlativo")
        # Causa/mecanismo: a moldura sai das pistas, mas a causa exige
        # linguagem causal no próprio fato (coocorrência não prova causa).
        moldura = re.match(
            r"(?:por que|porque|pq|o que (?:deixa|faz|torna|causa|provoca|explica)|"
            r"qual (?:e )?(?:a |o )?(?:causa|razao|motivo)(?: (?:de|do|da|dos|das))?|"
            r"de que (?:maneira|modo|forma)|por qual mecanismo|"
            r"qual (?:e )?o mecanismo(?: (?:de|do|da|dos|das))?)(?= |$)", n)
        causal = bool(moldura) and not re.match(r"(?:de que|por qual|qual (?:e )?o mecanismo)", n)
        comparacao = bool(re.search(r"\b(?:mais|menos|maior|menor|superior|inferior)\b.* (?:que|do que) ", n))
        # Grandezas pedem um valor: "qual a temperatura do Sol?".
        quantidade = bool(re.search(r"\b(quant[oa]s?|quanto tempo)\b", n) or re.match(
            r"qual (?:e )?(?:a |o )?(?:temperatura|distancia|massa|tamanho|diametro|velocidade|"
            r"duracao|altura|pressao|raio)\b", n))
        tempo = bool(re.search(r"\b(quando|idade|ha quanto tempo)\b", n))
        intencao = ("comparacao" if comparacao else "causa" if causal else
                    "mecanismo" if moldura or n.startswith("como ") else
                    "quantidade" if quantidade else "tempo" if tempo else "propriedade")
        pedido_nome = bool(re.match(
            r"(?:o que (?:e|eh|foi|sao|era|eram|aconteceu com)|quem (?:e|foi)|onde (?:fica|esta)|"
            r"(?:me )?(?:fale|fala|conte|conta) (?:sobre|do|da|de)) ", n))
        busca = " " * moldura.end() + n[moldura.end():] if moldura else n
        # Assunto: alias inteiro de um conceito com fontes, o mais longo.
        candidatos = []
        for alias, ident in self.aliases_busca.items():
            for m in re.finditer(self._padrao_alias(alias, ident), busca):
                candidatos.append((m.start(), m.end(), ident))
        candidatos.sort(key=lambda c: (-(c[1] - c[0]), c[0]))
        ocupados, assuntos = [], []
        for ini, fim, ident in candidatos:
            if any(ini < f and i < fim for i, f in ocupados):
                continue
            ocupados.append((ini, fim))
            assuntos.append((ini, ident))
        assuntos.sort()
        # "Urano tem estações": o segundo termo é uma propriedade do
        # primeiro, ligada só por posse; vira pista e não relação.
        if len({i for _, i in assuntos}) > 1:
            primeiro = min(ocupados)
            seguintes = sorted(o for o in ocupados if o != primeiro)
            ponte = busca[primeiro[1]:seguintes[0][0]].split()
            if ponte and set(ponte) <= {"tem", "possui", "possuem", "teve", "com", "e", "sao",
                                        "esta", "estao", "fica", "ficam", "em", "na", "no",
                                        "de", "do", "da", "dos", "das", "suas", "seus", "sua",
                                        "seu", "o", "a", "os", "as", "uma", "um"}:
                ocupados = [primeiro]
                assuntos = assuntos[:1]
        resto = busca
        for ini, fim in sorted(ocupados, reverse=True):
            resto = resto[:ini] + " " + resto[fim:]
        pistas = []
        for palavra in resto.replace("-", " ").replace(",", " ").split():
            if palavra in self._FORMA_PERGUNTA or len(palavra) < 2:
                continue
            palavra = self._FORMAS_VER.get(palavra, palavra)
            raiz = self._raiz(palavra)
            if raiz not in (p for p, _ in pistas):
                pistas.append((raiz, palavra))
        quadro = QuadroFactual(texto, busca, intencao, assuntos[0][1] if assuntos else None,
                               tuple(i for _, i in assuntos[1:]), tuple(pistas), "", pedido_nome)
        # Dois conceitos formam uma relação com direção ("a memória ajuda o
        # sono" ≠ "o sono ajuda a memória"); citar os dois não prova nenhuma.
        # Exceção: em "quanto tempo X leva para … Y" o valor pedido é de X; o
        # fato precisa ser da ficha de X e citar Y.
        # "A Lua causa as marés?": pergunta direta de causa entre dois
        # conceitos; vale só o fato que cita os dois com linguagem causal.
        if (len(quadro.outros) == 1 and not pistas and not comparacao and re.fullmatch(
                r"(?:(?:a|o|as|os) )?[a-z ]+? (?:causa|causam|provoca|provocam|produz|produzem|"
                r"gera|geram) (?:(?:a|o|as|os) )?[a-z ]+", n.strip(" ?!."))):
            return quadro._replace(intencao="causa")
        if quadro.outros and not comparacao and intencao not in ("quantidade", "tempo"):
            return quadro._replace(recusa="relacao_entre_conceitos")
        if len(pistas) > 6 or (not pistas and intencao not in ("quantidade", "tempo", "causa")):
            return quadro._replace(recusa="sem_pistas")
        return quadro

    @property
    def assunto_busca(self):
        return self.ultimo_quadro.assunto if self.ultimo_quadro else None

    @property
    def busca_explicativa(self):
        return bool(self.ultimo_quadro) and self.ultimo_quadro.intencao in ("causa", "mecanismo") \
            and not self.ultimo_quadro.forma.startswith("como ")

    def buscar_fatos(self, texto, contexto=None):
        """Localiza fatos cadastrados que contêm TODAS as pistas da pergunta.

        O assunto é um nome inteiro cadastrado; as outras palavras de
        conteúdo precisam aparecer no mesmo fato. Nenhum termo é descartado
        para aproximar outro assunto e nenhuma conclusão sim/não é gerada.
        Com vetores de palavras disponíveis, no máximo UMA pista pode casar
        por similaridade alta, e a resposta declara essa aproximação.
        """
        self.ultimo_quadro = quadro = self.interpretar(texto)
        if quadro is None or quadro.recusa:
            return None
        resultado = self._planejar(quadro, aproximar=False)
        # Léxico curado vale até para pergunta de uma só pista ("é feito de
        # quê?"); vetores, nunca sozinhos: exigem outra pista exata.
        if (resultado is None and quadro.pistas
                and (self.lexico.sinonimos or (self.vetores.disponivel and len(quadro.pistas) >= 2))):
            resultado = self._planejar(quadro, aproximar=True)
        return resultado

    def _planejar(self, quadro, aproximar):
        n = quadro.forma
        assunto = quadro.assunto
        quantidade = quadro.intencao == "quantidade" or (
            quadro.intencao == "comparacao" and bool(re.search(r"\bquant", n)))
        tempo = quadro.intencao == "tempo"
        causal = quadro.intencao == "causa" or (
            quadro.intencao == "comparacao" and bool(re.match(r"\s*(?:por que|porque|pq)\b", quadro.texto.casefold())))
        mecanismo = quadro.intencao == "mecanismo"
        comparacao = quadro.intencao == "comparacao"
        pistas = [p for p, _ in quadro.pistas]
        originais = dict(quadro.pistas)
        mencoes = list(quadro.outros)
        if mencoes and causal and not comparacao:
            envolvidos = [assunto] + mencoes
            escolhidos = [(e, i) for e in envolvidos for i, f in enumerate(self.itens[e]["fatos"])
                          if self._CAUSAL.search(normalizar(f["texto"]))
                          and all(self._menciona_conceito(o, normalizar(f["texto"]))
                                  for o in envolvidos if o != e)]
            if not escolhidos:
                return None
            e = escolhidos[0][0]
            _, resposta, ctx = self.compor((e,), "explicacao", selecionados=(escolhidos[0],),
                                           origem="conhecimento")
            return "escrita:explicacao", resposta, ctx
        if mencoes and not comparacao:
            # Quantidade/tempo com outro conceito citado: só a ficha do assunto.
            fatos = self.itens[assunto]["fatos"]
            escolhidos = [(assunto, i) for i, f in enumerate(fatos)
                          if all(self._menciona_conceito(o, normalizar(f["texto"])) for o in mencoes)
                          and re.search(r"\d", f["texto"])
                          and all(self._pista_no_fato(p, self._raizes(f["texto"])) for p in pistas)]
            if not escolhidos:
                return None
            _, resposta, ctx = self.compor((assunto,), "explicacao", selecionados=tuple(escolhidos[:2]),
                                           origem="conhecimento")
            return "escrita:explicacao", resposta, ctx
        aproximacoes = {}

        def casa(fato_texto, exigir_assunto=None):
            raizes = self._raizes(fato_texto)
            faltam = [p for p in pistas if not self._pista_no_fato(p, raizes)]
            if faltam:
                if not aproximar or len(faltam) != 1 or len(originais[faltam[0]]) < 4:
                    return False
                palavra = originais[faltam[0]]
                palavras = [w for w in re.findall(r"[a-z]+", normalizar(fato_texto))
                            if len(w) >= 4 and w not in self._FORMA_PERGUNTA]
                # Primeiro o léxico curado; os vetores só entram se aprovados
                # no controle de qualidade, e nunca para um antônimo listado.
                par = next((w for w in palavras if self.lexico.sinonimo(palavra, w)), None)
                if par is None and self.vetores.disponivel and len(pistas) >= 2:
                    par = self.vetores.mais_parecida(
                        palavra, [w for w in palavras if not self.lexico.antonimo(palavra, w)],
                        self.LIMIAR_VETOR)
                if par is None:
                    return False
                aproximacoes[fato_texto] = (originais[faltam[0]], par)
            texto_fato = normalizar(fato_texto)
            for ident in mencoes + ([exigir_assunto] if exigir_assunto else []):
                if not self._menciona_conceito(ident, texto_fato):
                    return False
            if (quantidade or tempo) and not pistas and not re.search(r"\d", texto_fato):
                return False
            if causal and not self._CAUSAL.search(texto_fato):
                return False
            return True

        prefixo = ""
        escolhidos = []
        if assunto is not None:
            escolhidos = [(assunto, i) for i, f in enumerate(self.itens[assunto]["fatos"])
                          if casa(f["texto"])]
            if not escolhidos and comparacao:
                # A comparação pode estar documentada na ficha do outro termo.
                escolhidos = [(e, i) for e in mencoes for i, f in enumerate(self.itens[e]["fatos"])
                              if casa(f["texto"], assunto)]
            if not escolhidos:
                # O assunto pode estar documentado na ficha de outro
                # conceito ("Mercúrio e Vênus não têm satélites...").
                escolhidos = [(e, i) for e in sorted(self.expandidos | self.fichas_busca) if e != assunto
                              for i, f in enumerate(self.itens[e]["fatos"])
                              if casa(f["texto"], assunto)]
                if len(escolhidos) > 3:
                    return None
        else:
            # Sem ficha própria, só um pedido sobre um NOME ("o que foi o
            # DART?") justifica procurar onde ele é citado.
            if not pistas or not quadro.pedido_nome or aproximar:
                return None
            frequencia = {}
            for e in self.expandidos:
                for f in self.itens[e]["fatos"]:
                    raizes = self._raizes(f["texto"])
                    for p in pistas:
                        if self._pista_no_fato(p, raizes):
                            frequencia[p] = frequencia.get(p, 0) + 1
            raras = [p for p in pistas if 0 < frequencia.get(p, 0) <= 3]
            if not raras:
                return None
            # "Missão", "sonda" etc. só nomeiam a categoria do nome raro.
            genericos = {self._raiz(g) for g in self._NOMES_GENERICOS}
            if any(p not in genericos for p in raras):
                pistas = [p for p in pistas if p not in genericos]
            escolhidos = [(e, i) for e in sorted(self.expandidos | self.fichas_busca)
                          for i, f in enumerate(self.itens[e]["fatos"]) if casa(f["texto"])]
            if not 1 <= len(escolhidos) <= 3:
                return None
            prefixo = ("Não tenho uma ficha própria sobre esse nome, mas ele aparece "
                       "nestes fatos cadastrados:\n\n")
        if not escolhidos:
            return None
        if (quantidade or tempo) and assunto is not None and not any(
                re.search(r"\d", self.itens[e]["fatos"][i]["texto"]) for e, i in escolhidos):
            # O valor pode estar na ficha de outro conceito que cita o assunto.
            outros = [(e, i) for e in sorted(self.expandidos | self.fichas_busca) if e != assunto
                      for i, f in enumerate(self.itens[e]["fatos"])
                      if re.search(r"\d", f["texto"]) and casa(f["texto"], assunto)]
            if 1 <= len(outros) <= 2:
                escolhidos = outros
        if quantidade or tempo:
            com_numero = [p for p in escolhidos
                          if re.search(r"\d", self.itens[p[0]]["fatos"][p[1]]["texto"])]
            if com_numero:
                # Número junto da palavra pedida ("95 luas") vem antes de
                # um número qualquer do mesmo fato ("em 1610").
                def junto(par):
                    palavras = normalizar(self.itens[par[0]]["fatos"][par[1]]["texto"]).split()
                    return any(re.fullmatch(r"[\d.,]+", a) and any(
                        self._pista_no_fato(p, [self._raiz(b)]) for p in pistas for b in palavras[k + 1:k + 3])
                        for k, a in enumerate(palavras))
                com_numero.sort(key=lambda par: not junto(par))
                escolhidos = com_numero
            elif not prefixo:
                prefixo = ("Não tenho esse valor numérico cadastrado. O que encontrei "
                           "sobre isso:\n\n")
        # Um fato de origem só responde primeiro a perguntas de origem:
        # "isótopos de vida curta" não trata de vida em Encélado.
        if not any(p.startswith(("form", "orig", "nasc", "surg")) for p in pistas):
            escolhidos.sort(key=lambda p: self.itens[p[0]]["fatos"][p[1]].get("aspecto") == "formacao")
        escolhidos = tuple(escolhidos[:2 if assunto is not None else 3])
        if (causal or mecanismo) and not prefixo:
            elo = self._elo(escolhidos[0], {e for e, _ in escolhidos} | ({assunto} if assunto else set()))
            if elo is not None:
                escolhidos = escolhidos[:1] + (elo,)
                prefixo = "Juntando fatos cadastrados ligados entre si:\n\n"
        ids = tuple(dict.fromkeys(e for e, _ in escolhidos))
        _, resposta, ctx = self.compor(ids, "explicacao", selecionados=escolhidos,
                                       origem="conhecimento")
        aproximadas = [aproximacoes[self.itens[e]["fatos"][i]["texto"]] for e, i in escolhidos
                       if self.itens[e]["fatos"][i]["texto"] in aproximacoes]
        if aproximadas:
            pergunta, fato = aproximadas[0]
            prefixo = ("Entendi “" + pergunta + "” como próximo de “" + fato + "”, termo usado "
                       "no fato cadastrado:\n\n") + prefixo
        resposta = prefixo + resposta
        # Ficha que herdou uma intenção editorial mantém o ID público dela.
        publico = self.itens[ids[0]].get("id_resposta") if len(ids) == 1 and not prefixo else None
        return publico or "escrita:explicacao", resposta, ctx._replace(texto=resposta)

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
        origem = re.fullmatch(r"(?:(?:me )?(?:explique|explica|conte|conta|fale|fala|descreva)|"
                              r"o que (?:e|eh|foi)) "
                              r"(?:a |sobre a )?(?:origem|formacao) (?:de|do|da|dos|das) (.+)", n)
        if origem and self.resolver(origem.group(1)) is not None:
            n = "como se formou " + origem.group(1)
        descricao = re.fullmatch(r"(?:me )?(?:descreva|descreve|descrever) (?:o |a |os |as )?(.+)", n)
        if descricao:
            alvo = self._descricao(descricao.group(1))
            if alvo is not None:
                return self._conceito(alvo)
        svo = re.fullmatch(r"como (?:(?:o|a|os|as|um|uma) )?(.+?) (se form(?:a|am|ou|aram)|"
                           r"nasc(?:e|em|eu|eram)|surg(?:e|em|iu|iram)|funcionam?)", n)
        if svo and self.resolver(svo.group(1)) is not None:
            n = "como " + svo.group(2) + " " + svo.group(1)
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
        # Aspectos de evidência/limite valem para qualquer catálogo, inclusive
        # conceitos documentais que não são classes da rede de intenções.
        # O alvo completo deve existir: qualificadores não são descartados.
        consulta_evidencia = re.fullmatch(
            r"(?:qual (?:e )?a (evidencia)|quais (?:sao )?as (evidencias)|"
            r"quais (?:sao )?(?:os|as) (limites|limitacoes)) "
            r"(?:(?:de|do|da|dos|das|sobre) (.+)|(disso|dele|dela))", n)
        if consulta_evidencia:
            alvo = consulta_evidencia.group(4) or consulta_evidencia.group(5)
            ident = (contexto.temas[0] if alvo in ("isso","ele","ela","disso","dele","dela")
                     and contexto and len(contexto.temas) == 1 else self.resolver(alvo))
            if ident in self.expandidos:
                limites = bool(consulta_evidencia.group(3))
                escolhidos = tuple((ident,i) for i,f in enumerate(self.itens[ident]["fatos"])
                    if (f.get("papel") == "limite" if limites else f.get("aspecto") == "evidencias"))
                if escolhidos:
                    return self.compor((ident,), "explicacao", selecionados=escolhidos[:3], origem="conhecimento")
                return "fora", "Reconheci o assunto, mas não tenho esse aspecto documentado.", None
            return "fora", "Não tenho evidência cadastrada para esse assunto completo.", None
        consulta_mundo = self._consulta_mundo(n, contexto)
        if consulta_mundo is not None:
            if consulta_mundo[0] == "fora":
                lembranca = self._resposta_associativa(n)
                if lembranca is not None:
                    return lembranca
            return consulta_mundo
        comparacao_geral = re.fullmatch(r"qual (?:e )?a diferenca entre (.+?) e (.+)", n)
        if comparacao_geral:
            ids = tuple(self.resolver(alvo) for alvo in comparacao_geral.groups())
            if all(ident in self.expandidos for ident in ids) and ids[0] != ids[1]:
                pares = tuple((ident, i) for ident in ids for i in range(min(2, len(self.itens[ident]["fatos"]))))
                _, resposta, ctx = self.compor(ids, "comparacao", selecionados=pares, origem="conhecimento")
                resposta = "Para comparar os dois, estes são os fatos disponíveis:\n\n" + resposta
                return "escrita:comparacao", resposta, ctx._replace(texto=resposta)
        # Conceitos editoriais ampliados também participam de perguntas
        # sobre função/funcionamento. Se não houver esse aspecto marcado,
        # mostrar os fatos disponíveis com o limite explícito impede que o
        # recuperador escolha uma resposta de outro assunto por semelhança.
        aspecto_geral = re.fullmatch(r"(?:qual (?:e )?a (funcao) (?:de|do|da)|"
                                    r"como (funcionam?|se form(?:a|am|ou|aram)|nasc(?:e|em|eu|eram)|"
                                    r"surg(?:e|em|iu|iram))|para que (serve|servem)) (.+)", n)
        if aspecto_geral:
            ident = self.resolver(aspecto_geral.group(4))
            if ident in self.expandidos:
                verbo = aspecto_geral.group(2)
                aspecto = ("funcao" if verbo is None else
                           "funcionamento" if verbo.startswith("funciona") else "formacao")
                fatos = self.itens[ident]["fatos"]
                pares = tuple((ident, i) for i, f in enumerate(fatos) if f.get("aspecto") == aspecto)
                if pares:
                    return self.compor((ident,), "explicacao", selecionados=pares[:3], origem="conhecimento")
                if aspecto in ("funcionamento", "formacao"):
                    return None
                return self._sem_aspecto(ident)
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
        # Normalização gramatical de pedidos de definição: extrai o alvo
        # inteiro, sem aproximar nomes ou apagar qualificadores desconhecidos.
        # Funciona para qualquer conceito cadastrado, inclusive sintéticos.
        definicao = re.fullmatch(
            r"(?:defina|definir|defina para mim|explique o significado de|"
            r"qual (?:e )?(?:a definicao|o significado|o sentido) de|"
            r"o que (?:quer dizer|vem a ser|se entende por)|"
            r"(?:me )?(?:diga|explique) o que (?:e|eh)) (.+)", n)
        if definicao:
            alvo = re.sub(r"^(?:o|a|um|uma|os|as) ", "", definicao.group(1))
            ident = self.resolver(alvo)
            if ident in self.expandidos:
                return self._conceito(ident)
            # Não reduzir "planeta fictício" a "planeta".
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
        m = re.fullmatch(r"(?:me )?(fale|fala|falar|conte|conta|contar|explique|explica|explicar|"
                         r"resuma|resumir)(?: (?:sobre|um pouco sobre|algo sobre))? (.+)", n)
        if m:
            ids, faltam = self._temas(m.group(2))
            if ids and not faltam:
                return self.compor(ids, "resumo" if m.group(1) in ("resuma", "resumir") else "explicacao")
        ident = self.resolver(n)
        if ident in self.expandidos:
            return self._conceito(ident)
        lembranca = self._resposta_associativa(n)
        if lembranca is not None:
            return lembranca
        # Nomes acrescentados ao currículo também podem aparecer no meio
        # de consultas legadas: "qual planeta é maior?", "a Lua orbita...".
        # Só bloquear pedidos explicitamente factuais *deste* motor; para
        # outros formatos, devolver o controle aos demais interpretadores.
        pedido_factual = re.match(
            r"^(?:o que (?:e|eh|sao)\b|o que significa\b|defina\b|"
            r"como\b|por que\b|porque\b|"
            r"(?:me )?(?:fale|explique|conte)\b|"
            r"(?:escreva|crie|faca|produza|resuma)\b|"
            r"qual (?:e )?(?:a|o) (?:funcao|papel|diferenca|distancia|origem|formacao)\b)",
            n)
        if pedido_factual and self._menciona_mundo(n):
            return ("fora", "Reconheci o assunto, mas não tenho evidência cadastrada "
                    "para essa pergunta completa.", None)
        return None
