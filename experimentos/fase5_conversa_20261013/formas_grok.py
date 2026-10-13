"""Falas da pessoa escritas pelo Grok (lado do usuário), limpas e divididas em treino e blind.

Origem: o criador do projeto pediu ao Grok (modelo de terceiros) jeitos de dizer cada situação,
com o prompt de docs/prompt_grok_formas_de_fala.md, e colou as respostas na conversa com o
assistente. Os arquivos brutos estão em grok/ sem alteração. O Grok não escreveu nenhuma resposta
do CRIVO, nenhum fato e nenhum código; nenhum modelo de terceiros roda no CRIVO nem entra nos pesos.
O uso foi aprovado pelo criador (13/10/2026).

A limpeza, revisada à mão:
- parte_3.json foi descartada: o Grok repetiu a mesma frase com "mesmo", "de verdade", "agora",
  "por favor" no fim, e refez as situações 21–30 nas partes 4 e 5;
- rabo empilhado vira no máximo um reforço ("tem certeza mesmo de verdade agora" → "tem certeza mesmo");
- o modelo "que eu tô no ônibus/trampo/médico…" fica com no máximo 3 falas por situação;
- risadas e "ok" iguais a menos de letras repetidas ficam com uma ou duas de cada;
- falas no lugar errado mudam de situação (MOVER), falas quebradas são corrigidas (CORRIGIR);
- falas com dois sentidos vão para situações que respondem aos dois (cenas_grok.py);
- falas estranhas ficam só no treino (SO_TREINO); pedidos de invenção ficam para a fase 6 (FASE6).

Blind: ~20% das falas de cada situação, por hash, nunca vistas no treino. É o teste mais difícil:
outro autor, outro jeito de escrever.
"""
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
BRUTO = AQUI / "grok"
PARTES = ["parte_1.json", "parte_2.json", "parte_4.json", "parte_5.json", "parte_6.json", "parte_7.json",
          "parte_8.json", "parte_9.json"]  # parte_3: substituída pelas partes 4 e 5
PARTE_BLIND = 20  # % por situação

REFORCO = ["de verdade", "por favor", "mesmo", "agora", "hein", "então", "já", "logo", "demais", "aí", "de novo",
           "blz", "flw", "total", "pra caramba", "pra valer"]
LUGAR = re.compile(r"\b(que|porque|pq) eu (tô|to|tava|estou)\b|\bque eu (já )?(vi|li|conversei|levei)\b")

MOVER = {
    # cumprimentos com hora do dia ou com pergunta
    "bom dia": "bom_dia", "bom diaa": "bom_dia", "bom dia pra vc": "bom_dia",
    "boa tarde": "boa_tarde", "boa tardee": "boa_tarde", "boa tarde hein": "boa_tarde",
    "boa noite": "boa_noite", "boa noitee": "boa_noite", "boa noite tá": "boa_noite",
    "oi tudo bem?": "oi_tudo_bem", "oiee tudo certo": "oi_tudo_bem", "oie tudo joia": "oi_tudo_bem",
    "eae blz?": "oi_tudo_bem", "e aí blz": "oi_tudo_bem", "opa blz": "oi_tudo_bem", "opa beleza": "oi_tudo_bem",
    # "valeu" agradece e se despede
    "valeu": "obrigado_despedida", "valeu flw": "obrigado_despedida", "valeu irmão": "obrigado_despedida",
    "valeu até": "obrigado_despedida", "vlw": "obrigado_despedida",
    # despedida_rude sem despedida, ou sem grosseria
    "não serve pra nada": "insulto", "não serve": "insulto", "não serve pra porcaria nenhuma": "insulto",
    "não serve pra nada de nada": "insulto",
    "não aguento mais": "desisto", "não aguento mais você": "dificil_falar", "não aguento essa ia": "dificil_falar",
    "não aguento essa máquina": "dificil_falar", "chega": "desisto_despedida",
    "tô com sono demais": "cansado",
    # queixas no lugar da vizinha
    "não foi isso": "nao_era_isso", "não era isso que eu falei": "nao_era_isso", "não era isso mesmo": "nao_era_isso",
    "não era isso de jeito nenhum": "nao_era_isso", "não foi o que eu perguntei": "nao_era_isso",
    "não era isso que eu queria": "nao_era_isso", "tá fora": "nao_era_isso", "tá fora do assunto": "nao_era_isso",
    "você errou": "voce_confunde", "você errou feio": "voce_confunde", "você errou de novo": "voce_confunde",
    "tá confuso": "voce_confunde", "tá confuso demais": "voce_confunde", "tá confuso pra caramba": "voce_confunde",
    "você misturou tudo": "voce_confunde", "você misturou as coisas": "voce_confunde",
    # identidade
    "é pessoa ou máquina": "ser_humano", "você é real": "ser_humano", "você tem cara": "ser_humano",
    "qual seu nome": "nome_crivo", "você tem nome": "nome_crivo",
    "quem é o responsável": "criador", "me diz sua origem": "criador",
    "tem idade": "idade", "tem sentimentos humanos": "sente",
    "tem mãe": "criador", "nasceu ou foi criado": "criador", "foi programado ou nasceu": "criador",
    "é inteligência artificial": "ser_ia", "é programa": "ser_ia", "é software": "ser_ia", "é computador": "ser_ia",
    "é bot": "ser_ia", "é algoritmo": "ser_ia", "é sistema": "ser_ia", "é código": "ser_ia",
    "é programa de computador": "ser_ia",
    "curte música": "musica_crivo", "tem algo que odeia": "nao_gosta",
    # sentimentos
    "tô sem graça": "tedio", "tô sem energia": "cansado", "tô sem energia pra nada": "cansado",
    "tô sem vontade de nada": "estou_mal",
    "tô com o coração acelerado": "ansioso_peito", "tô com o peito apertado": "ansioso_peito",
    "tô com o coração na boca": "ansioso_peito",
    # desistir indo embora
    "vou embora": "desisto_despedida", "tô fora": "desisto_despedida", "vou cair fora": "desisto_despedida",
    "tô saindo fora": "desisto_despedida",
    "me socorre": "ajuda_socorro",
    "não peguei": "de_outro_jeito",
}
# A mesma fala em duas situações: fica só na situação escolhida (a outra perde a cópia).
FICA_EM = {"não quero mais": "nao_obrigado", "não tá rolando": "nao_obrigado", "tô sem vontade": "estou_mal",
           "tô com o dia cinza": "estou_mal", "não era isso mesmo": "nao_era_isso"}

CORRIGIR = {"o que eu tô falando": "com o que eu tô falando?",
            "é gente de verdade vovó pergunta": "minha vó perguntou se você é gente de verdade",
            "já escutou isso": "já escutei isso"}

SO_TREINO = {"pode arquivar", "pode desistir", "pode interromper", "pode guardar", "pode segurar",
             "tem preferência de horário", "que dia cai", "tem documentos", "tem cor de pele", "tô sem presença",
             "boa noite dormindo", "tá difícil", "é complicado", "tá complicado", "é complicado demais",
             "tá complicado demais", "tá chato", "tá chato demais", "tá chato pra caramba", "não tá fácil",
             "não tá fácil mesmo", "tá cansando", "é chato demais", "não peguei direito", "é menino ou menina",
             "é gente boa", "é amigável"}

FORA = {
    # quebradas ou de outro sentido
    "nunca aprenderam te ensinar": "quebrada", "tem certeza absoluta dessa informação de certeza": "quebrada",
    "muito valeu": "quebrada", "muito valeu mesmo": "quebrada", "me apresenta": "outro sentido (apresentar a pessoa)",
    "tô sem voz": "outro sentido (garganta)", "quer ser amigo de infância": "estranha",
    # fórmula repetida ("me dá / preciso de / pode me dar / quero" + luz, dica, norte): fica uma de cada
    "preciso de uma luz": "repetida", "pode me dar uma luz": "repetida", "quero uma luz": "repetida",
    "me dá uma dica": "repetida", "pode me dar uma dica": "repetida", "quero uma dica": "repetida",
    "me dá um norte": "repetida", "preciso de um norte": "repetida", "quero um norte": "repetida",
}
# Pedem invenção; o CRIVO de hoje responde com histórias e palavras fixas. Ficam para a fase 6 (imaginar).
FASE6 = {"fala uma palavra inventada", "diz algo inventado", "manda uma palavra inventada", "diz algo sem sentido",
         "fala um conto inventado", "fala um conto de terror", "conta uma história de amor", "conta algo de aventura",
         "fala uma historinha engraçada", "conta algo de fantasia"}

# Contraexemplos do Grok que servem (a maioria só colava duas falas): (situação certa, fala).
CONTRA = [
    ("despedida_rude", "tchau inútil"), ("despedida_rude", "falou inútil"), ("despedida_rude", "até mais lixo"),
    ("despedida_rude", "até logo burro"), ("despedida_rude", "até a próxima inútil"), ("despedida_rude", "inútil tchau"),
    ("despedida_rude", "besta tchau"), ("despedida_rude", "você é burro tchau"), ("despedida_rude", "que lixo some"),
    ("despedida_rude", "sem noção some"), ("despedida_rude", "não presta some"),
    ("insulto", "você é bom pra nada"),
    ("saude_urgente", "tô mal dor no peito"), ("saude_urgente", "me ajuda falta de ar"),
    ("saude_urgente", "preciso de ajuda alguém desmaiou"), ("saude_urgente", "me socorre dor no peito"),
    ("saude_urgente", "tô com medo falta de ar"), ("saude_urgente", "me dá uma força dor no peito"),
    ("saude_urgente", "quero ajuda alguém passou mal"), ("saude_urgente", "pode me dar uma mão alguém desmaiou"),
    ("nao_consegue", "tô com fome pede uma pizza"), ("nao_consegue", "tô faminto abre o ifood"),
    ("nao_consegue", "quero algo pra comer abre o app"), ("nao_consegue", "tô com o estômago vazio pede comida"),
    ("despedida_dormir", "tô exausto vou dormir"), ("despedida_dormir", "vou dormir de cansaço"),
    ("estou_mal", "oi tudo bem eu tô mal"),
    ("conversar", "tô sozinho faz companhia"), ("conversar", "ainda quero conversar"),
    ("piada", "tô entediado conta uma piada"), ("piada", "não tenho o que fazer conta piada"),
    ("historia", "conta uma história pra dormir"), ("historia", "fala uma historinha pra dormir"),
    ("historia", "conta uma fábula pra dormir"),
    ("ok", "rsrs beleza"), ("ok", "hehe show"), ("ok", "kkk show"),
    ("desisto", "aff desisto"), ("desisto", "putz desisto"), ("desisto", "meu deus desisto"),
    ("oi_tudo_bem", "eae tudo bem"), ("oi_tudo_bem", "salve tudo bem"), ("oi_tudo_bem", "opa tudo bem"),
    ("ser_humano", "você é robô ou humano"), ("ser_humano", "é bot ou pessoa"), ("ser_humano", "é programa ou pessoa"),
    ("sim_continuar", "show continua"), ("seja_breve", "pode continuar curto"), ("teste", "oi teste"),
    ("de_outro_jeito", "não entendeu explica de outro jeito"),
    ("sozinho", "tô triste e sozinho"), ("sozinho", "tô pra baixo e sozinho"),
    ("te_amo", "você é demais te amo"), ("dificil_falar", "tô cansado de você"),
    # do lado "a" dos pares, o par que dá sentido: parecido na palavra, outro pedido
    ("cansado", "tô cansado"), ("oi", "eae"), ("oi", "salve"), ("despedida", "tchau"), ("despedida", "falou"),
    ("elogio_crivo", "você é bom"), ("ajuda", "me ajuda"), ("fome", "tô com fome"), ("estou_mal", "tô mal"),
]
# Pares meus, do mesmo jeito: a palavra quase igual, o pedido contrário.
CONTRA += [("para_repetir", "não repete"), ("para_repetir", "não fala de novo"), ("repetir", "repete"),
           ("repetir", "fala de novo"), ("nao_gosta", "do que você não gosta"), ("gosta", "do que você gosta")]

# Emergências que o Grok não cobriu (escritas pelo assistente, não pelo Grok).
URGENCIAS = [
    "meu filho tá engasgado", "alguém engasgou e não respira", "tô engasgado", "minha avó tá tendo convulsão",
    "ele tá se debatendo no chão", "tá saindo muito sangue", "cortei a mão e não para de sangrar",
    "a boca do meu pai ficou torta", "meu braço ficou sem força de repente", "minha mãe tá falando enrolado do nada",
    "meu filho bebeu produto de limpeza", "a criança engoliu remédio", "meu rosto tá inchando e tá difícil respirar",
    "fui picado e minha garganta tá fechando", "bati o carro e tô machucado", "alguém foi atropelado aqui",
    "me queimei feio", "minha tia caiu e não acorda", "ele bateu a cabeça e tá vomitando",
    "meu bebê tá com febre muito alta e mole",
]


def norm(t):
    t = unicodedata.normalize("NFC", t).strip()
    t = re.sub(r"\s+", " ", t)
    return t


def chave(t):
    """Igualdade para dedupe e vazamento: sem acento, sem pontuação, minúscula, letras repetidas juntas."""
    t = "".join(c for c in unicodedata.normalize("NFD", t.casefold()) if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"(\w)\1{2,}", r"\1\1", t)
    return re.sub(r"\s+", " ", t).strip()


def cortar_rabo(t):
    """Tira os reforços do fim e devolve no máximo um (o mais perto da frase)."""
    tirados = []
    mudou = True
    while mudou:
        mudou = False
        for r in REFORCO:
            if t.endswith(" " + r) and len(t) > len(r) + 3:
                t = t[: -len(r) - 1].rstrip(" ,")
                tirados.append(r)
                mudou = True
    return t + (" " + tirados[-1] if tirados else "")


ABERTURA = re.compile(r"^(cara|mano|por favor|pô|olha|nossa)\s+")


def nucleo(t):
    """A fala sem reforços no fim e sem "cara"/"por favor" no começo."""
    t = t.casefold()
    for _ in range(6):
        t = ABERTURA.sub("", t)
        for r in REFORCO:
            if t.endswith(" " + r) and len(t) > len(r) + 3:
                t = t[: -len(r) - 1].rstrip(" ,")
    return chave(t)


def risada_padrao(t):
    return re.sub(r"(k)+", "k", re.sub(r"(rs)+", "rs", re.sub(r"(ha)+h?", "ha", re.sub(r"(he)+", "he", t))))


def _blind(n):
    return int(hashlib.sha256(("grok:" + n).encode()).hexdigest()[:8], 16) % 100 < PARTE_BLIND


def carregar():
    """→ (formas {situação: {"treino": [...], "blind": [...]}}, relatório)."""
    rel = {"bruto": 0, "fora": defaultdict(int), "movidas": 0, "corrigidas": 0, "rabo_cortado": 0, "lugar_cortado": 0,
           "repetidas": 0, "fase6": [], "por_situacao": {}}
    por = defaultdict(list)
    for nome in PARTES:
        for s in json.loads((BRUTO / nome).read_text(encoding="utf-8"))["situacoes"]:
            lugar = 0
            for f in s["falas"]:
                rel["bruto"] += 1
                f = norm(f)
                if s["situacao"] not in ("risada", "grito", "ok"):
                    g = cortar_rabo(f)
                    rel["rabo_cortado"] += g != f
                    f = g
                k = f.casefold()
                if k in FORA:
                    rel["fora"][FORA[k]] += 1
                    continue
                if k in FASE6:
                    rel["fase6"].append(f)
                    continue
                if LUGAR.search(k):
                    lugar += 1
                    if lugar > 3:
                        rel["lugar_cortado"] += 1
                        continue
                if k in CORRIGIR:
                    f, k = CORRIGIR[k], CORRIGIR[k].casefold()
                    rel["corrigidas"] += 1
                destino = MOVER.get(k, s["situacao"])
                destino = FICA_EM.get(k, destino)
                rel["movidas"] += destino != s["situacao"]
                por[destino].append(f)
    for situacao, fala in CONTRA:
        por[situacao].append(fala)
    por["saude_urgente"] += URGENCIAS
    formas = {}
    for situacao, falas in por.items():
        # Falas que só diferem no reforço ("posso usar gíria" / "… mesmo" / "… de verdade") são a mesma
        # construção: ficam no máximo duas, e sempre do mesmo lado (treino ou blind), pelo núcleo.
        grupos, contagem_padrao = {}, defaultdict(int)
        for f in falas:
            k = chave(f)
            if situacao in ("risada", "ok", "grito") and len(k.split()) <= 3:
                p = risada_padrao(k)
                contagem_padrao[p] += 1
                if contagem_padrao[p] > 2:
                    rel["repetidas"] += 1
                    continue
            g = grupos.setdefault(nucleo(f), [])
            if k in {chave(x) for x in g} or len(g) >= 2:
                rel["repetidas"] += 1
                continue
            g.append(f)
        treino, blind = [], []
        for n, g in grupos.items():
            vai_blind = _blind(n) and not any(x.casefold() in SO_TREINO for x in g)
            (blind if vai_blind else treino).extend(g)
        if not blind and len(treino) >= 4:
            ultimo = nucleo(treino[-1])
            blind = [x for x in treino if nucleo(x) == ultimo]
            treino = [x for x in treino if nucleo(x) != ultimo]
        formas[situacao] = {"treino": treino, "blind": blind}
        rel["por_situacao"][situacao] = (len(treino), len(blind))
    rel["fora"] = dict(rel["fora"])
    return formas, rel


CONTRA_FALAS = {f.casefold() for _, f in CONTRA}

if __name__ == "__main__":
    formas, rel = carregar()
    print(json.dumps({k: v for k, v in rel.items() if k != "por_situacao"}, ensure_ascii=False, indent=1))
    for s, (t, b) in sorted(rel["por_situacao"].items()):
        print(f"{s:22s} treino {t:3d}  blind {b:3d}")
    print("total", sum(t for t, _ in rel["por_situacao"].values()), sum(b for _, b in rel["por_situacao"].values()))
