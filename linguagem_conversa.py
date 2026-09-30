"""Atos de conversa, memória explícita e realização textual do CRIVO.

A gramática descreve operações, nunca perguntas sobre assuntos específicos.
As transformações conservam os índices das evidências. A conversa aberta
organiza relatos do usuário; ela não transforma esses relatos em fatos globais.
"""
import json
import re
import unicodedata
from collections import deque
from functools import lru_cache
from pathlib import Path
from string import Formatter
from typing import NamedTuple

from composicao_textual import ContextoTexto, normalizar
from conversa_assistente import preparar_conversa, identificar_contato


class Ato(NamedTuple):
    nome: str
    operacao: str
    alvo: str = ""
    consulta: str = ""
    formato: str = ""


class Preparacao(NamedTuple):
    ato: Ato
    resultado: object = None


class Lembranca(NamedTuple):
    identificador: str
    texto: str
    contexto: object
    turno: int


FORMATOS = {"", "reformulacao", "simples", "resumo", "topicos", "exploracao", "exemplo", "fontes"}
OPERACOES = {"consulta", "transformar", "retomar", "recapitular", "dialogar", "cancelar"}


def trecho_original(texto, trecho):
    """Reconstrói um argumento sem normalizar seus nomes ou operadores.

    Os índices acompanham a remoção de acentos e a redução de espaços.
    Assim a gramática reconhece operadores em minúsculas, mas a consulta
    recebe 'HTML e CSS' e também conserva pontuação dentro do argumento.
    """
    if not trecho:
        return ""
    letras, posicoes = [], []
    for i, original in enumerate(preparar_conversa(texto)):
        for c in unicodedata.normalize("NFD", original.lower()):
            if unicodedata.category(c) == "Mn":
                continue
            c = c if re.fullmatch(r"[a-z0-9+#_,\-]", c) else " "
            if c != " " or letras and letras[-1] != " ":
                letras.append(c)
                posicoes.append(i)
    preparado = preparar_conversa(texto)
    encontrados = list(re.finditer(re.escape(trecho), "".join(letras)))
    if not encontrados:
        return trecho
    m = encontrados[-1]
    return preparado[posicoes[m.start()]:posicoes[m.end() - 1] + 1]


@lru_cache(maxsize=16)
def carregar_gramatica(caminho):
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if (not isinstance(dados, dict) or dados.get("versao") != 1 or
            not isinstance(dados.get("atos"), list) or not 1 <= len(dados["atos"]) <= 64):
        raise ValueError("Gramática de conversa inválida")
    regras, vistos = [], set()
    for item in dados["atos"]:
        if (not isinstance(item, dict) or not isinstance(item.get("id"), str) or
                not re.fullmatch(r"[a-z_]{1,40}", item["id"]) or item["id"] in vistos or
                not isinstance(item.get("operacao"), str) or item["operacao"] not in OPERACOES or
                not isinstance(item.get("canonico", ""), str) or
                len(item.get("canonico", "")) > 200 or not isinstance(item.get("formato", ""), str) or
                item.get("formato", "") not in FORMATOS or
                not isinstance(item.get("padroes"), list) or not 1 <= len(item["padroes"]) <= 32):
            raise ValueError("Ato de conversa inválido ou duplicado")
        vistos.add(item["id"])
        try:
            campos = {c for _, c, fmt, conv in Formatter().parse(item.get("canonico", ""))
                      if c is not None and not fmt and conv is None}
            if any(fmt or conv for _, _, fmt, conv in Formatter().parse(item.get("canonico", ""))):
                raise ValueError("Formato canônico inválido")
        except ValueError as exc:
            raise ValueError("Formato canônico inválido") from exc
        for padrao in item["padroes"]:
            if not isinstance(padrao, str) or not 1 <= len(padrao) <= 800:
                raise ValueError("Padrão de conversa inválido")
            try:
                regra = re.compile(padrao)
            except re.error as exc:
                raise ValueError("Padrão de conversa inválido") from exc
            if not set(regra.groupindex) <= {"alvo", "outro"} or not campos <= set(regra.groupindex):
                raise ValueError("Campos de conversa inválidos")
            regras.append((item["id"], item["operacao"], regra,
                           item.get("canonico", ""), item.get("formato", "")))
    return tuple(regras)


def reescrever(frase, nome="", variante=0, simples=False):
    """Muda a realização da proposição sem cortar condições ou negações.

    Não processa código, citações, números ou bibliografias. As substituições
    são locais; os fatos completos continuam disponíveis para auditoria.
    """
    if any(c in frase for c in ('`', '"', '“', '”')):
        return frase
    m = re.fullmatch(r"(.+?) (é|são) (.+)", frase)
    if nome and m and not re.search(r"\b(?:não|pode|podem|se|quando)\b", m.group(1), re.I):
        corpo = m.group(3)
        formas = ("O termo {nome} designa {corpo}", "Por {nome}, entende-se {corpo}",
                  "A definição de {nome} é: {corpo}")
        frase = formas[variante % len(formas)].format(nome=nome, corpo=corpo)
    elif nome:
        m = re.fullmatch(r"(.+?) (descreve|define|armazena) (.+)", frase)
        if m and not re.search(r"\b(?:não|pode|podem|se|quando)\b", m.group(1), re.I):
            frase = "O que " + m.group(1) + " " + m.group(2) + " é " + m.group(3)
    equivalencias = (
        (r"\bespecializada em\b", "voltada a"),
        (r"\benvolvida na formação de\b", "que participa da formação de"),
        (r"\bparticipa da\b", "tem participação na"),
        (r"\bparticipa do\b", "tem participação no"),
        (r"\bpermite\b", "torna possível"), (r"\bpermitem\b", "tornam possível"),
        (r"\batravés de\b", "por meio de"), (r"\bconserva\b", "mantém"),
        (r"\bse comunicam\b", "trocam sinais"), (r"\bse comunica\b", "troca sinais"),
    )
    if simples:
        equivalencias += ((r"\breceber e transmitir\b", "receber e enviar"),
                         (r"\bcotidiana\b", "do dia a dia"))
    for padrao, substituto in equivalencias:
        frase = re.sub(padrao, substituto, frase)
    return frase


class Conversacao:
    MAX_LEMBRANCAS = 8
    MAX_INTERVALO = 10

    def __init__(self, caminho=None, usar_neural=True):
        caminho = caminho or Path(__file__).with_name("conhecimento_linguagem.json")
        self.regras = carregar_gramatica(str(Path(caminho).resolve()))
        self.lembrancas = deque(maxlen=self.MAX_LEMBRANCAS)
        self.relatos = deque(maxlen=self.MAX_LEMBRANCAS)
        self.situacoes = deque(maxlen=self.MAX_LEMBRANCAS)
        self.turno = self.variante = self.etapa = 0
        self.pendente = self.assunto = self.objetivo = None
        self.usar_neural = usar_neural
        self.ultimo_quadro_neural = None
        self.erro_neural = None

    def _analisar_neural(self, texto):
        if not self.usar_neural:
            return None
        caminho = Path(__file__).with_name("rede_linguagem.json")
        if not caminho.is_file():
            return None
        try:
            from linguagem_neural import carregar
            rede = carregar(str(caminho.resolve()), caminho.stat().st_mtime_ns)
            q = rede.analisar(texto)
        except (ValueError, KeyError, TypeError, OSError) as exc:
            self.erro_neural = str(exc)
            return None
        if (q is None or q.ato == "outro" or q.confianca < rede.limiar or
                q.margem < .15 or not q.conservado or q.confianca_spans < .15):
            return None
        from rede_sequencial import palavras, token_estrutura
        operadores = {token_estrutura(t, rede.estruturais) for t, _, _ in palavras(texto)}
        evidencias = {"definir": {"definicao", "significado", "entender", "explicar", "que", "termo", "nome"},
                     "funcionamento": {"funciona"}, "funcao": {"funcao", "serve"},
                     "comparar": {"diferenca", "comparacao", "igual"},
                     "negado": {"definicao", "explicar", "fale", "pedido"}}
        if q.ato in evidencias and not operadores & evidencias[q.ato]:
            return None
        self.ultimo_quadro_neural = q._asdict()
        if q.negacao_pedido:
            return Ato("negado_neural", "consulta", q.alvo, texto)
        if q.condicao:
            return Ato("condicional_neural", "consulta", q.alvo, texto)
        formatos = {"reformular": "reformulacao", "simplificar": "simples",
                    "resumir": "resumo", "topicos": "topicos", "fontes": "fontes"}
        if q.ato in formatos:
            if q.alvo or q.outro:
                return None
            return Ato(q.ato, "transformar", formato=formatos[q.ato])
        if q.ato == "retomar" and q.alvo:
            return Ato("retomar", "retomar", q.alvo)
        canonicos = {"definir": "o que é ", "funcionamento": "como funciona ",
                     "funcao": "qual é a função de "}
        if q.ato in canonicos and q.alvo and not q.outro:
            return Ato(q.ato, "consulta", q.alvo, canonicos[q.ato] + q.alvo)
        if q.ato == "comparar" and q.alvo and q.outro:
            return Ato(q.ato, "consulta", q.alvo, "qual é a diferença entre " + q.alvo + " e " + q.outro)
        return None

    def analisar(self, texto, usar_neural=True):
        # Nomes técnicos e operadores são preservados pela normalização do
        # compositor. Código e citações seguem para seus motores originais.
        if not isinstance(texto, str) or len(texto) > 1200 or any(c in texto for c in ('`', '"', '“', '”')):
            return None
        n = normalizar(preparar_conversa(texto))
        if (identificar_contato(texto) is not None or n in
                ("explique melhor", "explica melhor", "me explique melhor") or
                re.match(r"(?:me )?(?:fale|fala) sobre ", n)):
            return None
        n = re.sub(r"^(?:por favor|por gentileza) ", "", n)
        n = re.sub(r" (?:por favor|por gentileza)$", "", n)
        for _ in range(3):
            n = re.sub(r"^(?:voce |vc |tu )?(?:pode|poderia|consegue|conseguiria) (?:me )?"
                       r"(?=(?:explicar|dizer|falar|contar|reformular|reescrever|desenvolver|"
                       r"resumir|organizar|mostrar|dar|retomar|voltar|simplificar|conversar)\b)", "", n)
        estilo = ""
        m = re.fullmatch(r"(.+?) (?:mas |e )?(?:com|em) outras palavras", n)
        if m and re.search(r"\b(?:o que|como|por que|qual)\b", m.group(1)):
            n, estilo = m.group(1), "reformulacao"
        # Operações específicas antes da explicação genérica. Um pedido
        # 'explique por que X não Y' conserva a oração interrogativa inteira.
        especificas = [r for r in self.regras if r[0] != "definir"]
        genericas = [r for r in self.regras if r[0] == "definir"]
        for regras in (especificas, genericas):
            if regras is genericas:
                indireta = re.fullmatch(
                    r"(?:(?:me )?(?:explica|explique|explicar|diga|dizer|conte|contar)|"
                    r"(?:eu )?(?:quero|queria|gostaria de) (?:saber|entender|compreender)) "
                    r"(?P<consulta>(?:o que|por que|porque|como|qual|quais|onde|quando|se) .+)", n)
                if indireta:
                    consulta = trecho_original(texto, indireta.group("consulta"))
                    consulta = re.sub(r"^se ", "", consulta, flags=re.I)
                    consulta = re.sub(r"^o que seria ", "o que é ", consulta, flags=re.I)
                    return Ato("pergunta_indireta", "consulta", consulta=consulta, formato=estilo)
            for nome, operacao, regra, canonico, formato in regras:
                m = regra.fullmatch(n)
                if m:
                    campos = {k: trecho_original(texto, v or "") for k, v in m.groupdict().items()}
                    return Ato(nome, operacao, campos.get("alvo", ""),
                               canonico.format(**campos), estilo or formato)
        if estilo:
            return Ato("estilo", "consulta", consulta=n, formato=estilo)
        return self._analisar_neural(texto) if usar_neural else None

    def _atual(self, bot):
        ctx = bot.contexto_textual
        if ctx is not None:
            origem = bot.ultimo_turno.get("prova_origem", bot.ultimo_turno["id"])
            if ctx.origem == "base" and len(ctx.temas) == 1 and "\n\nRelações verificadas:" in ctx.texto:
                origem = ctx.temas[0]
            return Lembranca(origem, ctx.texto, ctx, self.turno)
        if bot.ultima_resposta_mostrada and bot.ultimo_turno:
            origem = bot.ultimo_turno.get("prova_origem", bot.ultimo_turno["id"])
            if origem == "composto:definicao" and bot.historico:
                ids = tuple(bot.historico[-1].get("fontes_ids", ()))
                pares = tuple((e, i) for e in ids if e in bot.compositor.itens
                              for i, f in enumerate(bot.compositor.itens[e]["fatos"])
                              if f["texto"] in bot.ultima_resposta_mostrada)
                if pares:
                    ctx = ContextoTexto(tuple(dict.fromkeys(e for e, _ in pares)), pares, pares,
                                        "texto", bot.ultima_resposta_mostrada, "base")
                    return Lembranca(origem, ctx.texto, ctx, self.turno)
            return Lembranca(origem, bot.ultima_resposta_mostrada, None, self.turno)
        return None

    def _esclarecer(self, ato, ctx, bot):
        self.pendente = (ato, ctx)
        opcoes = "\n".join(str(i + 1) + ". " + bot.compositor.itens[e]["nome"]
                           for i, e in enumerate(ctx.temas))
        return "duvida", "De qual assunto você quer tratar?\n" + opcoes + "\nEscolha o nome ou o número.", None, ""

    def _escolher(self, texto, bot):
        if self.pendente is None:
            return None
        ato, ctx = self.pendente
        n = normalizar(texto)
        if n in ("nao", "nenhum", "nenhuma", "cancelar"):
            self.pendente = None
            return Preparacao(ato, ("duvida", "Certo. Qual assunto você quer abordar?", None, ""))
        numero = bot._escolha_ordinal(n)
        ident = bot.compositor.resolver(n)
        if numero is not None and 0 <= numero < len(ctx.temas):
            ident = ctx.temas[numero]
        if ident in ctx.temas:
            self.pendente = None
            if ato.operacao == "consulta":
                nome = bot.compositor.itens[ident]["nome"]
                consulta = ("como funciona " if ato.nome == "funcionamento" else "qual é a função de ") + nome
                return Preparacao(ato._replace(alvo=nome, consulta=consulta))
            pares = tuple(p for p in ctx.exibidos if p[0] == ident)
            sub = ctx._replace(temas=(ident,), exibidos=pares)
            return Preparacao(ato, self.transformar(ato.formato, Lembranca("", sub.texto, sub, self.turno), bot))
        if numero is not None or n in ("sim", "isso", "aquela"):
            return Preparacao(ato, self._esclarecer(ato, ctx, bot))
        self.pendente = None
        return None

    def preparar(self, texto, bot):
        self.turno += 1
        self.ultimo_quadro_neural = None
        self.lembrancas = deque((l for l in self.lembrancas
                                if self.turno - l.turno <= self.MAX_INTERVALO), maxlen=self.MAX_LEMBRANCAS)
        self.situacoes = deque((s for s in self.situacoes if self.turno - s[4] <= self.MAX_INTERVALO),
                               maxlen=self.MAX_LEMBRANCAS)
        escolha = self._escolher(texto, bot)
        if escolha is not None:
            return escolha
        ato = self.analisar(texto, usar_neural=False)
        if ato is None:
            relato = self._relato(texto)
            if relato:
                return Preparacao(Ato("relato", "dialogar"), relato)
            return None
        return self.preparar_ato(ato, bot)

    def preparar_ato(self, ato, bot):
        """Executa um quadro já selecionado, sem avançar o turno novamente."""
        if ato.nome == "negado_neural":
            return Preparacao(ato, ("linguagem:negado",
                "Entendi que você não pediu essa explicação. Qual é o pedido que quer fazer?", None, ""))
        if ato.nome == "condicional_neural":
            return Preparacao(ato, ("duvida", "Esse pedido inclui uma condição que preciso esclarecer. "
                "Pode explicar a condição: “" + self.ultimo_quadro_neural["condicao"] + "”?", None, ""))
        atual = self._atual(bot)
        if ato.operacao == "consulta":
            if ato.nome in ("funcionamento", "funcao") and normalizar(ato.alvo) in ("", "isso", "ele", "ela", "essa coisa"):
                if atual is None or atual.contexto is None:
                    return Preparacao(ato, ("duvida", "De qual assunto você quer saber isso?", None, ""))
                if len(atual.contexto.temas) > 1:
                    return Preparacao(ato, self._esclarecer(ato, atual.contexto, bot))
                nome = bot.compositor.itens[atual.contexto.temas[0]]["nome"]
                consulta = ("como funciona " if ato.nome == "funcionamento" else "qual é a função de ") + nome
                ato = ato._replace(alvo=nome, consulta=consulta)
            self.assunto = self.objetivo = None
            return Preparacao(ato)
        if ato.operacao == "cancelar":
            self.lembrancas.clear()
            self.relatos.clear()
            self.situacoes.clear()
            self.assunto = self.objetivo = self.pendente = None
            return Preparacao(ato, ("conversa:reinicio", "Vamos começar outra conversa. Que assunto você quer trazer?", None, ""))
        if ato.operacao == "transformar":
            if atual and atual.contexto and len(atual.contexto.temas) > 1 and ato.formato in ("exploracao", "exemplo"):
                return Preparacao(ato, self._esclarecer(ato, atual.contexto, bot))
            return Preparacao(ato, self.transformar(ato.formato, atual, bot))
        if ato.operacao == "retomar":
            ident = bot.compositor.resolver(ato.alvo) if ato.alvo else None
            candidatos = list(self.lembrancas)
            if ato.alvo:
                candidatos = [l for l in candidatos if ident and ident in l.contexto.temas]
            elif atual and atual.contexto and candidatos and candidatos[-1].contexto.temas == atual.contexto.temas:
                candidatos = candidatos[:-1]
            if not candidatos:
                situacoes = [s for s in self.situacoes if ato.alvo and normalizar(s[0]) == normalizar(ato.alvo)]
                if situacoes:
                    assunto, objetivo, relatos, etapa, _ = situacoes[-1]
                    self.assunto, self.objetivo, self.etapa = assunto, objetivo, etapa
                    self.relatos = deque(relatos, maxlen=self.MAX_LEMBRANCAS)
                    resposta = "Voltando a “" + assunto + "”. Você tinha contado: “" + relatos[-1] + "”."
                    if objetivo:
                        resposta += " Seu objetivo declarado era “" + objetivo + "”."
                    return Preparacao(ato, ("conversa:retomada", resposta + "\n\nO que mudou desde então?", None, ""))
                return Preparacao(ato, ("duvida", "Não encontrei esse assunto na memória recente. Qual tema você quer retomar?", None, ""))
            lembranca = candidatos[-1]
            if ident:
                ctx = lembranca.contexto
                ctx = ctx._replace(temas=(ident,), exibidos=tuple(p for p in ctx.exibidos if p[0] == ident))
                lembranca = lembranca._replace(contexto=ctx)
            elif len(lembranca.contexto.temas) > 1:
                return Preparacao(ato._replace(formato="reformulacao"), self._esclarecer(
                    ato._replace(formato="reformulacao"), lembranca.contexto, bot))
            return Preparacao(ato, self.transformar("retomada", lembranca, bot))
        if ato.operacao == "recapitular":
            return Preparacao(ato, self._recapitular(bot))
        if ato.operacao == "dialogar":
            self.assunto, self.objetivo, self.etapa = ato.alvo or None, None, 0
            self.relatos.clear()
            ids, faltam = bot.compositor._temas(ato.alvo) if ato.alvo else ((), [])
            if ids and not faltam:
                _, resposta, ctx = bot.compositor.compor(ids, limite=max(2, len(ids)))
                resposta += "\n\n" + self._caminhos(ctx, bot)
                return Preparacao(ato, ("escrita:conversa", resposta, ctx._replace(texto=resposta), ""))
            resposta = ("Vamos conversar sobre “" + ato.alvo + "”. Você quer entender uma ideia, contar uma situação ou pensar numa decisão?"
                        if ato.alvo else "Que assunto você quer explorar? Pode trazer uma pergunta, uma situação ou uma ideia.")
            return Preparacao(ato, ("conversa:abertura", resposta, None, ""))
        return None

    def _relato(self, texto):
        if not self.assunto:
            return None
        n = normalizar(texto)
        if n in ("o que voce acha", "e agora", "o que eu faco", "como posso decidir") and self.relatos:
            referencia = self.objetivo or self.relatos[-1]
            resposta = ("Vamos partir do que você trouxe: “" + referencia + "”. "
                        "Que opções você está considerando e qual critério pesa mais para você?")
            return "conversa:reflexao", resposta, None, ""
        if not re.match(r"^(?:eu |estou |to |tenho |sinto |me sinto |quero |pretendo |"
                        r"meu objetivo |o problema |minha dificuldade |nao consigo |ja tentei |tentei |fico |mas )", n):
            return None
        # Relato é citado como relato, nunca promovido ao currículo ou à rede.
        original = texto.strip()[:600]
        self.relatos.append(original)
        objetivo = re.fullmatch(r"(?:eu )?(?:quero|pretendo|meu objetivo e) (.+)", n)
        if objetivo:
            self.objetivo, self.etapa = objetivo.group(1), 1
            pergunta = "Qual é a principal dificuldade para chegar a esse objetivo?"
        elif self.etapa <= 1:
            self.etapa = 2
            pergunta = "O que você já tentou e como isso funcionou para você?"
        elif self.etapa == 2:
            self.etapa = 3
            pergunta = "O que você gostaria que fosse diferente nessa situação?"
        else:
            pergunta = "Qual pequeno próximo passo parece possível para você?"
        resposta = "Você contou: “" + original + "”."
        if self.objetivo and not objetivo:
            resposta += " Seu objetivo declarado é “" + self.objetivo + "”."
        self.situacoes = deque((s for s in self.situacoes if s[0] != self.assunto), maxlen=self.MAX_LEMBRANCAS)
        self.situacoes.append((self.assunto, self.objetivo, tuple(self.relatos), self.etapa, self.turno))
        return "conversa:relato", resposta + "\n\n" + pergunta, None, ""

    @staticmethod
    def _caminhos(ctx, bot):
        fatos = [f for e in ctx.temas for f in bot.compositor.itens[e]["fatos"]]
        opcoes = []
        if any(f.get("aspecto") == "funcionamento" for f in fatos):
            opcoes.append("como funciona")
        if any(f.get("papel") == "exemplo" for f in fatos):
            opcoes.append("um exemplo")
        if any(f.get("papel") == "limite" for f in fatos):
            opcoes.append("os limites dessa explicação")
        return ("Quer explorar " + ", ".join(opcoes) + "?" if opcoes
                else "Qual parte você quer explorar? Posso reformular a explicação ou mostrar as fontes disponíveis.")

    def _recapitular(self, bot):
        pares = tuple(dict.fromkeys(l.contexto.exibidos[0] for l in self.lembrancas if l.contexto.exibidos))
        frases = [bot.compositor.itens[e]["fatos"][i]["texto"] for e, i in pares]
        if self.relatos:
            frases.append("Você contou: “" + "”; “".join(self.relatos) + "”.")
        if not frases:
            return "duvida", "Ainda não há assuntos ou relatos na memória recente. O que você quer conversar?", None, ""
        texto = "Até aqui na conversa:\n" + "\n".join("- " + f for f in frases)
        ctx = ContextoTexto(tuple(dict.fromkeys(e for e, _ in pares)), pares, pares,
                            "recapitulacao", texto, "conversa") if pares else None
        return "escrita:recapitulacao" if ctx else "conversa:recapitulacao", texto, ctx, ""

    def transformar(self, formato, lembranca, bot):
        if lembranca is None:
            return "duvida", "Qual explicação você quer que eu reformule? Preciso de uma resposta anterior ou de um assunto.", None, ""
        ctx = lembranca.contexto
        if ctx is None:
            if formato in ("fontes", "exemplo", "exploracao"):
                return "duvida", "Diga qual assunto você quer explorar. Não tenho unidades editoriais dessa resposta para acrescentar detalhes.", None, ""
            # Provas e exemplos de código continuam íntegros. A nova forma
            # apresenta a conclusão sem alterar operadores ou premissas.
            texto = re.sub(r"^(?:A ideia central é a seguinte:\n\n)+", "", lembranca.texto)
            resposta = reescrever(texto)
            self.variante += 1
            positivos = ("O encadeamento registrado permite responder que sim: ",
                         "A conclusão é sim. A sequência de relações cadastradas é: ")
            resposta = re.sub(r"^(?:Sim\. Consigo concluir isso pelas relações cadastradas: |"
                              r"O encadeamento registrado permite responder que sim: |"
                              r"A conclusão é sim\. A sequência de relações cadastradas é: )",
                              positivos[self.variante % 2], resposta, count=1)
            resposta = resposta.replace("Não. A incompatibilidade foi cadastrada explicitamente: ",
                                        "A resposta é não. O motivo está nesta incompatibilidade registrada: ", 1)
            if formato == "topicos" and "```" not in resposta:
                resposta = "\n".join("- " + p for p in re.split(r"\n\n", resposta))
            elif resposta == texto and not lembranca.identificador.startswith("logica:"):
                resposta = "A ideia central é a seguinte:\n\n" + resposta
            return "escrita:" + formato, resposta, None, lembranca.identificador
        if formato == "fontes":
            return (*bot.compositor._fontes(ctx), "")
        pares = ctx.exibidos
        if formato == "exemplo":
            pares = tuple((e, i) for e in ctx.temas for i, f in enumerate(bot.compositor.itens[e]["fatos"])
                          if f.get("papel") == "exemplo")[:3]
            if not pares:
                return "fora", "Não tenho um exemplo cadastrado desse assunto. Quer reformular a explicação disponível?", None, ""
        elif formato == "exploracao":
            pares = bot.compositor._selecionar(ctx.temas, 3, ctx.usados) or pares
        elif formato == "resumo":
            pares = tuple(next(p for p in pares if p[0] == e) for e in ctx.temas if any(p[0] == e for p in pares))
        if not pares:
            return "duvida", "Qual parte da explicação você quer retomar?", None, ""
        self.variante += 1
        frases = []
        for e, i in pares:
            fato = bot.compositor.itens[e]["fatos"][i]
            frase = fato["texto"]
            if formato not in ("resumo", "topicos"):
                frase = reescrever(frase, bot.compositor.itens[e]["nome"] if fato["papel"] == "definicao" else "",
                                   self.variante, simples=formato == "simples")
            frases.append(frase)
        texto = "\n".join("- " + f for f in frases) if formato == "topicos" else "\n\n".join(frases)
        if formato in ("reformulacao", "simples", "retomada", "topicos"):
            blocos = re.findall(r"```.*?```", ctx.texto, re.S)
            if blocos:
                texto += "\n\n" + "\n\n".join(blocos)
        if ctx.origem == "base" and "\n\nRelações verificadas:" in ctx.texto:
            prova = ctx.texto.split("\n\nRelações verificadas:", 1)[1]
            texto += "\n\nRelações verificadas:" + prova
        if formato == "exploracao":
            texto += "\n\n" + self._caminhos(ctx, bot)
        usados = tuple(dict.fromkeys(ctx.usados + pares))
        novo = ctx._replace(exibidos=pares, usados=usados, formato=formato, texto=texto)
        return "escrita:" + formato, texto, novo, lembranca.identificador

    def registrar(self, identificador, texto, contexto):
        if identificador.startswith("conversa:") or identificador in ("escrita:fontes", "escrita:recapitulacao", "escrita:fim"):
            return
        if contexto is None:
            return
        lembranca = Lembranca(identificador, texto, contexto, self.turno)
        if self.lembrancas and self.lembrancas[-1].contexto.temas == contexto.temas:
            self.lembrancas[-1] = lembranca
        else:
            self.lembrancas.append(lembranca)
