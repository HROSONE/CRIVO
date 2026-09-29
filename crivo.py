#!/usr/bin/env python3
"""
Crivo v0.1 - assistente de conversa em português.

Assuntos do primeiro teste: plantas, animais, clima, tempo, estações do ano,
sistema solar e coisas de casa.

Uso:
    python crivo.py                 conversa no terminal
    python crivo.py "sua pergunta"  responde uma vez
    python crivo.py --teste         roda a bateria de testes (testes.json)

Sem dependências externas: só a biblioteca padrão do Python 3.8+.
"""
import datetime
import json
import math
import random
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

VERSAO = "0.2"
PASTA = Path(__file__).resolve().parent

TOPICOS = {
    "plantas": "plantas",
    "animais": "animais",
    "clima": "clima",
    "tempo": "tempo (horas, datas, calendário)",
    "estacoes": "estações do ano",
    "sistema_solar": "sistema solar",
    "casa": "coisas de casa",
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
    rs = [SINONIMOS.get(r, r) for r in (radical(p) for p in ps if p not in STOP and len(p) > 1)]
    return rs


# ------------------------------------------------------------- modelo ------
class Crivo:
    def __init__(self, caminho_base=None, agora=None):
        caminho = Path(caminho_base) if caminho_base else PASTA / "conhecimento.json"
        self.caminho_base = caminho
        self.base = json.loads(caminho.read_text(encoding="utf-8"))
        self._agora = agora  # permite fixar a data em testes
        self._indexar()
        self.ultimos = []     # ranking da última pergunta, para "mais"
        self.pos_ultimo = 0
        self.historico = []
        self.ultimo_assunto = None
        self.rede = None
        self.limiar_rede = 0.80
        pesos = caminho.with_name('rede_crivo.json')
        if pesos.is_file():
            self.carregar_rede(pesos)

    def carregar_rede(self, caminho, limiar=0.80):
        from rede_neural import RedeCrivo
        rede = RedeCrivo.carregar(caminho)
        if set(rede.rotulos) != {e["id"] for e in self.base}:
            raise ValueError("Rede incompatível com a base; treine novamente")
        if not 0 < limiar <= 1:
            raise ValueError("Limiar inválido")
        self.rede = rede
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
            for q in e["perguntas"]:
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
        self.idf_raro = max(self.idf.values())
        self.vetores = []
        for c in docs:
            v = {t: (1 + math.log(f)) * self.idf[t] for t, f in c.items()}
            norma = math.sqrt(sum(x * x for x in v.values())) or 1.0
            self.vetores.append({t: x / norma for t, x in v.items()})

    def _ranking(self, texto):
        c = Counter(tokens(texto))
        if not c:
            return []
        q = {t: (1 + math.log(f)) * self.idf.get(t, 0.0) for t, f in c.items()}
        norma = math.sqrt(sum(x * x for x in q.values())) or 1.0
        q = {t: x / norma for t, x in q.items()}
        pontos = []
        total = sum(self.idf.get(t, self.idf_raro) for t in c) or 1.0
        for i, v in enumerate(self.vetores):
            s = sum(x * v.get(t, 0.0) for t, x in q.items())
            # cobertura: quanto do peso da pergunta esta entrada explica
            cob = sum(self.idf[t] for t in c if t in self.termos[i]) / total
            s += 0.4 * cob
            # bônus se as palavras da pergunta batem com alguma pergunta-exemplo
            tq = set(q)
            for pergunta in self.base[i]["perguntas"]:
                tp = set(tokens(pergunta))
                if tp and tq:
                    s += 0.35 * len(tq & tp) / len(tq | tp)
            pontos.append((s, i))
        nq = normalizar(texto)
        if re.search(r"\b(por que|porque|o que faz|o que causa)\b", nq):
            for k, (score, idx) in enumerate(pontos):
                exemplos = " ".join(normalizar(p) for p in self.base[idx]["perguntas"])
                if re.search(r"\b(por que|porque|o que causa|o que faz)\b", exemplos):
                    pontos[k] = (score + 0.16, idx)
        pontos.sort(reverse=True)
        return [(s, i) for s, i in pontos if s > 0]


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
        if re.search(r"\bque horas\b|\bhoras sao\b|\bhora atual\b|\bque hora e\b|\bhora certa\b", n):
            return "dyn:hora", f"Agora são {d:%H:%M}."
        if re.search(r"\bque dia (e )?hoje\b|\bdata de hoje\b|\bqual (e )?a data\b|"
                     r"\bhoje e que dia\b|\bdia da semana\b|\bque dia e hoje\b", n):
            return "dyn:data", (f"Hoje é {DIAS[d.weekday()]}, {d.day} de "
                                f"{MESES[d.month - 1]} de {d.year}.")
        if re.search(r"\bque mes\b|\bem que mes\b", n):
            return "dyn:mes", f"Estamos em {MESES[d.month - 1]} de {d.year}."
        if re.search(r"\bque ano\b|\bem que ano\b", n):
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
            return "social:oi", "Oi! Sou o Crivo. Pergunte sobre plantas, animais, clima, estações, sistema solar ou coisas de casa."
        if re.search(r"\b(obrigad[oa]|valeu|brigado|thanks)\b", n):
            return "social:obrigado", "Por nada! Se quiser saber mais alguma coisa, é só perguntar."
        if re.search(r"\b(tchau|ate logo|ate mais|falou|adeus)\b", n):
            return "social:tchau", "Até logo!"
        if re.search(r"\b(tudo bem|como vai|como voce esta|como vc esta)\b", n):
            return "social:tudobem", "Tudo bem por aqui! E com você? Sobre o que vamos conversar?"
        if re.search(r"\b(quem e voce|seu nome|quem te criou|o que voce e)\b", n):
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
                ex.append(random.choice(qs))
            return "social:exemplos", "Experimente perguntar, por exemplo:\n- " + "\n- ".join(ex)
        return None

    # ---------------------------------------------------- resposta -------
    def responder(self, texto):
        """Devolve (id, resposta)."""
        n = normalizar(texto).strip()
        if not n:
            return "vazio", "Pode falar, estou ouvindo."

        if re.fullmatch(r"(mais|outra|outra resposta|e mais|continue|continua)", n):
            if self.ultimos and self.pos_ultimo + 1 < len(self.ultimos):
                self.pos_ultimo += 1
                s, i = self.ultimos[self.pos_ultimo]
                return self.base[i]["id"], self.base[i]["resposta"]
            return "mais:fim", "Não tenho mais nada sobre esse assunto. Quer perguntar outra coisa?"

        d = self._dinamico(n)
        if d:
            return d
        s = self._social(n)
        if s:
            return s

        original = texto
        if re.search(r"\b(nao|nunca|jamais|sem)\b", n) and re.search(r"\b(pode|posso|devo|precisa|seguro|mistur|comer)\b", n):
            return "duvida", "Ainda não interpreto essa negação com segurança. Reformule a pergunta diretamente."
        if self.ultimo_assunto and re.search(r"\b(isso|disso|dele|dela)\b", n) and len(tokens(texto)) <= 3:
            texto = texto + " " + self.ultimo_assunto
        if "abelha" in n and re.search(r"\b(ajudam|ajuda|natureza|importantes)\b", n):
            e = next(e for e in self.base if e["id"] == "abelhas")
            return e["id"], e["resposta"]
        if "estacoes" in n and re.search(r"\b(existirem|existem|causa|por que)\b", n):
            e = next(e for e in self.base if e["id"] == "causa_estacoes")
            return e["id"], e["resposta"]
        rank = self._ranking(texto)
        toks = tokens(texto)
        desconhecidas = [t for t in toks if t not in self.idf]
        # se metade ou mais das palavras é desconhecida, o Crivo prefere admitir que não sabe
        if rank and toks and len(desconhecidas) / len(toks) >= 0.5 and rank[0][0] < 0.9:
            rank = []
        # Rede e recuperador precisam concordar; sem acordo, mantém-se
        # o comportamento original. O limiar não é garantia de calibração.
        neural = self.previsao_neural(original)
        if (neural and neural[1] >= self.limiar_rede and rank
                and self.base[rank[0][1]]["id"] == neural[0]
                and rank[0][0] >= LIMIAR_DUVIDA
                and len(desconhecidas) < max(1, len(toks) / 2)):
            e = self.base[rank[0][1]]
            self.ultimo_assunto = e["perguntas"][0]
            self.historico.append({"pergunta": original, "id": e["id"]})
            self.historico = self.historico[-20:]
            return e["id"], e["resposta"]
        if rank and rank[0][0] >= LIMIAR:
            self.ultimos = [(sc, i) for sc, i in rank[:4] if sc >= LIMIAR * 0.8]
            self.pos_ultimo = 0
            e = self.base[rank[0][1]]
            self.ultimo_assunto = e["perguntas"][0]
            self.historico.append({"pergunta": original, "id": e["id"]})
            self.historico = self.historico[-20:]
            return e["id"], e["resposta"]
        if rank and rank[0][0] >= LIMIAR_DUVIDA and not desconhecidas:
            e = self.base[rank[0][1]]
            return "duvida", (f"Não tenho certeza se entendi. Você quis perguntar algo como "
                              f"\"{e['perguntas'][0]}\"?")
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
