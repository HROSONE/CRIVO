"""Integra escrita aprendida à conversa, com estado e argumentos auditáveis.

Pedidos de criação são ficção explícita; referências pessoais vêm somente
do que foi dito na sessão. Fatos, código e provas continuam nos motores
existentes. A GRU escreve palavras; este módulo resolve intenção/argumentos,
verifica a saída e gerencia a continuidade, sem um banco de respostas.
"""
import re
from pathlib import Path

from composicao_textual import normalizar


def criacao(texto):
    prefixo = (r"(?:por favor,?\s+)?(?:(?:(?:voc[eê]\s+)?(?:pode(?:ria)?|consegue)\s+)?"
               r"(?:me\s+)?(?:invente|inventa|inventar|crie|cria|criar|escreva|escreve|escrever|"
               r"fa[cç]a|fazer|conte|conta|contar|componha|compor|imagine|imaginar)|quero|queria|gostaria de)\s+")
    padrao = (prefixo+r"(?:(?:uma?|alguns?|algumas?)\s+)?"
              r"(?P<tipo>hist[oó]ria|conto|narrativa|poema|versos)"
              r"(?:\s+(?:curt[ao]|breve|pequen[ao]|inventad[ao]|simples|leve|de aventura))*\s+"
              r"(?:sobre|com|envolvendo|que (?:junte|juntasse))\s+(?P<tema>.+)")
    m = re.fullmatch(padrao,texto.strip().strip(".?! "),re.I)
    if not m:
        return None
    assunto = m.group("tema")
    if len(assunto)>400:
        return None
    estilo = "neutro"
    qualificacao = normalizar(texto[:m.start("tema")])
    final = re.search(r"\s+(?:em (?:um )?tom|de (?:um )?jeito)\s+(leve|simples|de aventura)$",assunto,re.I)
    if final:
        qualificacao += " "+normalizar(final.group(1));assunto=assunto[:final.start()]
    if "aventura" in qualificacao: estilo="aventura"
    elif "leve" in qualificacao: estilo="leve"
    elif "simples" in qualificacao: estilo="simples"
    partes = re.split(r"\s+(?:e|com)\s+",assunto,maxsplit=1,flags=re.I)
    slots = {"tema1":partes[0].strip()}
    if len(partes)==2: slots["tema2"]=partes[1].strip()
    if not all(slots.values()): return None
    acao = "poema" if normalizar(m.group("tipo")) in ("poema","versos") else "historia"
    return {"acao":acao,"estilo":estilo,"slots":slots}


def geracao_valida(g, obrigatorios):
    ts = g["tokens"]
    if not g["completa"] or not 6<=len(ts)<=96 or g["log_prob_media"]<-.65:
        return False
    if ts[-1] not in (".","?","!") or any("@"+s not in ts for s in obrigatorios):
        return False
    # Uma sequência repetida indica um laço de decodificação; tenta outra
    # variante em vez de entregar uma frase quebrada ou cortar o texto.
    ngramas = [tuple(ts[i:i+4]) for i in range(len(ts)-3)]
    return len(set(ngramas))==len(ngramas)


class GeracaoConversa:
    MAX_INTERVALO = 10

    def __init__(self, usar_neural=True):
        self.usar_neural=usar_neural
        self.ultima_criacao=None
        self.ultima_resposta=""
        self.variante=0
        self.ultimo_quadro=None
        self.ultima_decisao=None
        self.erro=None

    def limpar(self):
        self.ultima_criacao=None
        self.ultima_resposta=""
        self.variante=0
        self.ultimo_quadro=None
        self.ultima_decisao=None

    def _relato(self, conversa):
        return conversa.dialogo.dados.get("ultimo_relato") or (conversa.relatos[-1] if conversa.relatos else "")

    def _contexto(self, texto, bot, conversa):
        n=normalizar(texto)
        if n in ("me explique seu raciocinio", "explique como chegou a essa resposta") and self.ultima_decisao:
            d=self.ultima_decisao
            fontes="; ".join(nome+": “"+valor+"”" for nome,valor in d["slots"].items())
            return {"justificar":"Usei a operação “"+d["acao"]+"” e estes argumentos da conversa: "+fontes+
                    ". O texto foi previsto palavra por palavra pelo meu modelo pequeno. Isso explica os dados e o processo usados; não é uma prova da conclusão nem um pensamento pessoal."}
        pedido=criacao(texto)
        if pedido is not None:
            return pedido
        final = re.fullmatch(r"(?:(?:agora|entao) )?(?:(?:me )?(?:de|invente|crie) (?:um )?outro (?:final|desfecho)|"
                             r"mude o final(?: da historia)?|como (?:essa|a) historia poderia terminar de outro jeito|"
                             r"queria outro final para esse conto|que outro final daria para imaginar)",n)
        versao = re.fullmatch(r"(?:(?:agora|entao) )?(?:pode (?:fazer|criar) (?:uma )?outra versao|"
                              r"(?:fa[cz]a|escreva|crie) (?:uma )?outra versao|"
                              r"deixe (?:a historia|o poema|o texto) mais (?:leve|simples)|"
                              r"(?:troque|substitua) .+ por .+)",n)
        if final or versao:
            anterior=self.ultima_criacao
            if anterior is None:
                # Reformulações factuais conservam seus operadores/provas.
                if bot.contexto_textual is not None: return None
                return {"esclarecer":"Qual texto você quer mudar? Pode pedir uma história ou um poema e depois uma nova versão."}
            pedido={"acao":"final" if final else anterior["acao"],
                    "estilo":anterior["estilo"],"slots":dict(anterior["slots"])}
            if re.search(r"mais leve$",n): pedido["estilo"]="leve"
            elif re.search(r"mais simples$",n): pedido["estilo"]="simples"
            troca=re.fullmatch(r"(?:troque|substitua)\s+(.+?)\s+por\s+(.+)",texto.strip().strip(".?! "),re.I)
            if troca:
                nome,novo=troca.groups();alvos=[k for k,v in pedido["slots"].items() if normalizar(v)==normalizar(nome) or
                    re.sub(r"^(?:um|uma|o|a) ","",normalizar(v))==normalizar(nome)]
                if len(alvos)!=1 or len(novo)>400:
                    return {"esclarecer":"Qual elemento você quer substituir? Use o nome que apareceu no texto."}
                pedido["slots"][alvos[0]]=novo
            return pedido
        relato=self._relato(conversa)
        if re.fullmatch(r"(?:voce entendeu o que (?:me incomodou|eu quis dizer)|"
                        r"o que voce entendeu do que contei|como voce entendeu a situacao que eu trouxe|"
                        r"me diga o que entendeu de mim)",n):
            return {"acao":"escuta","slots":{"relato":relato}} if relato else {"esclarecer":"Qual situação você quer que eu acompanhe? Ainda não tenho um relato seu nesta conversa."}
        if re.fullmatch(r"(?:voce (?:ja me perguntou isso|esta repetindo a mesma pergunta|continua fazendo a mesma pergunta)|"
                        r"essa (?:sugestao|resposta) nao me ajudou|o que disse nao resolveu minha dificuldade)",n):
            return {"acao":"ajuste","slots":{"relato":relato}} if relato else None
        if re.fullmatch(r"(?:fa[cz]a uma sugestao diferente|me de outra possibilidade|quero tentar outro caminho|"
                        r"tem um jeito diferente de lidar com isso|sugira outra abordagem para meu objetivo)",n):
            slots={"relato":relato} if relato else {}
            objetivo=conversa.dialogo.dados.get("objetivo") or conversa.objetivo
            if objetivo: slots["objetivo"]=objetivo
            for item in reversed(conversa.relatos):
                if re.search(r"\b(?:minutos?|horas?|tempo|prazo|dinheiro)\b",normalizar(item)):
                    slots["restricao"]=item[:400];break
            return {"acao":"alternativa","slots":slots} if objetivo or relato else None
        if (re.search(r"\b(?:incapaz|minha capacidade|nao consigo|nunca vou conseguir)\b",n) and
                re.search(r"\b(?:errei|tentativa|fracassou|nao funcionou|deu errado|erro)\b",n) and
                ("?" in texto or re.match(r"(?:uma |errei |se |so porque )",n))):
            return {"acao":"apoio","slots":{"relato":texto.strip()}}
        if re.fullmatch(r"(?:me de uma ideia concreta usando essas informacoes|crie uma ideia a partir do que contei|"
                        r"combine esses dois elementos numa ideia|o que da para criar juntando essas coisas|"
                        r"proponha uma possibilidade com esses elementos)",n):
            if conversa.dialogo.opcoes:
                a,b=conversa.dialogo.opcoes
            else:
                partes=re.split(r"\s+(?:e|com)\s+",relato,maxsplit=1,flags=re.I)
                if len(partes)!=2:
                    return {"esclarecer":"Quais dois elementos você quer combinar? Posso criar uma possibilidade com os elementos que você escolher."}
                a,b=partes
            return {"acao":"ideia","slots":{"tema1":a[:400],"tema2":b[:400]}}
        return None

    def preparar(self, texto, bot, conversa):
        self.ultimo_quadro=None
        if (not self.usar_neural or not isinstance(texto,str) or not texto.strip() or
                len(texto)>1200 or "`" in texto or "\x00" in texto): return None
        if self.ultima_criacao and conversa.turno-self.ultima_criacao["turno"]>self.MAX_INTERVALO:
            self.ultima_criacao=None
        pedido=self._contexto(texto,bot,conversa)
        if pedido is None: return None
        from linguagem_conversa import Ato,Preparacao
        if "esclarecer" in pedido:
            return Preparacao(Ato("geracao_esclarecer","dialogar"),("duvida",pedido["esclarecer"],None,""))
        if "justificar" in pedido:
            return Preparacao(Ato("geracao_justificar","dialogar"),("conversa:justificativa",pedido["justificar"],None,""))
        caminho=Path(__file__).with_name("rede_geracao.json")
        if not caminho.is_file(): return None
        from linguagem_gerativa import carregar,renderizar
        contexto={"acao":pedido["acao"],"estilo":pedido.get("estilo","neutro"),"slots":pedido["slots"],
                  "mensagem":texto,"historico":[h["pergunta"] for h in bot.historico[-3:]]}
        if pedido["acao"] in ("historia","poema","final","ideia"):
            obrigatorios=set(pedido["slots"])
        elif pedido["acao"]=="alternativa":
            obrigatorios={"objetivo" if pedido["slots"].get("objetivo") else "relato"}
            if pedido["slots"].get("restricao"): obrigatorios.add("restricao")
        else: obrigatorios={"relato"}
        try:
            modelo=carregar(str(caminho.resolve()),caminho.stat().st_mtime_ns)
            for tentativa in range(4):
                contexto["variante"]=(self.variante+tentativa)%4
                g=modelo.gerar(contexto)
                if not geracao_valida(g,obrigatorios): continue
                resposta=renderizar(g,pedido["slots"])
                if resposta==self.ultima_resposta or len(resposta)>2400: continue
                self.variante=(contexto["variante"]+1)%4
                self.ultima_resposta=resposta
                acao=pedido["acao"]
                self.ultimo_quadro={"modelo":"GRU autoral autoregressiva","acao":acao,"tokens":g["quantidade_tokens"],
                                   "log_prob_media":g["log_prob_media"],"variante":contexto["variante"],
                                   "slots_copiados":sorted(obrigatorios)}
                self.ultima_decisao={"acao":acao,"slots":dict(pedido["slots"])}
                if acao in ("historia","poema","final"):
                    self.ultima_criacao={"acao":"historia" if acao=="final" else acao,
                                        "slots":dict(pedido["slots"]),"estilo":contexto["estilo"],"turno":conversa.turno}
                    resposta=("Poema:\n" if acao=="poema" else "Ficção:\n")+resposta
                return Preparacao(Ato("geracao_"+acao,"dialogar"),("conversa:gerada_"+acao,resposta,None,""))
        except (ValueError,KeyError,TypeError,OSError) as exc:
            self.erro=str(exc)
            return None
        # Uma saída incerta não substitui a geração por uma resposta
        # selecionada de exemplos de treino; pede um detalhe para tentar.
        return Preparacao(Ato("geracao_incerta","dialogar"),("duvida",
            "Não consegui completar uma resposta coerente para esse pedido. Pode especificar o tema ou o que quer mudar?",None,""))

    def registrar(self, identificador):
        if identificador=="conversa:reinicio": self.limpar()
        elif identificador=="conversa:abertura":
            self.ultima_criacao=self.ultima_decisao=None
        elif not identificador.startswith("conversa:") and identificador!="duvida":
            self.ultima_criacao=self.ultima_decisao=None
