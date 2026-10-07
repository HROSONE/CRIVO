"""Aprender com a conversa e ter curiosidade (07/10/2026).

Três peças, como memória de curto prazo, de longo prazo e consolidação:

  1. Correção na conversa. Depois de uma resposta factual, "não é isso" /
     "está errado" faz o CRIVO oferecer as outras fichas que a busca achou;
     a escolhida passa a responder aquela pergunta até o fim da conversa. Se
     a pessoa conta a resposta certa, ela é anotada como lacuna com a
     resposta do usuário, a conferir em fonte: nunca vira fato sozinha.
  2. Curiosidade. Cada pergunta factual recusada vira uma lacuna. "O que você
     não sabe?" lista as lacunas; na terceira recusa da conversa o CRIVO
     convida a pessoa a ensinar, uma vez só.
  3. Memória e consolidação. Aprendizados e lacunas viajam na memória do
     navegador (só de quem optou por ela) e scripts/consolidar_aprendizados.py
     junta os de várias conversas em dados/aprendizados.json, que os treinos
     (busca, codificador de sentido) usam como exemplos.
"""
import re

from composicao_textual import normalizar

LIMITE_MEMORIA = 20

_NEGATIVO = re.compile(
    r"^(?:(?:nao|n),?\s+)?(?:nao (?:e|era|foi) (?:isso|essa|esse|sobre isso)|nao e isso que eu (?:perguntei|quis)|"
    r"nao perguntei (?:isso|sobre isso)|(?:ta|esta|isso (?:ta|esta)|ta tudo|esta tudo) errad[oa]|errad[oa]|"
    r"resposta errada|voce errou|errou|isso nao responde|nao respondeu|nao tem nada a ver|nada a ver)"
    r"(?:\s+\w+){0,4}[\s.!?]*$")
_POSITIVO = re.compile(
    r"^(?:isso|isso mesmo|exato|exatamente|certo|correto|isso ai|era isso|e isso|perfeito)"
    r"(?:[,!.]?\s*(?:obrigad[oa]|valeu|era isso))?[\s.!?]*$")
_PERGUNTA_LACUNAS = re.compile(
    r"\b(?:o que (?:voce|vc) (?:nao sabe|ainda nao sabe|quer aprender|gostaria de aprender)|"
    r"quais (?:sao )?(?:as )?suas (?:duvidas|lacunas)|o que (?:voce|vc) nao conseguiu responder)\b")
_ESCOLHA = re.compile(r"^\s*(?:a |o |opcao |opção |numero |número )?([1-3])\s*[.!]?\s*$")
FACTUAIS = ("escrita:", "conhecimento:", "leitura:", "aprendizado:")
RECUSAS = ("fora", "duvida", "nocao:nao_sei")


def _chave(texto):
    return " ".join(normalizar(texto).split())


class Aprendizado:
    def __init__(self, bot):
        self.bot = bot
        self.ultima = None        # última resposta factual: pergunta, temas
        self.pendente = None      # correção em andamento: pergunta, opções
        self.sessao = {}          # pergunta → (assunto, índice) aprendido
        self.aprendizados = []    # [{pergunta, assunto, fato, sinal}]
        self.lacunas = []         # [{pergunta, resposta_usuario?}]
        self.recusas = 0
        self.convidou = False

    # ------------------------------------------------------------ memória
    def carregar(self, memoria):
        for a in memoria.get("aprendizados", []):
            if a.get("assunto") in self.bot.compositor.itens:
                self.aprendizados.append(dict(a))
                if a.get("sinal", 1) > 0:
                    self.sessao[_chave(a["pergunta"])] = (a["assunto"], a["fato"])
        self.lacunas.extend(dict(l) for l in memoria.get("lacunas", []))

    def exportar(self):
        return {"aprendizados": self.aprendizados[-LIMITE_MEMORIA:], "lacunas": self.lacunas[-LIMITE_MEMORIA:]}

    # ------------------------------------------------------- antes do turno
    def antes(self, texto):
        """Resposta própria (correção, escolha, lacunas, já aprendido) ou None."""
        n = _chave(texto)
        if self.pendente is not None:
            pendente, self.pendente = self.pendente, None
            escolha = _ESCOLHA.match(n)
            if escolha and int(escolha.group(1)) <= len(pendente["opcoes"]):
                assunto, indice = pendente["opcoes"][int(escolha.group(1)) - 1]
                self._guardar(pendente["pergunta"], assunto, indice, 1)
                return self._mostrar(assunto, indice, "aprendizado:correcao",
                                     "Entendi, obrigado pela correção. ")
            if pendente.get("aceita_resposta") and len(n.split()) >= 2 and not n.endswith("?"):
                self._lacuna(pendente["pergunta"], texto.strip()[:200])
                return ("aprendizado:anotado",
                        "Obrigado! Anotei o que você disse sobre “%s”. Vou conferir isso numa fonte antes de "
                        "usar como fato." % pendente["pergunta"])
        if self.ultima is not None and _NEGATIVO.match(n):
            return self._corrigir()
        if self.ultima is not None and _POSITIVO.match(n) and self.ultima.get("temas"):  # só após resposta
            assunto, indice = self.ultima["temas"][0]
            self._guardar(self.ultima["pergunta"], assunto, indice, 1)
            self.ultima = None
            return "aprendizado:confirmado", "Que bom! Vou lembrar disso."
        if _PERGUNTA_LACUNAS.search(n):
            return self._listar_lacunas()
        aprendido = self.sessao.get(n)
        if aprendido is not None:
            return self._mostrar(*aprendido, "aprendizado:sessao", "")
        return None

    # ------------------------------------------------------ depois do turno
    def depois(self, texto, ident, resposta):
        """Registra a resposta do turno; pode acrescentar o convite a ensinar."""
        if not isinstance(texto, str) or ident.startswith("aprendizado:"):
            return ident, resposta
        ctx = self.bot.contexto_textual
        temas = list(ctx.exibidos) if ctx is not None and ident.startswith(FACTUAIS) else []
        if temas:
            self.ultima = {"pergunta": texto.strip(), "temas": temas}
            return ident, resposta
        self.ultima = None
        quadro = getattr(getattr(self.bot, "estado_interno", None), "quadro", None)
        factual = quadro is not None and not quadro.recusa and "?" in texto
        if ident in RECUSAS and factual:
            # "Não é isso" depois de uma recusa ou dúvida também pede as
            # alternativas que a busca achou.
            self.ultima = {"pergunta": texto.strip(), "temas": []}
            antes = len(self.lacunas)
            self._lacuna(texto.strip())
            self.recusas += len(self.lacunas) > antes
            if self.recusas >= 3 and not self.convidou:
                self.convidou = True
                resposta += ("\n\nPercebi que já são %d perguntas que não sei responder nesta conversa. "
                             "Se você souber alguma resposta, me conte: eu anoto para aprender." % self.recusas)
        return ident, resposta

    # ------------------------------------------------------------ internos
    def _corrigir(self):
        ultima, self.ultima = self.ultima, None
        mostrados = {a for a, _ in ultima["temas"]}
        for a, i in ultima["temas"][:1]:
            self._guardar(ultima["pergunta"], a, i, -1)
        opcoes = []
        try:
            from leitura_ficha import busca_aprendida
            busca = busca_aprendida(self.bot.compositor)
            achados = busca.buscar(ultima["pergunta"], k=12) if busca.aprendida else []
        except Exception:
            achados = []
        for _, assunto, indice in achados:
            if assunto not in mostrados and assunto not in {a for a, _ in opcoes}:
                opcoes.append((assunto, indice))
            if len(opcoes) == 3:
                break
        self.pendente = {"pergunta": ultima["pergunta"], "opcoes": opcoes, "aceita_resposta": True}
        if not opcoes:
            return ("aprendizado:sem_opcao", "Desculpe, entendi errado. Ainda não sei responder isso direito. "
                    "Se você me contar a resposta certa, eu anoto para aprender.")
        itens = self.bot.compositor.itens
        linhas = ["%d. %s" % (k + 1, itens[a]["nome"]) for k, (a, _) in enumerate(opcoes)]
        return ("aprendizado:opcoes", "Desculpe, entendi errado. Você quis saber sobre:\n" + "\n".join(linhas) +
                "\n\nResponda com o número, ou me conte a resposta certa que eu anoto.")

    def _mostrar(self, assunto, indice, ident, prefixo):
        comp = self.bot.compositor
        if assunto not in comp.itens or indice >= len(comp.itens[assunto]["fatos"]):
            return None
        _, texto, ctx = comp.compor((assunto,), "explicacao", selecionados=((assunto, indice),),
                                    origem="conhecimento")
        self.bot.contexto_textual = ctx
        self.bot.ultima_resposta_mostrada = texto
        return ident, prefixo + texto

    def _guardar(self, pergunta, assunto, indice, sinal):
        chave = _chave(pergunta)
        self.aprendizados = [a for a in self.aprendizados
                             if not (_chave(a["pergunta"]) == chave and a["assunto"] == assunto)]
        self.aprendizados.append({"pergunta": pergunta[:300], "assunto": assunto, "fato": int(indice),
                                  "sinal": sinal})
        if sinal > 0:
            self.sessao[chave] = (assunto, int(indice))
        elif self.sessao.get(chave, (None,))[0] == assunto:
            del self.sessao[chave]

    def _lacuna(self, pergunta, resposta_usuario=None):
        chave = _chave(pergunta)
        for l in self.lacunas:
            if _chave(l["pergunta"]) == chave:
                if resposta_usuario:
                    l["resposta_usuario"] = resposta_usuario
                return
        item = {"pergunta": pergunta[:300]}
        if resposta_usuario:
            item["resposta_usuario"] = resposta_usuario
        self.lacunas.append(item)

    def _listar_lacunas(self):
        if not self.lacunas:
            return ("aprendizado:lacunas", "Nesta conversa ainda não apareceu nada que eu não soubesse. "
                    "Quando eu não souber, anoto aqui para aprender depois.")
        linhas = ["- " + l["pergunta"] for l in self.lacunas[-5:]]
        return ("aprendizado:lacunas", "Coisas que me perguntaram e eu ainda não sei:\n" + "\n".join(linhas) +
                "\n\nSe souber alguma, me conte: eu anoto para aprender.")
