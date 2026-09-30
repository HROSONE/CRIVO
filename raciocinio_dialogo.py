"""Raciocínio limitado sobre premissas explícitas e contas de uma compra.

As premissas são hipóteses da sessão, nunca fatos inseridos no currículo.
Só são executados quadros completos; não há eval, execução de código nem
conclusões pela ausência de uma regra. Quantidades/preços são conservados.
"""
import re
import unicodedata
from collections import deque
from decimal import Decimal, InvalidOperation

def sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def chave(texto):
    n = " ".join(sem_acento(texto.casefold()).split())
    return re.sub(r"^(?:um|uma|o|a|os|as)\s+", "", n)


class RaciocinioDialogo:
    MAX_INTERVALO = 10

    def __init__(self):
        self.regras = deque(maxlen=12)
        self.nomes = {}
        self.turno_hipotese = -100
        self.compra = None

    def limpar(self):
        self.regras.clear()
        self.nomes.clear()
        self.turno_hipotese = -100
        self.compra = None

    @staticmethod
    def _regra(texto):
        m = re.fullmatch(r"tod[oa]\s+([\wÀ-ÿ]+(?: [\wÀ-ÿ]+){0,3}?)\s+(n[aã]o\s+)?[eé]\s+"
                         r"(n[aã]o\s+)?(?:(?:um|uma)\s+)?([\wÀ-ÿ]+(?: [\wÀ-ÿ]+){0,3})", texto, re.I)
        if not m:
            return None
        a, negacao_antes, negacao_depois, b = m.groups()
        if negacao_antes and negacao_depois:
            return None
        negativo = negacao_antes or negacao_depois
        # Negações/quantificadores dentro do nome não são apagados.
        if any(re.search(r"\b(?:nao|todo|toda|algum|alguma|se|ou|talvez|geralmente)\b", chave(x)) for x in (a, b)):
            return None
        return a, b, bool(negativo)

    def _guardar_regra(self, regra):
        a, b, negativo = regra
        ka, kb = chave(a), chave(b)
        self.nomes[ka], self.nomes[kb] = a, b
        if (ka, kb, negativo) not in self.regras:
            self.regras.append((ka, kb, negativo))
        vivos = {n for a, b, _ in self.regras for n in (a, b)}
        self.nomes = {k: v for k, v in self.nomes.items() if k in vivos}

    def _caminho(self, origem, destino, negativo=False):
        fila = deque([(origem, (origem,))])
        vistos = set()
        while fila:
            atual, caminho = fila.popleft()
            if atual in vistos:
                continue
            vistos.add(atual)
            for a, b, neg in self.regras:
                if a != atual:
                    continue
                if b == destino and neg == negativo:
                    return caminho + (b,)
                if not neg and b not in vistos:
                    fila.append((b, caminho + (b,)))
        return None

    def _concluir(self, consulta):
        pergunta = re.fullmatch(r"(?:(?:ent[aã]o|logo)\s+)?(?:(?:um|uma|todo|toda)\s+)?"
                               r"([\wÀ-ÿ]+(?: [\wÀ-ÿ]+){0,3}?)\s+(n[aã]o\s+)?[eé]\s+"
                               r"(?:(?:um|uma)\s+)?([\wÀ-ÿ]+(?: [\wÀ-ÿ]+){0,3})", consulta, re.I)
        if not pergunta:
            return None
        a, negado, b = pergunta.groups()
        ka, kb = chave(a), chave(b)
        if ka not in self.nomes or kb not in self.nomes:
            return "conversa:hipotese", "Não há premissas suficientes nessa hipótese para concluir isso. Quais relações você quer assumir?", None, ""
        sim, nao = self._caminho(ka, kb), self._caminho(ka, kb, True)
        if sim and nao:
            return "conversa:hipotese", "As premissas entram em conflito: permitem afirmar e negar a mesma relação. Precisamos corrigir a hipótese antes de concluir.", None, ""
        caminho = nao if negado and nao else sim if not negado and sim else sim or nao
        if caminho is None:
            return "conversa:hipotese", "Não consigo concluir essa relação a partir das premissas dadas. Não encontrar um caminho não prova que a afirmação seja falsa.", None, ""
        corresponde = bool(nao) if negado else bool(sim)
        passos = " → ".join(self.nomes[n] for n in caminho)
        resposta = ("Sim" if corresponde else "Não") + ", supondo verdadeiras as premissas que você deu: " + passos + "."
        if nao:
            resposta += " A última relação é negativa; isso não autoriza inverter a implicação."
        resposta += " Essa é uma conclusão dentro da hipótese, não um fato novo sobre o mundo."
        return "conversa:hipotese", resposta, None, ""

    def _hipotese(self, texto, turno):
        n = texto.strip().strip(".?! ")
        inicio = re.match(r"^(?:suponha que|supondo que|considere que|se)\s+", n, re.I)
        if inicio:
            corpo = n[inicio.end():]
            # Separador da pergunta não pode consumir parte de uma premissa.
            partes = re.split(r"[.;,]\s*", corpo)
            if not 1 <= len(partes) <= 2:
                return None
            regras = [self._regra(p.strip()) for p in re.split(r"\s+e\s+(?=tod[oa]\s)", partes[0], flags=re.I)]
            if not regras or any(r is None for r in regras) or len(regras) > 6:
                return None
            # Confere também a pergunta antes de modificar o estado.
            if len(partes) == 2 and not re.fullmatch(r"(?:(?:ent[aã]o|logo)\s+)?(?:(?:um|uma|todo|toda)\s+)?"
                                                    r"[\wÀ-ÿ ]+\s+[eé]\s+[\wÀ-ÿ ]+", partes[1], re.I):
                return None
            self.regras.clear(); self.nomes.clear()
            for regra in regras:
                self._guardar_regra(regra)
            self.turno_hipotese = turno
            if len(partes) == 2:
                return self._concluir(partes[1])
            resposta = "Vou tratar como hipótese: " + partes[0] + ". Que conclusão você quer verificar?"
            return "conversa:hipotese", resposta, None, ""
        if self.regras and turno - self.turno_hipotese <= self.MAX_INTERVALO:
            regra = self._regra(re.sub(r"^e\s+", "", n, flags=re.I))
            if regra:
                self._guardar_regra(regra)
                self.turno_hipotese = turno
                return "conversa:hipotese", "Acrescentei à hipótese: “" + n + "”. Que conclusão quer testar?", None, ""
            # Só continuação explícita usa premissas de turnos anteriores.
            if re.match(r"^(?:ent[aã]o|logo)\s+", n, re.I) and "?" in texto:
                return self._concluir(n)
        elif self.regras:
            self.regras.clear(); self.nomes.clear()
        return None

    @staticmethod
    def _numero(texto):
        nomes = {"um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4,
                 "cinco": 5, "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10}
        nome = sem_acento(texto.strip().casefold())
        if nome in nomes:
            return Decimal(nomes[nome])
        try:
            return Decimal(texto.replace(",", "."))
        except InvalidOperation:
            return None

    def _conta(self, texto, turno):
        n = texto.strip().strip(".?! ")
        compra = re.fullmatch(r"(?:eu\s+)?(?:comprei|paguei por)\s+"
                              r"(\d{1,5}|um|uma|dois|duas|tr[eê]s|quatro|cinco|seis|sete|oito|nove|dez)\s+"
                              r"([\wÀ-ÿ ]+?)\s+(?:por|a)\s+(?:R\$\s*)?(\d{1,7}(?:[,.]\d{1,2})?)\s*"
                              r"(?:reais\s+)?cada(?:\s+um|\s+uma)?"
                              r"(?:[.;]\s*(?:quanto (?:gastei|paguei)|qual (?:foi )?o total))?", n, re.I)
        if compra:
            quantidade, objeto, preco = compra.groups()
            # Modificadores de preço/quantidade não são ignorados.
            if re.search(r"\b(?:desconto|gratis|devolvi|menos|mais|frete|mas|se|nao)\b", chave(objeto)):
                return None
            q, p = self._numero(quantidade), self._numero(preco)
            self.compra = (q, p, turno)
        elif re.fullmatch(r"quanto (?:gastei|paguei)|qual (?:foi )?o total", n, re.I):
            if self.compra is None or turno - self.compra[2] != 1:
                return None
            q, p, _ = self.compra
        else:
            return None
        def formatar(valor):
            return format(valor, "f").replace(".", ",")
        resposta = "O total é R$ " + formatar(q * p) + ": " + formatar(q) + " × R$ " + formatar(p) + ". Usei a quantidade e o preço por unidade que você informou."
        return "conversa:calculo", resposta, None, ""

    def preparar(self, texto, turno):
        if not isinstance(texto, str) or len(texto) > 1200 or any(c in texto for c in ('`', '"', '“', '”')):
            return None
        return self._hipotese(texto, turno) or self._conta(texto, turno)
