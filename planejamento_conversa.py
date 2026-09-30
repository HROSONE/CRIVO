"""Planejamento composicional com dependências, esclarecimento e evidências.

Até seis etapas reutilizam os motores existentes e o catálogo ativo.
Cada trecho precisa ser interpretado inteiro. Os resultados de cada etapa
ficam isolados; a conversa recebe uma só resposta e uma só atualização.
"""
import copy
import re
from typing import NamedTuple

from composicao_textual import tema
from evidencias_conversa import IndiceEvidencias, normalizar
from conversa_assistente import preparar_conversa


class Etapa(NamedTuple):
    operacao: str
    alvo: str = ""
    consulta: str = ""
    uma_frase: bool = False


class Plano(NamedTuple):
    etapas: tuple
    original: str


COMANDO = r"(?:explique|explica|explique-me|defina|o que|como|qual|para que|pra que|resuma|resumir|resum[aoi]|reformule|reescreva|simplifique|organize|coloque|mostre|cite|de |me |aprofunde|desenvolva|compare|em topicos)"
LIGACAO = r"(?:(?:e )?(?:depois|em seguida|entao|ao final|no fim|por fim|agora) )?"
ROTULOS = {"definir": "Explicação", "funcionamento": "Funcionamento", "funcao": "Função",
           "exemplo": "Exemplo", "resumo": "Resumo", "reformulacao": "Reformulação", "simples": "Explicação simples",
           "topicos": "Em tópicos", "fontes": "Fontes", "aprofundar": "Mais detalhes", "comparar": "Comparação",
           "detalhe": "Detalhe", "consulta": "Resposta"}
REFERENCIAS = {tema(t) for t in ("", "isso", "isto", "ele", "ela", "dele", "dela", "disso", "disto", "essa coisa", "esse assunto", "essa explicacao", "essa resposta", "os dois", "ambos", "tudo isso", "a resposta", "a explicacao")}


def limpar_pedido(texto):
    texto = re.sub(r"^\s*(?:oi|ola|bom dia|boa tarde|boa noite)[,!:. ]+", "", texto)
    texto = re.sub(r"^(?:por favor|por gentileza)[,: ]+", "", texto)
    texto = re.sub(r" (?:por favor|por gentileza)$", "", texto)
    for _ in range(3):
        texto = re.sub(r"^(?:voce |vc )?(?:pode|poderia|consegue) (?:me )?(?="+COMANDO+r")", "", texto)
        texto = re.sub(r"^(?:eu )?(?:quero|queria|gostaria de) (?="+COMANDO+r")", "", texto)
        texto = re.sub(r"^"+LIGACAO, "", texto)
    return texto.strip(" ?!.;,")


def analisar_etapa(texto):
    n = limpar_pedido(texto)
    uma_frase = False
    if re.search(r" em (?:uma|1) frase$", n):
        n = re.sub(r" em (?:uma|1) frase$", "", n)
        uma_frase = True
    indireta = re.fullmatch(r"(?:me )?explique ((?:por que|como|qual|onde) .+)", n)
    if indireta:
        return Etapa("consulta", consulta=indireta.group(1))
    # Formas fechadas evitam remover qualificadores no final de um nome.
    formatos = (
        ("resumo", r"(?:resuma|resumir|encurte|faca um resumo)(?: (?:de |da |do )?(.+?))?"),
        ("reformulacao", r"(?:reformule|reescreva)(?: (?:de |da |do )?(.+))?"),
        ("simples", r"(?:simplifique)(?: (?:de |da |do )?(.+))?"),
        ("topicos", r"(?:organize|coloque|mostre)(?: (.+?))? em topicos"),
        ("fontes", r"(?:mostre|cite|diga)(?: (?:a|as|suas) )?(?:fontes|referencias)(?: (?:de |da |do )?(.+))?"),
        ("aprofundar", r"(?:aprofunde|desenvolva)(?: (?:de |da |do )?(.+))?"),
        ("exemplo", r"(?:me )?(?:de|mostre)(?: (?:um|outro))? exemplo(?: (?:(?:de|do|da|sobre) )?(.+))?"),
    )
    for operacao, padrao in formatos:
        m = re.fullmatch(padrao, n)
        if m:
            if uma_frase and operacao != "resumo":
                return None
            return Etapa(operacao, m.group(1) or "", uma_frase=uma_frase)
    if n in ("em topicos", "com outras palavras", "em uma frase"):
        return Etapa({"em topicos": "topicos", "com outras palavras": "reformulacao", "em uma frase": "resumo"}[n])
    m = re.fullmatch(r"(?:compare|faca uma comparacao entre) (.+)", n)
    if m:
        return Etapa("comparar", m.group(1))
    for operacao, padrao in (
        ("funcionamento", r"(?:(?:me )?(?:explique|mostre) )?como (?:funciona|funcionam)(?: (.+))?"),
        ("funcao", r"(?:(?:me )?(?:explique|mostre) )?(?:para que|pra que) (?:serve|servem)(?: (.+))?"),
        ("funcao", r"qual (?:e )?a funcao (?:de|do|da) (.+)"),
        ("definir", r"(?:o que (?:e|sao)|defina|(?:me )?(?:explique|explica))(?: sobre)? (.+)"),
    ):
        m = re.fullmatch(padrao, n)
        if m:
            return Etapa(operacao, m.group(1) or "")
    # Consultas completas continuam nos motores anteriores, sem reduzir
    # uma pergunta causal ou técnica à definição de uma palavra isolada.
    if re.match(r"(?:como|por que|qual|quais|onde|quanto|quantos) ", n):
        return Etapa("consulta", consulta=n)
    return None


class PlanejadorConversa:
    MAX_ETAPAS = 6

    def __init__(self, compositor):
        self.indice = IndiceEvidencias(compositor)
        self.opcoes = ()
        self.pendente = None
        self.ultima_operacao = None
        self.ultimo = None

    def analisar(self, texto):
        if not isinstance(texto, str) or len(texto) > 1200 or any(c in texto for c in ('`', '"', '“', '”')):
            return None
        preparada = preparar_conversa(texto)
        if preparada != texto:
            preparada = re.sub(r"^crivo\b[!,:; .]+", "", preparada, flags=re.I)
        n = normalizar(preparada).strip()
        if re.fullmatch(r".+ e o que[?!.]*", n):
            return None
        m = re.fullmatch(r"sobre (.+?),\s*(.+)", n)
        if m:
            partes = re.split(r"(?:[;?!]\s*|,\s*|\s+e\s+)(?="+LIGACAO+COMANDO+r")", m.group(2))
            if len(partes) > self.MAX_ETAPAS:
                return Plano((Etapa("limite"),), texto)
            etapas = [Etapa("detalhe", m.group(1), partes[0].strip("?!."))]
            for parte in partes[1:]:
                passo = analisar_etapa(parte)
                if passo is None:
                    return Plano((Etapa("nao_interpretado", consulta=parte),), texto)
                etapas.append(passo)
            return Plano(tuple(etapas), texto)
        # Somente separadores seguidos de um comando abrem outra etapa.
        # 'HTML e CSS' e 'campo antes da ponte' continuam nomes inteiros.
        separador = r"(?:[;?!]\s*|,\s*|\s+e\s+)(?="+LIGACAO+COMANDO+r")"
        partes = re.split(separador, n)
        if (len(partes) > 1 and analisar_etapa(partes[0]) is None and
                not re.search(r"[;?!]", n.rstrip(" ?!."))):
            # Um relato seguido de vírgula e pergunta constitui uma
            # consulta contextual, não dois comandos independentes.
            return None
        if len(partes) > self.MAX_ETAPAS:
            return Plano((Etapa("limite"),), texto)
        if len(partes) > 1:
            etapas = []
            for parte in partes:
                passo = analisar_etapa(parte)
                if passo is None:
                    return Plano((Etapa("nao_interpretado", consulta=parte),), texto)
                etapas.append(passo)
            return Plano(tuple(etapas), texto)
        m = re.fullmatch(r"(?:na verdade[, ]+)?(?:nao[, ]+)?(?:quis dizer|eu estava falando de|estava falando de) (.+?)[.!?]*", n)
        if m and self.ultima_operacao:
            return Plano((Etapa(self.ultima_operacao, m.group(1)),), texto)
        etapa = analisar_etapa(n)
        if etapa and etapa.alvo and (re.search(r"\b(primeir[oa]|segund[oa]|terceir[oa]|ultimo|ultima)\b", etapa.alvo)
                                     or len(self.opcoes) > 1 and tema(etapa.alvo) in REFERENCIAS):
            return Plano((etapa,), texto)
        return None

    def _alvos(self, alvo, contexto, bot, escolhidos=None):
        comp = bot.compositor
        n = tema(alvo)
        m = re.fullmatch(r"(?:primeir[oa]|segund[oa]|terceir[oa]|ultim[oa])(?: (?:assunto|tema|conceito|coisa))?", n)
        if m:
            opcoes = escolhidos or self.opcoes or (contexto.temas if contexto else ())
            numero = {"primeiro": 0, "primeira": 0, "segundo": 1, "segunda": 1, "terceiro": 2, "terceira": 2,
                      "ultimo": len(opcoes)-1, "ultima": len(opcoes)-1}[n.split()[0]]
            return (opcoes[numero],) if 0 <= numero < len(opcoes) else ()
        if n in REFERENCIAS:
            ids = escolhidos or (contexto.temas if contexto else ())
            if n in ("dois", "ambos", "tudo isso", "", "resposta", "explicacao", "essa resposta", "essa explicacao"):
                return ids
            return ids if len(ids) == 1 else None
        ids, faltam = comp._temas(alvo)
        return ids if not faltam else ()

    @staticmethod
    def _motor(bot, consulta, contexto):
        # Os índices e pesos são somente lidos. Estado conversacional e
        # histórico são isolados para impedir efeitos parciais no usuário.
        filho = copy.copy(bot)
        filho.historico, filho.ultimos = [], []
        filho.esclarecimento = None
        filho._pedido_turno = None
        filho._contexto_textual_anterior = contexto
        filho.contexto_textual = None
        filho._ato_social_anterior = None
        filho._turno_anterior = None
        filho._referencia_turno_anterior = contexto.texto if contexto else None
        ident, texto = filho._responder_impl(consulta)
        ctx = filho.contexto_textual or filho.compositor.contexto_editorial(ident, texto)
        return ident, texto, ctx

    def preparar(self, texto, bot):
        self.ultimo = None
        if not isinstance(texto, str):
            return None
        n = tema(texto)
        plano = None
        escolhidos = None
        if self.pendente:
            pendente, ids = self.pendente
            ordinal = bot._escolha_ordinal(n)
            ident = bot.compositor.resolver(texto)
            if ordinal is not None and 0 <= ordinal < len(ids):
                ident = ids[ordinal]
            if ident in ids:
                plano, escolhidos = pendente, (ident,)
                self.pendente = None
            elif n in ("sim", "ok", "certo"):
                return self._preparacao("duvida", "Escolha o nome ou o número do assunto; essa confirmação não seleciona um deles.")
            else:
                self.pendente = None
        if plano is None:
            from crivo import chave_pergunta
            if chave_pergunta(preparar_conversa(texto)) in bot.indices_exatos:
                return None
        plano = plano or self.analisar(texto)
        if plano is None:
            return None
        return self.executar(plano, bot, escolhidos)

    @staticmethod
    def _preparacao(ident, texto, contexto=None, origem=""):
        from linguagem_conversa import Ato, Preparacao
        return Preparacao(Ato("plano", "executar"), (ident, texto, contexto, origem))

    def executar(self, plano, bot, escolhidos=None):
        from linguagem_conversa import Lembranca, reescrever
        comp = bot.compositor
        contexto = bot.contexto_textual
        acumulados, temas, blocos, passos, provas = [], [], [], [], []
        atual = contexto
        lembranca = bot.conversacao._atual(bot)
        for etapa in plano.etapas:
            op = etapa.operacao
            if op in ("limite", "nao_interpretado"):
                return self._preparacao("duvida", "Preciso de até seis etapas com pedidos claros. Há um trecho que não consegui interpretar por inteiro.")
            contexto_alvo = atual
            if acumulados and op in ("resumo", "topicos", "fontes", "comparar") and tema(etapa.alvo) in (
                    "", "dois", "ambos", "tudo isso", "resposta", "explicacao"):
                contexto_alvo = self.indice.contexto(temas, acumulados, "\n\n".join(blocos))
            ids = self._alvos(etapa.alvo, contexto_alvo, bot, escolhidos)
            if op == "comparar" and not ids and re.search(r"\s+com\s+", etapa.alvo):
                partes = re.split(r"\s+com\s+", etapa.alvo)
                if len(partes) == 2:
                    a, b = (self._alvos(p, atual, bot, escolhidos) for p in partes)
                    if a and b:
                        ids = tuple(dict.fromkeys(a+b))
            if ids is None:
                candidatos = atual.temas if atual else self.opcoes
                self.pendente = (plano, candidatos)
                lista = "\n".join(str(i+1)+". "+comp.itens[e]["nome"] for i,e in enumerate(candidatos))
                return self._preparacao("duvida", "De qual assunto você está falando?\n"+lista+"\nEscolha o nome ou o número.")
            pares = ()
            resposta = ""
            sucesso = True
            if (op in ("resumo", "reformulacao", "simples", "topicos") and lembranca is not None
                    and lembranca.contexto is None and tema(etapa.alvo) in REFERENCIAS):
                _, resposta, _, origem = bot.conversacao.transformar(op, lembranca, bot)
                passos.append({"operacao": op, "estado": "atendida", "id": origem, "evidencias": []})
                blocos.append(ROTULOS[op]+":\n"+resposta)
                continue
            if op == "consulta":
                ident, resposta, novo = self._motor(bot, etapa.consulta, atual)
                sucesso = ident not in ("fora", "duvida", "vazio", "logica:desconhecido", "logica:sem_ligacao",
                                       "frutas:desconhecido", "escrita:fim") and not ident.startswith(("social:", "contexto:"))
                if novo is not None:
                    ids, pares = novo.temas, novo.exibidos
                if sucesso:
                    lembranca = Lembranca(ident, resposta, novo, bot.conversacao.turno)
                    if ident.startswith("logica:") and ident not in ("logica:desconhecido", "logica:sem_ligacao") or (
                            ident in {e["id"] for e in bot.base} and "\n\nRelações verificadas:" in resposta):
                        provas.append((ident, resposta))
                if sucesso and not pares:
                    # Provas e código mantêm a redação e o motor original;
                    # ficam identificados como resultados, não fatos novos.
                    passos.append({"operacao": op, "estado": "atendida", "id": ident, "evidencias": []})
                    blocos.append(ROTULOS[op]+":\n"+resposta)
                    atual = None
                    continue
            elif not ids:
                sucesso = False
                resposta = "Não encontrei o assunto completo desse pedido na base ativa: “"+etapa.alvo+"”."
                atual = None
                lembranca = None
            elif op == "fontes":
                pares = tuple(p for p in acumulados if p[0] in ids) or tuple(p for p in (atual.exibidos if atual else ()) if p[0] in ids)
                if pares:
                    ctx = self.indice.contexto(ids, pares, "")
                    _, resposta, _ = comp._fontes(ctx)
                else:
                    sucesso = False
                    resposta = "Preciso de fatos apresentados para indicar suas fontes."
            elif op == "comparar":
                if len(ids) != 2:
                    sucesso = False
                    resposta = "Preciso de dois conceitos completos para comparar as definições disponíveis."
                else:
                    consulta = "qual e a diferenca entre "+comp.itens[ids[0]]["nome"]+" e "+comp.itens[ids[1]]["nome"]
                    curada = comp._consulta_mundo(normalizar(consulta), atual)
                    if curada is not None and curada[2] is not None:
                        resposta, pares = curada[1], curada[2].exibidos
                    else:
                        pares = tuple((e, 0) for e in ids)
                        resposta = "\n\n".join(comp.itens[e]["nome"]+": "+comp.itens[e]["fatos"][0]["texto"] for e in ids)
                        resposta += "\n\nEsta comparação reúne as definições disponíveis; não estabelece uma relação causal entre os conceitos."
            elif op == "detalhe":
                pares = tuple(p for e in ids for p in self.indice.buscar(e, etapa.consulta))
                if not pares:
                    sucesso = False
                    resposta = "Reconheci o assunto, mas não tenho uma evidência que cubra esse detalhe completo: “"+etapa.consulta+"”."
            else:
                pares = self.indice.selecionar(ids, op, contexto_alvo)
                if not pares:
                    sucesso = False
                    resposta = "Não tenho "+ROTULOS[op].lower()+" cadastrado para esse assunto."
                elif op in ("reformulacao", "simples"):
                    frases = [reescrever(comp.itens[e]["fatos"][i]["texto"], comp.itens[e]["nome"] if i == 0 else "",
                                         variante=len(passos)+1, simples=op == "simples") for e,i in pares]
                    resposta = "\n\n".join(frases)
            if sucesso and pares and not resposta:
                frases = [comp.itens[e]["fatos"][i]["texto"] for e,i in pares]
                resposta = "\n".join("- "+f for f in frases) if op == "topicos" else "\n\n".join(frases)
                if etapa.uma_frase:
                    resposta = "; ".join(f.rstrip(".!?") for f in frases)+"."
            if sucesso and op in ("resumo", "reformulacao", "simples", "topicos"):
                for _, prova in provas:
                    if prova not in resposta:
                        resposta += "\n\n"+prova
            passos.append({"operacao": op, "alvo": [comp.itens[e]["nome"] for e in ids],
                           "estado": "atendida" if sucesso else "sem_evidencia", "evidencias": self.indice.fontes(pares)})
            blocos.append(ROTULOS[op]+":\n"+resposta)
            if sucesso and pares:
                acumulados.extend(p for p in pares if p not in acumulados)
                temas.extend(e for e in ids if e not in temas)
                if op != "fontes":
                    atual = self.indice.contexto(ids, pares, resposta, atual)
                    lembranca = Lembranca("escrita:plano", resposta, atual, bot.conversacao.turno)
                    self.ultima_operacao = op
        texto = "\n\n".join(blocos)
        atendidas = sum(p["estado"] == "atendida" for p in passos)
        self.ultimo = {"etapas": passos, "completo": atendidas == len(passos)}
        ctx = self.indice.contexto(temas, acumulados, texto, contexto, provas) if acumulados else None
        if temas:
            self.opcoes = tuple(temas) if len(temas) > 1 or not set(temas) <= set(self.opcoes) else self.opcoes
        identificador = "escrita:plano" if atendidas == len(passos) else "escrita:plano_parcial" if atendidas else "fora"
        origem = lembranca.identificador if lembranca is not None and ctx is None else ""
        return self._preparacao(identificador, texto, ctx, origem)

    def registrar(self, identificador, contexto):
        if identificador.startswith(("social:", "conversa:")):
            self.opcoes = ()
            self.pendente = None
            self.ultima_operacao = None
        elif contexto is not None and self.ultimo is None:
            self.opcoes = contexto.temas
            self.ultima_operacao = "definir"
        elif contexto is None and self.ultimo is None and self.pendente is None:
            self.opcoes = ()
            self.ultima_operacao = None
