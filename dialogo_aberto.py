"""Diálogo sobre relatos, escolhas e objetivos sem ampliar a base factual.

O classificador aprendido escolhe atos. Argumentos, nomes e negações são
conservados; memória é local à sessão e opiniões são hipóteses/sugestões,
nunca experiências pessoais do bot ou fatos globais aprendidos do usuário.
"""
import re
from collections import OrderedDict
from pathlib import Path

from composicao_textual import normalizar
from conversa_assistente import identificar_contato


def disponibilidade_negada(texto):
    """Ausência direta de tempo, sem confundir crença com disponibilidade."""
    n=normalizar(texto)
    if any(c in texto for c in ('?','`','"','“','”')) or re.search(r"\b(?:se|caso|quando|desde que)\b",n):
        return False
    return bool(re.match(r"(?:eu )?nao (?:(?:tenho|disponho de) |(?:posso|consigo) "
            r"(?:(?:dedicar|reservar|separar|arrumar|encontrar|gastar|ter) )?)"
            r"(?:(?:mais|nenhum|nem|sequer|tanto|o|esse) )?(?:\d{1,4} )?"
            r"(?:tempo|minutos?|horas?)\b",n))

class DialogoAberto:
    def __init__(self, usar_neural=True):
        self.usar_neural = usar_neural
        self.ativo = False
        self.espera = None
        self.dados = OrderedDict()
        self.opcoes = ()
        self.opiniao = self.motivo = self.ultima_resposta = ""
        self.ultimo_quadro = None
        self.erro_neural = None

    def limpar(self):
        self.ativo, self.espera = False, None
        self.dados.clear()
        self.opcoes = ()
        self.opiniao = self.motivo = self.ultima_resposta = ""

    def iniciar_assunto(self):
        for chave in ("objetivo", "minutos", "ultimo_relato"):
            self.dados.pop(chave, None)
        self.opcoes = ()
        self.opiniao = self.motivo = ""
        self.espera = None

    def estado(self, bot, conversa):
        if self.ativo or conversa.assunto:
            return "pendente" if self.espera else "pessoal"
        return "factual" if bot.contexto_textual is not None else "livre"

    def _pedido_prioritario(self, texto, bot, conversa):
        """Consulta apenas reconhecedores puros; não executa uma resposta."""
        from crivo import LIMIAR, chave_pergunta, normalizar as normalizar_crivo
        n = normalizar_crivo(texto).strip().strip("?.,;! ")
        if re.fullmatch(r"por que(?: (?:isso|isto) acontece| voce (?:acha|diz|sugeriu) isso)?|porque|"
                        r"qual (?:e )?meu nome|como eu me chamo|voce lembra meu nome", n):
            return False
        if bot._dinamico(n) is not None or bot._social(n) is not None:
            return True
        if n in ("mais", "continue", "continua", "outra", "outra resposta", "e mais"):
            return True
        if bot._escolha_ordinal(n) is not None or bot.esclarecimento and n in ("sim", "nao", "isso", "isso mesmo", "nenhuma"):
            return True
        consulta = chave_pergunta(texto)
        if consulta in bot.indices_exatos:
            return True
        composicao = bot.compositor.responder(texto, bot.contexto_textual)
        if composicao is not None and composicao[0] != "fora":
            return True
        if bot.interpretador_pedidos.analisar(texto) is not None:
            return True
        if bot.consultas_relacionais.responder(texto, bot.contexto_consulta) is not None:
            return True
        if bot.frutas is not None and bot.frutas.responder(texto, bot.contexto_frutas) is not None:
            return True
        aprender = re.fullmatch(r"(?:eu )?(?:quero|pretendo|estou pensando em) (?:aprender|estudar|praticar|treinar) .+", n)
        if not aprender and re.search(r"\b(?:python|javascript|html|css|sql|git|programacao|codigo|script|programa|http)\b", n):
            return True
        rank = bot._ranking(texto)
        ts = set(bot._tokens_consulta(texto))
        if rank and ts:
            score, indice = rank[0]
            cobertura = len(ts & bot.termos[indice]) / len(ts)
            pessoal = re.match(r"(?:(?:so|mas|hoje|agora|amanha) )?"
                               r"(?:eu|meu|minha|meus|minhas|me|estou|to|tenho|quero|pretendo|"
                               r"gostaria|gosto|curto|prefiro|adoro|acho|penso|sinto|fiquei|acabei|"
                               r"foi|aconteceu|ja tentei|tentei|nao consigo|nao quero|na verdade)\b", n)
            referencia = re.search(r"\b(?:isso|isto|disso|disto|aquilo|esse|essa|desse|dessa|"
                                  r"nesse|nessa|comigo|voce|meu|minha|meus|minhas)\b", n)
            interrogativo = re.match(r"(?:o que|como|por que|qual|quais|quanto|quantos|quantas|"
                                     r"quem|onde|quando|existe)\b", n)
            conteudo = ts - {"vale", "pena", "organizar", "comecar", "decidir", "avaliar", "melhor",
                            "primeiro", "passo", "ideia", "ideias", "criterio", "criterios", "mais",
                            "ajuda", "ajudar", "posso"}
            # Consultas editoriais continuam válidas dentro de uma conversa
            # pessoal e sem '?'. Já 'como organizar isso' precisa do relato,
            # mesmo que 'organizar' tenha alta similaridade com 'geladeira'.
            if conteudo and not pessoal and not referencia and (
                    score >= LIMIAR and cobertura >= .60 or
                    interrogativo and score >= .90 and cobertura >= .50):
                return True
            if not (self.ativo or conversa.assunto) and not referencia and score >= .90:
                if cobertura >= .60:
                    return True
                nome_intencao = set(bot.base[indice]["id"].split("_"))
                if re.match(r"(?:eu )?quero (?!aprender|estudar|praticar|treinar)", n) and ts & nome_intencao:
                    return True
        return False

    def analisar(self, texto, bot, conversa):
        self.ultimo_quadro = None
        if (not self.usar_neural or not isinstance(texto, str) or not texto.strip()
                or len(texto) > 1200 or any(c in texto for c in ('`', '"', '“', '”'))
                or identificar_contato(texto) is not None):
            return None
        caminho = Path(__file__).with_name("rede_dialogo.json")
        if not caminho.is_file():
            return None
        try:
            from dialogo_neural import carregar
            rede = carregar(str(caminho.resolve()), caminho.stat().st_mtime_ns)
            q = rede.analisar(texto, self.estado(bot, conversa))
        except (ValueError, KeyError, TypeError, OSError) as exc:
            self.erro_neural = str(exc)
            return None
        self.ultimo_quadro = q
        limiar = (.55 if q["estado"] == "pendente" and q["ato"] in ("resposta", "relato") else rede.limiar)
        from dialogo_neural import ATOS_PESSOAIS
        pessoal = (q["ato"] in ATOS_PESSOAIS and q["confianca_pessoal"] >= .92 and
                   bool(self.ativo or conversa.assunto))
        if q["ato"] == "outro" or not pessoal and (q["confianca"] < limiar or q["margem"] < .2):
            return None
        n = normalizar(texto)
        if q["ato"] == "lembrar" and not (
                re.search(r"\b(?:meu|minha|eu|mim)\b", n) and
                re.search(r"\b(?:nome|chamo|objetivo|meta|opcoes|preferencias?|gosto|curto|contei|disse|falei|lembra|tenho)\b", n)):
            return None
        if re.search(r"\b(?:o que (?:e|eh|sao|seria|significa)|como funciona|"
                     r"para que serve|defina|definir|reescreva|reescrever|reformule|retom\w*|"
                     r"fontes?|diferenca entre)\b", n):
            return None
        if q["ato"] == "criterios" and not re.fullmatch(
                r"(?:o que (?:faz|torna) .+ (?:ser |dar )?(?:bom|boa|interessante|util|certo|uma boa escolha)|"
                r"como (?:posso |sei se |saber se )?(?:avaliar .+|.+ vale a pena|.+ ficou bom)|"
                r"quais criterios usar para .+|qual a melhor forma de avaliar .+)", n):
            return None
        if q["ato"] == "abrir" and re.search(r"\b(?:sobre|a respeito de)\b", n):
            return None
        # Uma pergunta nova não vira resposta a uma pergunta pendente
        # só porque suas palavras se parecem com as de um relato.
        if q["ato"] in ("relato", "preferencia", "objetivo", "ponto_de_vista", "resposta"):
            if "?" in texto or re.match(r"(?:o que|como|por que|qual|quais|quanto|quantos|quantas|"
                                       r"quem|onde|quando|existe)\b", n) or re.search(
                    r"\b(?:me explique|defina|para que serve)\b", n):
                return None
        if q["ato"] == "resposta" and not (self.ativo or conversa.assunto):
            return None
        return q["ato"]

    def _guardar(self, chave, valor):
        self.dados.pop(chave, None)
        self.dados[chave] = valor.strip().strip(".?! ")[:400]
        while len(self.dados) > 12:
            self.dados.popitem(last=False)

    def _extrair(self, texto):
        """Slots só são guardados com uma declaração explícita, inteira."""
        original = texto.strip().strip(".?! ")
        prefixo = r"(?:(?:na verdade|corrigindo|aqui)[,:]?\s*)?"
        nome = re.fullmatch(prefixo + r"(?:meu nome [eé]|me chamo|(?:aqui )?pode me chamar de)\s+(.+)", original, re.I)
        if nome and re.fullmatch(r"[\wÀ-ÿ]+(?:[ '\-][\wÀ-ÿ]+){0,5}", nome.group(1)):
            self._guardar("nome", nome.group(1))
        else:
            nome = None
        gosto = re.fullmatch(prefixo + r"(?:eu\s+)?(?:gosto(?: muito)? de|curto|adoro|sou f[aã] de|"
                              r"meu passatempo preferido [eé]|prefiro)\s+(.+)", original, re.I)
        if gosto:
            self._guardar("preferencia", gosto.group(1))
            self.dados.pop("aversao", None)
        negativo = re.fullmatch(r"(?:eu\s+)?n[aã]o\s+gosto\s+de\s+(.+)", original, re.I)
        if negativo:
            self._guardar("aversao", negativo.group(1))
            # Uma retratação do mesmo gosto não mantém a afirmação antiga.
            if normalizar(self.dados.get("preferencia", "")) == normalizar(negativo.group(1)):
                self.dados.pop("preferencia", None)
        objetivo = re.fullmatch(prefixo + r"(?:eu\s+)?(?:quero|pretendo|queria(?: conseguir)?|gostaria de|"
                                r"tenho vontade de|estou pensando em|ando querendo|meu objetivo [eé]|"
                                r"(?:a )?minha meta [eé]|meu plano [eé]|(?:a )?minha inten[cç][aã]o [eé])\s+(.+)", original, re.I)
        if objetivo and not re.match(r"(?:saber|entender|compreender)\s+(?:o que|como|por que|se)\b", objetivo.group(1), re.I):
            self._guardar("objetivo", objetivo.group(1))
        if re.match(r"(?:eu )?nao (?:quero|pretendo|vou)\b", normalizar(original)):
            self.dados.pop("objetivo", None)
        tempo = re.match(r"(?:(?:so|apenas|mas|hoje|agora) )?(?:eu )?(?:so |apenas )?"
                         r"(?:tenho|disponho de|sobraram) (\d{1,4}) minutos?\b",normalizar(original))
        condicional=bool(re.search(r"\b(?:se|caso|quando|desde que)\b",normalizar(original)))
        tempo_negado=disponibilidade_negada(original)
        if tempo_negado and not condicional:
            self.dados.pop("minutos",None)
        elif tempo and not condicional and 1 <= int(tempo.group(1)) <= 1440:
            self._guardar("minutos", tempo.group(1))
        opcoes = re.fullmatch(r"(?:tenho (?:duas|2) op[cç][oõ]es\s*:\s*|estou entre\s+|"
                              r"n[aã]o sei se\s+)(.+?)\s+(?:ou|e)\s+(.+)", original, re.I)
        if opcoes:
            self.opcoes = (opcoes.group(1), opcoes.group(2))
        return nome, gosto, negativo, objetivo

    def _lembrar(self, texto, conversa):
        n = normalizar(texto)
        if re.search(r"\b(?:nome|chamo|chamar)\b", n):
            valor = self.dados.get("nome")
            resposta = "Você disse que seu nome é " + valor + "." if valor else "Você ainda não me disse seu nome nesta conversa. Como quer que eu te chame?"
        elif re.search(r"\b(?:gosto|gosta|curto|preferencia|preferencias|favorit\w*)\b", n):
            partes = []
            if self.dados.get("preferencia"):
                partes.append("Você disse que gosta de “" + self.dados["preferencia"] + "”.")
            if self.dados.get("aversao"):
                partes.append("Você também disse que não gosta de “" + self.dados["aversao"] + "”.")
            resposta = " ".join(partes) or "Você ainda não contou suas preferências nesta conversa. Do que você gosta?"
        elif re.search(r"\b(?:objetivo|quero|meta)\b", n):
            valor = self.dados.get("objetivo")
            resposta = "Seu objetivo declarado é “" + valor + "”." if valor else "Ainda não tenho um objetivo declarado por você. O que quer fazer?"
        elif re.search(r"\b(?:tempo|minutos)\b", n):
            valor = self.dados.get("minutos")
            resposta = "Você disse que tem " + valor + " minutos." if valor else "Você ainda não especificou quanto tempo tem disponível."
        elif re.search(r"\b(?:opcoes|alternativas)\b", n):
            resposta = "Você está entre “" + "” e “".join(self.opcoes) + "”." if self.opcoes else "Você ainda não apresentou duas opções. Quais está considerando?"
        else:
            partes = ["Seu nome é " + self.dados["nome"] + "."] if self.dados.get("nome") else []
            if self.dados.get("objetivo"):
                partes.append("Você quer “" + self.dados["objetivo"] + "”.")
            if conversa.relatos:
                partes.append("Você contou: “" + "”; “".join(list(conversa.relatos)[-3:]) + "”.")
            resposta = " ".join(partes) or "Ainda não tenho relatos seus nesta conversa. Pode me contar algo."
        return "conversa:memoria", resposta, None, ""

    def _salvar_situacao(self, conversa):
        conversa.situacoes = type(conversa.situacoes)(
            (s for s in conversa.situacoes if s[0] != conversa.assunto), maxlen=conversa.MAX_LEMBRANCAS)
        conversa.situacoes.append((conversa.assunto, conversa.objetivo, tuple(conversa.relatos),
                                   conversa.etapa, conversa.turno))

    def _relatar(self, texto, ato, conversa):
        era_ativo = self.ativo or bool(conversa.assunto)
        self.ativo = True
        nome, gosto, negativo, objetivo = self._extrair(texto)
        if re.match(r"(?:eu )?nao (?:quero|pretendo|vou)\b", normalizar(texto)):
            conversa.objetivo = None
        original = texto.strip()[:600]
        if not conversa.assunto:
            conversa.assunto = self.dados.get("objetivo", "sua situação")
        conversa.relatos.append(original)
        self._guardar("ultimo_relato", original)
        if nome:
            self.espera = "interesse"
            resposta = "Prazer, " + self.dados["nome"] + ". O que você quer conversar hoje?"
        elif gosto:
            self.espera = "preferencia"
            resposta = "Você gosta de “" + self.dados["preferencia"] + "”. O que mais te chama a atenção nisso?"
        elif negativo:
            self.espera = "preferencia"
            resposta = "Entendi: você não gosta de “" + self.dados["aversao"] + "”. O que te incomoda nisso?"
        elif objetivo:
            self.opiniao = ""
            self.opcoes = ()
            conversa.objetivo, conversa.etapa = self.dados.get("objetivo"), 1
            self.espera = "obstaculo"
            resposta = "Você contou: “" + original + "”. Seu objetivo declarado é “" + (conversa.objetivo or original) + "”. Qual é a principal dificuldade para chegar a esse objetivo?"
        elif self.opcoes and re.match(r"(?:tenho (?:duas|2) opcoes|estou entre)\b", normalizar(texto)):
            self.espera = "criterio"
            resposta = "Você está entre “" + "” e “".join(self.opcoes) + "”. O que pesa mais nessa escolha: o resultado, o prazo ou como você está agora?"
        elif ato == "ponto_de_vista":
            self.opiniao = original
            self.espera = "argumento"
            resposta = "Você trouxe a ideia: “" + original + "”. Que experiência te fez pensar nisso?"
        elif not era_ativo and re.search(r"\b(?:cansad\w*|puxad\w*|triste|frustrad\w*|esgotad\w*)\b", normalizar(texto)):
            self.espera = "detalhe"
            resposta = "Pelo que você contou, o dia pesou: “" + original + "”. Quer falar do que aconteceu ou pensar em como descansar agora?"
        elif ato == "resposta" and self.espera in ("tema", "interesse"):
            assunto = re.sub(r"^sobre\s+", "", original, flags=re.I)
            conversa.assunto = assunto
            self.espera = "detalhe"
            resposta = "Vamos falar de “" + assunto + "”. O que aconteceu ou o que você quer explorar?"
        else:
            resposta = "Você contou: “" + original + "”."
            if conversa.objetivo:
                resposta += " Seu objetivo declarado é “" + conversa.objetivo + "”."
            if conversa.etapa <= 1:
                conversa.etapa = 2
                self.espera = "tentativa"
                pergunta = "O que você já tentou e como isso funcionou para você?"
            elif conversa.etapa == 2:
                conversa.etapa = 3
                self.espera = "mudanca"
                pergunta = "O que você gostaria que fosse diferente nessa situação?"
            else:
                self.espera = "proximo_passo"
                pergunta = "Qual pequeno próximo passo parece possível para você?"
            resposta += "\n\n" + pergunta
        self._salvar_situacao(conversa)
        self.motivo = "Parti do que você contou, sem assumir detalhes que você ainda não explicou. A pergunta ajuda a entender o que é mais importante para você."
        return "conversa:relato", resposta, None, ""

    def _planejar(self, conversa):
        objetivo = self.dados.get("objetivo") or conversa.objetivo
        if not objetivo:
            self.espera = "objetivo"
            return "conversa:planejamento", "Vamos montar um começo. Qual resultado você quer alcançar?", None, ""
        self.espera = "proximo_passo"
        minutos = self.dados.get("minutos")
        resposta = "Para “" + objetivo + "”, eu começaria com um teste pequeno, que você consiga avaliar.\n"
        if minutos and int(minutos) >= 3:
            total = int(minutos)
            preparar, rever = max(1, total // 5), max(1, total // 5)
            praticar = total - preparar - rever
            resposta += ("Você tem " + minutos + " minutos. Uma divisão possível é:\n"
                         "1. " + str(preparar) + " min para escolher uma tarefa pequena.\n"
                         "2. " + str(praticar) + " min para tentar essa tarefa.\n"
                         "3. " + str(rever) + " min para anotar o que funcionou e o próximo ajuste.")
        else:
            resposta += ("1. Defina uma parte do objetivo que caiba no tempo que você tem.\n"
                         "2. Faça uma tentativa curta com um resultado observável.\n"
                         "3. Compare o resultado com o que queria e ajuste a próxima tentativa.")
        resposta += "\nQual parte desse objetivo você gostaria de tentar primeiro?"
        self.motivo = "Sugeri uma tentativa pequena porque seu objetivo é “" + objetivo + "”."
        if minutos:
            self.motivo += " Também respeitei os " + minutos + " minutos que você disse ter."
        self.motivo += " A ideia é obter um resultado concreto antes de assumir um plano grande; isso é uma sugestão, não uma garantia."
        return "conversa:planejamento", resposta, None, ""

    def _refletir(self, texto, conversa):
        if not conversa.relatos and not self.opiniao:
            self.espera = "detalhe"
            return "conversa:reflexao", "Posso ajudar a pensar. Qual é a situação e quais opções você está considerando?", None, ""
        n = normalizar(texto)
        if re.search(r"\b(?:ele|ela) (?:esta|ta|ficou|e)\b", n) and "sera" in n:
            referencia = self.dados.get("ultimo_relato", conversa.relatos[-1])
            resposta = ("Você contou: “" + referencia + "”. Só isso não permite saber o que a outra pessoa está sentindo. "
                        "Pode haver mais de uma explicação; antes de concluir, vale buscar uma informação direta. "
                        "Aconteceu algo entre vocês antes disso?")
            self.motivo = "O comportamento que você descreveu não revela, sozinho, a intenção ou o sentimento de outra pessoa. Por isso separei o que você observou do que ainda é uma hipótese."
        elif self.opcoes:
            referencia = conversa.relatos[-1]
            resposta = ("Você está entre “" + "” e “".join(self.opcoes) + "” e contou: “" + referencia + "”. "
                        "Eu compararia as opções pelo que precisa acontecer primeiro, pelo custo de cada uma "
                        "e pelo que pode ser adiado. Também dá para pensar numa versão menor de uma opção, "
                        "em vez de tratar a escolha como tudo ou nada. Qual é o prazo e o que você não pode abrir mão?")
            self.motivo = "Usei as duas opções que você apresentou e o seu relato mais recente. Sem saber suas prioridades, não tenho como declarar uma delas melhor; por isso propus critérios e uma alternativa intermediária."
        elif self.opiniao:
            resposta = ("Eu trataria “" + self.opiniao + "” como uma hipótese para examinar. "
                        "O que você observou pode apoiar essa ideia em algumas situações, mas precisamos "
                        "comparar com casos em que acontece diferente. Que exemplo apoia sua opinião? "
                        "Consegue pensar em um exemplo que a colocaria em dúvida?")
            self.motivo = "Uma impressão pode ser um bom ponto de partida, mas um exemplo sozinho não estabelece uma regra geral. Comparar casos e explicações alternativas ajuda a avaliar a ideia que você trouxe."
        else:
            referencia = conversa.objetivo or self.dados.get("objetivo") or conversa.relatos[-1]
            resposta = ("Vamos partir do que você trouxe: “" + referencia + "”. "
                        "Que opções você está considerando e qual critério pesa mais para você?")
            self.motivo = "Sua decisão depende do que você quer alcançar e do que é possível na situação que contou. Preciso dessas prioridades para comparar opções sem decidir por você."
        self.espera = "criterio"
        return "conversa:reflexao", resposta, None, ""

    def _ideias(self, conversa):
        referencia = conversa.objetivo or self.dados.get("objetivo") or self.dados.get("ultimo_relato")
        if not referencia:
            self.espera = "detalhe"
            return "conversa:ideias", "Vamos pensar em ideias. O que você está criando e o que gostaria de conseguir com isso?", None, ""
        detalhes = self.dados.get("ultimo_relato", "")
        resposta = "Para “" + referencia + "”, dá para experimentar três caminhos:"
        if detalhes and detalhes != referencia:
            resposta += " Você também trouxe “" + detalhes + "”."
        resposta += ("\n- Reduzir a ideia a uma versão pequena e testar a parte mais importante."
                     "\n- Mudar uma regra ou uma limitação e observar como o resultado muda."
                     "\n- Combinar dois elementos que você já trouxe de uma forma diferente."
                     "\nQual desses caminhos você quer desenvolver? Me diga dois elementos que devem aparecer e posso ajudar a combiná-los.")
        self.espera = "elementos"
        self.motivo = "As sugestões partem de “" + referencia + "”. São maneiras de variar e testar uma ideia sem inventar requisitos que você não contou."
        return "conversa:ideias", resposta, None, ""

    def preparar_restricao(self, texto, bot, conversa):
        """Retração declarada passa antes de operadores de negação factual."""
        if re.search(r"\b(?:o que [eé]|como funciona|defina|explique|liste|mostre|"
                     r"c[oó]digo|script|python|javascript|html|css|sql|git|http)\b",texto,re.I):
            return None
        if re.search(r"\b(?:se|caso|quando|desde que)\b",normalizar(texto)):
            return None
        if self.ativo and disponibilidade_negada(texto):
            from linguagem_conversa import Ato,Preparacao
            resultado=self._relatar(texto,"relato",conversa)
            self.ultima_resposta=resultado[1]
            return Preparacao(Ato("restricao_negada","dialogar"),resultado)
        return None

    def preparar_objetivo_pessoal(self, texto, conversa):
        """Uma ação sobre algo próprio declara objetivo, não retoma um fato."""
        n=normalizar(texto)
        if any(c in texto for c in ('?','`','"','“','”')):
            return None
        if not re.fullmatch(r"(?:eu )?(?:quero|pretendo|queria|gostaria de|estou pensando em) "
                r"(?:retomar|continuar|terminar|melhorar|cuidar de|ampliar|reorganizar|"
                r"criar|revisar|organizar|praticar|estudar|aprender) .+",n):
            return None
        if not re.search(r"\b(?:meu|minha|meus|minhas)\b",n) or re.search(
                r"\b(?:o que e|como funciona|defina|explique|liste|mostre)\b",n):
            return None
        from linguagem_conversa import Ato,Preparacao
        resultado=self._relatar(texto,"objetivo",conversa)
        self.ultima_resposta=resultado[1]
        return Preparacao(Ato("objetivo_pessoal_explicito","dialogar"),resultado)

    def preparar(self, texto, bot, conversa):
        from linguagem_conversa import Ato, Preparacao
        import conversa_assistente
        if conversa_assistente.responder(conversa_assistente.normalizar(texto), bot, {}, bot.ultimo_ato_social) is not None:
            return None
        if bot.ultimo_ato_social in ("social:assuntos", "social:pensamento") and normalizar(texto) == "como assim":
            return None
        if not isinstance(texto, str) or len(texto) > 1200:
            return None
        if self._pedido_prioritario(texto, bot, conversa):
            # Uma orientação factual pode responder ao objetivo declarado
            # sem impedir que esse objetivo seja lembrado no próximo turno.
            if re.fullmatch(r"(?:eu\s+)?(?:quero|pretendo|estou pensando em)\s+(?:aprender|estudar|praticar|treinar|montar|poupar|organizar)\s+[^?`\"“”]+", texto.strip().strip(". "), re.I):
                self._extrair(texto)
            return None
        retratada=self.preparar_restricao(texto,bot,conversa)
        if retratada is not None: return retratada
        if (self.ativo and "?" not in texto and not any(c in texto for c in ('`','"','“','”')) and
                re.match(r"(?:eu\s+)?(?:fiquei|senti|esqueci|preparei|tentei|percebi|aconteceu|"
                         r"consegui|decidi|estava|terminei)\s+",texto.strip(),re.I) and
                not re.search(r"\b(?:o que [eé]|como funciona|defina|explique|c[oó]digo|script)\b",texto,re.I)):
            resultado=self._relatar(texto,"relato",conversa)
            self.ultima_resposta=resultado[1]
            return Preparacao(Ato("relato_explicito","dialogar"),resultado)
        # Depois de perguntar o tema, 'sobre X' preenche esse slot. Não
        # exige adivinhar X na rede nem tratá-lo como uma consulta factual.
        if self.ativo and self.espera in ("tema", "interesse"):
            tema = re.fullmatch(r"sobre\s+(.+)", texto.strip().strip(". "), re.I)
            if tema and "?" not in texto and not re.search(r"\b(?:o que [eé]|como funciona|defina|explique)\b", texto, re.I):
                resultado = self._relatar(texto, "resposta", conversa)
                self.ultima_resposta = resultado[1]
                return Preparacao(Ato("dialogo_tema", "dialogar"), resultado)
        ato = self.analisar(texto, bot, conversa)
        # Uma declaração completa de objetivo pode preencher o slot mesmo
        # com um verbo fora do treino. Não converte pedidos de conhecimento,
        # escrita ou código em relatos pessoais.
        if ato is None and isinstance(texto, str) and len(texto) <= 1200 and not any(c in texto for c in ('?', '`', '"', '“', '”')):
            objetivo = re.fullmatch(r"(?:eu\s+)?(?:quero|pretendo|gostaria de|estou pensando em)\s+([\wÀ-ÿ]+)\s+(.+)", texto.strip().strip(". "), re.I)
            pedidos = {"saber", "entender", "compreender", "explicar", "resumir", "listar", "definir", "retomar", "voltar", "conhecer", "falar", "conversar", "escrever"}
            if objetivo and normalizar(objetivo.group(1)).endswith(("ar", "er", "ir")) and normalizar(objetivo.group(1)) not in pedidos and not re.search(r"\b(?:codigo|programa|script|funcao)\b", normalizar(objetivo.group(2))):
                ato = "objetivo"
                if self.ultimo_quadro is not None:
                    self.ultimo_quadro["fallback"] = "objetivo_explicito"
        if ato is None:
            return None
        resultado = None
        if ato == "lembrar":
            resultado = self._lembrar(texto, conversa)
        elif ato == "abrir":
            self.iniciar_assunto()
            conversa.assunto = conversa.objetivo = None
            conversa.relatos.clear()
            conversa.etapa = 0
            self.ativo, self.espera = True, "tema"
            resultado = ("conversa:abertura", "Pode falar. Quer me contar uma situação, explorar uma ideia ou só conversar sobre como foi seu dia?", None, "")
        elif ato == "reparar":
            atual = conversa._atual(bot)
            if atual:
                return Preparacao(Ato("reparar_dialogo", "transformar", formato="simples"), conversa.transformar("simples", atual, bot))
            if self.ultima_resposta and self.ativo:
                referencia = conversa.objetivo or self.dados.get("ultimo_relato", "a situação")
                resultado = ("conversa:reformulacao", "Vou simplificar: estamos falando de “" + referencia + "”. Podemos escolher um próximo passo pequeno. Qual parte ficou confusa?", None, "")
            else:
                resultado = ("duvida", "Qual explicação ficou confusa? Preciso de uma resposta anterior ou do trecho que você quer esclarecer.", None, "")
        elif ato == "motivo":
            atual = conversa._atual(bot)
            if atual and atual.contexto:
                causal = bot.compositor.responder("por que", atual.contexto)
                resultado = (*causal, "")
            elif self.motivo and self.ativo:
                resultado = ("conversa:justificativa", self.motivo, None, "")
            else:
                resultado = ("duvida", "De qual afirmação você quer saber o motivo? Pode citar o trecho ou indicar o assunto.", None, "")
        elif ato == "reciproco":
            if self.ativo or conversa.assunto:
                referencia = self.dados.get("preferencia") or conversa.assunto or "essa ideia"
                resultado = ("conversa:perspectiva", "Não tenho gostos ou experiências pessoais. Posso explorar “" + referencia + "” com você e ajudar a comparar ideias. O que te interessa mais nisso?", None, "")
            else:
                resultado = ("duvida", "Você quer saber o que penso sobre qual ideia?", None, "")
        elif ato in ("relato", "preferencia", "objetivo", "ponto_de_vista", "resposta"):
            resultado = self._relatar(texto, ato, conversa)
        elif ato == "planejar":
            resultado = self._planejar(conversa)
        elif ato == "refletir":
            resultado = self._refletir(texto, conversa)
        elif ato == "ideias":
            resultado = self._ideias(conversa)
        elif ato == "criterios":
            referencia = (self.dados.get("preferencia") or conversa.objetivo or self.dados.get("objetivo")) if self.ativo or conversa.assunto else None
            resposta = "Para avaliar sua pergunta “" + texto.strip()[:240] + "”, precisamos de um critério."
            if referencia:
                resposta += " Você trouxe “" + referencia + "”; isso pode servir de ponto de partida para avaliar o resultado."
            resposta += " Eu compararia o que se esperava com o que foi entregue, o que funcionou e o que poderia melhorar. Qual qualidade é mais importante para você nesse caso?"
            self.espera = "criterio"
            self.motivo = "Uma avaliação depende do resultado esperado e do critério usado. Parti da sua pergunta e das preferências que você contou, sem declarar uma resposta universal."
            resultado = ("conversa:criterios", resposta, None, "")
        if resultado:
            if resultado[0].startswith("conversa:"):
                self.ativo = True
                self.ultima_resposta = resultado[1]
            return Preparacao(Ato("dialogo_" + ato, "dialogar"), resultado)
        return None

    def registrar(self, identificador, texto, conversa):
        if identificador == "conversa:reinicio":
            self.limpar()
        elif identificador.startswith("conversa:neural_"):
            # O fallback sabe que houve conversa. O texto gerado não
            # preenche dados pessoais nem vira relato do usuário.
            self.ativo, self.espera = True, None
            self.ultima_resposta = texto
        elif identificador == "conversa:abertura":
            self.ativo, self.espera = True, "tema"
            self.ultima_resposta = texto
        elif identificador == "conversa:retomada":
            self.ativo, self.espera = True, "detalhe"
            self.ultima_resposta = texto
            self.iniciar_assunto()
            perfil = {k: v for k, v in self.dados.items() if k in ("nome", "preferencia", "aversao")}
            for relato in conversa.relatos:
                self._extrair(relato)
                self._guardar("ultimo_relato", relato)
            for k in ("nome", "preferencia", "aversao"):
                self.dados.pop(k, None)
            self.dados.update(perfil)
            self.espera = "detalhe"
            if conversa.objetivo:
                self._guardar("objetivo", conversa.objetivo)
        elif identificador in ("conversa:calculo", "conversa:hipotese"):
            self.ativo, self.espera = True, None
            self.ultima_resposta = texto
            self.motivo = texto
        elif not identificador.startswith(("conversa:", "social:")):
            # Uma consulta factual suspende o diálogo pessoal. Os slots
            # declarados ficam disponíveis somente para lembrança explícita.
            self.ativo, self.espera = False, None
            self.motivo = ""
