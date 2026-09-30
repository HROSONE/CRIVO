"""Escrita aprendida, interpretação e argumentos conservados na sessão."""
import re
from collections import deque
from pathlib import Path

from composicao_textual import normalizar
from pedidos_gerativos import criacao, mensagem, reflexao, revisao, texto_pedido


def geracao_valida(g, obrigatorios, acao=None):
    ts=g["tokens"]
    if not g["completa"] or not 6<=len(ts)<=128 or g["log_prob_media"]<-.65:
        return False
    if ts[-1] not in (".","?","!") or any("@"+s not in ts for s in obrigatorios):
        return False
    if acao=="exploracao" and "?" not in ts:
        return False
    ngramas=[tuple(ts[i:i+4]) for i in range(len(ts)-3)]
    return len(set(ngramas))==len(ngramas)


class GeracaoConversa:
    MAX_INTERVALO=10

    def __init__(self, usar_neural=True):
        self.usar_neural=usar_neural
        self.erro=None
        self.limpar()

    def limpar(self):
        self.ultima_criacao=self.ultima_escrita=self.ultima_decisao=None
        self.ultima_resposta=self.resposta_anterior=""
        self.respostas_recentes=deque(maxlen=3)
        self.relatos_recentes=deque(maxlen=8)
        self.pendente=None
        self.objetivo_declarado=None
        self.variante=0
        self.ultimo_quadro=None

    def _relatos(self, conversa):
        return [r["texto"] for r in self.relatos_recentes if conversa.turno-r["turno"]<=self.MAX_INTERVALO]

    def _relato(self, conversa):
        relatos=self._relatos(conversa)
        return relatos[-1] if relatos else ""

    def _pessoais(self, conversa):
        relatos=self._relatos(conversa)
        if not relatos: return {}
        slots={"relato":relatos[-1]}
        if len(relatos)>1 and relatos[-2]!=relatos[-1]: slots["detalhe"]=relatos[-2]
        return slots

    def _objetivo(self, conversa):
        d=self.objetivo_declarado
        atual=conversa.dialogo.dados.get("objetivo") or conversa.objetivo
        return atual if d and d["valor"]==atual and conversa.turno-d["turno"]<=self.MAX_INTERVALO else None

    def _restricao(self, conversa):
        for item in reversed(self._relatos(conversa)):
            if re.search(r"\b(?:minutos?|horas?|tempo|prazo|dinheiro|orcamento)\b",normalizar(item)):
                return item
        return ""

    def _estado(self, conversa):
        return {"relato":bool(self._relato(conversa)),"objetivo":bool(self._objetivo(conversa)),
                "restricao":bool(self._restricao(conversa)),"criacao":self.ultima_criacao is not None,
                "tipo_escrita":self.ultima_escrita["tipo"] if self.ultima_escrita else ""}

    def _pedido_pessoal(self, acao, conversa, explicito=False):
        if not explicito and not conversa.dialogo.ativo:
            return {"esclarecer":"Você quer voltar a qual situação pessoal? Conte o objetivo ou indique o relato que devo considerar."}
        if acao=="plano" or acao=="alternativa" and self._objetivo(conversa):
            objetivo=self._objetivo(conversa)
            if not objetivo: return {"esclarecer":"Qual resultado você quer alcançar? Conte o objetivo e as restrições que devo considerar."}
            slots={"objetivo":objetivo}
            restricao=self._restricao(conversa)
            if restricao: slots["restricao"]=restricao
        else:
            slots=self._pessoais(conversa)
            if not slots: return {"esclarecer":"Qual situação você quer explorar? Ainda não tenho um relato recente seu nesta conversa."}
            if acao not in ("resumo","reformulacao"):
                slots.pop("detalhe",None)
        return {"acao":acao,"slots":slots}

    def _revisar(self, mudanca, conversa, bot):
        anterior=self.ultima_escrita
        if anterior is None:
            if bot.contexto_textual is not None: return None
            return {"esclarecer":"Qual texto você quer mudar? Pode pedir uma história, um poema, uma mensagem ou um diálogo e depois uma nova versão."}
        tipo=anterior["tipo"];operacao=mudanca["operacao"]
        if operacao in ("final","continuacao") and tipo not in ("historia","dialogo"):
            return {"esclarecer":"Você quer uma nova versão deste texto ou continuar uma história? Indique qual desses pedidos prefere."}
        pedido={"acao":operacao if operacao in ("final","continuacao") else tipo,
                "estilo":mudanca.get("estilo",anterior["estilo"]),"slots":dict(anterior["slots"]),"tipo":tipo}
        pedido["slots"].pop("detalhe",None)
        if operacao=="continuacao":
            cenas=re.split(r"(?<=[.!?])\s+",anterior["texto"])
            cena=cenas[-1].strip() if cenas else ""
            if cena: pedido["slots"]["detalhe"]=cena[:600]
        if mudanca.get("troca"):
            nome,novo=mudanca["troca"]
            nome_limpo=re.sub(r"^(?:um|uma|o|a) ","",normalizar(nome))
            alvos=[k for k,v in pedido["slots"].items() if k in ("tema1","tema2","destinatario") and
                   (normalizar(v)==normalizar(nome) or
                    re.sub(r"^(?:um|uma|o|a) ","",normalizar(v))==nome_limpo)]
            if len(alvos)!=1 or not 1<=len(novo)<=400:
                return {"esclarecer":"Qual elemento você quer substituir? Use o nome que apareceu no texto."}
            pedido["slots"][alvos[0]]=novo
        if mudanca.get("encurtar"): pedido["encurtar"]=True
        return pedido

    def _esclarecer_escrita(self, texto, conversa):
        n=texto_pedido(texto)
        m=re.fullmatch(r"(?:me )?(?:invente|inventa|inventar|crie|cria|criar|escreva|escreve|escrever|"
                       r"fa[cz]a|fazer|conte|conta|contar|quero|queria) (?:uma? )?"
                       r"(historia|conto|poema|dialogo|mensagem)(?: (?:curt[ao]|breve))?",n)
        if m:
            acao={"conto":"historia"}.get(m.group(1),m.group(1))
            return {"esclarecer":"Sobre o que você quer esse texto?" if acao!="mensagem" else
                    "O que você quer comunicar na mensagem? Pode informar também para quem ela é.",
                    "pendente":{"acao":acao,"estilo":"neutro","slots":{},"turno":conversa.turno}}
        m=re.fullmatch(r"(?:me\s+)?(?:escreva|escreve|escrever|crie|criar|prepare|redija|quero|queria)"
                       r"\s+(?:uma?\s+)?mensagem\s+(?:para|pra|pro)\s+(.+)",texto.strip().strip(".?! "),re.I)
        if m and len(m.group(1))<=400:
            return {"esclarecer":"O que você quer comunicar para “"+m.group(1)+"”?",
                    "pendente":{"acao":"mensagem","estilo":"neutro","slots":{"destinatario":m.group(1)},"turno":conversa.turno}}
        return None

    def _completar(self, texto, conversa, bot):
        if not self.pendente: return None
        p=self.pendente
        if conversa.turno-p["turno"]>3:
            self.pendente=None;return None
        if conversa.dialogo._pedido_prioritario(texto,bot,conversa):
            self.pendente=None;return None
        n=texto_pedido(texto)
        if (n in ("oi","ola","nao","nao obrigado","cancelar","esqueca essa conversa","mudar de assunto") or
                re.match(r"(?:eu )?nao (?:quero|preciso|vou|pretendo|escreva|crie|continue|fa[cz]a|fazer)\b",n) or
                re.fullmatch(r"(?:cancele|cancelar|cancela)(?: (?:esse|o|este) pedido)?",n) or
                re.match(r"(?:o que|como|por que|qual|quais|quanto|quem|onde|quando|"
                         r"explique|explicar|defina|definir|liste|listar|mostre|mostrar|"
                         r"escreva|crie|invente|resuma|reformule)\b",n)):
            self.pendente=None;return None
        if "?" in texto or len(texto)>600: return None
        assunto=re.sub(r"^(?:sobre|a respeito de|dizendo que)\s+","",texto.strip().strip(". "),flags=re.I)
        if not assunto: return None
        if p["acao"]=="mensagem":
            pedido={"acao":"mensagem","estilo":p["estilo"],"slots":dict(p["slots"],relato=assunto)}
        else:
            nome={"historia":"história","poema":"poema","dialogo":"diálogo"}[p["acao"]]
            pedido=criacao("Crie um "+nome+" sobre "+assunto)
        if pedido is not None: self.pendente=None
        return pedido

    def _rotear(self, texto, bot, conversa):
        if bot.contexto_textual is not None or not conversa.dialogo.ativo: return None
        n=normalizar(texto)
        # Um relato novo atualiza as fontes; palavras como "meu" não
        # autorizam transformar uma declaração em pedido de reescrita.
        if ("?" not in texto and not re.match(r"(?:me |voce |ajude |ajuda |resuma |"
                r"reformule |organize |sugira |fa[cz]a |diga |mostre |"
                r"como |o que |qual |quais |tem (?:um|uma|outro|outra) )",n)):
            return None
        if (not self._relato(conversa) or re.match(r"(?:nao |se |quando |caso )",n) or
                any(c in texto for c in ('"','“','”')) or
                not re.search(r"\b(?:isso|disso|nisso|contei|relato|minhas?|meu|voce|pergunta|ideias?|"
                              r"sugestao|ajude|ajuda|pensar|decidir|organizar|comecar|entendeu)\b",n)):
            return None
        if conversa.dialogo._pedido_prioritario(texto,bot,conversa): return None
        if conversa.analisar(texto,usar_neural=False) is not None: return None
        antigo=conversa.dialogo.analisar(texto,bot,conversa)
        if antigo not in (None,"relato","resposta"): return None
        caminho=Path(__file__).with_name("rede_intencao_gerativa.json")
        if not caminho.is_file(): return None
        try:
            from intencao_gerativa import carregar
            modelo=carregar(str(caminho.resolve()),caminho.stat().st_mtime_ns)
            q=modelo.analisar(texto,self._estado(conversa))
            if not q.get("aceita"): return None
            acao=q["acao"]
            if acao in ("resumo","reformulacao","exploracao","escuta","ajuste","plano"):
                pedido=self._pedido_pessoal(acao,conversa);pedido["roteador"]=q;return pedido
            if acao=="alternativa":
                pedido=self._pedido_pessoal("alternativa",conversa)
                if "acao" in pedido: pedido["roteador"]=q
                return pedido
        except (ValueError,KeyError,TypeError,OSError) as exc:
            self.erro=str(exc)
        return None

    def _contexto(self, texto, bot, conversa):
        n=texto_pedido(texto)
        if n in ("me explique seu raciocinio","explique como chegou a essa resposta") and self.ultima_decisao:
            d=self.ultima_decisao
            fontes="; ".join(nome+": “"+valor+"”" for nome,valor in d["slots"].items())
            return {"justificar":"Usei a operação “"+d["acao"]+"” e estes argumentos da conversa: "+fontes+
                    ". O texto foi previsto palavra por palavra, usando também a resposta anterior. Esses são os dados e o processo usados; a explicação não cria uma prova da conclusão."}
        pedido=criacao(texto) or mensagem(texto)
        if pedido is not None:
            if pedido["acao"]=="mensagem" and normalizar(pedido["slots"]["relato"]) in ("isso","o que contei","o que te contei"):
                relato=self._relato(conversa)
                if not relato: return {"esclarecer":"O que você quer comunicar na mensagem? Ainda não tenho esse relato."}
                pedido["slots"]["relato"]=relato
            self.pendente=None;return pedido
        mudanca=revisao(texto)
        if mudanca: return self._revisar(mudanca,conversa,bot)
        reflexiva=reflexao(texto)
        if (reflexiva and not re.search(r"\b(?:todo|toda|todos|todas|cada|orbita|parte de|tipo de|"
                r"incapaz|minha capacidade|nao consigo|nunca vou conseguir)\b",normalizar(texto)) and
                not conversa.dialogo._pedido_prioritario(texto,bot,conversa)):
            return reflexiva
        relato=self._relato(conversa)
        if re.fullmatch(r"(?:voce entendeu o que (?:me incomodou|eu quis dizer)|o que voce entendeu do que contei|"
                        r"como voce entendeu a situacao que eu trouxe|me diga o que entendeu de mim)",n):
            if not conversa.dialogo.ativo:
                return {"esclarecer":"Qual relato pessoal você quer retomar? Ainda não tenho uma situação ativa para acompanhar."}
            return {"acao":"escuta","slots":{"relato":relato}} if relato else {"esclarecer":"Qual situação você quer que eu acompanhe? Ainda não tenho um relato seu nesta conversa."}
        if re.fullmatch(r"(?:voce (?:ja me perguntou isso|esta repetindo a mesma pergunta|continua fazendo a mesma pergunta|"
                        r"esta falando sempre a mesma coisa)|essa (?:sugestao|resposta) nao me ajudou|"
                        r"o que disse nao resolveu minha dificuldade|nao era isso que eu queria|"
                        r"isso nao ajudou|nao gostei dessa resposta)",n):
            if not conversa.dialogo.ativo: return None
            return {"acao":"ajuste","slots":{"relato":relato}} if relato else None
        if re.fullmatch(r"(?:fa[cz]a uma sugestao diferente|me de outra possibilidade|quero tentar outro caminho|"
                        r"tem um jeito diferente de lidar com isso|sugira outra abordagem para meu objetivo)",n):
            if not conversa.dialogo.ativo: return None
            slots={"relato":relato} if relato else {};objetivo=self._objetivo(conversa)
            if objetivo: slots["objetivo"]=objetivo
            restricao=self._restricao(conversa)
            if restricao: slots["restricao"]=restricao
            return {"acao":"alternativa","slots":slots} if objetivo or relato else None
        if (re.search(r"\b(?:incapaz|minha capacidade|nao consigo|nunca vou conseguir)\b",n) and
                re.search(r"\b(?:errei|tentativa|fracassou|nao funcionou|deu errado|erro)\b",n) and
                ("?" in texto or re.match(r"(?:uma |errei |se |so porque )",n))):
            return {"acao":"apoio","slots":{"relato":texto.strip()}}
        if re.fullmatch(r"(?:me de uma ideia concreta usando essas informacoes|crie uma ideia a partir do que contei|"
                        r"combine esses dois elementos numa ideia|o que da para criar juntando essas coisas|"
                        r"proponha uma possibilidade com esses elementos)",n):
            if conversa.dialogo.opcoes: a,b=conversa.dialogo.opcoes
            else:
                partes=re.split(r"\s+(?:e|com)\s+",relato,maxsplit=1,flags=re.I)
                if len(partes)!=2: return {"esclarecer":"Quais dois elementos você quer combinar? Escolha os elementos que devem aparecer."}
                a,b=partes
            return {"acao":"ideia","slots":{"tema1":a[:400],"tema2":b[:400]}}
        pessoal=re.fullmatch(r"(?:me )?(resuma|resumir|reformule|reformular|reescreva|reescrever) (?:o que (?:eu )?"
                             r"(?:te |lhe )?(?:contei|disse)|meu relato|minha situacao|isso que contei|"
                             r"o que acabei de contar)(?: (?:em poucas palavras|de outro jeito))?",n)
        if pessoal:
            return self._pedido_pessoal("resumo" if pessoal.group(1).startswith("resum") else "reformulacao",conversa,explicito=True)
        if re.fullmatch(r"(?:junte|junta|reuna) o que (?:eu )?(?:te )?contei (?:num|em um) resumo",n):
            return self._pedido_pessoal("resumo",conversa,explicito=True)
        if n in ("dizer isso de outro jeito","diga isso de outro jeito","diz isso de outro jeito"):
            if bot.contexto_textual is not None: return None
            return self._pedido_pessoal("reformulacao",conversa)
        inline=re.fullmatch(r"(?:me\s+)?(resuma|reformule|reescreva)\s*(?:este (?:texto|relato)\s*)?:\s*(.+)",texto.strip(),re.I)
        if inline and len(inline.group(2))<=1000:
            return {"acao":"resumo" if inline.group(1).lower()=="resuma" else "reformulacao","slots":{"relato":inline.group(2)}}
        if re.fullmatch(r"(?:me )?(?:fa[cz]a|fazer) (?:uma|outra|mais uma) pergunta(?: (?:para (?:eu )?pensar(?: melhor)? (?:nisso|sobre isso)|"
                        r"sobre (?:isso|o que contei|minha situacao|a historia)))?|"
                        r"(?:quais|que) perguntas eu (?:deveria|posso) me fazer antes de decidir|"
                        r"me ajude a (?:explorar|pensar melhor sobre) (?:isso|minha situacao)",n):
            if "historia" in n and self.ultima_criacao:
                return {"acao":"exploracao","slots":{"relato":self.ultima_resposta[:600]}}
            return self._pedido_pessoal("exploracao",conversa)
        if re.fullmatch(r"(?:me )?(?:ajude|ajuda|ajudar) a organizar (?:minhas ideias|meu objetivo|isso)|"
                        r"organize (?:minhas ideias|um plano com o que contei)|"
                        r"como posso comecar de um jeito diferente|me sugira (?:um )?proximo passo",n):
            return self._pedido_pessoal("plano",conversa)
        condicao=re.fullmatch(r"e se (?:eu )?(?:tiver|tivesse|so tiver|so tivesse) (?:so |apenas )?(\d{1,4}) minutos(?: (?:por dia|a noite))?",n)
        if condicao and conversa.dialogo.ativo and self._objetivo(conversa) and 1<=int(condicao.group(1))<=1440:
            return {"acao":"plano","slots":{"objetivo":self._objetivo(conversa),"restricao":texto.strip().rstrip("?")},"hipotese":True}
        if n=="separe o que eu sei do que estou supondo":
            anterior=self.ultima_decisao
            if anterior and anterior["acao"]=="reflexao":
                return {"acao":"reflexao","slots":dict(anterior["slots"]),"hipotese":anterior.get("hipotese",False)}
            return {"esclarecer":"O que aconteceu e qual conclusão você está considerando? Preciso dessas duas partes para comparar."}
        esclarecimento=self._esclarecer_escrita(texto,conversa)
        if esclarecimento: return esclarecimento
        completado=self._completar(texto,conversa,bot)
        return completado if completado else self._rotear(texto,bot,conversa)

    def preparar(self, texto, bot, conversa):
        self.ultimo_quadro=None
        if (not self.usar_neural or not isinstance(texto,str) or not texto.strip() or
                len(texto)>1200 or "`" in texto or "\x00" in texto): return None
        if self.ultima_escrita and conversa.turno-self.ultima_escrita["turno"]>self.MAX_INTERVALO:
            self.ultima_escrita=self.ultima_criacao=None
        if self.ultima_decisao and conversa.turno-self.ultima_decisao["turno"]>self.MAX_INTERVALO:
            self.ultima_decisao=None
        if re.match(r"nao (?:invente|escreva|crie|resuma|reformule|continue|fa[cz]a|fazer)\b",texto_pedido(texto)):
            self.pendente=None
            from linguagem_conversa import Ato,Preparacao
            return Preparacao(Ato("geracao_cancelar","dialogar"),
                    ("conversa:cancelamento","Pedido de escrita cancelado.",None,""))
        pedido=self._contexto(texto,bot,conversa)
        if pedido is None: return None
        from linguagem_conversa import Ato,Preparacao
        if "esclarecer" in pedido:
            if pedido.get("pendente"): self.pendente=pedido["pendente"]
            return Preparacao(Ato("geracao_esclarecer","dialogar"),("duvida",pedido["esclarecer"],None,""))
        if "justificar" in pedido:
            return Preparacao(Ato("geracao_justificar","dialogar"),("conversa:justificativa",pedido["justificar"],None,""))
        caminho=Path(__file__).with_name("rede_geracao.json")
        if not caminho.is_file(): return None
        from linguagem_gerativa import VARIANTES,carregar,renderizar,slots_requeridos
        contexto={"acao":pedido["acao"],"estilo":pedido.get("estilo","neutro"),"slots":pedido["slots"],
                  "mensagem":texto,"historico":[h["pergunta"] for h in bot.historico[-3:]],"resposta_anterior":self.resposta_anterior}
        obrigatorios=slots_requeridos(pedido["acao"],pedido["slots"])
        try:
            modelo=carregar(str(caminho.resolve()),caminho.stat().st_mtime_ns)
            for tentativa in range(VARIANTES):
                contexto["variante"]=(self.variante+tentativa)%VARIANTES
                g=modelo.gerar(contexto,max_tokens=128)
                if not geracao_valida(g,obrigatorios,pedido["acao"]): continue
                resposta=renderizar(g,pedido["slots"])
                if resposta in self.respostas_recentes or len(resposta)>2400: continue
                if pedido.get("encurtar") and self.ultima_escrita and len(resposta.split())>=len(self.ultima_escrita["texto"].split()): continue
                self.variante=(contexto["variante"]+1)%VARIANTES;self.ultima_resposta=resposta
                self.respostas_recentes.append(resposta);acao=pedido["acao"]
                self.ultimo_quadro={"modelo":"GRU autoral autoregressiva","acao":acao,"tokens":g["quantidade_tokens"],
                                   "log_prob_media":g["log_prob_media"],"variante":contexto["variante"],
                                   "slots_copiados":sorted(obrigatorios),"usa_resposta_anterior":bool(self.resposta_anterior)}
                if pedido.get("roteador"): self.ultimo_quadro["roteador"]=pedido["roteador"]
                self.ultima_decisao={"acao":acao,"slots":dict(pedido["slots"]),"turno":conversa.turno,"hipotese":pedido.get("hipotese",False)}
                if acao in ("historia","poema","dialogo","mensagem","final","continuacao"):
                    tipo=pedido.get("tipo",acao if acao not in ("final","continuacao") else "historia")
                    self.ultima_escrita={"acao":acao,"tipo":tipo,"slots":dict(pedido["slots"]),"estilo":contexto["estilo"],"turno":conversa.turno,"texto":resposta}
                    self.ultima_criacao=self.ultima_escrita if tipo in ("historia","poema","dialogo") else None
                    resposta=("Poema:\n" if tipo=="poema" else "Rascunho:\n" if tipo=="mensagem" else "Ficção:\n")+resposta
                elif acao=="ideia": resposta="Ideia inventada:\n"+resposta
                if pedido.get("hipotese"): resposta="Na hipótese que você propôs:\n"+resposta
                self.pendente=None
                return Preparacao(Ato("geracao_"+acao,"dialogar"),("conversa:gerada_"+acao,resposta,None,""))
        except (ValueError,KeyError,TypeError,OSError) as exc:
            self.erro=str(exc);return None
        return Preparacao(Ato("geracao_incerta","dialogar"),("duvida",
            "Não consegui completar uma resposta coerente para esse pedido. Pode especificar o tema ou o que quer mudar?",None,""))

    def registrar(self, identificador, texto="", conversa=None, pergunta=""):
        if identificador=="conversa:reinicio": self.limpar();return
        if identificador=="conversa:abertura": self.limpar()
        elif identificador=="conversa:retomada" and conversa is not None:
            self.limpar()
            for relato in conversa.relatos:
                self.relatos_recentes.append({"texto":relato,"turno":conversa.turno})
        elif identificador=="conversa:relato" and conversa is not None and conversa.relatos:
            self.relatos_recentes.append({"texto":pergunta or conversa.relatos[-1],"turno":conversa.turno})
        elif not identificador.startswith("conversa:") and identificador!="duvida":
            self.ultima_criacao=self.ultima_escrita=self.ultima_decisao=None;self.pendente=None
        if not identificador.startswith("conversa:gerada_") and identificador!="conversa:justificativa":
            self.ultima_decisao=None
        if conversa is not None:
            objetivo=conversa.dialogo.dados.get("objetivo") or conversa.objetivo
            declarado=bool(re.match(r"(?:(?:na verdade|corrigindo|aqui)[,:]? )?(?:eu )?"
                    r"(?:quero|pretendo|queria|gostaria de|tenho vontade de|estou pensando em|"
                    r"ando querendo|meu objetivo e|(?:a )?minha meta e|meu plano e|"
                    r"(?:a )?minha intencao e)\b",normalizar(pergunta)))
            if not objetivo: self.objetivo_declarado=None
            elif identificador in ("conversa:relato","conversa:retomada") and (
                    declarado or identificador=="conversa:retomada" or
                    self.objetivo_declarado is None or self.objetivo_declarado["valor"]!=objetivo):
                self.objetivo_declarado={"valor":objetivo,"turno":conversa.turno}
        self.resposta_anterior=texto[:2400]
