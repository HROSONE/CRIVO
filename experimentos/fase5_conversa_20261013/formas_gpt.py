"""Falas da pessoa da parte 2 (GPT), limpas e divididas em treino e blind, para a v3.

Origem: o criador do projeto pediu ao GPT (ChatGPT, modelo de terceiros) jeitos de dizer as 68
situações que ficaram em 0% de sentido na v2, com o prompt de
docs/prompt_grok_formas_de_fala_parte2.md, e colou as respostas na conversa. Os arquivos brutos são
grok/parte2_*_gpt.json (autoria em grok/AUTORIA.md). O GPT não escreveu nenhuma resposta do CRIVO,
nenhum fato e nenhum código. O uso como dado de treino foi aprovado pelo criador (13/10/2026).

A limpeza (revisada à mão) usa as mesmas funções de formas_grok.py e estas regras:
- cumprimento com hora (bom dia, boa tarde, boa noite) sem a palavra da hora vai para oi;
- risada escrita ("kkkkkk", "ksksks") que veio em sem_sentido vai para risada;
- "Hã?", "Ahn?", "Hein" vão para repetir;
- ansioso_peito sem sintoma no corpo (peito, coração, respiração, ar, tremor) vai para ansioso;
- ajuda_socorro sem sinal de urgência ou de aflição vai para ajuda;
- desisto_despedida sem despedida vai para desisto;
- nas perguntas sobre a própria IA, falas com mais de 14 palavras ficam de fora: são perguntas
  técnicas ou filosóficas que as respostas dessas situações não respondem;
- pedidos de poema com tema e de jogos específicos ficam para a fase 6 (imaginar).

Blind: ~20% das falas de cada situação, por hash do núcleo, nunca vistas no treino. Como o GPT
escreveu essas situações pela primeira vez, este é o teste limpo da v3.
"""
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import formas_grok as fg

AQUI = Path(__file__).resolve().parent
PARTES = sorted((AQUI / "grok").glob("parte2_*_gpt.json"), key=lambda p: int(re.search(r"parte2_(\d+)", p.name).group(1)))
PARTE_BLIND = 20

HORA = re.compile(r"dia|manh|matin|tarde|vesper|noite|notur")
RISO = re.compile(r"^(?:k+|(?:ks)+k*|(?:ka)+|(?:ja)+|(?:hue)+|(?:rs)+)[\W\s]*$")
CORPO = re.compile(r"peito|cora[cç]|respira|\bar\b|trem|aflição|frio na barriga")
URGENCIA = re.compile(r"socorro|urgente|\bagr\b|agora|importante|ignora|algu[eé]m a[ií]|apoio|escute|"
                      r"conversando|lidar|complicada|falar com algu[eé]m|precisando de vc|preciso de vc")
TCHAU = re.compile(r"\bfui\b|tchau|\bat[eé]\b|vou nessa|sair|indo|encerrar|deu\b|valeu")
SOBRE_A_IA = {"consciencia", "medo", "lembra", "voce_aprende", "aprendeu_algo", "sabe_tudo", "ser_ia", "onde_mora",
              "idade", "nome_crivo", "cor_favorita", "comida_crivo", "musica_crivo", "bicho_favorito", "nao_gosta", "fe",
              "criador"}
POEMA_TEMA = re.compile(r"sobre|de amor|triste|engra[cç]ad|sem rimar|esperan|misterios|saudade|clima|marcante|"
                        r"pare[cç]a uma conversa")
JOGO_ESPECIFICO = re.compile(r"perguntas e respostas|verdadeiro ou falso|quiz|completar frases|mem[oó]ria|"
                             r"palavras|personagens|competi[cç][aã]o|decis[oõ]es|adivinha[cç][aã]o|sem precisar de imagem|"
                             r"s[oó] na conversa|quem acerta")

MOVER = {
    "hã?": "repetir", "ahn?": "repetir", "hein": "repetir",
    "tu é um robô?": "robo", "vc é humano?": "ser_humano", "tem uma pessoa respondendo aí?": "ser_humano",
    "tem alguém digitando as respostas no seu lugar?": "ser_humano",
    "é um robô virtual ou uma pessoa por trás?": "ser_humano",
    "me indica um estilo musical pra conhecer": "recomenda",
    "vc acredita q existe algo depois da morte?": "opiniao_religiao",
    "tá meio repetitivo isso aí": "para_repetir", "vc pode parar de repetir a mesma ideia?": "para_repetir",
    "tenta variar um pouco as respostas": "para_repetir",
    "vc consegue aprender com o q eu falar?": "voce_aprende",
    "vc consegue guardar uma explicação pra usar depois?": "lembra",
    "to só o pó": "cansado", "dormi mal e tô acabado": "sono", "faz uns dias q não durmo direito": "sono",
    "tem algo q eu possa fazer pra dormir melhor?": "sono", "pq fico com sono mesmo depois de descansar?": "sono",
    "me sinto sem energia ultimamente": "cansado",
}
FORA = {
    "tenho medo de cobra kkk": "sentido contrário (não gostar)",
    "vc consegue reconhecer uma música pela letra?": "pergunta o que ele sabe fazer",
    "vc consegue analisar uma letra de música?": "pergunta o que ele sabe fazer",
    "me indica algo legal pra fazer no tempo livre": "não é filme, música, série nem livro",
    "dinheiro_bom:quitei uma dívida.": "erro de digitação no bruto (QuiteI); entra corrigida",
}
CORRIGIR = {"quitei uma dívida.": "Quitei uma dívida."}
SO_TREINO = {"n aguento mais isso kkk", "só queria ir embora logo", "voltei!!", "já to em casa", "finalmente de volta",
             "me dá uma luz aí", "fui bem hj", "meu cérebro travou legal"}
FICA_EM = {"to sem vontade": "estou_mal", "me dá uma força": "ajuda", "ei, me dá uma força": "ajuda",
           "me dá uma luz aí": "ajuda", "caraca!": "expressao_curta", "caraca": "expressao_curta"}


def _destino(situacao, fala):
    k = fala.casefold().strip()
    if k in FORA:
        return None, FORA[k]
    if k in FICA_EM:
        return FICA_EM[k], None
    if k in MOVER:
        return MOVER[k], None
    if situacao in ("bom_dia", "boa_tarde", "boa_noite") and not HORA.search(k):
        return "oi", None
    if situacao == "sem_sentido" and RISO.match(re.sub(r"[^\w\s]", "", k).strip() or "x"):
        return "risada", None
    if situacao == "ansioso_peito" and not CORPO.search(k):
        return "ansioso", None
    if situacao == "ajuda_socorro" and not URGENCIA.search(k):
        return "ajuda", None
    if situacao == "desisto_despedida" and not TCHAU.search(k):
        return "desisto", None
    if situacao in SOBRE_A_IA and len(k.split()) > 14:
        return None, "pergunta técnica ou filosófica longa"
    if situacao == "poema" and POEMA_TEMA.search(k):
        return None, "fase6"
    if situacao == "jogar_agora" and JOGO_ESPECIFICO.search(k):
        return None, "fase6"
    return situacao, None


def _blind(n):
    return int(hashlib.sha256(("gpt:" + n).encode()).hexdigest()[:8], 16) % 100 < PARTE_BLIND


def carregar():
    rel = {"bruto": 0, "fora": defaultdict(int), "fase6": [], "movidas": 0, "repetidas": 0, "por_situacao": {}}
    por = defaultdict(list)
    for p in PARTES:
        for s in json.loads(p.read_text(encoding="utf-8"))["situacoes"]:
            for f in s["falas"]:
                rel["bruto"] += 1
                f = fg.norm(f)
                f = CORRIGIR.get(f.casefold(), f)
                destino, motivo = _destino(s["situacao"], f)
                if destino is None:
                    if motivo == "fase6":
                        rel["fase6"].append(f)
                    else:
                        rel["fora"][motivo] += 1
                    continue
                rel["movidas"] += destino != s["situacao"]
                por[destino].append(f)
    formas = {}
    for situacao, falas in por.items():
        grupos, vistos = {}, set()
        for f in falas:
            k = fg.chave(f)
            if k in vistos:
                rel["repetidas"] += 1
                continue
            vistos.add(k)
            grupos.setdefault(fg.nucleo(f), []).append(f)
        treino, blind = [], []
        for n, g in grupos.items():
            (blind if _blind(n) and not any(x.casefold() in SO_TREINO for x in g) else treino).extend(g)
        if not blind and len(treino) >= 4:
            blind.append(treino.pop())
        formas[situacao] = {"treino": treino, "blind": blind}
        rel["por_situacao"][situacao] = (len(treino), len(blind))
    rel["fora"] = dict(rel["fora"])
    return formas, rel


if __name__ == "__main__":
    formas, rel = carregar()
    print(json.dumps({k: v for k, v in rel.items() if k not in ("por_situacao", "fase6")}, ensure_ascii=False, indent=1))
    print("fase6:", len(rel["fase6"]))
    for s, (t, b) in sorted(rel["por_situacao"].items()):
        print(f"{s:22s} treino {t:3d}  blind {b:3d}")
    print("total", sum(t for t, _ in rel["por_situacao"].values()), sum(b for _, b in rel["por_situacao"].values()))
