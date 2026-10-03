#!/usr/bin/env python3
"""
Crivo v0.4 - assistente de conversa em português.

Assuntos do primeiro teste: plantas, animais, clima, tempo, estações do ano,
sistema solar, coisas de casa e fundamentos de programação.

Uso:
    python crivo.py                 conversa no terminal
    python crivo.py "sua pergunta"  responde uma vez
    python crivo.py --teste         roda a bateria de testes (testes.json)

Sem dependências externas: só a biblioteca padrão do Python 3.8+.
"""
import datetime
import difflib
import json
import math
import random
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path
import conversa_assistente

VERSAO = "0.4"
PASTA = Path(__file__).resolve().parent

TOPICOS = {
    "plantas": "plantas",
    "animais": "animais",
    "clima": "clima",
    "tempo": "tempo (horas, datas, calendário)",
    "estacoes": "estações do ano",
    "sistema_solar": "sistema solar",
    "casa": "coisas de casa",
    "programacao": "programação (fundamentos, Python, HTML, CSS, JavaScript, SQL e Git)",
    "mundo": "ciência e psicologia (cérebro, memória, sono, emoções, biologia e ambiente)",
}

LIMIAR = 0.46        # abaixo disso o Crivo não responde direto
LIMIAR_DUVIDA = 0.30  # entre os dois limiares, ele pergunta se você quis dizer outra coisa

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
        "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


# ---------------------------------------------------------------- texto ----
def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def normalizar(s):
    return sem_acento(s.lower())


def chave_pergunta(texto):
    """Ignora pontuação de frase sem apagar operadores ou nomes como C++ e C#."""
    return " ".join(re.findall(
        r"[a-z0-9_]+(?:\+\+|#)?|===|!==|==|!=|<=|>=|=>|\*\*|[=<>+*/%]",
        normalizar(texto)))


_STOP = """a o as os um uma uns umas de do da dos das em no na nos nas por para
pra com sem e ou que qual quais quem como onde quando quanto quantos quantas
quanta me te se ao aos eh ser sao foi tem ter tenho existe existem isso isto
esse essa esses essas aquilo eu voce vc mim meu minha muito mais mas pois
porque porquê fala falar diga explique explica sobre pode poder posso fazer
faz vai vou esta estao estou esta ha la aqui ai ja so tambem entao pois
gostaria queria quero saber me diz fale conte pro num numa existir existirem ajuda ajude ajudar
faz""".split()
STOP = {normalizar(p) for p in _STOP}


SINONIMOS = {
    "molhar": "regar", "molhe": "regar", "molha": "regar",
    "alimento": "comida", "escuro": "sombra",
    "troveja": "trovao", "trovejar": "trovao",
    "viver": "vida", "vive": "vida", "vivem": "vida",
    "veneno": "toxico", "venenoso": "toxico", "venenosa": "toxico",
    "envenenar": "toxico",
    "molho": "regar", "vasinho": "vaso", "ajudam": "ajuda",
    "paises": "pais", "diferente": "diferenca",
    "existirem": "existir", "existem": "existir",
    "bicho": "animal", "passaro": "ave",
    "estragou": "velho", "estragado": "velho",
    "adubar": "adubo", "fertilizante": "adubo",
    "alimentar": "comida", "alimenta": "comida", "alimentam": "comida",
    "amarelada": "amarelo", "amareladas": "amarelo", "amarela": "amarelo",
    "amarelando": "amarelo", "amarelas": "amarelo",
    "cuidados": "cuidar", "cuidado": "cuidar",
    "servem": "serve", "funcao": "serve",
    "veloz": "rapido", "velozes": "rapido",
    "brasileiro": "brasil", "brasileiros": "brasil",
    "poupar": "economizar", "remover": "tirar",
    "toxico": "toxico", "toxica": "toxico", "toxicas": "toxico",
    "respira": "respirar", "respiram": "respirar",
    "migra": "migrar", "migram": "migrar", "migracao": "migrar",
    "regue": "regar", "regam": "regar",
}

# Termos técnicos explícitos. Palavras comuns como "nome", "tipo" ou "ler"
# não indicam programação: também aparecem nos assuntos gerais.
TERMOS_PROGRAMACAO = {
    "unittest", "dict", "dicionario", "try", "except", "return", "def",
    "while", "const", "let", "array", "queryselector", "dom", "promise",
    "await", "async", "select", "where", "join", "commit", "branch",
    "repositorio", "loop", "laco", "indentacao", "input", "print",
}


def radical(p):
    """Redução simples de plural/diminutivo, igual para pergunta e base."""
    if len(p) > 6:
        p = re.sub(r"inh([ao])s?$", r"\1", p)
    if p.endswith("oes") and len(p) > 4:
        return p[:-3] + "ao"
    if p.endswith("ais") and len(p) > 4:
        return p[:-3] + "al"
    if re.search(r"(r|z|s)es$", p) and len(p) > 4:
        return p[:-2]
    if p.endswith("s") and len(p) > 3:
        return p[:-1]
    return p


def tokens(texto):
    ps = re.findall(r"[a-z0-9]+", normalizar(texto))
    rs = [SINONIMOS.get(r, r) for r in (radical(SINONIMOS.get(p, p))
          for p in ps if p not in STOP and len(p) > 1)]
    return rs


# Ponte lexical restrita às consultas técnicas. Não muda os documentos
# cadastrados, nem cria respostas: associa formas descritivas a termos já
# ensinados no currículo. Uma pergunta fora dele continua sem resposta.
SINONIMOS_CONSULTA_TECNICA = {
    "coletar": "receber",
    "informacao": "dados",
    "digitado": "teclado",
    "digitada": "teclado",
    "inspecionar": "comparar",
}

# ------------------------------------------------------------- modelo ------
class Crivo:
    def __init__(self, caminho_base=None, agora=None, usar_linguagem_neural=True,
                 usar_dialogo_contextual=False, modelo_linguagem=None, gerador_programacao=None):
        caminho = Path(caminho_base) if caminho_base else PASTA / "conhecimento.json"
        self.gerador_programacao = gerador_programacao
        self.caminho_base = caminho
        from curriculo_mundo import carregar_base, ler_curriculo
        self.curriculo_mundo = ler_curriculo(caminho.with_name("conhecimento_mundo.json"))
        self.base = carregar_base(caminho, self.curriculo_mundo)
        # Grafo explicável opcional, vinculado à pasta da base escolhida.
        # Bases temporárias personalizadas não recebem fatos da base padrão.
        from raciocinio import GrafoRaciocinio
        caminho_relacoes = caminho.with_name("relacoes.json")
        self.raciocinio = (GrafoRaciocinio.carregar(caminho_relacoes)
                          if caminho_relacoes.is_file() else None)
        # Conhecimento estruturado e independente da rede neural: o mesmo
        # arquivo precisa estar junto da base ativa. Bancos temporários sem
        # o arquivo não herdam nenhuma fruta da instalação padrão.
        from frutas import ConhecimentoFrutas
        caminho_frutas = caminho.with_name("frutas.json")
        self.frutas = (ConhecimentoFrutas.carregar(caminho_frutas)
                       if caminho_frutas.is_file() else None)
        from conhecimento_programacao import ConhecimentoProgramacao
        acervo = caminho.parent / "docs/pesquisa_conhecimento/programacao/catalogo-avancado.json"
        self.programacao = ConhecimentoProgramacao(acervo) if acervo.is_file() else None
        self.contexto_frutas = None
        # Intenção abstrata para continuação do próximo turno, não
        # identifica entidades nem persiste além da pergunta seguinte.
        from interpretacao_geral import InterpretadorGeral
        self.interpretador_geral = InterpretadorGeral(self.raciocinio)
        # Os mesmos quadros sujeito/ação/objeto valem para todas as
        # entidades de qualquer grafo; não adiciona respostas isoladas.
        from analisador_portugues import AnalisadorPortugues
        self.analisador_portugues = AnalisadorPortugues(self.raciocinio)
        from consultas_relacionais import ConsultasRelacionais
        self.consultas_relacionais = ConsultasRelacionais(self.raciocinio)
        self.contexto_consulta = None
        self.contexto_geral = None
        self._agora = agora  # permite fixar a data em testes
        self._indexar()
        from composicao_textual import CompositorTextual
        self.compositor = CompositorTextual(
            self.base, caminho.with_name("conhecimento_expandido.json"), self._alvo_definicao,
            self.curriculo_mundo)
        from interpretacao_pedidos import InterpretadorPedidos
        self.interpretador_pedidos = InterpretadorPedidos(self.raciocinio, self.consultas_relacionais)
        from linguagem_conversa import Conversacao
        self.conversacao = Conversacao(usar_neural=usar_linguagem_neural,
                                      usar_dialogo_contextual=usar_dialogo_contextual,
                                      modelo_linguagem=modelo_linguagem)
        from planejamento_conversa import PlanejadorConversa
        self.planejador = PlanejadorConversa(self.compositor)
        self._pedido_turno = None
        self.contexto_textual = None
        self._contexto_textual_anterior = None
        self.ultimo_ato_social = None
        self._ato_social_anterior = None
        self.ultimo_turno = None
        self._turno_anterior = None
        self.ultimos = []     # ranking da última pergunta, para "mais"
        self.pos_ultimo = 0
        self.historico = []
        # Último conceito com ficha de que a conversa tratou ("ele", "lá"…).
        self.assunto_conversa = None
        self.linguagem_conversa = None
        self.nocao_conversa = None
        self.memoria_relatos = None
        from presenca import Perfil
        self.perfil = Perfil()
        self.variacao = None
        # Última resposta efetivamente proferida; o servidor HTTP
        # reconstrói esse estado pelo replay seguro do histórico.
        self.ultima_resposta_mostrada = None
        self._referencia_turno_anterior = None
        self.ultimo_assunto = None
        self.esclarecimento = None
        self.rede = None
        self.limiar_rede = 0.80
        self.erro_rede = None
        pesos = caminho.with_name('rede_crivo.json')
        if pesos.is_file():
            try:
                self.carregar_rede(pesos)
            except (ValueError, OSError, KeyError, TypeError) as exc:
                # Pesos antigos ou corrompidos nao devem impedir o chatbot
                # de funcionar via recuperador de conhecimento.
                self.erro_rede = str(exc)

    def carregar_rede(self, caminho, limiar=0.80):
        from rede_neural import RedeCrivo, assinatura_base, assinatura_regras
        rede = RedeCrivo.carregar(caminho)
        if set(rede.rotulos) != {e["id"] for e in self.base}:
            raise ValueError("Rede incompatível com a base; treine novamente")
        if (rede.assinatura_base is not None and
                rede.assinatura_base != assinatura_base(self.base)):
            raise ValueError("Perguntas da base mudaram; treine a rede novamente")
        if (rede.assinatura_regras is not None and
                rede.assinatura_regras != assinatura_regras(rede.modo)):
            raise ValueError("Regras linguisticas mudaram; treine a rede novamente")
        if not 0 < limiar <= 1:
            raise ValueError("Limiar inválido")
        self.rede = rede
        self.erro_rede = None
        self.limiar_rede = limiar

    def previsao_neural(self, pergunta):
        """Retorna (id, probabilidade) sem alterar a resposta do recuperador."""
        if self.rede is None:
            return None
        return self.rede.prever(pergunta)

    # "treino": monta o índice TF-IDF da base
    def _indexar(self):
        docs = []
        self.indices_exatos = {}
        for indice, e in enumerate(self.base):
            c = Counter()
            for chave in {chave_pergunta(p) for p in e["perguntas"]}:
                self.indices_exatos.setdefault(chave, []).append(indice)
            for q in dict.fromkeys(e["perguntas"]):
                for t in tokens(q):
                    c[t] += 3
            for t in tokens(e["resposta"]):
                c[t] += 1
            for t in tokens(e["topico"].replace("_", " ")):
                c[t] += 1
            docs.append(c)
        self.termos = [set(c) for c in docs]
        n = len(docs)
        df = Counter()
        for c in docs:
            df.update(c.keys())
        self.idf = {t: math.log((n + 1) / (d + 1)) + 1 for t, d in df.items()}
        self.idf_raro = max(self.idf.values(), default=1.0)
        self.exemplos = [[set(tokens(p)) for p in dict.fromkeys(e["perguntas"])]
                         for e in self.base]
        # Núcleo de cada entrada: o assunto dela (palavras da maioria dos
        # exemplos e do identificador). "Conceitos" são os núcleos de todas.
        self.nucleos = []
        for i, e in enumerate(self.base):
            freq = Counter(t for ex in self.exemplos[i] for t in ex)
            nucleo = {t for t, f in freq.items() if f * 2 >= len(self.exemplos[i])}
            # Um exemplo de uma palavra só ("o que é uma galáxia") também é assunto.
            sozinhas = {t for ex in self.exemplos[i] if len(ex) == 1 for t in ex}
            self.nucleos.append(nucleo | sozinhas | set(tokens(e["id"].replace("_", " "))))
        self.conceitos = set().union(*self.nucleos) - self._GENERICOS if self.nucleos else set()
        # Um currículo novo não deve alterar o peso das palavras de outro domínio.
        self.grupos = ["mundo" if e.get("origem_curriculo") == "mundo" else
                       "programacao" if e["topico"] == "programacao" else "geral"
                       for e in self.base]
        self.idf_grupos = {}
        for grupo in set(self.grupos):
            indices = [i for i, g in enumerate(self.grupos) if g == grupo]
            frequencias = Counter(t for i in indices for t in docs[i])
            self.idf_grupos[grupo] = {
                t: math.log((len(indices) + 1) / (d + 1)) + 1
                for t, d in frequencias.items()}
        self.vetores = []
        for i, c in enumerate(docs):
            idf = self.idf_grupos[self.grupos[i]]
            v = {t: (1 + math.log(f)) * idf[t] for t, f in c.items()}
            norma = math.sqrt(sum(x * x for x in v.values())) or 1.0
            self.vetores.append({t: x / norma for t, x in v.items()})

    def _tokens_consulta(self, texto, vocabulario=None):
        vocabulario = self.idf if vocabulario is None else vocabulario
        resultado = []
        # Só aplica equivalências técnicas quando a linguagem/ambiente
        # está explícito; consultas gerais preservam sua tokenização.
        tecnico = bool(re.search(
            r"\b(python|javascript|js|git|sql)\b", normalizar(texto)))
        for t in tokens(texto):
            # "Como funciona X?" usa "funciona" como verbo de pergunta;
            # sozinho ele não identifica um tópico. Retirá-lo apenas da
            # consulta não modifica o conhecimento indexado.
            if t == "funciona":
                continue
            if tecnico:
                t = SINONIMOS_CONSULTA_TECNICA.get(t, t)
            if t not in vocabulario and len(t) >= 5:
                # Só corrigir grafias muito próximas e com candidato único.
                proximos = difflib.get_close_matches(t, vocabulario, n=2, cutoff=0.88)
                if len(proximos) == 1:
                    t = proximos[0]
            resultado.append(t)
        # Em Git, revisar diferenças de arquivos/alterações é a operação
        # "diff". Não usar essa pista quando a consulta menciona outros
        # comandos explicitamente: "diferença entre commit e push" não
        # pede executar nem explicar git diff.
        n = normalizar(texto)
        if (re.search(r"\bgit\b", n) and
                re.search(r"\b(diferencas?|comparar|inspecionar|revisar)\b", n) and
                re.search(r"\b(arquivos?|alteracoes?|mudancas?)\b", n) and
                not re.search(r"\b(commit|push|branch)\b", n) and
                "diff" in vocabulario and "diff" not in resultado):
            resultado.append("diff")
        # Pistas de interação humano-programa: perguntar ou coletar um dado
        # da pessoa que digita não é o mesmo que ler arquivo, consultar API
        # ou declarar variável. Usa termos JÁ presentes no índice, sem
        # inventar uma intenção nem ampliar o currículo.
        if (re.search(r"\bpython\b", n) and
                re.search(r"\b(obter|pegar|pedir|perguntar|solicitar|informe|informar|"
                          r"recolher|capturar|receber|coletar|aguardar)\b", n) and
                re.search(r"\b(usuario|pessoa|alguem|quem usa|"
                          r"teclado|console|terminal|digitacao|digitad[oa]s?)\b", n) and
                not re.search(r"\b(arquivo|json|api|http|sql|dicionario|"
                              r"variavel|telefone|gps|whatsapp|mensagem|"
                              r"excecao|keyerror|nameerror|typeerror|"
                              r"print|saida|formulario|web|site|navegador|"
                              r"camera|imagem|video|microfone|audio|"
                              r"socket|endpoint)\b", n)):
            for pista in ("input", "teclado", "usuario"):
                if pista in vocabulario and pista not in resultado:
                    resultado.append(pista)
        # Uma operação de JavaScript sobre elemento/campo HTML pertence
        # ao DOM; HTML é o alvo, não uma segunda linguagem exigida.
        if (re.search(r"\b(javascript|js)\b", n) and
                re.search(r"\b(html|pagina|dom)\b", n) and
                re.search(r"\b(campo|elemento|tag|no)\b", n) and
                re.search(r"\b(ler|valor|selecionar|alterar|texto|pegar|obter)\b", n) and
                not re.search(r"\b(sql|css|java|python|api)\b", n)):
            for pista in ("dom", "elemento"):
                if pista in vocabulario and pista not in resultado:
                    resultado.append(pista)
        return resultado

    def _indices_consulta(self, texto):
        """Respeita a linguagem pedida e os identificadores ensinados na base."""
        n = normalizar(texto)
        aliases = {
            "python": r"\b(python|py|pip|venv)\b",
            "javascript": r"\b(javascript|js|nodejs|node\.js)\b",
            "html": r"\bhtml\b", "css": r"\bcss\b",
            "sql": r"\b(sql|sqlite3?)\b", "git": r"\bgit\b",
        }
        linguagens = {nome for nome, padrao in aliases.items() if re.search(padrao, n)}
        # HTML e CSS podem ser o objeto manipulado por JavaScript, não
        # linguagens adicionais exigidas do mesmo exemplo. Python + JS,
        # por outro lado, continua sendo uma consulta multi-linguagem.
        exigidas = linguagens - {"html", "css"} if "javascript" in linguagens else linguagens
        sem_conteudo = re.search(
            r"\b(java|rust|kotlin|swift|ruby|php|typescript)\b|"
            r"(?<!\w)c(?:\+\+|#)(?!\w)", n)
        if sem_conteudo:
            return []
        identificadas = {i for i, e in enumerate(self.base) if any(
            re.search(r"\b" + re.escape(normalizar(t)) + r"\b", n)
            for t in e.get("identificadores", []))}
        programacao = bool(linguagens or identificadas or
            set(tokens(texto)) & TERMOS_PROGRAMACAO or re.search(r"\btipos? de dados\b", n) or re.search(
            r"\b(programacao|programar|codigo|algoritmo|variavel|variaveis|"
            r"booleano|debug|depurar|bug|api|http|software|script|compilador)\b", n))
        if not programacao:
            return [i for i, g in enumerate(self.grupos) if g == "geral"]
        indices = []
        for i, e in enumerate(self.base):
            if e["topico"] != "programacao":
                continue
            cobertas = set(e.get("linguagens", [e.get("area")]))
            if exigidas and not exigidas <= cobertas:
                if not (len(exigidas) == 1 and e.get("area") in (None, "fundamentos")):
                    continue
            if identificadas and i not in identificadas:
                continue
            indices.append(i)
        return indices

    def _contexto_consulta(self, texto):
        indices = self._indices_consulta(texto)
        idf = self.idf_grupos[self.grupos[indices[0]]] if indices else {}
        return indices, idf

    _GENERICOS = {"tempo", "dura", "vida", "tipo", "diferenca", "entre", "usar", "serve", "fazer", "casa",
                  "dia", "ano", "coisa", "nome", "agua", "forma", "ideal", "precisa", "bom", "boa", "nao",
                  "melhor", "maior", "menor", "quanto", "quando", "porque"}
    # Símbolos de código: a pergunta é de programação.
    _CODIGO = re.compile(r"===?|!==?|=>|&&|\|\||\+\+|\w\(\)|\bdef \w|\bfunction\b|\bconsole\.|\bprint\(")
    # "Se todo A é B…": hipótese, nunca um fato cadastrado.
    _HIPOTESE = re.compile(r"^\s*se (?:todo|toda|todos|todas|nenhum|nenhuma|algum|alguma|um|uma|eu|o|a|x)\b.*\?")
    # Conta: números com operação, ou "quantos sobram/ficaram".
    _CONTA = re.compile(r"\d+\s*(?:[-+*/x^]|mais|menos|vezes|dividido|elevado)\s*(?:a |por )?\d+|"
                        r"\bquant[oa]s? (?:sobra|sobram|ficam|ficaram|resta|restam|sobrou|ficou)\b")

    _GERAR = re.compile(r"\s*(?:me )?(?:escreva|escreve|crie|cria|faca|faz|implemente|implementa|gere|programe)\b")

    def _conceitos_com_entidades(self):
        """Núcleos da base mais os seres e astros do grafo de relações
        ("golfinho", "morcego"), uma vez por instância."""
        if getattr(self, "_conceitos_cache", None) is None:
            extra = set()
            grafo = getattr(self, "raciocinio", None)
            for nome in (getattr(grafo, "nomes", None) or {}):
                if "_" not in nome:
                    extra |= set(tokens(nome))
            # Partes de seres ("penas", "folha") não são assuntos à parte, e
            # "pena" aparece em "vale a pena".
            extra -= {"pena", "raiz", "folha", "caule", "celula"}
            self._entidades = extra - self._GENERICOS
            self._conceitos_cache = (self.conceitos | extra) - self._GENERICOS
        return self._conceitos_cache

    def _fora_do_assunto(self, texto, indice):
        """A entrada só coincide com a pergunta numa palavra lateral ("Por que
        o céu é azul?" × cores da reciclagem) ou deixa de fora outro assunto
        que a pergunta cita ("Plantas respiram?" × peixes)."""
        _, vocabulario = self._contexto_consulta(texto)
        toks = list(dict.fromkeys(self._tokens_consulta(texto, vocabulario)))
        bate = [t for t in toks if t in self.termos[indice]]
        resto = [t for t in toks if t not in self.termos[indice]]
        nucleo = self.nucleos[indice]
        conceitos = self._conceitos_com_entidades()
        # "Morcego é ave?": classificação de X só com entrada que fale de X.
        classe = re.fullmatch(r"(?:o |a |um |uma )?(\w+) (?:e|eh) (?:um |uma )?(\w+)", normalizar(texto).strip(" ?.!"))
        if classe:
            sujeito = [t for t in tokens(classe.group(1))]
            if sujeito and not any(t in self.termos[indice] for t in sujeito):
                return True
        if len(bate) == 1 and resto and bate[0] not in nucleo:
            return True
        outros = [t for t in resto if t in conceitos and t not in nucleo]
        # Quando a pergunta cita o assunto do próprio identificador ("mofo no
        # guarda-roupa" × mofo), só outro ser ou astro citado a desqualifica.
        cita_assunto = bool(set(bate) & set(tokens(self.base[indice]["id"].replace("_", " "))))
        if cita_assunto:
            outros = [t for t in outros if t in self._entidades]
        if outros and (len(bate) <= 1 or not (set(bate) & nucleo) - self._GENERICOS):
            return True
        # "Golfinho respira debaixo d'água?" × peixes: outro ser citado e metade
        # ou mais do assunto da entrada ausente da pergunta.
        seres = [t for t in outros if t in self._entidades]
        if seres and not cita_assunto and nucleo and len(nucleo - set(bate)) * 2 >= len(nucleo):
            return True
        # "Escreva fatorial em JavaScript": pedido de algo que não conheço não
        # vira a introdução da linguagem.
        verbos = {"faca", "faz", "descreva", "escreva", "escreve", "crie", "cria", "implemente", "implementa",
                  "gere", "programe"}
        if self._GERAR.match(normalizar(texto)) and any(t not in vocabulario and t not in verbos for t in toks):
            return True
        return False

    def _ranking(self, texto):
        indices, idf = self._contexto_consulta(texto)
        idf_raro = max(idf.values(), default=1.0)
        c = Counter(self._tokens_consulta(texto, idf))
        if not c:
            return []
        q = {t: (1 + math.log(f)) * idf.get(t, 0.0) for t, f in c.items()}
        norma = math.sqrt(sum(x * x for x in q.values())) or 1.0
        q = {t: x / norma for t, x in q.items()}
        pontos = []
        total = sum(idf.get(t, idf_raro) for t in c) or 1.0
        for i in indices:
            v = self.vetores[i]
            s = sum(x * v.get(t, 0.0) for t, x in q.items())
            # cobertura: quanto do peso da pergunta esta entrada explica
            cob = sum(idf[t] for t in c if t in self.termos[i]) / total
            s += 0.4 * cob
            # Um exemplo forte vale mais que repetir exemplos parecidos.
            # O peso IDF preserva os termos que distinguem duas intenções.
            tq = set(q)
            similares = []
            for tp in self.exemplos[i]:
                uniao = tq | tp
                if uniao:
                    inter = sum(idf.get(t, idf_raro) for t in tq & tp)
                    peso = sum(idf.get(t, idf_raro) for t in uniao)
                    similares.append(inter / peso)
            s += 0.35 * max(similares, default=0.0) + 1.05 * sum(similares) / max(1, len(similares))
            pontos.append((s, i))
        nq = normalizar(texto)
        if re.search(r"\b(por que|porque|o que faz|o que causa)\b", nq):
            for k, (score, idx) in enumerate(pontos):
                exemplos = " ".join(normalizar(p) for p in self.base[idx]["perguntas"])
                if score > 0 and re.search(r"\b(por que|porque|o que causa|o que faz)\b", exemplos):
                    pontos[k] = (score + 0.30, idx)
        pontos.sort(reverse=True)
        return [(s, i) for s, i in pontos if s > 0]


    @staticmethod
    def _alvo_definicao(texto):
        """Extrai somente pedidos diretos de definição de um conceito.

        Não confunde comparação, causa ou característica com definição.
        A interpretação é deliberadamente estreita, não generativa.
        """
        n = normalizar(conversa_assistente.preparar_pedido(texto)).strip().strip("?.,;! ")
        expressoes = (
            r"(?:e\s+)?(?:(?:poderia|pode) me explicar |explique )?o que (?:e|eh|sao) (.+)",
            r"o que (?:significa|quer dizer) (.+)",
            r"qual (?:e )?(?:o )?significado (?:de|do|da) (.+)",
            r"defina (.+)",
            r"(?:qual e a |qual a )definicao de (.+)",
            r"definicao de (.+)",
        )
        for padrao in expressoes:
            match = re.fullmatch(padrao, n)
            if match:
                conceito = re.sub(r"^(?:um|uma|o|a|os|as)\s+", "", match.group(1))
                conceito = re.sub(r"^(?:termo|conceito)\s+", "", conceito)
                # "variável num programa" e "variável em programação"
                # referem-se ao mesmo conceito geral. Não apaga contexto
                # de linguagem específica, como "em Python".
                conceito = re.sub(
                    r"\s+(?:(?:num|em um|no) programa|(?:em|na) programacao)$",
                    "", conceito)
                if not conceito or re.match(r"^(?:diferenca|melhor|mais|menos)\b", conceito):
                    return None
                return conceito
        return None

    def _responder_definicao(self, texto, original):
        """Só usa uma entrada cuja pergunta define o MESMO conceito.

        O compartilhamento isolado de uma palavra não constitui evidência
        de que o texto recuperado defina o termo pedido. A correção de
        pequenos erros de grafia utiliza o vocabulário já indexado.
        """
        alvo = self._alvo_definicao(texto)
        if alvo is None:
            return None
        # "o fenômeno El Niño" é o conceito El Niño, não um fenômeno
        # arbitrário. Não remove qualificadores que mudam o significado
        # ("árvore binária", "árvore genealógica" etc.).
        alvo = re.sub(r"^(?:fenomeno|conceito|termo)\s+", "", alvo)
        alvo_tokens = tuple(self._tokens_consulta(alvo))
        if not alvo_tokens:
            return None
        permitidas = set(self._indices_consulta(texto))
        candidatas = []
        for indice in permitidas:
            entrada = self.base[indice]
            conceitos = [
                conceito for pergunta in entrada["perguntas"]
                for conceito in [self._alvo_definicao(pergunta)]
                if conceito is not None
            ] + entrada.get("definicoes", [])
            for conceito in conceitos:
                definidos = tuple(self._tokens_consulta(conceito))
                if definidos == alvo_tokens:
                    candidatas.append(indice)
                    break
                # Modificador único que conste na própria explicação:
                # "solstício de verão" tem evidência para verão; "árvore
                # de decisão" NÃO pode herdar definição de árvore.
                extras = alvo_tokens[len(definidos):]
                if (definidos and len(extras) == 1 and
                        alvo_tokens[:len(definidos)] == definidos and
                        extras[0] in tokens(entrada["resposta"])):
                    candidatas.append(indice)
                    break
        if len(candidatas) == 1:
            indice = candidatas[0]
            self.ultimos = [(1.0, indice)]
            self.pos_ultimo = 0
            ident, resposta = self._registrar(indice, original)
            definicao_editorial = self.base[indice].get("resposta_definicao")
            if definicao_editorial:
                resposta = definicao_editorial + "\n\n" + resposta
            return ident, resposta
        if len(candidatas) > 1:
            return self._pedir_esclarecimento(candidatas[:2], original)
        # Sem pergunta definicional equivalente, uma explicação pode
        # descrever o conceito no próprio texto. Isso preserva paráfrases
        # sem liberar respostas que apenas mencionam a palavra incidentalmente.
        rank = self._ranking(texto)
        if rank and rank[0][0] >= LIMIAR:
            indice = rank[0][1]
            entry = self.base[indice]
            if set(alvo_tokens) <= self.termos[indice]:
                if len(alvo_tokens) >= 2:
                    # Qualificadores também precisam ter presença no texto
                    # do candidato; árvore binária ≠ árvore botânica.
                    return None
                termo = alvo_tokens[0]
                id_tokens = tuple(tokens(entry["id"].replace("_", " ")))
                if id_tokens == (termo,):
                    return None
                for frase in re.split(r"[.!?;]", entry["resposta"]):
                    palavras = re.findall(r"[a-z]+", normalizar(frase))
                    while palavras and palavras[0] in (
                            "o", "a", "os", "as", "um", "uma", "no", "na", "la", "el"):
                        palavras.pop(0)
                    if (palavras and len(termo) >= 4 and
                            palavras[0].startswith(termo[:4]) and
                            any(v in ("e", "sao", "tem", "possuem", "da",
                                      "consiste", "protege", "significa")
                                for v in palavras[1:6])):
                        return None
                # Conceito em aposto explicativo: "A Via Láctea é a
                # nossa galáxia, um conjunto de estrelas..." define
                # galáxia, mas "entre nuvem e solo" não define nuvem.
                padrao = (r"\be\s+(?:(?:a|o|um|uma|nossa|nosso)\s+){0,2}" +
                          re.escape(normalizar(alvo)) +
                          r"\s*,\s+(?:um|uma)\s+")
                if re.search(padrao, normalizar(entry["resposta"])):
                    return None
        self.esclarecimento = None
        self.ultimo_assunto = None
        return ("fora",
                "Ainda não tenho uma definição cadastrada para esse conceito. "
                "Conhecer palavras parecidas não basta para responder com segurança.")

    def _responder_definicoes_coordenadas(self, texto):
        """Compor definições de 2-3 conceitos sem seleção por ranking.

        Cada item tem de possuir uma definição EDITORIAL explicitamente
        associada ao conceito por pergunta ou alias. Um desconhecido
        invalida a composição inteira. Só apresenta a primeira frase
        factual, sem copiar exemplos de código sem solicitação.
        """
        from interpretacao_geral import extrair_definicoes_coordenadas
        alvos = extrair_definicoes_coordenadas(texto)
        if alvos is None:
            return None

        partes, faltantes, ambiguos, fontes = [], [], [], []
        for alvo in alvos:
            # Restrição de domínio e de linguagem é a mesma das perguntas
            # simples; não herda a definição de HTML de JavaScript.
            consulta = "o que e " + alvo
            indices = self._indices_consulta(consulta)
            conceito = self._alvo_definicao(consulta)
            chave = chave_pergunta(conceito) if conceito else ""
            encontrados = []
            for idx in indices:
                entrada = self.base[idx]
                declaracoes = [
                    definido for pergunta in entrada["perguntas"]
                    for definido in [self._alvo_definicao(pergunta)]
                    if definido is not None
                ] + entrada.get("definicoes", [])
                if any(chave_pergunta(definido) == chave for definido
                       in declaracoes):
                    encontrados.append(idx)

            if len(encontrados) == 0:
                faltantes.append(alvo)
                continue
            if len(encontrados) > 1:
                ambiguos.append(alvo)
                continue
            entrada = self.base[encontrados[0]]
            fonte = entrada.get("resposta_definicao") or entrada["resposta"]
            resumo = re.split(r"(?<=[.!?])\s+", fonte.strip(), maxsplit=1)[0]
            partes.append(alvo + ": " + resumo)
            fontes.append(entrada["id"])

        if faltantes and not partes and not ambiguos:
            # Uma pergunta editorial sobre um CONCEITO COMPOSTO
            # (ex.: rotação e translação) pode ter resposta própria,
            # mesmo sem duas definições separadas. Nesse caso, usar
            # os mecanismos já existentes; não causar regressão
            # impondo falsamente um desmembramento em partes.
            return None
        if faltantes or ambiguos:
            self.esclarecimento = None
            self.ultimo_assunto = None
            self.contexto_geral = None
            itens = faltantes + ambiguos
            return ("fora",
                    "Ainda não tenho uma definição específica e inequívoca "
                    "para " + ", ".join(itens) +
                    ". Não vou preencher essa lacuna com um assunto "
                    "apenas parecido.")
        if len(set(fontes)) != len(fontes):
            return ("duvida",
                    "Os nomes mencionados apontam para a mesma definição "
                    "cadastrada. Pode especificar a distinção desejada?")

        resposta = "\n\n".join(partes)
        self.esclarecimento = None
        self.ultimo_assunto = None
        self.contexto_geral = "definicao"
        self.historico.append({"pergunta": texto, "id": "composto:definicao",
                               "mecanismo": "composicao_definicional",
                               "fontes_ids": fontes})
        self.historico = self.historico[-20:]
        return ("composto:definicao", resposta)

    def ensinar(self, identificador, topico, perguntas, resposta, salvar=True):
        """Adiciona conhecimento explicitamente validado pelo desenvolvedor."""
        if topico not in TOPICOS:
            raise ValueError("Topico invalido")
        if not re.fullmatch(r"[a-z][a-z0-9_]{1,63}", identificador):
            raise ValueError("ID invalido")
        if any(e["id"] == identificador for e in self.base):
            raise ValueError("ID duplicado")
        if not isinstance(perguntas, list) or not perguntas or not all(isinstance(p, str) and p.strip() for p in perguntas):
            raise ValueError("Perguntas invalidas")
        if not isinstance(resposta, str) or not resposta.strip():
            raise ValueError("Resposta invalida")
        nova_base = self.base + [{"id": identificador, "topico": topico, "perguntas": perguntas, "resposta": resposta}]
        if salvar:
            temp = self.caminho_base.with_suffix(".tmp")
            editorial = [e for e in nova_base if e.get("origem_curriculo") != "mundo"]
            temp.write_text(json.dumps(editorial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temp.replace(self.caminho_base)
        self.base = nova_base
        self._indexar()
        from composicao_textual import CompositorTextual
        self.compositor = CompositorTextual(
            self.base, self.caminho_base.with_name("conhecimento_expandido.json"), self._alvo_definicao,
            self.curriculo_mundo)
        from interpretacao_pedidos import InterpretadorPedidos
        self.interpretador_pedidos = InterpretadorPedidos(self.raciocinio, self.consultas_relacionais)
        from linguagem_conversa import Conversacao
        self.conversacao = Conversacao()
        from planejamento_conversa import PlanejadorConversa
        self.planejador = PlanejadorConversa(self.compositor)
        self.contexto_textual = None
        self.ultimo_ato_social = None
        self.ultimo_turno = None
        self.rede = None
        self.esclarecimento = None
        self.contexto_consulta = None
        self.ultimos = []
        self.pos_ultimo = 0

    def _quadro_registro(self):
        quadro = self.compositor.ultimo_quadro
        if quadro is None:
            return None
        return {"intencao": quadro.intencao, "assunto": quadro.assunto, "outros": list(quadro.outros),
                "pistas": [p for _, p in quadro.pistas], "recusa": quadro.recusa}

    def _buscar_fatos(self, texto):
        """Busca factual, salvo relações com sujeito/objeto ("a Lua orbita o
        Sol"), que pertencem ao raciocinador e dependem da direção."""
        if self.raciocinio is not None:
            relacao = self.raciocinio.identificar_relacao(texto)
            if relacao is not None and relacao[2] != "tem_caracteristica":
                return None
        return self.compositor.buscar_fatos(texto)

    def _base_cobre(self, texto, n, assunto=None, tolerancia=None):
        """A base anterior tem resposta confiável sobre o mesmo assunto?

        Com um assunto identificado, a entrada precisa mencioná-lo; sem
        assunto, precisa conter todas as palavras de conteúdo da pergunta.
        """
        if len(self.indices_exatos.get(chave_pergunta(n), [])) == 1:
            return True
        rank = self._ranking(texto)
        if not rank or rank[0][0] < LIMIAR:
            return False
        if len(rank) > 1 and rank[0][0] - rank[1][0] < 0.06:
            return False
        entrada = self.base[rank[0][1]]
        evidencia = set(tokens(" ".join(entrada["perguntas"]) + " " + entrada["resposta"]))
        if tolerancia is not None:
            # Assunto obrigatório na entrada; tolera uma palavra acessória.
            # Radical do compositor: "fases" e "fase" coincidem.
            def raizes(t):
                return {self.compositor._raiz(w) for w in re.findall(r"[a-z0-9]+", normalizar(t))
                        if w not in STOP and len(w) > 1}
            evidencia = raizes(" ".join(entrada["perguntas"]) + " " + entrada["resposta"])
            # O assunto precisa ser o TEMA da entrada (suas perguntas), não uma
            # menção de passagem na resposta ("…a volta no Sol" em bissexto).
            # Para a resposta antiga vencer uma ficha que tem o fato
            # (tolerância 0), o nome completo do assunto precisa estar nas
            # perguntas dela; para evitar a recusa, basta um nome ("Lua").
            perguntas = normalizar(" ".join(entrada["perguntas"]))
            if assunto is None:
                tema_ok = True
            elif tolerancia == 0:
                tema_ok = raizes(self.compositor.itens[assunto]["nome"]) <= raizes(perguntas)
            else:
                tema_ok = self.compositor._menciona_conceito(assunto, perguntas)
            pergunta = raizes(texto)
            return bool(pergunta) and tema_ok and len(pergunta - evidencia) <= tolerancia
        exigidos = set(tokens(self.compositor.itens[assunto]["nome"] if assunto else texto))
        return bool(exigidos) and exigidos <= evidencia

    def _registrar(self, indice, pergunta):
        e = self.base[indice]
        self.esclarecimento = None
        self.ultimo_assunto = e["perguntas"][0]
        self.historico.append({"pergunta": pergunta, "id": e["id"]})
        self.historico = self.historico[-20:]
        self.contexto_geral = ("definicao"
                              if self._alvo_definicao(pergunta) is not None
                              else None)
        resposta = e["resposta"]
        exemplo = e.get("exemplo")
        if exemplo:
            resposta += ("\n\nExemplo:\n```" + exemplo["linguagem"] + "\n" +
                         exemplo["codigo"] + "\n```")
        return e["id"], resposta

    # --------------------------------------------- esclarecimento --------
    @staticmethod
    def _escolha_ordinal(n):
        escolha = re.fullmatch(
            r"(?:[ao] )?(?:(?:opcao|alternativa|resposta) )?"
            r"(\d+[ªº]?|primeir[ao]|segund[ao]|terceir[ao]|quart[ao])"
            r"(?: (?:opcao|alternativa|resposta))?", n)
        if not escolha:
            return None
        valor = escolha.group(1).rstrip("ªº")
        ordinais = {"primeira": 0, "primeiro": 0, "segunda": 1, "segundo": 1,
                    "terceira": 2, "terceiro": 2, "quarta": 3, "quarto": 3}
        if valor in ordinais:
            return ordinais[valor]
        # Números longos também são opções inválidas, sem converter inteiros enormes.
        return int(valor) - 1 if len(valor) <= 2 else -1

    def _texto_esclarecimento(self):
        indices = self.esclarecimento["indices"]
        perguntas = [self.base[i]["perguntas"][0] for i in indices]
        if len(perguntas) == 1:
            return (f'Não tenho certeza se entendi. Você quis perguntar algo como '
                    f'"{perguntas[0]}"? Responda sim, não ou faça outra pergunta.')
        opcoes = "\n".join(f"{i + 1}. {p}" for i, p in enumerate(perguntas))
        return ("Encontrei duas possibilidades próximas. Qual delas você quer?\n" +
                opcoes + "\nResponda com o número, o nome da opção ou 'nenhuma'.")

    def _pedir_esclarecimento(self, indices, pergunta):
        self.esclarecimento = {"indices": list(indices), "pergunta": pergunta}
        self.ultimo_assunto = None
        return "duvida", self._texto_esclarecimento()

    def _resolver_esclarecimento(self, n, original):
        """Resolve somente as opções oferecidas no turno pendente desta sessão."""
        posicao = self._escolha_ordinal(n)
        if self.esclarecimento is None:
            if posicao is not None:
                return "duvida", "Não há uma escolha pendente. Qual é a sua pergunta?"
            return None

        indices = self.esclarecimento["indices"]
        afirmacao = n in ("sim", "isso", "isso mesmo", "exatamente", "certo", "correto")
        if re.fullmatch(r"nao|nenhum[ao](?: del[ae]s| das (?:duas|opcoes)| dos dois)?|"
                        r"outra coisa|cancelar?|deixa pra la", n):
            self.esclarecimento = None
            self.ultimo_assunto = None
            self.ultimos = []
            return "duvida", "Certo. Diga com outras palavras o que você quer saber."

        if afirmacao and len(indices) == 1:
            posicao = 0
        if posicao is not None:
            if not 0 <= posicao < len(indices):
                return "duvida", "Essa opção não está na lista. " + self._texto_esclarecimento()
        elif afirmacao or n in ("mais", "continue", "continua"):
            return "duvida", "Preciso que você escolha uma opção. " + self._texto_esclarecimento()
        else:
            # Um nome curto pode escolher a opção. Perguntas novas e negações
            # passam pelo caminho normal, sem herdar uma intenção pendente.
            termos = set(self._tokens_consulta(n))
            nomes = [set(t for p in self.base[i]["perguntas"] for t in tokens(p))
                     for i in indices]
            candidatos = [k for k, nome in enumerate(nomes) if termos and termos <= nome]
            pergunta_nova = re.search(
                r"\b(por que|porque|como|quando|quanto\w*|onde|quem|qual|quais|"
                r"nao|nunca|jamais|sem)\b", n)
            if candidatos and not pergunta_nova:
                if len(candidatos) != 1:
                    return "duvida", self._texto_esclarecimento()
                posicao = candidatos[0]
            else:
                self.esclarecimento = None
                self.ultimo_assunto = None
                return None

        pergunta_contexto = self.esclarecimento["pergunta"]
        indice = indices[posicao]
        self.ultimos = [(1.0, indice)]
        self.pos_ultimo = 0
        resposta = self._registrar(indice, original)
        self.historico[-1]["pergunta_contexto"] = pergunta_contexto
        return resposta

    # ----------------------------------------------------- relógio -------
    def agora(self):
        return self._agora or datetime.datetime.now()

    @staticmethod
    def estacao_de(d):
        md = (d.month, d.day)
        if md >= (12, 21) or md < (3, 20):
            return "verão"
        if md < (6, 21):
            return "outono"
        if md < (9, 22):
            return "inverno"
        return "primavera"

    def _dinamico(self, n):
        """Perguntas que dependem do relógio do computador."""
        d = self.agora()
        # Só perguntas sobre o relógio local; datas históricas e outros
        # lugares precisam passar pela base, nunca receber a hora daqui.
        if re.fullmatch(r"(que horas( sao)?|horas sao|qual (e )?a hora( atual| certa)?|hora atual|hora certa|que hora e)( agora| aqui)?", n):
            return "dyn:hora", f"Agora são {d:%H:%M}."
        if re.fullmatch(r"(que dia (e )?hoje|data de hoje|qual (e )?a data( de hoje)?|hoje e que dia|dia da semana|que dia da semana e hoje)", n):
            return "dyn:data", (f"Hoje é {DIAS[d.weekday()]}, {d.day} de "
                                f"{MESES[d.month - 1]} de {d.year}.")
        if re.fullmatch(r"(em )?que mes( (e|estamos|a gente esta))?( agora| hoje)?", n):
            return "dyn:mes", f"Estamos em {MESES[d.month - 1]} de {d.year}."
        if re.fullmatch(r"(em )?que ano( (e|estamos|a gente esta))?( agora| hoje)?", n):
            return "dyn:ano", f"Estamos em {d.year}."
        if "estacao" in n and re.search(r"estamos|atual|agora|hoje|neste momento", n):
            est = self.estacao_de(d)
            art = "na" if est == "primavera" else "no"
            return "dyn:estacao", (f"Estamos {art} {est} (hemisfério sul). "
                                   "As datas de troca variam um dia conforme o ano.")
        return None

    # ------------------------------------------------- conversa fiada ----
    def _social(self, n):
        # Não inferir o horário LOCAL do usuário pelo relógio do servidor:
        # uma saudação explícita pode ser simplesmente correspondida.
        periodo = re.fullmatch(
            r"(bom dia|boa tarde|boa noite)(?:[, ]+crivo)?", n)
        if periodo:
            saud = periodo.group(1).capitalize()
            return "social:oi", f"{saud}! Sou o Crivo. Sobre o que quer conversar?"
        if re.fullmatch(
                r"(?:oi+|ola|e ai|eai|eae|opa|salve|hey|hello)"
                r"(?:[, ]+crivo)?", n):
            return "social:oi", ("Oi! Sou o Crivo. Como você está? Pode me contar como foi seu dia "
                                 "ou perguntar sobre astronomia, natureza, ciência ou programação.")
        if re.fullmatch(r"(?:obrigad[oa]|valeu|brigad[oa]|thanks)(?: crivo)?", n):
            return "social:obrigado", "Por nada! Se quiser saber mais alguma coisa, é só perguntar."
        if re.fullmatch(r"(?:(?:muito )?obrigad[oa]|valeu|brigad[oa]) (?:por|pela|pelo) "
                        r"(?:me )?(?:ouvir|escutar|conversar|a conversa|conversa|o papo|papo|tudo|a ajuda|ajuda|"
                        r"ajudar|forca|companhia)(?: crivo)?", n):
            return "social:obrigado", "Eu que agradeço pela conversa! Quando quiser, é só voltar."
        # Despedida é um ato de fala COMPLETO. "Você falou do Sol?"
        # contém o verbo "falou", mas não é uma despedida.
        if re.fullmatch(r"(?:tchau|ate logo|ate mais|falou|adeus)[!. ]*", n):
            return "social:tchau", "Até logo!"
        if re.fullmatch(r"(?:tudo bem|como vai|como voce esta|como vc esta)(?: com voce)?", n):
            return "social:tudobem", "Tudo bem por aqui! E com você? Sobre o que vamos conversar?"
        # Pedir que um programa solicite o nome de alguém NÃO é perguntar
        # pelo nome do próprio assistente. Intenção social deve ser a frase
        # inteira, não uma substring de outra tarefa.
        if re.fullmatch(r"(?:quem e voce|quem te criou|o que voce e|"
                        r"(?:(?:qual (?:e )?(?:o )?)|(?:me (?:diga|fale) (?:o )?))?seu nome)", n):
            return "social:quem", (f"Sou o Crivo, versão {VERSAO}: um assistente de conversa em português, "
                                   "ainda em fase de teste. Digite 'ajuda' para ver "
                                   "as capacidades e o conhecimento desta instalação.")
        if re.fullmatch(r"(exemplos?|me de exemplos|sugestoes?)", n.strip()):
            ex = []
            for t in TOPICOS:
                qs = [q for e in self.base if e["topico"] == t for q in e["perguntas"][:1]]
                if qs:
                    ex.append(random.choice(qs))
            return "social:exemplos", "Experimente perguntar, por exemplo:\n- " + "\n- ".join(ex)
        return None

    def _registrar_social(self, resultado, original):
        self.esclarecimento = None
        self.ultimo_assunto = None
        self.ultimos = []
        self.pos_ultimo = 0
        self.historico.append({"pergunta": original, "id": resultado[0],
                               "mecanismo": "conversa_assistente"})
        self.historico = self.historico[-20:]
        return resultado

    # ---------------------------------------------------- resposta -------
    def _executar_preparacao(self, preparacao, texto, registro_anterior):
        self.ultimo_ato_social = self.ultimo_turno = None
        self.contexto_textual = self.ultima_resposta_mostrada = None
        origem = ""
        if self.gerador_programacao is not None and re.search(
                r"\b(?:gere|crie|implemente|escreva|faca)\b", normalizar(texto)) and re.search(
                r"\b(?:javascript|typescript|js|ts)\b", normalizar(texto)):
            try:
                saida = self.gerador_programacao.gerar(texto)
                resposta = ("Geração experimental; código não verificado. " +
                            ("A geração terminou." if saida["completa"] else "A geração ficou incompleta.") +
                            "\n\n```\n" + saida["codigo"] + "\n```")
                ident = "programacao:experimental"
            except ValueError as exc:
                ident, resposta = "programacao:limite", "Pedido fora do contexto do modelo: " + str(exc)
            self.historico.append({"pergunta": texto, "id": ident, "mecanismo": "programacao_neural_experimental"})
            self.historico = self.historico[-20:]
            return (ident, resposta), ""
        if preparacao is not None and preparacao.resultado is not None:
            ident, resposta, self.contexto_textual, origem = preparacao.resultado
            resultado = ident, resposta
            self.contexto_frutas = self.contexto_consulta = self.contexto_geral = None
            self.esclarecimento = self.ultimo_assunto = None
            self.ultimos, self.pos_ultimo = [], 0
            self.historico.append({"pergunta": texto, "id": ident, "mecanismo": "linguagem_conversa",
                                   "ato": preparacao.ato._asdict()})
            self.historico = self.historico[-20:]
        else:
            consulta = preparacao.ato.consulta if preparacao is not None else texto
            resultado = self._responder_impl(consulta)
            if preparacao is not None:
                if self.historico and self.historico[-1] is not registro_anterior:
                    self.historico[-1]["pergunta"] = texto
                else:
                    self.historico.append({"pergunta": texto, "id": resultado[0]})
                    self.historico = self.historico[-20:]
                self.historico[-1]["ato"] = preparacao.ato._asdict()
                if preparacao.ato.formato:
                    if self.contexto_textual is None:
                        self.contexto_textual = self.compositor.contexto_editorial(*resultado)
                    if self.contexto_textual is not None:
                        from linguagem_conversa import Lembranca
                        snap = Lembranca(resultado[0], resultado[1], self.contexto_textual, self.conversacao.turno)
                        ident, resposta, self.contexto_textual, origem = self.conversacao.transformar(
                            preparacao.ato.formato, snap, self)
                        resultado = ident, resposta
                        self.historico[-1]["id"] = ident
        consulta_programacao = self.programacao.responder(texto) if self.programacao else None
        if consulta_programacao is not None and resultado[0] in ("fora", "duvida", "social:nao_entendido"):
            ident, resposta, unidade = consulta_programacao
            if self.historico and self.historico[-1].get("pergunta") == texto:
                self.historico.pop()
            self.contexto_frutas = self.contexto_consulta = self.contexto_geral = None
            self.esclarecimento = self.ultimo_assunto = None
            self.ultimos, self.pos_ultimo = [], 0
            self.historico.append({"pergunta": texto, "id": ident,
                                   "mecanismo": "conhecimento_programacao",
                                   "catalogo_sha256": unidade["catalogo_sha256"],
                                   "fontes": [f["url"] for f in unidade["referencias"]]})
            self.historico = self.historico[-20:]
            return (ident, resposta), ""

        return resultado, origem

    _PRONOMES = re.compile(r"(?<![\w])(?:(n|d)(ele|ela|eles|elas)|(ele|ela)|(lá))(?![\w])", re.IGNORECASE)

    def _resolver_pronome(self, texto):
        """Troca "ele/ela/lá/nele/dela…" pelo assunto da conversa.

        Só em perguntas, e só quando o turno anterior tratou de um conceito
        com ficha. "Ele" sem preposição não é trocado se a pergunta já cita
        outro conceito ("a Terra está nela?" troca só "nela").
        """
        if not self.assunto_conversa or self.assunto_conversa not in self.compositor.itens:
            return texto
        n = normalizar(texto)
        if not ("?" in texto or re.match(r"(?:e |o que|como|quant|qual|quais|por ?que|onde|quando|"
                                         r"tem |ha |existe|da pra|dá pra|e possivel)", n)):
            return texto
        nome = self.compositor.itens[self.assunto_conversa]["nome"]
        outro = self.compositor.assunto_mencionado(texto)

        # "lá e aqui" contrasta lugares; não retoma o assunto.
        contraste = bool(re.search(r"\b(?:aqui|ca)\b", n))

        def troca(m):
            prep, pron, sujeito, la = m.groups()
            if la:
                return m.group(0) if contraste else "em " + nome
            if prep:
                return ("em " if prep.lower() == "n" else "de ") + nome
            return m.group(0) if outro else nome
        novo = self._PRONOMES.sub(troca, texto)
        return novo

    _LINGUAGENS = (("python", re.compile(r"\bpython\b", re.I)),
                   ("javascript", re.compile(r"\b(?:javascript|js)\b", re.I)))
    _TERMO_PROGRAMACAO = re.compile(
        r"\b(?:loop|lacos?|la[cç]os?|repeti[cç][aã]o|if|else|condicional|fun[cç](?:[aã]o|[oõ]es)|"
        r"variave(?:l|is)|vari[aá]ve(?:l|is)|for|while|listas?|arrays?|dicion[aá]rios?|classes?|"
        r"objetos?|import|m[oó]dulos?|try|except|exce[cç](?:[aã]o|[oõ]es)|print|input)\b", re.I)

    def _completar_linguagem(self, texto):
        """“como faço um loop?” depois de falar de Python vira
        “como faço um loop em python?”. Só vale para termos de programação."""
        # Preservar termos técnicos do catálogo (event loop não é um laço).
        if self.programacao is not None and self.programacao.responder(texto) is not None:
            return texto
        if self.gerador_programacao is not None and re.search(r"\b(?:javascript|typescript|js|ts)\b", normalizar(texto)):
            return texto
        if any(p.search(texto) for _, p in self._LINGUAGENS):
            return re.sub(r"\bloops?\b", "laço de repetição", texto, flags=re.I)
        if self.linguagem_conversa and self._TERMO_PROGRAMACAO.search(texto):
            texto = re.sub(r"\bloops?\b", "laço de repetição", texto, flags=re.I)
            return texto.rstrip(" ?!.") + " em " + self.linguagem_conversa + ("?" if "?" in texto else "")
        return texto

    NAO_ENTENDI = "Hum, não entendi bem."

    # ----- memória entre conversas (guardada só no navegador, opcional) -----
    def carregar_memoria(self, memoria):
        dados = self.conversacao.dialogo.dados
        if memoria.get("nome"):
            dados["nome"] = memoria["nome"]
        self.perfil.nomes.update(memoria.get("nomes", {}))
        for tema, tom, agente in memoria.get("temas", []):
            self.perfil.temas.append((-10, tema, tom, "", agente))
        for relato in memoria.get("relatos", []):
            try:
                self._memoria().guardar(relato, antigo=True)
            except Exception:
                pass
        self.memoria_anterior = bool(memoria.get("nome") or memoria.get("temas") or memoria.get("nomes"))

    def exportar_memoria(self):
        dados = self.conversacao.dialogo.dados
        saida = {"nomes": dict(list(self.perfil.nomes.items())[-10:]), "relatos": [], "temas": []}
        if isinstance(dados.get("nome"), str) and 0 < len(dados["nome"]) <= 40:
            saida["nome"] = dados["nome"]
        vistos = []
        memoria = getattr(self, "memoria_relatos", None)
        for _, frase in (memoria.eventos if memoria is not None else []):
            if frase not in vistos and len(frase) <= 300:
                vistos.append(frase)
        saida["relatos"] = vistos[-8:]
        temas = {}
        for t in self.perfil.temas:  # o mais recente de cada assunto
            if t[1] and t[1] != "isso" and len(t[1]) <= 40:
                temas.pop(t[1], None)
                temas[t[1]] = [t[1], t[2], (t[4] or "")[:60]]
        saida["temas"] = list(temas.values())[-6:]
        return saida

    def _nao_entendi_com_presenca(self, texto, resposta):
        """Durante uma conversa, "não entendi" retoma o assunto em vez de
        oferecer um menu."""
        from conversa_cotidiana import _observacao, _presenca
        if "?" not in texto:
            anterior = (self.historico[-2] if len(self.historico) > 1 else {}).get("id", "")
            reacao = _observacao(texto, self, anterior, forcar=True)
            if reacao is not None:
                ident, texto_resp = reacao[0], reacao[1]
                if self.historico and self.historico[-1].get("pergunta") == texto:
                    self.historico[-1]["id"] = ident
                self.ultimo_turno = {"pergunta": texto, "id": ident}
                return ident, texto_resp
        perfil = getattr(self, "perfil", None)
        if perfil is None or not perfil.recente(3) or "?" in texto:
            return "fora", resposta
        tema = perfil.temas[-1][1]
        v = _presenca(self)
        texto_resp = v.escolher((
            "Não peguei bem essa. A gente ainda está falando de %s? Me conta de outro jeito." % tema,
            "Hum, essa eu não entendi. Pode explicar de outro jeito? Se quiser, continua me contando de %s." % tema,
            "Acho que me perdi nessa. Você pode dizer de outro jeito?"))
        if self.historico and self.historico[-1].get("pergunta") == texto:
            self.historico[-1]["id"] = "conversa:esclarecer"
        self.ultimo_turno = {"pergunta": texto, "id": "conversa:esclarecer"}
        return "conversa:esclarecer", texto_resp

    _PERGUNTA_MEMORIA = re.compile(r"\s*(?:e )?(?:por que|porque|pq|por qual motivo|quem|quando|onde|aonde|o que|que|qual)\b")

    def _memoria(self):
        if getattr(self, "memoria_relatos", None) is None:
            from sentido_frases import MemoriaRelatos
            self.memoria_relatos = MemoriaRelatos()
        return self.memoria_relatos

    def _memoria_guardar(self, texto):
        """Relatos ("meu cachorro latiu porque viu um gato") viram eventos
        na memória da conversa, com quem, o quê, por quê, quando e onde."""
        from nocoes import _NAO_AFIRMACAO
        n = normalizar(texto).strip()
        if (not isinstance(texto, str) or "?" in texto or len(n.split()) < 3 or len(texto) > 300
                or _NAO_AFIRMACAO.match(n)):
            return
        try:
            self._memoria().guardar(texto)
        except Exception:  # a memória nunca derruba a conversa
            pass

    def _memoria_responder(self, texto):
        memoria = getattr(self, "memoria_relatos", None)
        if memoria is None or not memoria.eventos or not isinstance(texto, str):
            return None
        if not self._PERGUNTA_MEMORIA.match(normalizar(texto)):
            return None
        # "O que eu faço?" depois de um relato pede ajuda para pensar, não
        # que o Crivo repita o que ouviu.
        if re.fullmatch(r"\s*(?:e )?(?:o )?que (?:eu )?(?:faco|devo fazer|eu faco|posso fazer|faco agora)\s*[?!.]*",
                        normalizar(texto)):
            perfil = getattr(self, "perfil", None)
            reflexao = perfil.temas[-1][3] if perfil is not None and perfil.temas else ""
            contexto = ("Pelo que você contou, %s. " % reflexao) if reflexao else ""
            return ("conversa:conselho",
                    "Não tenho uma resposta certa para isso, mas posso pensar junto com você. " + contexto +
                    "Qual seria um primeiro passo pequeno que você conseguiria dar?")
        try:
            achado = memoria.responder(texto)
        except Exception:
            return None
        if achado is None:
            return None
        self.esclarecimento = None
        self.contexto_textual = None
        self.ultimo_turno = {"pergunta": texto, "id": "memoria:relato"}
        self.historico.append({"pergunta": texto, "id": "memoria:relato", "mecanismo": "memoria_relatos"})
        self.historico = self.historico[-20:]
        return "memoria:relato", achado[0]

    def _registrar_nocao(self, texto, ident, resposta, nocao):
        self.nocao_conversa = nocao
        self.esclarecimento = None
        self.contexto_textual = None
        self.ultimo_turno = {"pergunta": texto, "id": ident}
        self.historico.append({"pergunta": texto, "id": ident, "mecanismo": "nocao"})
        self.historico = self.historico[-20:]
        return ident, resposta

    def _nocao_limite(self, texto, depois_de_fora=False):
        """“Como funciona a geladeira por dentro?”: sem ficha nem resposta
        cadastrada que cubra a pergunta, dizer o básico como noção e admitir
        que não sabe o resto, em vez de responder outra coisa."""
        from conversa_cotidiana import nocoes
        if "?" not in texto and not re.match(r"\s*(?:como|por que)\b", normalizar(texto)):
            return None
        achado = nocoes().nao_sei(texto, getattr(self, "nocao_conversa", None))
        if achado is None or self.compositor.assunto_mencionado(achado[2]) is not None:
            return None
        if not depois_de_fora and (self.compositor.assunto_mencionado(texto) is not None
                                   or self._base_cobre(texto, normalizar(texto))):
            return None
        if depois_de_fora and self.historico and self.historico[-1].get("pergunta") == texto:
            self.historico.pop()
        return self._registrar_nocao(texto, "nocao:nao_sei", achado[1], achado[0])

    def _nocao_definicao(self, texto):
        from conversa_cotidiana import nocoes
        achado = nocoes().definir(texto)
        # Conceito com ficha (o Sol, a Lua) nunca é respondido por noção.
        if achado is None or self.compositor.assunto_mencionado(texto) is not None:
            return None
        if self.historico and self.historico[-1].get("pergunta") == texto:
            self.historico.pop()
        return self._registrar_nocao(texto, "nocao:definicao", achado[1], achado[0])

    def _herdar_pergunta(self, texto):
        """“e em Marte?” logo após “quanto tempo dura um dia em Vênus?”
        (respondida por uma ficha) vira a mesma pergunta sobre Marte."""
        m = re.fullmatch(r"\s*e (?:(?:em|no|na|de|do|da|sobre|com|o|a|os|as) )?(.+?)\s*\??\s*", texto, re.I)
        anterior = self.historico[-1] if self.historico else {}
        quadro = anterior.get("quadro_factual") or {}
        if not m or anterior.get("mecanismo") != "busca_factual" or not quadro.get("assunto") \
                or quadro.get("intencao") == "propriedade" and not quadro.get("pistas"):
            return texto
        c = self.compositor
        novo = c.aliases_busca.get(re.sub(r"^(?:o|a|os|as) ", "", normalizar(m.group(1))))
        velho = quadro["assunto"]
        if novo is None or novo == velho or novo not in c.itens:
            return texto
        pergunta = normalizar(anterior.get("pergunta", ""))
        for alias, destino in sorted(c.aliases_busca.items(), key=lambda a: -len(a[0])):
            if destino == velho and re.search(c._padrao_alias(alias, velho), pergunta):
                return re.sub(c._padrao_alias(alias, velho), m.group(1).strip(), pergunta, count=1) + "?"
        return texto

    def responder(self, texto):
        """Protocolo de crise antes de tudo; depois, o turno comum."""
        import crise
        if isinstance(texto, str):
            urgente = crise.responder(texto, self)
            if urgente is not None:
                self.ultimo_turno = {"pergunta": texto, "id": urgente[0]}
                if getattr(self, "perfil", None) is not None:
                    self.perfil.turno += 1
                return urgente
        ident, resposta = self._responder_comum(texto)
        return crise.ajustar(ident, resposta, self)

    def _responder_comum(self, texto):
        """Contexto implícito de um turno e retomada explícita da conversa."""
        original_usuario = texto
        texto = self._completar_linguagem(self._resolver_pronome(self._herdar_pergunta(texto)))
        if getattr(self, "perfil", None) is not None:
            self.perfil.turno += 1
        try:
            lembrado = self._memoria_responder(original_usuario)
            if lembrado is not None:
                return lembrado
            limite = self._nocao_limite(texto)
            if limite is not None:
                return limite
            ident, resposta = self._responder_turno(texto)
            if ident in ("fora", "duvida", "social:nao_entendido"):
                nocao = self._nocao_definicao(texto) or self._nocao_limite(texto, depois_de_fora=True)
                if nocao is not None:
                    return nocao
            if ident == "social:oi" and getattr(self, "memoria_anterior", False) and self.perfil.turno <= 1:
                from presenca import de_volta
                from conversa_cotidiana import _presenca
                resposta = de_volta(self, _presenca(self)) or resposta
            if ident == "fora" and resposta.startswith(self.NAO_ENTENDI):
                return self._nao_entendi_com_presenca(texto, resposta)
            if ident == "conversa:planejamento" and getattr(self, "perfil", None) is not None and self.perfil.temas:
                from conversa_cotidiana import _CURTAS, _presenca
                if _CURTAS.fullmatch(normalizar(original_usuario).strip(" .!")):
                    from presenca import ACOLHER_CURTO, CONTINUAR
                    tom = self.perfil.temas[-1][2]
                    v = _presenca(self)
                    return "nocao:reacao", v.escolher(ACOLHER_CURTO[tom]) + " " + v.escolher(CONTINUAR[tom])
            if ident == "conversa:relato":
                try:
                    from conversa_cotidiana import relato_com_presenca
                    resposta = relato_com_presenca(original_usuario, self, resposta)
                except Exception:
                    pass
            return ident, resposta
        finally:
            self._memoria_guardar(original_usuario)
            for nome, padrao in self._LINGUAGENS:
                if padrao.search(texto):
                    self.linguagem_conversa = nome
            self._atualizar_assunto(texto)
            if texto != original_usuario and self.historico:
                self.historico[-1].setdefault("pronome_resolvido", texto)

    def _atualizar_assunto(self, texto):
        ident = self.ultimo_turno.get("id", "") if self.ultimo_turno else ""
        if ident.startswith(("social:", "conversa:", "duvida", "vazio", "mais:")):
            return
        ctx = self.contexto_textual
        if ctx is not None and len(ctx.temas) == 1 and ctx.temas[0] in self.compositor.itens:
            self.assunto_conversa = ctx.temas[0]
            return
        mencionado = self.compositor.assunto_mencionado(texto)
        if mencionado is not None:
            self.assunto_conversa = mencionado

    def _responder_turno(self, texto):
        preparacao = self.conversacao.preparar(texto, self)
        registro_anterior = self.historico[-1] if self.historico else None
        anterior = self.ultima_resposta_mostrada
        atributos_estado = ("contexto_textual", "ultima_resposta_mostrada", "ultimo_turno",
            "ultimo_ato_social", "ultimo_assunto", "contexto_frutas", "contexto_consulta",
            "contexto_geral", "esclarecimento", "ultimos", "pos_ultimo", "historico")
        estado = {a: getattr(self, a) for a in atributos_estado}
        estado["historico"] = list(self.historico)
        estado["ultimos"] = list(self.ultimos)
        self._contexto_textual_anterior = self.contexto_textual
        self._ato_social_anterior = self.ultimo_ato_social
        self._turno_anterior = self.ultimo_turno
        self.ultimo_ato_social = None
        self.ultimo_turno = None
        self.contexto_textual = None
        self.ultima_resposta_mostrada = None
        self._referencia_turno_anterior = anterior
        self._pedido_turno = None
        try:
            # A preparação neural/social pode classificar uma citação como
            # relato antes que o motor comum veja o verbo "interprete".
            # Leitura textual explícita tem precedência, mas ainda passa por
            # todo o registro de turno abaixo.
            from compreensao_textual import responder as compreender_texto
            resultado = compreender_texto(texto, self._contexto_textual_anterior)
            if resultado is not None:
                origem = None
                preparacao = None
                self.historico.append({"pergunta": texto, "id": resultado[0],
                                       "mecanismo": "compreensao_textual"})
                self.historico = self.historico[-20:]
            else:
                resultado, origem = self._executar_preparacao(preparacao, texto, registro_anterior)
            if (preparacao is None and resultado[0] in ("fora", "duvida", "social:nao_entendido")
                    and self._pedido_turno is None):
                ato_neural = self.conversacao._analisar_neural(texto)
                novo_registro = self.historico[-1] if self.historico else None
                especializado = (novo_registro is not None and novo_registro is not registro_anterior
                    and novo_registro.get("mecanismo") not in (None, "conversa_assistente", "recuperador"))
                # Recusas de motores factuais/relacionais são preservadas.
                # Uma definição com alvo completo já cadastrado pode corrigir
                # a forma do pedido; uma negação jamais produz conteúdo factual.
                permitido = (ato_neural is not None and (not especializado or
                    ato_neural.nome == "negado_neural" or ato_neural.nome == "definir"
                    and self.compositor.resolver(ato_neural.alvo) is not None))
                if resultado[0] == "social:nao_entendido" and not re.search(
                        r"\b(explic\w*|defin\w*|signific\w*|entend\w*|compreend\w*|funciona|serve|"
                        r"compar\w*|diferenc\w*|retom\w*|resum\w*|reform\w*)\b", normalizar(texto)):
                    permitido = False
                if permitido:
                    for a,v in estado.items():
                        setattr(self, a, v)
                    preparacao = self.conversacao.preparar_ato(ato_neural, self)
                    resultado, origem = self._executar_preparacao(preparacao, texto, registro_anterior)
                else:
                    self.conversacao.ultimo_quadro_neural = None
            identificador = resultado[0]
            self.ultimo_turno = {"pergunta": texto, "id": identificador}
            if origem:
                self.ultimo_turno["prova_origem"] = origem
                self.historico[-1]["prova_origem"] = origem
            if self._pedido_turno is not None:
                if not self.historico or self.historico[-1].get("pergunta") != texto:
                    self.historico.append({"pergunta": texto, "id": identificador,
                                           "mecanismo": "interpretacao_pedido"})
                    self.historico = self.historico[-20:]
                self.historico[-1]["pedido"] = self._pedido_turno._asdict()
            if self.conversacao.ultimo_quadro_neural is not None and self.historico:
                self.historico[-1]["quadro_neural"] = self.conversacao.ultimo_quadro_neural
            if identificador in ("social:assuntos", "social:pensamento"):
                self.ultimo_ato_social = identificador
            if self.contexto_textual is None:
                self.contexto_textual = self.compositor.contexto_editorial(identificador, resultado[1])
            self.conversacao.registrar(identificador, resultado[1], self.contexto_textual)
            self.conversacao.dialogo.registrar(identificador, resultado[1], self.conversacao)
            if self.conversacao.dialogo.ultimo_quadro is not None and self.historico:
                self.historico[-1]["quadro_dialogo"] = self.conversacao.dialogo.ultimo_quadro
            if self.conversacao.geracao.ultimo_quadro is not None and self.historico:
                self.historico[-1]["quadro_geracao"] = self.conversacao.geracao.ultimo_quadro
                self.historico[-1]["mecanismo"] = "geracao_neural"
            self.conversacao.geracao.registrar(identificador, resultado[1], self.conversacao, texto)
            self.conversacao.contextual.registrar(texto, resultado[1], identificador)
            if identificador.startswith("conversa:neural_") and self.historico:
                self.historico[-1]["quadro_contextual"] = self.conversacao.contextual.painel()
                self.historico[-1]["mecanismo"] = "dialogo_contextual_neural"
            self.planejador.registrar(identificador, self.contexto_textual)
            if self.planejador.ultimo is not None and self.historico:
                self.historico[-1]["plano"] = self.planejador.ultimo
            if (preparacao is None and self.contexto_textual is not None or
                    identificador.startswith("social:")):
                self.conversacao.assunto = self.conversacao.objetivo = None
            # Nenhuma pergunta seguinte herda saudações, recusas,
            # dúvidas ou solicitações de esclarecimento.
            if (identificador in {e["id"] for e in self.base} or
                    identificador.startswith(("logica:", "frutas:")) and
                    identificador not in ("logica:sem_ligacao",
                                         "logica:desconhecido",
                                         "frutas:desconhecido") or
                    identificador == "composto:definicao" or
                    identificador.startswith("conhecimento:") or
                    identificador.startswith("escrita:") and identificador != "escrita:fim"):
                self.ultima_resposta_mostrada = resultado[1]
            if identificador != "conversa:repeticao":
                self.conversacao.ultima_resposta_texto = resultado[1]
            return resultado
        finally:
            self._referencia_turno_anterior = None
            self._contexto_textual_anterior = None
            self._ato_social_anterior = None
            self._turno_anterior = None
            self._pedido_turno = None

    def _responder_impl(self, texto):
        """Motor de diálogo; o wrapper expira o contexto com segurança."""
        original = texto
        # Um fragmento como "E a banana?" utiliza somente o assunto do
        # turno IMEDIATAMENTE anterior, não um fruto citado muito antes.
        contexto_frutas_anterior = self.contexto_frutas
        self.contexto_frutas = None
        contexto_geral_anterior = self.contexto_geral
        self.contexto_geral = None
        n = normalizar(texto).strip().strip("?.,; ").rstrip("!")
        contexto_consulta_anterior = self.contexto_consulta
        self.contexto_consulta = None
        # Antes de retirar saudações ou interpretar negações factuais,
        # reconhecer o ato social COMPLETO ('eae beleza', críticas, etc.).
        contato = conversa_assistente.responder_contato(original, self._turno_anterior)
        if contato is not None:
            return self._registrar_social(contato, original)
        # Identificar atos de fala INTRODUTÓRIOS e retirar apenas eles.
        # Preservar o resto da consulta com acentos/maiúsculas, necessário
        # para os definidores compostos ("HTML e CSS") e para auditoria.
        prefixo = (
            r"^\s*(?:(?:oi+|ol[aá]|e\s+a[ií]|eai|eae|opa|salve|"
            r"bom dia|boa tarde|boa noite|obrigad[oa])\b[!,. :;\-]*"
            r"(?:crivo\b[!,. :;\-]*)?|por (?:favor|gentileza)[,: ]*)"
        )
        introducao = re.match(prefixo, texto, flags=re.IGNORECASE)
        if introducao is not None:
            resto = texto[introducao.end():].strip(" \t\r\n,;:.!?-")
            if resto:
                texto = resto
                n = normalizar(texto).strip().strip("?.,; ").rstrip("!")
        resto = re.sub(r"[,; ]+(?:por favor|obrigad[oa])[!. ]*$", "",
                       texto, flags=re.IGNORECASE).strip()
        if resto:
            texto = resto
            n = normalizar(texto).strip().strip("?.,; ").rstrip("!")
        texto = conversa_assistente.preparar_conversa(texto)
        texto = conversa_assistente.preparar_pedido(texto)
        # "Não é mais X" relata mudança de estado, não nega uma propriedade:
        # equivale a "deixou de ser X" e não deve cair no filtro de negações.
        texto = re.sub(r"\bn[aã]o (?:é|e|eh) mais\b", "deixou de ser", texto, flags=re.IGNORECASE)
        texto = re.sub(r"\bn[aã]o s[aã]o mais\b", "deixaram de ser", texto, flags=re.IGNORECASE)
        n = normalizar(texto).strip().strip("?.,;! ")
        if not n:
            return "vazio", "Pode falar, estou ouvindo."

        esclarecida = self._resolver_esclarecimento(n, original)
        if esclarecida:
            return esclarecida

        # Pedidos sobre o sentido da própria mensagem precisam ser lidos
        # como um todo antes dos recuperadores por assunto. Isso evita que
        # "interprete este poema" vire relato pessoal e que uma descrição
        # do Crivo seja ecoada como se falasse sobre o usuário.
        from compreensao_textual import responder as compreender_texto
        compreensao = compreender_texto(texto, self._contexto_textual_anterior)
        if compreensao is not None:
            self.esclarecimento = None
            self.ultimo_assunto = None
            self.historico.append({"pergunta": original, "id": compreensao[0],
                                   "mecanismo": "compreensao_textual"})
            self.historico = self.historico[-20:]
            return compreensao

        # Uma interpretação comum vem ANTES dos motores de assunto.
        # 'Você conhece' é um operador do pedido, não uma propriedade
        # que o motor de relações deve tentar atribuir às galáxias/aves/etc.
        pedido = self.interpretador_pedidos.analisar(texto)
        if pedido is not None:
            self._pedido_turno = pedido
            self.esclarecimento = None
            self.ultimo_assunto = None
            self.ultimos = []
            self.pos_ultimo = 0
            consulta_pedido = self.interpretador_pedidos.responder(pedido)
            if consulta_pedido is not None:
                ident, resposta, self.contexto_consulta = consulta_pedido
                self.esclarecimento = None
                self.ultimo_assunto = None
                self.ultimos = []
                self.pos_ultimo = 0
                self.historico.append({"pergunta": original, "id": ident,
                                       "mecanismo": "consulta_relacional" if ident.startswith("logica:")
                                       else "interpretacao_pedido"})
                self.historico = self.historico[-20:]
                return ident, resposta
            if pedido.intencao == "listar":
                # Não confundir ausência de uma classe no grafo com
                # ausência em outro catálogo ativo. O provedor curado
                # interpreta o pedido original usando seu próprio esquema.
                outro_catalogo = (self.frutas.responder(original, contexto_frutas_anterior)
                                  if self.frutas is not None else None)
                if outro_catalogo is not None:
                    ident, resposta, intencao, entidade = outro_catalogo
                    self.contexto_frutas = (intencao, entidade) if entidade is not None else None
                    self.esclarecimento = None
                    self.ultimo_assunto = None
                    self.historico.append({"pergunta": original, "id": ident,
                                           "mecanismo": "conhecimento_frutas"})
                    self.historico = self.historico[-20:]
                    return ident, resposta
                if pedido.explicito:
                    return "fora", "Não reconheci a categoria completa “" + pedido.alvo + "” nos catálogos desta instalação."
                # Lista editorial sem classe/critério no esquema do grafo:
                # mantém o pedido INTEIRO no motor existente, inclusive a
                # ordenação ou o qualificador. Não fabrica uma definição.
            else:
                if pedido.intencao == "retomar_item":
                    alvo = self.interpretador_pedidos.retomar(pedido, contexto_consulta_anterior)
                    if alvo is None:
                        return "duvida", "Preciso de uma lista no turno anterior com esse item. Qual assunto você quer?"
                else:
                    alvo = pedido.alvo
                if self.compositor.resolver(alvo) is None:
                    fatos = self.interpretador_pedidos.informacoes(alvo)
                    if fatos is not None:
                        self.esclarecimento = None
                        self.ultimo_assunto = None
                        self.historico.append({"pergunta": original, "id": fatos[0],
                                               "mecanismo": "consulta_relacional"})
                        self.historico = self.historico[-20:]
                        return fatos[:2]
                texto = "o que é " + alvo
                n = normalizar(texto).strip().strip("?.,;! ")

        auto = conversa_assistente.responder(
            n, self, TOPICOS, self._ato_social_anterior)
        if auto is not None:
            return self._registrar_social(auto, original)

        # Instruções de edição/contexto vêm antes dos atos sociais e do
        # antigo comando de ranking 'mais'. 'Em tópicos' é uma mudança
        # de formato, e continuar um texto não consulta outro assunto.
        composicao = self.compositor.responder(texto, self._contexto_textual_anterior)
        # "Fale sobre X" já é um comando editorial direto em parte da
        # base histórica. Conservar a resposta exata antiga e evitar que
        # novas fichas com o mesmo nome quebrem contratos existentes.
        if (composicao is not None and re.fullmatch(r"fale sobre .+", n)
                and len(self.indices_exatos.get(chave_pergunta(n), [])) == 1):
            indice_antigo = self.indices_exatos[chave_pergunta(n)][0]
            if self.base[indice_antigo].get("origem_curriculo") != "mundo":
                composicao = None
        # Novas palavras como "planeta" nao podem ocultar respostas ja
        # cadastradas para a pergunta completa na base anterior.
        if (composicao is not None and composicao[0] == "fora" and
                len(self.indices_exatos.get(chave_pergunta(n), [])) == 1):
            composicao = None
        # Um conceito novo pode compartilhar seu nome com uma pergunta
        # causal anterior. Só ceder à fonte legada quando o sujeito da
        # pergunta e TODOS os termos consultados constarem na evidência
        # editorial preexistente, sem aceitar qualificadores desconhecidos.
        if (composicao is not None and composicao[0] == "fora" and
                n.startswith("por que ")):
            sujeito = re.match(r"^por que (?:o |a |um |uma )?([a-z0-9_-]+)\b", n)
            if sujeito and self.compositor.resolver(sujeito.group(1)) in self.compositor.mundo_ids:
                assunto = sujeito.group(1)
                termos_pedido = set(tokens(texto))
                legadas = []
                for entrada in self.base:
                    if entrada.get("origem_curriculo") == "mundo":
                        continue
                    perguntas = entrada["perguntas"]
                    causal = any(normalizar(p).startswith("por que " + assunto + " ")
                                 for p in perguntas)
                    evidencia = set(tokens(" ".join(perguntas) + " " + entrada["resposta"]))
                    if causal and termos_pedido <= evidencia:
                        legadas.append(entrada["id"])
                if len(legadas) == 1:
                    composicao = None
        if (composicao is not None and composicao[0] == "fora" and
                self.compositor._menciona_mundo(n)):
            # O currículo novo não invalida uma prova já cadastrada em
            # outro provedor. Só ceder quando o pedido INTEIRO tem prova,
            # nunca por ranking, palavra comum ou diagnóstico presumido.
            alternativas = [self.interpretador_geral.interpretar(texto)]
            if self.raciocinio is not None:
                alternativas.append(self.raciocinio.interpretar(texto))
            quadro_mundo = self.analisador_portugues.analisar(texto)
            if quadro_mundo is not None:
                if quadro_mundo.intencao == "definir":
                    alvo = self.compositor.resolver(quadro_mundo.sujeito)
                    if alvo in self.compositor.mundo_ids:
                        composicao = self.compositor._conceito(alvo)
                else:
                    alternativas.append(self.analisador_portugues.responder(quadro_mundo))
            if (any(r is not None and r[0].startswith("logica:") and r[0] not in
                   ("logica:desconhecido", "logica:sem_ligacao") for r in alternativas)
                    or (self.raciocinio is not None and len(alternativas) > 1
                        and alternativas[1] is not None
                        and alternativas[1][0] in ("logica:desconhecido", "logica:sem_ligacao"))):
                # Uma relacao analisada por inteiro pode retornar abstenção;
                # o nome "orbita" nao deve mascarar o verbo "orbita".
                composicao = None
        if composicao is not None and composicao[0] == "fora":
            # A recusa do compositor não oculta uma resposta cadastrada que
            # cobre TODAS as palavras da pergunta ("Por que Plutão não é
            # mais planeta?"). Sem essa cobertura, procurar o fato completo.
            assunto_ficha = self.compositor.assunto_mencionado(texto)
            busca = self._buscar_fatos(texto) if assunto_ficha else None
            # Ficha com o fato pedido vence a resposta antiga aproximada.
            if busca is not None and not self._base_cobre(texto, n, assunto_ficha, tolerancia=0):
                composicao = busca
            elif (self._base_cobre(texto, n, assunto_ficha, tolerancia=1) if assunto_ficha
                    else self._base_cobre(texto, n)):
                composicao = None
            else:
                composicao = busca or self._buscar_fatos(texto) or composicao
        if composicao is not None:
            ident, resposta, self.contexto_textual = composicao
            self.esclarecimento = None
            self.ultimo_assunto = None
            if (self.contexto_textual is not None and
                    self.contexto_textual.origem == "base"):
                self.contexto_geral = "definicao"
            self.historico.append({"pergunta": original, "id": ident,
                                   "mecanismo": "composicao_factual"})
            self.historico = self.historico[-20:]
            return ident, resposta

        pronome = re.fullmatch(r"(?:ele|ela|isso) (.+)", n)
        if pronome:
            contexto = self._contexto_textual_anterior
            if contexto is None or len(contexto.temas) != 1:
                return "duvida", "De qual assunto você está falando? Preciso de uma referência única na resposta anterior."
            nome = self.compositor.itens[contexto.temas[0]]["nome"]
            proposta = nome + " " + pronome.group(1)
            if (self.raciocinio is not None and
                    (self.raciocinio.identificar_relacao(proposta) is not None or
                     self.analisador_portugues.analisar(proposta) is not None)):
                texto = proposta
                n = normalizar(proposta).strip().strip("?.,;! ")
            else:
                return "fora", "Reconheci a referência a " + nome + ", mas não tenho uma relação interpretável para essa pergunta."

        if re.fullmatch(r"(mais|outra|outra resposta|e mais|continue|continua)", n):
            if self.ultimos and self.pos_ultimo + 1 < len(self.ultimos):
                self.pos_ultimo += 1
                s, i = self.ultimos[self.pos_ultimo]
                return self._registrar(i, original)
            return "mais:fim", "Não tenho mais nada sobre esse assunto. Quer perguntar outra coisa?"

        self.ultimos = []
        self.pos_ultimo = 0
        d = self._dinamico(n)
        if d:
            return d
        s = self._social(n)
        if s:
            return self._registrar_social(s, original)

        # A pergunta 'você falou de X?' pergunta sobre a CONVERSA,
        # não pela definição de X. Verificar apenas o último turno.
        from referencias_dialogo import conferir_mencao_anterior
        mencao = conferir_mencao_anterior(
            texto, self._referencia_turno_anterior)
        if mencao is not None:
            self.esclarecimento = None
            self.ultimo_assunto = None
            return mencao

        prevencao = re.sub(r"^(?:o que fazer (?:pra|para)|como fazer para|como) nao (?:ter|pegar)\b", "como evitar", n)
        if prevencao != n:
            texto = n = prevencao
        exatas = self.indices_exatos.get(chave_pergunta(n), [])
        if len(exatas) == 1:
            i = exatas[0]
            self.ultimos = [(1.0, i)]
            return self._registrar(i, original)
        if len(exatas) > 1:
            return "duvida", "Há mais de uma resposta cadastrada para essa pergunta. Pode detalhar?"
        # Consultas com variável, múltiplas condições e refinamento da
        # lista anterior. A negação só é aceita com prova de disjunção.
        consulta = self.consultas_relacionais.responder(texto, contexto_consulta_anterior)
        if consulta is not None:
            ident, resposta, self.contexto_consulta = consulta
            # Uma lista editorial pode cobrir EXATAMENTE um conjunto de
            # classes e ser mais completa que o grafo parcial. A cobertura
            # é declarada nos dados; não se decide por similaridade lexical.
            if ident == "logica:consulta":
                plano = self.consultas_relacionais.analisar(texto, contexto_consulta_anterior)
                if (plano.sujeito is None and plano.candidatos is None and
                        all(c.relacao == "tipo_de" and not c.inversa and
                            not c.negativa for c in plano.condicoes)):
                    classes = {c.alvo for c in plano.condicoes}
                    fontes = [i for i, e in enumerate(self.base)
                              if any(set(cobertura) == classes for cobertura
                                     in e.get("listas_relacionais", []))]
                    if len(fontes) == 1:
                        self.contexto_consulta = None
                        self.ultimos = [(1.0, fontes[0])]
                        resultado = self._registrar(fontes[0], original)
                        self.historico[-1]["mecanismo"] = "lista_editorial"
                        return resultado
                    if len(fontes) > 1:
                        self.contexto_consulta = None
                        return "duvida", "Há listas editoriais conflitantes para essa consulta. Pode especificar?"
            self.esclarecimento = None
            self.ultimo_assunto = None
            self.historico.append({"pergunta": original, "id": ident,
                                   "mecanismo": "consulta_relacional"})
            self.historico = self.historico[-20:]
            return ident, resposta
        # "não muda" descreve imutabilidade em JS, não uma proibição.
        # Não libera outras negações, sobretudo consultas de segurança.
        negacao_const = (bool(re.search(r"\b(javascript|js)\b", n)) and
                         bool(re.search(r"\b(variavel|const)\b", n)) and
                         bool(re.search(r"\bnao (?:muda|mudar|altera|alterar)\b", n)))
        if (not negacao_const and re.search(r"\b(nao|nunca|jamais)\b", n)) or (
                re.search(r"\bsem\b", n) and
                re.search(r"\b(pode|posso|devo|precisa|seguro|misturar|comer)\b", n)):
            return "duvida", "Ainda não interpreto essa negação com segurança. Reformule a pergunta diretamente."
        # O módulo curado responde por propriedades e categorias; não
        # tenta completar perguntas fora de suas relações cadastradas.
        if self.frutas is not None:
            resultado_fruta = self.frutas.responder(original, contexto_frutas_anterior)
            if resultado_fruta is not None:
                identificador, resposta, intencao, entidade = resultado_fruta
                self.esclarecimento = None
                self.ultimo_assunto = None
                self.contexto_frutas = ((intencao, entidade)
                                       if entidade is not None else None)
                self.historico.append({"pergunta": original, "id": identificador,
                                       "mecanismo": "conhecimento_frutas"})
                self.historico = self.historico[-20:]
                return identificador, resposta
        # Recupera a intenção do turno anterior sem carregar uma resposta
        # antiga como se fosse conhecimento do novo conceito. O novo alvo
        # precisa ser encontrado explicitamente na mesma base ativa.
        from interpretacao_geral import (
            preparar_elipse_definicional, esclarecer_coordenacao_ou_classificacao)
        # Perguntas com "X e um(a) Y" podem ser duas definições
        # ou uma classificação: não presumir semântica da conjunção.
        esclarecimento_forma = esclarecer_coordenacao_ou_classificacao(texto)
        if esclarecimento_forma is not None:
            self.esclarecimento = None
            self.ultimo_assunto = None
            return ("duvida", esclarecimento_forma)
        definicoes_compostas = self._responder_definicoes_coordenadas(texto)
        if definicoes_compostas is not None:
            if self.historico and self.historico[-1]["pergunta"] == texto:
                self.historico[-1]["pergunta"] = original
            return definicoes_compostas
        reescrita = preparar_elipse_definicional(texto, contexto_geral_anterior)
        if reescrita is not None:
            definicao_eliptica = self._responder_definicao(reescrita, original)
            ids_validos = {e["id"] for e in self.base}
            if (definicao_eliptica is not None and
                    definicao_eliptica[0] in ids_validos):
                self.contexto_geral = "definicao"
                return definicao_eliptica
            self.esclarecimento = None
            self.ultimo_assunto = None
            return ("fora",
                    "Entendi que você continua pedindo uma definição, "
                    "mas não tenho uma definição cadastrada desse conceito. "
                    "Não vou substituir por um assunto semelhante.")

        geral = self.interpretador_geral.interpretar(texto)
        if geral is not None:
            self.esclarecimento = None
            self.ultimo_assunto = None
            self.historico.append({"pergunta": original, "id": geral[0],
                                   "mecanismo": "interpretacao_geral"})
            self.historico = self.historico[-20:]
            return geral

        definicao = self._responder_definicao(n, original)
        if definicao is not None:
            return definicao
        # Inferência estruturada somente para relações comprováveis.
        # Os casos não reconhecidos continuam no recuperador habitual.
        if self.raciocinio is not None:
            inferencia = self.raciocinio.interpretar(texto)
            if inferencia is not None:
                # Fonte editorial explícita e existente pode explicar uma
                # prova comprovada, sem converter um ranking aproximado em
                # negação ou atribuir certeza a uma base desconhecida.
                fonte_id = self.raciocinio.fonte_para(texto, inferencia[0])
                if fonte_id is not None:
                    indice_fonte = next((i for i, item in enumerate(self.base)
                                         if item["id"] == fonte_id), None)
                    if indice_fonte is not None:
                        self.ultimos = [(1.0, indice_fonte)]
                        identificador, explicacao = self._registrar(
                            indice_fonte, original)
                        self.historico[-1]["mecanismo"] = "raciocinio_e_base"
                        return (identificador, explicacao +
                                "\n\nRelações verificadas:\n" + inferencia[1])
                self.esclarecimento = None
                self.ultimo_assunto = None
                # Sem relação no grafo, um fato documentado pode tratar
                # exatamente da pergunta ("Mercúrio e Vênus não têm...").
                if inferencia[0] in ("logica:desconhecido", "logica:sem_ligacao"):
                    busca = self._buscar_fatos(texto)
                    if busca is not None:
                        ident, resposta, self.contexto_textual = busca
                        self.historico.append({"pergunta": original, "id": ident,
                                               "mecanismo": "busca_factual",
                                   "quadro_factual": self._quadro_registro()})
                        self.historico = self.historico[-20:]
                        return ident, resposta
                self.historico.append({"pergunta": original, "id": inferencia[0],
                                       "mecanismo": "raciocinio_relacional"})
                self.historico = self.historico[-20:]
                return inferencia
        # Camada NOVA de interpretação superficial do português: somente
        # após perguntas exatas, definições, raciocinador e conhecimento
        # curado. Desse modo, ampliação da gramática não desestabiliza as
        # intenções existentes nem altera respostas do currículo original.
        quadro = self.analisador_portugues.analisar(texto)
        if quadro is not None:
            if quadro.intencao == "definir":
                definicao_nova = self._responder_definicao(
                    "o que e " + quadro.sujeito, original)
                if definicao_nova is not None:
                    if definicao_nova[0] in {e["id"] for e in self.base}:
                        self.contexto_geral = "definicao"
                        if self.historico and self.historico[-1]["pergunta"] == original:
                            self.historico[-1]["mecanismo"] = "analise_portugues"
                    return definicao_nova
            else:
                resultado_estruturado = self.analisador_portugues.responder(quadro)
                if resultado_estruturado is not None:
                    self.esclarecimento = None
                    self.ultimo_assunto = None
                    self.historico.append({
                        "pergunta": original,
                        "id": resultado_estruturado[0],
                        "mecanismo": "analise_portugues",
                        "quadro": {
                            "intencao": quadro.intencao,
                            "sujeito": quadro.sujeito,
                            "predicado": quadro.predicado,
                            "objeto": quadro.objeto,
                        },
                    })
                    self.historico = self.historico[-20:]
                    return resultado_estruturado
        # Antes do ranking lexical, detectar uma pergunta que aponta para
        # um detalhe da RESPOSTA imediatamente anterior. Sem evidência
        # para o detalhe, admitir limite em vez de retornar outro tema.
        from referencias_dialogo import interpretar_referencia
        referencia = interpretar_referencia(
            texto, self._referencia_turno_anterior)
        if referencia is not None:
            self.esclarecimento = None
            self.ultimo_assunto = None
            return referencia

        # "Como você acha que ele tá?": a pergunta é sobre alguém que a pessoa
        # contou (o cachorro doente), não sobre o Crivo.
        terceiro = re.search(r"\b(?:voce|vc) acha que (ele|ela)\b.*\b(?:esta|ta|vai|fica|melhora)\b", n)
        if terceiro and getattr(self, "perfil", None) is not None and self.perfil.temas:
            pron = terceiro.group(1)
            return self._registrar_social((
                "conversa:opiniao_terceiro",
                "Daqui eu não consigo saber como %s está, mas torço para que %s fique bem. "
                "E você, como está com isso?" % (pron, pron),
            ), original)
        if conversa_assistente.pergunta_pessoal(texto):
            return self._registrar_social((
                "social:nao_entendido",
                "Essa sobre mim eu não sei responder bem. Sou um programa: não tenho gostos nem "
                "uma vida fora da conversa. Mas adoro quando você me conta das suas coisas, "
                "e posso explicar como eu funciono, se quiser.",
            ), original)

        if self.ultimo_assunto and re.search(r"\b(isso|disso|dele|dela)\b", n) and len(tokens(texto)) <= 3:
            texto = texto + " " + self.ultimo_assunto
        if "estacoes" in n and re.search(r"\b(o que faz existirem|o que causa|por que)\b", n):
            indice = next((i for i, e in enumerate(self.base) if e["id"] == "causa_estacoes"), None)
            if indice is not None:
                self.ultimos = [(1.0, indice)]
                return self._registrar(indice, original)
        # Fatos documentados do assunto citado vêm antes de uma resposta
        # aproximada que nem menciona esse assunto ("Quantas luas tem
        # Júpiter?" não é uma pergunta sobre a Lua da Terra).
        busca = self._buscar_fatos(texto)
        # "Por que/de que maneira": a resposta antiga precisa cobrir a
        # pergunta inteira, não só citar o assunto.
        # A ficha tem prioridade: a resposta antiga só vence se cobrir TODAS as
        # palavras da pergunta e mencionar o assunto.
        if busca is not None and not self._base_cobre(
                texto, n, self.compositor.assunto_busca, tolerancia=0):
            ident, resposta, self.contexto_textual = busca
            self.esclarecimento = None
            self.ultimo_assunto = None
            self.historico.append({"pergunta": original, "id": ident,
                                   "mecanismo": "busca_factual",
                                   "quadro_factual": self._quadro_registro()})
            self.historico = self.historico[-20:]
            return ident, resposta
        # Assunto com ficha e sem o fato pedido: uma resposta antiga por
        # semelhança só vale se cobrir a pergunta inteira; senão, admitir.
        if busca is None:
            assunto = self.compositor.assunto_mencionado(texto)
            if assunto is not None and not self._base_cobre(texto, n, assunto, tolerancia=1):
                self.esclarecimento = None
                self.ultimo_assunto = None
                return ("fora", "Reconheci o assunto " + self.compositor.itens[assunto]["nome"] +
                        ", mas não tenho evidência cadastrada para essa pergunta completa.")
        rank = self._ranking(texto)
        # Hipótese e conta não são fatos cadastrados; código só casa com
        # programação; e a entrada precisa tratar do assunto perguntado.
        nq = normalizar(original)
        if self._HIPOTESE.match(nq) or self._CONTA.search(nq):
            rank = []
        elif rank:
            codigo = bool(self._CODIGO.search(original))
            rank = [(s, i) for s, i in rank
                    if not (codigo and self.base[i]["topico"] != "programacao")
                    and not self._fora_do_assunto(texto, i)]
        _, vocabulario = self._contexto_consulta(texto)
        toks = self._tokens_consulta(texto, vocabulario)
        desconhecidas = [t for t in toks if t not in vocabulario]
        # O classificador treinado pode reconhecer a intencao "receber
        # dados" e ainda assim desconhecer a FONTE: camera, radio,
        # satelite, API ou qualquer outra que ainda nao tenha sido ensinada.
        # Verificar a fonte gramatical contra evidencias da intencao,
        # em vez de aprovar a resposta apenas por pontuacao neural.
        if rank and self.base[rank[0][1]]["id"] == "py_input":
            metodo = re.search(
                r"\b(?:pelo|pela|pelos|pelas|via|por meio (?:de|da|do)|"
                r"atraves (?:de|da|do)|usando|utilizando)\s+"
                r"(?:o |a |os |as |um |uma )?([a-z][a-z0-9_-]*)\b", n)
            if metodo:
                entrada = self.base[rank[0][1]]
                evidencias = set(tokens(" ".join(entrada["perguntas"]) +
                                      " " + entrada["resposta"]))
                if metodo.group(1) not in evidencias:
                    return "fora", (
                        "Reconheci o pedido de obter dados, mas não há instrução "
                        "cadastrada para o meio de entrada especificado. "
                        "Não vou substituir esse meio pelo teclado.")
        # se metade ou mais das palavras é desconhecida, o Crivo prefere admitir que não sabe
        if rank and toks and len(desconhecidas) / len(toks) >= 0.5 and rank[0][0] < 0.9:
            rank = []
        if len(rank) > 1 and rank[0][0] >= LIMIAR_DUVIDA and rank[0][0] - rank[1][0] < 0.06:
            return self._pedir_esclarecimento([i for _, i in rank[:2]], original)
        # Rede e recuperador precisam concordar; sem acordo, mantém-se
        # o comportamento original. O limiar não é garantia de calibração.
        neural = self.previsao_neural(original)
        if (neural and neural[1] >= self.limiar_rede and rank
                and self.base[rank[0][1]]["id"] == neural[0]
                and rank[0][0] >= LIMIAR_DUVIDA
                and len(desconhecidas) < max(1, len(toks) / 2)):
            # A confirmação neural não deve retirar as alternativas que o
            # recuperador já ofereceria para o comando "mais".
            self.ultimos = ([(sc, i) for sc, i in rank[:4] if sc >= LIMIAR * 0.8]
                            if rank[0][0] >= LIMIAR else [rank[0]])
            self.pos_ultimo = 0
            return self._registrar(rank[0][1], original)
        if rank and rank[0][0] >= LIMIAR:
            self.ultimos = [(sc, i) for sc, i in rank[:4] if sc >= LIMIAR * 0.8]
            self.pos_ultimo = 0
            return self._registrar(rank[0][1], original)
        if rank and rank[0][0] >= LIMIAR_DUVIDA and not desconhecidas:
            return self._pedir_esclarecimento([rank[0][1]], original)
        return "fora", (self.NAO_ENTENDI + " Pode dizer de outro jeito? Pode ser uma pergunta "
                        "ou algo que aconteceu com você. Se quiser ver o que eu sei fazer, digite 'ajuda'.")


# ------------------------------------------------------------- testes ------
def rodar_testes(caminho=None):
    caminho = Path(caminho) if caminho else PASTA / "testes.json"
    casos = json.loads(caminho.read_text(encoding="utf-8"))
    fixa = datetime.datetime(2026, 9, 29, 15, 30)  # terça-feira
    ok = 0
    falhas = []
    for c in casos:
        bot = Crivo(agora=fixa)
        id_obtido, resp = bot.responder(c["pergunta"])
        esperado = c["esperado"]
        if id_obtido == esperado:
            ok += 1
        else:
            falhas.append((c["pergunta"], esperado, id_obtido))
    total = len(casos)
    print(f"Crivo {VERSAO} - teste: {ok}/{total} acertos ({100 * ok / total:.0f}%)")
    for q, esp, obt in falhas:
        print(f"  ERRO: \"{q}\"\n        esperado={esp}  obtido={obt}")
    return ok, total


# ---------------------------------------------------------------- CLI ------
def conversar(usar_dialogo_contextual=False):
    bot = Crivo(usar_dialogo_contextual=usar_dialogo_contextual)
    print(f"Crivo {VERSAO} - digite 'sair' para encerrar, 'assuntos' para ver os temas.\n")
    while True:
        try:
            fala = input("você > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nCrivo > Até logo!")
            return
        if normalizar(fala) in ("sair", "exit", "quit"):
            print("Crivo > Até logo!")
            return
        _, resp = bot.responder(fala)
        print(f"Crivo > {resp}\n")


if __name__ == "__main__":
    args = sys.argv[1:]
    experimental = bool(args and args[0] == "--dialogo-experimental")
    if experimental:
        args = args[1:]
    if args and args[0] == "--teste":
        ok, total = rodar_testes()
        sys.exit(0 if ok == total else 1)
    elif args:
        print(Crivo(usar_dialogo_contextual=experimental).responder(" ".join(args))[1])
    else:
        conversar(usar_dialogo_contextual=experimental)
