"""Extrai pedidos de escrita sem usar nomes ou temas de um catálogo.

Operadores têm construções abertas; argumentos mantêm grafia e negações.
Este módulo não decide verdade, não gera texto e não resolve fatos.
"""
import re

from composicao_textual import normalizar


ESTILOS = {
    "leve":"leve", "simples":"simples", "aventura":"aventura",
    "carinhoso":"carinhoso", "carinhosa":"carinhoso", "amigavel":"carinhoso",
    "formal":"formal", "divertido":"divertido", "divertida":"divertido",
    "engracado":"divertido", "engracada":"divertido", "misterioso":"misterioso",
    "misteriosa":"misterioso", "misterio":"misterioso",
}
ADJETIVOS = (r"curt[ao]|curtinh[ao]|breve|pequen[ao]|inventad[ao]|simples|leve|"
             r"de aventura|carinhos[ao]|formal|divertid[ao]|engra[cç]ad[ao]|misterios[ao]|de mist[eé]rio")
PREFIXO = (r"(?:por favor,?\s+)?(?:ser[aá] que\s+)?(?:(?:voc[eê]|c[eê])\s+)?"
           r"(?:(?:pode(?:ria)?|consegue|conseguiria)\s+)?(?:me\s+)?")
ESCRITA = r"(?:invente|inventa|inventar|crie|cria|criar|escreva|escreve|escrever|fa[cç]a|faz|fazer|conte|conta|contar|componha|compor|imagine|imaginar)"


def texto_pedido(texto):
    """Remove cortesias e modais só no início do operador normalizado."""
    n=normalizar(texto)
    n=re.sub(r"^(?:por favor,? |ei,? )", "", n)
    n=re.sub(r"^(?:voce |ce )?(?:pode(?:ria)? |consegue |conseguiria )", "", n)
    return n


def estilo(texto, padrao="neutro"):
    n=normalizar(texto)
    for palavra in reversed(n.split()):
        if palavra in ESTILOS: return ESTILOS[palavra]
    return padrao


_PERSONAGEM=re.compile(
    r"(?P<antes>.*?)(?:^|[,;]?\s+)(?:(?:e|com|onde|em que|cuja?|tendo)\s+)?"
    r"(?:(?:uma?|o|a)\s+[\wÀ-ÿ]+\s+|personagem\s+|protagonista\s+)?"
    r"chamad[ao]\s+(?P<nome>[A-ZÀ-Ý][\wÀ-ÿ'-]*)(?P<depois>.*)", re.S)


def _temas(assunto):
    """Separa o personagem nomeado do cenário: em “um farol abandonado, com uma
    personagem chamada Lia”, a instrução “uma personagem chamada” não é nome."""
    m=_PERSONAGEM.fullmatch(assunto.strip())
    if m:
        depois=m.group("depois").strip(" ,;.")
        # “chamado Zeca que aprende a cozinhar” descreve o personagem; não é cenário.
        if re.match(r"(?:que|quem|cujo|cuja)\b",depois,re.I): depois=""
        cenario=(m.group("antes").strip(" ,;.")+" "+depois).strip(" ,;.")
        cenario=re.sub(r"^(?:(?:sobre|com|de|e)\s+)+","",cenario,flags=re.I)
        slots={"tema1":m.group("nome")}
        if cenario: slots["tema2"]=cenario
        return slots if all(len(x)<=400 for x in slots.values()) else None
    assunto=assunto.strip(" ,;")
    partes=re.split(r"\s+(?:e|com)\s+",assunto,maxsplit=1,flags=re.I)
    slots={"tema1":partes[0].strip(" ,;")}
    if len(partes)==2: slots["tema2"]=partes[1].strip(" ,;")
    return slots if all(slots.values()) and all(len(x)<=400 for x in slots.values()) else None


def criacao(texto):
    pedido=texto.strip().strip(".?! ")
    prefixo=PREFIXO+r"(?:(?:ajude|ajuda|ajudar)\s+a\s+)?(?:"+ESCRITA+r"|quero|queria|gostaria de)\s+"
    padrao=(prefixo+r"(?:(?:uma?|alguns?|algumas?)\s+)?"
            r"(?P<tipo>hist[oó]ria|conto|narrativa|poema|versos|di[aá]logo|conversa fict[ií]cia)"
            r"(?:\s+(?:"+ADJETIVOS+r"))*\s+"
            r"(?:sobre|com|entre|envolvendo|a respeito de|de|que (?:junte|juntasse|envolva|tenha))\s+(?P<tema>.+)")
    m=re.fullmatch(padrao,pedido,re.I)
    if not m: return None
    assunto=m.group("tema");qualificacao=pedido[:m.start("tema")]
    fim=re.search(r"\s+(?:em (?:um )?tom|de (?:um )?jeito|num tom|com (?:um )?tom)\s+("+ADJETIVOS+r")$",assunto,re.I)
    if fim: qualificacao+=" "+fim.group(1);assunto=assunto[:fim.start()]
    slots=_temas(assunto)
    if not slots: return None
    tipo=normalizar(m.group("tipo"))
    acao="poema" if tipo in ("poema","versos") else "dialogo" if tipo in ("dialogo","conversa ficticia") else "historia"
    return {"acao":acao,"estilo":estilo(qualificacao),"slots":slots}


def mensagem(texto):
    pedido=texto.strip().strip(".?! ")
    prefixo=PREFIXO+r"(?:(?:ajude|ajuda|ajudar)\s+a\s+)?(?:"+ESCRITA+r"|redija|redigir|prepare|preparar|quero|queria|gostaria de)\s+"
    m=re.fullmatch(prefixo+r"(?:uma?\s+)?(?:mensagem|bilhete|e-?mail)"
                   r"(?P<qualificacao>(?:\s+(?:"+ADJETIVOS+r"))*)\s+"
                   r"(?:(?:para|pra|pro|ao|[aà])\s+(?P<destinatario>.+?)\s+)?"
                   r"(?:sobre|a respeito de|dizendo(?: que)?|contando(?: que)?)\s+(?P<relato>.+)",pedido,re.I)
    if not m: return None
    relato=m.group("relato");qualificacao=m.group("qualificacao")
    fim=re.search(r"\s+(?:em (?:um )?tom|de (?:um )?jeito|num tom)\s+("+ADJETIVOS+r")$",relato,re.I)
    if fim: qualificacao+=" "+fim.group(1);relato=relato[:fim.start()]
    slots={"relato":relato.strip()}
    if m.group("destinatario"): slots["destinatario"]=m.group("destinatario").strip()
    if not all(slots.values()) or any(len(v)>600 for v in slots.values()): return None
    return {"acao":"mensagem","estilo":estilo(qualificacao),"slots":slots}


def revisao(texto):
    n=texto_pedido(texto)
    n=re.sub(r"^(?:agora|entao) ","",n)
    final = re.fullmatch(r'(?:mude|muda|troque) o final(?: da história)?:\s*(.+?)(?:,? em vez de .+)?[.!?]*', texto.strip(), re.I)
    if final:
        return {"operacao":"final", "detalhe_final":final[1].strip()}
    if re.fullmatch(r"(?:me )?(?:de|invente|crie) (?:um )?outro (?:final|desfecho)|"
                    r"mude o final(?: da historia)?|como (?:essa|a) historia poderia terminar de outro jeito|"
                    r"queria outro final para esse conto|que outro final daria para imaginar",n):
        return {"operacao":"final"}
    if re.fullmatch(r"(?:continue|continua|continuar|prossiga)(?: (?:a historia|o conto|a narrativa|"
                    r"o dialogo|a conversa(?: dos personagens| deles)?|de onde parou|de onde voce parou|esse texto))?",n):
        return {"operacao":"continuacao"}
    if re.fullmatch(r"(?:me )?(?:fa[cz]a|fazer|escreva|crie|criar) (?:uma )?(?:outra|nova) versao",n):
        return {"operacao":"versao"}
    if re.fullmatch(r"(?:me )?(?:fa[cz]a|fazer|deixe|deixar|torne|tornar) (?:uma versao |"
                    r"a historia |o poema |o texto |a mensagem |o dialogo )?mais (?:curt[ao]|breve)",n):
        return {"operacao":"versao","estilo":"simples","encurtar":True}
    tom=re.fullmatch(r"(?:me )?(?:deixe|deixa|deixar|torne|tornar|fa[cz]a|fazer)(?: (?:a historia|o poema|o texto|a mensagem|o dialogo|uma versao))?"
                     r" mais (.+)|(?:deixe|deixa|deixar) (?:esse conto|essa historia|esse texto) com (?:um )?clima (.+)|"
                     r"(?:mude|muda|mudar|troque|trocar)(?: o)? (?:tom|clima)(?: (?:da historia|do texto|"
                     r"da mensagem|do dialogo|do poema))? para (.+)",n)
    if tom:
        alvo=next(g for g in tom.groups() if g)
        if alvo in ESTILOS: return {"operacao":"versao","estilo":ESTILOS[alvo]}
    troca=re.fullmatch(PREFIXO+r"(?:troque|troca|substitua|substituir|trocar|mude|muda)\s+(.+?)\s+(?:por|para)\s+(.+)",texto.strip().strip(".?! "),re.I)
    if troca: return {"operacao":"versao","troca":troca.groups()}
    return None


def reflexao(texto):
    """Conserva uma observação e a conclusão perguntada, sem inferir causa."""
    m=re.fullmatch(r"(?:se\s+)?(.+?)[,;.]\s*(?:isso (?:quer dizer|significa)|"
                  r"posso concluir|devo concluir)\s+(?:que\s+)?(.+?)\??",texto.strip().strip(". "),re.I)
    if m and all(1<=len(v)<=600 for v in m.groups()):
        return {"acao":"reflexao","slots":{"premissa":m.group(1).strip(),"conclusao":m.group(2).strip().rstrip("?")},
                "hipotese":bool(re.match(r"se\s+",texto.strip(),re.I))}
    return None
