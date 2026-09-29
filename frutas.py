"""Conhecimento botânico estruturado sobre frutos, independente de LLM.

Lê fatos e explicações revisáveis de frutas.json. Interpreta formatos
restritos, combina propriedades registradas e prefere "não sei" a
inventar preço, propriedades médicas, sazonalidade ou outras informações.
"""
import json
import re
import unicodedata
from pathlib import Path


def normalizar_fruta(texto):
    t = unicodedata.normalize("NFD", texto.lower().replace("-", " "))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return " ".join(re.sub(r"[^a-z0-9\s]", " ", t).split())


def plural(nome):
    """Só gera variantes morfológicas para os nomes curados, não texto livre."""
    if nome.endswith("ao"):
        return nome[:-2] + "oes"
    if nome.endswith("a") or nome.endswith("o") or nome.endswith("e") or nome.endswith("u"):
        return nome + "s"
    if nome.endswith("m"):
        return nome[:-1] + "ns"
    return nome + "s"


class ConhecimentoFrutas:
    def __init__(self, dados):
        if not isinstance(dados, dict) or dados.get("versao") != 1:
            raise ValueError("Formato de conhecimento de frutas inválido")
        grupos = dados.get("grupos")
        itens = dados.get("itens")
        if not isinstance(grupos, dict) or not isinstance(itens, list):
            raise ValueError("Grupos/itens de frutas inválidos")
        if not 1 <= len(itens) <= 500:
            raise ValueError("Número de frutos inválido")
        self.grupos = grupos
        self.itens = {}
        self.aliases = {}
        for e in itens:
            if (not isinstance(e, dict) or
                    not all(k in e for k in
                            ("id", "nome", "tipo", "descricao", "sementes", "culinaria", "aliases"))
                    or e["id"] in self.itens or e["tipo"] not in grupos or
                    not isinstance(e["culinaria"], bool) or
                    any(not isinstance(e[k], str) or not e[k].strip()
                        for k in ("id", "nome", "tipo", "descricao", "sementes")) or
                    not isinstance(e["aliases"], list) or
                    not all(isinstance(a, str) for a in e["aliases"]) or
                    (e.get("estrutura_consumida") is not None and
                     (not isinstance(e["estrutura_consumida"], str) or
                      not e["estrutura_consumida"].strip())) or
                    (e.get("destaque_comparativo") is not None and
                     (not isinstance(e["destaque_comparativo"], str) or
                      not e["destaque_comparativo"].strip()))):
                raise ValueError("Fruto com dados incompletos")
            self.itens[e["id"]] = e
            nomes = [e["nome"]] + e["aliases"]
            for nome in nomes:
                raiz = normalizar_fruta(nome)
                for alias in (raiz, plural(raiz)):
                    if alias in self.aliases and self.aliases[alias] != e["id"]:
                        raise ValueError("Nome de fruto ambíguo: " + alias)
                    self.aliases[alias] = e["id"]

    @classmethod
    def carregar(cls, caminho):
        return cls(json.loads(Path(caminho).read_text(encoding="utf-8")))

    def _item(self, alvo):
        s = normalizar_fruta(alvo)
        s = re.sub(r"^(?:o|a|os|as|um|uma|uns|umas|do|da|dos|das|de)\s+", "", s)
        ident = self.aliases.get(s)
        return self.itens.get(ident) if ident else None

    def _resposta_item(self, item, intencao):
        nome = item["nome"]
        grupo = self.grupos[item["tipo"]]
        if intencao == "sementes":
            return ("Sobre as sementes de " + nome + ": " + item["sementes"] +
                    " A presença e o tamanho podem variar com a variedade.")
        if intencao == "tipo":
            return ("Na classificação botânica cadastrada, " + nome +
                    " pertence ao grupo " + grupo + ". " + item["descricao"])
        if intencao == "culinaria":
            if item["tipo"] == "pseudofruto":
                return (item["descricao"] + " Na linguagem culinária é chamada fruta, "
                        "mas sua parte suculenta não é o fruto botânico.")
            resposta = "Na botânica, sim: " + nome + " é fruto. "
            resposta += "É também chamada fruta no uso culinário. " if item["culinaria"] else (
                "Na culinária, costuma ser usada como hortaliça, grão ou outro alimento, "
                "e não como fruta de sobremesa. ")
            return resposta + item["descricao"]
        return (item["descricao"] + " Classificação botânica: " + grupo +
                ". Sementes: " + item["sementes"])

    def _resultado(self, item, intencao):
        return ("frutas:" + item["id"], self._resposta_item(item, intencao),
                intencao, item["id"])

    def _exemplos(self, grupo=None, limite=12):
        itens = [e for e in self.itens.values()
                 if e["culinaria"] and (grupo is None or e["tipo"] in grupo)]
        itens = itens[:max(1, min(limite, 30))]
        return ", ".join(item["nome"] for item in itens) if itens else "nenhum exemplo cadastrado"

    def _conceito_geral(self, n):
        if re.fullmatch(
                r"(?:e\s+)?(?:qual (?:e )?a diferenca entre|diferenca entre)\s+fruto\s+e\s+fruta",
                n):
            return ("frutas:conceito",
                    "Na botânica, fruto é a estrutura que em geral se forma a partir do "
                    "ovário da flor e ajuda a proteger ou dispersar sementes. "
                    "Fruta é uma palavra de uso cotidiano, principalmente para "
                    "frutos ou estruturas vegetais comestíveis. Assim, tomate e "
                    "pepino são frutos na botânica, mas costumam ser tratados como "
                    "hortaliças na culinária. Maçã e morango também envolvem "
                    "tecidos florais além do ovário.",
                    "conceito", None)
        if re.fullmatch(r"(?:e\s+)?(?:o que sao|quais sao|quais os) tipos (?:de )?frutos", n):
            return ("frutas:tipos",
                    "A botânica classifica frutos conforme sua formação: simples "
                    "(ex.: bagas como uva, drupas como manga e pomos como maçã), "
                    "agregados (framboesa), múltiplos (abacaxi) e acessórios "
                    "(morango). Também existem frutos secos, como cariopses "
                    "(grãos de milho) e legumes botânicos (vagens). "
                    "As categorias podem se sobrepor: morango é agregado e acessório.",
                    "tipos", None)
        if re.fullmatch(r"(?:e\s+)?(?:como|de que modo) (?:se )?(?:formam|nascem|surgem) os frutos", n):
            return ("frutas:formacao",
                    "Em plantas com flores, o fruto normalmente se desenvolve após a "
                    "fecundação: o ovário amadurece e os óvulos podem formar sementes. "
                    "Alguns frutos cultivados desenvolvem-se sem sementes viáveis. "
                    "Polinização é o transporte do pólen e não a definição de fruto.",
                    "formacao", None)
        if re.fullmatch(r"(?:e\s+)?(?:para que servem|qual a funcao d[oe]s?) frutos", n):
            return ("frutas:funcao",
                    "Os frutos geralmente protegem sementes durante seu desenvolvimento "
                    "e favorecem sua dispersão por animais, água, vento ou outros "
                    "mecanismos. Nem todo fruto é comestível.",
                    "funcao", None)
        return None

    def _grupo_pergunta(self, n):
        padroes = (
            (r"(?:frutas|frutos)\s+(?:citricos|citricas|de citricos|do tipo citrico)", 
             ("hesperidio",), "Frutos cítricos"),
            (r"(?:frutas|frutos)\s+(?:de caroco|com caroco|drupas)", 
             ("drupa",), "Frutos de caroço"),
            (r"(?:frutas|frutos)\s+(?:do tipo baga|que sao bagas|bagas)", 
             ("baga",), "Bagas botânicas"),
            (r"(?:frutas|frutos)\s+(?:agregados|agregadas)", 
             ("agregado", "acessorio_agregado"), "Frutos agregados"),
            (r"(?:frutas|frutos)\s+(?:multiplos|multiplas)", 
             ("multiplo",), "Frutos múltiplos"),
        )
        if not re.search(r"\b(quais|liste|exemplos|cite|de|me|o que sao)\b", n):
            return None
        for padrao, tipos, legenda in padroes:
            if re.search(padrao, n):
                chave = ("citricas" if "hesperidio" in tipos else
                         "drupas" if "drupa" in tipos else
                         "bagas" if "baga" in tipos else
                         "agregados" if "agregado" in tipos else "multiplos")
                return ("frutas:grupo:" + chave,
                        legenda + " cadastrados: " + self._exemplos(tipos) +
                        ". É uma seleção da base, não uma lista de todas as espécies.",
                        "grupo", None)
        m = re.fullmatch(r"(?:me de|cite|liste|quais sao|quais|me diga)\s+"
                         r"(?:(\d{1,2})\s+)?(?:exemplos de )?(?:frutas|frutos)(?:\s+conhecidos)?", n)
        if m:
            total = int(m.group(1)) if m.group(1) else 12
            return ("frutas:grupo:geral",
                    "Exemplos de frutas cadastradas: " + self._exemplos(limite=total) +
                    ". São exemplos, não a totalidade das frutas do mundo.",
                    "grupo", None)
        return None

    @staticmethod
    def _frase_curta(item):
        """Seleciona um fato pequeno da curadoria; não gera novos fatos.

        Quando falta um destaque específico, seleciona apenas a PRIMEIRA
        frase da descrição conhecida, em vez de despejar o registro todo.
        """
        texto = item.get("destaque_comparativo") or item["descricao"]
        frase = re.split(r"(?<=[.!?])\s+", texto.strip(), maxsplit=1)[0]
        return frase if frase.endswith((".", "!", "?")) else frase + "."

    def _comparar(self, a, b, modo):
        """Explica semelhanças e diferenças relevantes de dois registros.

        Usa classificação, exceções botânicas e até um destaque por espécie.
        Não copia os textos integrais, não inventa propriedades ou relações
        ausentes, não pede inferência a nenhum modelo externo.
        """
        nome_a, nome_b = a["nome"], b["nome"]
        classe_a = self.grupos[a["tipo"]].split(":", 1)[0].strip()
        classe_b = self.grupos[b["tipo"]].split(":", 1)[0].strip()
        iguais = a["tipo"] == b["tipo"]

        # Nem toda parte consumida é o próprio fruto. Com exceções
        # estruturadas, evita "ambos são frutos botânicos" irrestrito.
        excecoes = [e["nome"] + ": " + e["estrutura_consumida"].rstrip(".")
                    for e in (a, b) if e.get("estrutura_consumida")]
        if excecoes:
            comum = (nome_a + " e " + nome_b +
                     " constam do catálogo de frutos e estruturas vegetais "
                     "relacionadas, mas é preciso distinguir a parte consumida "
                     "do fruto: " + "; ".join(excecoes) + ".")
        elif "pseudofruto" in (a["tipo"], b["tipo"]):
            comum = (nome_a + " e " + nome_b +
                     " constam do catálogo botânico, mas nem toda parte "
                     "consumida é o próprio fruto.")
        else:
            comum = (nome_a + " e " + nome_b + " são frutos botânicos.")

        if iguais:
            classes = ("Na classificação cadastrada, ambos pertencem "
                       "ao mesmo grupo: " + classe_a + ".")
        else:
            classes = ("Suas classificações são diferentes: " +
                       nome_a + " é " + classe_a + "; " +
                       nome_b + " é " + classe_b + ".")

        if modo == "mesmo_tipo":
            resposta = ("Sim. " if iguais else "Não. ") + classes
        elif modo == "tipos_diferentes":
            resposta = ("Não: eles não são de tipos diferentes. " if iguais
                        else "Sim, são de tipos diferentes. ") + classes
        elif modo == "hortalicas":
            # O campo culinaria indica ser chamada fruta, mas não prova
            # que a alternativa seria especificamente uma hortaliça.
            descricoes = (normalizar_fruta(a["descricao"]),
                          normalizar_fruta(b["descricao"]))
            eh_hortalica = all(
                "hortalica" in descricao or
                "legume no uso culinario" in descricao
                for descricao in descricoes)
            if eh_hortalica:
                resposta = (comum + " " + classes +
                            " Na culinária, ambos são frequentemente usados "
                            "como hortaliças.")
            else:
                resposta = (comum + " " + classes +
                            " Não há descrição cadastrada suficiente para "
                            "confirmar que ambos são usados como hortaliças.")
        elif modo in ("frutos", "semelhanca"):
            resposta = comum + " " + classes
            if (modo == "semelhanca" and
                    a["culinaria"] and b["culinaria"]):
                resposta += (" No uso culinário, ambos também costumam "
                             "ser chamados de frutas.")
        else:  # modo == comparar
            resposta = comum + " " + classes
            # Uma observação individual útil de cada registro, nunca
            # o bloco completo de descrição/grupo/sementes de ambos.
            if excecoes:
                # O fato sobre parte consumida já foi exibido; evite
                # repeti-lo em uma longa descrição.
                destaque = [e for e in (a, b)
                            if not e.get("estrutura_consumida")]
            else:
                destaque = (a, b)
            if destaque:
                resposta += " " + " ".join(
                    self._frase_curta(item) for item in destaque)

        return ("frutas:comparar" if modo == "comparar" else "frutas:relacao",
                resposta.strip(), modo, None)

    def _relacao_entre_frutas(self, n):
        """Reconhece perguntas binárias estreitas e combina atributos
        do catálogo, sem substituir o recuperador para outros assuntos.
        """
        padroes = (
            ("comparar",
             r"(?:qual (?:e )?a diferenca entre|compare|comparar)\s+"
             r"(.+?)\s+e\s+(.+)"),
            ("semelhanca",
             r"(?:qual (?:e )?a semelhanca entre|semelhanca entre)\s+"
             r"(.+?)\s+e\s+(.+)"),
            ("semelhanca",
             r"o que\s+(.+?)\s+e\s+(.+?)\s+tem em comum"),
            ("mesmo_tipo",
             r"por que\s+(.+?)\s+e\s+(.+?)\s+sao do mesmo tipo(?: botanico)?"),
            ("mesmo_tipo",
             r"(.+?)\s+e\s+(.+?)\s+sao do mesmo tipo(?: botanico)?"),
            ("tipos_diferentes",
             r"por que\s+(.+?)\s+e\s+(.+?)\s+sao (?:frutos )?de tipos diferentes"),
            ("hortalicas",
             r"por que\s+(.+?)\s+e\s+(.+?)\s+sao frutos mas "
             r"(?:usados|usadas) como hortalicas"),
            ("frutos",
             r"por que\s+(.+?)\s+e\s+(.+?)\s+sao frutos"),
        )
        for modo, padrao in padroes:
            m = re.fullmatch(padrao, n)
            if m is None:
                continue
            a, b = self._item(m.group(1)), self._item(m.group(2))
            if not a or not b or a["id"] == b["id"]:
                return None
            return self._comparar(a, b, modo)
        return None

    def responder(self, texto, contexto=None):
        """Retorna (ID, resposta, intenção, fruto), ou None.

        Cada formato tem seu próprio alvo; "árvore de decisão", preço,
        efeitos terapêuticos e propriedades não cadastradas não se tornam
        fatos apenas por compartilharem uma palavra com alguma fruta.
        """
        n = normalizar_fruta(texto).strip()
        if not n:
            return None

        # Termos gerais não devem engolir pergunta sobre fruto específico.
        conceito = self._conceito_geral(n)
        if conceito is not None:
            return conceito
        grupo = self._grupo_pergunta(n)
        if grupo is not None:
            return grupo

        relacao = self._relacao_entre_frutas(n)
        if relacao is not None:
            return relacao

        # Fragmentos isolados só herdam a intenção do turno imediatamente
        # anterior, recuperado do histórico enviado na mesma aba.
        match = re.fullmatch(r"e (?:o|a|os|as|um|uma) (.+)", n)
        if match:
            item = self._item(match.group(1))
            if item:
                if contexto and contexto[0] in ("definicao", "sementes", "tipo", "culinaria"):
                    return self._resultado(item, contexto[0])
                return ("frutas:desconhecido", "Você quer a definição, as sementes ou a classificação botânica de " + item["nome"] + "?", "desconhecido", None)

        # Primeiramente sementes, tipo e uso culinário. Depois definições.
        especiais = [
            ("sementes", (
                r"(.+?) (?:tem|possui|contem|apresenta) (?:as |os |uma |varias |algumas )?sementes?"
                r"(?: (?:do lado de fora|dentro|na parte de fora))?",
                r"(?:por que|porque) (.+?) (?:nao )?tem sementes?",
            )),
            ("tipo", (
                r"qual (?:e )?(?:o |a )?tipo (?:botanico )?(?:de fruto )?"
                r"(?:da|do|de|das|dos)?\s*(.+)",
                r"que tipo de fruto (?:e|eh) (.+)",
                r"(?:a|o|um|uma)?\s*(.+?) (?:e|sao) (?:uma? )?"
                r"(?:baga|drupa|pomo|citrico|hesperidio|pepo)",
            )),
            ("culinaria", (
                r"(.+?) (?:e|sao) (?:uma? )?(?:fruta|fruto|legume|hortalica)"
                r"(?: ou (?:legume|fruta|fruto|hortalica))?",
            )),
            ("definicao", (
                r"(?:e\s+)?o que (?:e|sao) (.+)",
                r"(?:e\s+)?(?:defina|definicao de|o que significa) (.+)",
                r"(?:pode|poderia) (?:me )?explicar o que (?:e|sao) (.+)",
                r"explique o que (?:e|sao) (.+)",
            )),
        ]
        for intencao, padroes in especiais:
            for padrao in padroes:
                m = re.fullmatch(padrao, n)
                if m:
                    item = self._item(m.group(1))
                    if item:
                        return self._resultado(item, intencao)
                    # A pergunta não nomeia um item exatamente conhecido.
                    # Deixe o recuperador geral decidir se sabe o conceito.
                    break

        # Perguntas novas específicas com fruta identificada não devem
        # receber uma resposta inventada pelo ranking lexical do currículo.
        if re.search(
            r"\b(preco|custa|hoje|cura|previne|diabetes|alergia|medicamento|"
            r"agrotoxico|melhor fruta|mais saudavel|mais nutritiv[ao])\b", n
        ):
            for alias in self.aliases:
                if len(alias) >= 4 and re.search(
                    r"(?:^|\s)" + re.escape(alias) + r"(?:$|\s)", n
                ):
                    return ("frutas:desconhecido",
                            "Não tenho evidência cadastrada suficiente sobre "
                            "essa propriedade específica. Não vou deduzir isso "
                            "só por conhecer o nome do fruto.",
                            "desconhecido", None)
        return None
