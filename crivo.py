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
    def __init__(self, caminho_base=None, agora=None):
        caminho = Path(caminho_base) if caminho_base else PASTA / "conhecimento.json"
        self.caminho_base = caminho
        self.base = json.loads(caminho.read_text(encoding="utf-8"))
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
        self.contexto_frutas = None
        self._agora = agora  # permite fixar a data em testes
        self._indexar()
        self.ultimos = []     # ranking da última pergunta, para "mais"
        self.pos_ultimo = 0
        self.historico = []
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
        for e in self.base:
            c = Counter()
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
        # Um currículo novo não deve alterar o peso das palavras de outro domínio.
        self.grupos = ["programacao" if e["topico"] == "programacao" else "geral"
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
        n = normalizar(texto).strip().strip("?.,;! ")
        expressoes = (
            r"(?:e\s+)?(?:(?:poderia|pode) me explicar |explique )?o que (?:e|eh|sao) (.+)",
            r"o que significa (.+)",
            r"defina (.+)",
            r"(?:qual e a |qual a )definicao de (.+)",
            r"definicao de (.+)",
        )
        for padrao in expressoes:
            match = re.fullmatch(padrao, n)
            if match:
                conceito = re.sub(r"^(?:um|uma|o|a|os|as)\s+", "", match.group(1))
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
            temp.write_text(json.dumps(nova_base, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            temp.replace(self.caminho_base)
        self.base = nova_base
        self._indexar()
        self.rede = None
        self.esclarecimento = None
        self.ultimos = []
        self.pos_ultimo = 0

    def _registrar(self, indice, pergunta):
        e = self.base[indice]
        self.esclarecimento = None
        self.ultimo_assunto = e["perguntas"][0]
        self.historico.append({"pergunta": pergunta, "id": e["id"]})
        self.historico = self.historico[-20:]
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
        h = self.agora().hour
        if re.search(r"\b(bom dia|boa tarde|boa noite)\b", n):
            saud = "Bom dia" if h < 12 else "Boa tarde" if h < 18 else "Boa noite"
            return "social:oi", f"{saud}! Sou o Crivo. Sobre o que quer conversar?"
        if re.match(r"^(oi+|ola|e ai|opa|eai|salve|hey|hello)\b", n):
            return "social:oi", "Oi! Sou o Crivo. Pergunte sobre " + ", ".join(TOPICOS.values()) + "."
        if re.search(r"\b(obrigad[oa]|valeu|brigado|thanks)\b", n):
            return "social:obrigado", "Por nada! Se quiser saber mais alguma coisa, é só perguntar."
        if re.search(r"\b(tchau|ate logo|ate mais|falou|adeus)\b", n):
            return "social:tchau", "Até logo!"
        if re.search(r"\b(tudo bem|como vai|como voce esta|como vc esta)\b", n):
            return "social:tudobem", "Tudo bem por aqui! E com você? Sobre o que vamos conversar?"
        # Pedir que um programa solicite o nome de alguém NÃO é perguntar
        # pelo nome do próprio assistente. Intenção social deve ser a frase
        # inteira, não uma substring de outra tarefa.
        if re.fullmatch(r"(?:quem e voce|quem te criou|o que voce e|"
                        r"(?:(?:qual (?:e )?(?:o )?)|(?:me (?:diga|fale) (?:o )?))?seu nome)", n):
            return "social:quem", (f"Sou o Crivo, versão {VERSAO}: um assistente de conversa em português, "
                                   "ainda em fase de teste. Por enquanto só falo sobre alguns assuntos "
                                   "(digite 'assuntos' para ver).")
        if re.search(r"\b(assuntos?|topicos?|o que voce sabe|o que voce faz|sobre o que)\b|^(ajuda|help)$", n):
            lista = ", ".join(TOPICOS.values())
            return "social:assuntos", f"Por enquanto eu converso sobre: {lista}. Pode perguntar à vontade!"
        if re.fullmatch(r"(exemplos?|me de exemplos|sugestoes?)", n.strip()):
            ex = []
            for t in TOPICOS:
                qs = [q for e in self.base if e["topico"] == t for q in e["perguntas"][:1]]
                if qs:
                    ex.append(random.choice(qs))
            return "social:exemplos", "Experimente perguntar, por exemplo:\n- " + "\n- ".join(ex)
        return None

    # ---------------------------------------------------- resposta -------
    def responder(self, texto):
        """Devolve (id, resposta)."""
        original = texto
        # Um fragmento como "E a banana?" utiliza somente o assunto do
        # turno IMEDIATAMENTE anterior, não um fruto citado muito antes.
        contexto_frutas_anterior = self.contexto_frutas
        self.contexto_frutas = None
        n = normalizar(texto).strip().strip("?.,; ").rstrip("!")
        # Cumprimentos não devem engolir a pergunta que vem junto.
        prefixo = r"^(?:(?:oi+|ola|bom dia|boa tarde|boa noite|obrigad[oa])\b[!,. :;-]*|por (?:favor|gentileza)[,: ]*)"
        resto = re.sub(prefixo, "", n).strip()
        if resto and resto != n:
            n = resto
            texto = resto
        resto = re.sub(r"[,; ]+(?:por favor|obrigad[oa])$", "", n).strip()
        if resto:
            n = resto
            texto = resto
        if not n:
            return "vazio", "Pode falar, estou ouvindo."

        esclarecida = self._resolver_esclarecimento(n, original)
        if esclarecida:
            return esclarecida

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
            return s

        prevencao = re.sub(r"^(?:o que fazer (?:pra|para)|como fazer para|como) nao (?:ter|pegar)\b", "como evitar", n)
        if prevencao != n:
            texto = n = prevencao
        exatas = [i for i, e in enumerate(self.base) if any(
            chave_pergunta(p) == chave_pergunta(n) for p in e["perguntas"])]
        if len(exatas) == 1:
            i = exatas[0]
            self.ultimos = [(1.0, i)]
            return self._registrar(i, original)
        if len(exatas) > 1:
            return "duvida", "Há mais de uma resposta cadastrada para essa pergunta. Pode detalhar?"
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
        definicao = self._responder_definicao(n, original)
        if definicao is not None:
            return definicao
        # Inferência estruturada somente para relações comprováveis.
        # Os casos não reconhecidos continuam no recuperador habitual.
        if self.raciocinio is not None:
            inferencia = self.raciocinio.interpretar(original)
            if inferencia is not None:
                # Fonte editorial explícita e existente pode explicar uma
                # prova comprovada, sem converter um ranking aproximado em
                # negação ou atribuir certeza a uma base desconhecida.
                fonte_id = self.raciocinio.fonte_para(original, inferencia[0])
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
                self.historico.append({"pergunta": original, "id": inferencia[0],
                                       "mecanismo": "raciocinio_relacional"})
                self.historico = self.historico[-20:]
                return inferencia
        if self.ultimo_assunto and re.search(r"\b(isso|disso|dele|dela)\b", n) and len(tokens(texto)) <= 3:
            texto = texto + " " + self.ultimo_assunto
        if "estacoes" in n and re.search(r"\b(o que faz existirem|o que causa|por que)\b", n):
            indice = next((i for i, e in enumerate(self.base) if e["id"] == "causa_estacoes"), None)
            if indice is not None:
                self.ultimos = [(1.0, indice)]
                return self._registrar(indice, original)
        rank = self._ranking(texto)
        _, vocabulario = self._contexto_consulta(texto)
        toks = self._tokens_consulta(texto, vocabulario)
        desconhecidas = [t for t in toks if t not in vocabulario]
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
        lista = ", ".join(TOPICOS.values())
        return "fora", (f"Ainda não sei responder isso. Por enquanto converso sobre: {lista}. "
                        "Tente reformular ou escolha um desses assuntos.")


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
def conversar():
    bot = Crivo()
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
    if args and args[0] == "--teste":
        ok, total = rodar_testes()
        sys.exit(0 if ok == total else 1)
    elif args:
        print(Crivo().responder(" ".join(args))[1])
    else:
        conversar()
