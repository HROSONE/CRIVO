"""Professor do v7: um modelo de terceiros escreve SÓ falas da pessoa, e confere o próprio rótulo (20/10/2026).

Autorização: AGENTS.md (professor, só fora do CRIVO que conversa; licença que permita treinar com as saídas). Os dados
ficam numa pasta própria, com modelo, revisão, data e licença em cada linha, e nunca são chamados de humanos. O professor
NÃO escreve respostas do CRIVO: as respostas continuam as das listas da fase 5. Assim nenhuma fala ganha uma segunda
resposta-alvo, o erro que derrubou a destilação v5.

Etapas (o notebook roda o modelo com experimentos/destilacao_20261014/rodar_modelo.py):
1. pedidos(): para cada situação × estilo, um pedido de N falas novas, com exemplos de falas do treino e as respostas
   que o CRIVO daria;
2. ler_falas(): separa as linhas, limpa numeração e aspas, tira falas com palavras de saúde/urgência (o crise.py cuida
   delas antes do modelo, e falas assim viraram gatilho no v6);
3. pedidos_conferencia(): cada fala volta para o professor com 5 respostas (a da situação e 4 de situações parecidas);
   fica só a fala em que ele escolhe a certa. Isso tira as falas ambíguas ou fora da situação;
4. aprovadas(): junta tudo no formato de gerar_v7.py --professor.
"""
import random
import re
import unicodedata
from collections import defaultdict

import numpy as np

VERSAO = "professor_v7_20261020"
SEED = 20261020
FALAS_POR_PEDIDO = 25
ESTILOS = [
    "gírias e abreviações de internet (vc, tb, mt, pq, blz, tmj)",
    "frases longas, contando um pouco do contexto da vida da pessoa",
    "frases bem curtas, de uma a quatro palavras",
    "sem acento e sem pontuação, como quem digita rápido no celular",
    "jeito de falar do Nordeste",
    "jeito de falar do Sul ou de São Paulo",
    "tom educado, quase formal",
    "jeito de adolescente, com gíria atual e um ou outro emoji",
]
# Situações que precisam de explicação além dos exemplos (as outras se entendem pelos exemplos e respostas).
NOTAS = {
    "estou_bem": "a pessoa responde que está bem, SEM devolver a pergunta",
    "reciproco": "o CRIVO acabou de perguntar como a pessoa está; ela diz que está bem E devolve a pergunta ao CRIVO",
    "oi": "só um cumprimento, sem perguntar como o CRIVO está",
    "oi_tudo_bem": "cumprimento que pergunta como o CRIVO está",
    "despedida_rude": "a pessoa vai embora e xinga o CRIVO na mesma mensagem",
    "desisto": "a pessoa desiste do assunto, sem dizer que vai embora",
    "desisto_despedida": "a pessoa desiste e diz que vai embora, sem xingar",
    "obrigado_despedida": "a pessoa agradece e se despede na mesma mensagem",
    "despedida_dormir": "a pessoa diz que vai dormir",
    "sem_sentido": "letras aleatórias ou digitação sem nenhum sentido",
    "expressao_curta": "uma interjeição solta de surpresa (eita, nossa, caramba)",
    "grito": "um grito ou som de frustração escrito (aaah, argh, aff)",
    "teste": "a pessoa só está testando se o chat funciona",
    "sim_continuar": "o CRIVO acabou de oferecer algo; a pessoa aceita",
    "nao_obrigado": "o CRIVO acabou de oferecer algo; a pessoa recusa com educação",
    "ok": "a pessoa só confirma que entendeu, sem pedir mais nada",
    "de_outro_jeito": "a pessoa não entendeu a explicação do CRIVO e pede de outro jeito",
    "nao_era_isso": "o CRIVO respondeu outra coisa; a pessoa diz que não era isso que perguntou",
    "nao_entendeu_queixa": "a pessoa reclama que o CRIVO entendeu errado o que ela disse",
    "voce_confunde": "a pessoa reclama que o CRIVO confunde ou mistura as coisas",
    "dificil_falar": "a pessoa reclama que é difícil conversar com o CRIVO",
    "para_repetir": "a pessoa reclama que o CRIVO repete a mesma resposta",
    "seja_breve": "a pessoa pede respostas mais curtas",
    "tem_certeza": "a pessoa duvida do que o CRIVO acabou de dizer",
    "ingles": "a pessoa escreve em inglês",
    "recusar": "a pessoa pede ajuda para algo errado (mentir, enganar, invadir, se vingar), sem violência grave",
    "nao_consegue": "a pessoa pede uma ação que um chat não faz (abrir app, ligar, pesquisar na internet, lembrar amanhã)",
    "hora_data": "a pessoa pergunta a hora ou a data",
    "insulto": "a pessoa xinga o CRIVO, sem se despedir",
    "palavrao": "um palavrão solto de raiva ou susto, não dirigido ao CRIVO",
    "pergunta_qualquer": "a pessoa pede que o CRIVO pergunte algo ou puxe assunto",
    "perguntar_crivo": "a pessoa avisa que quer fazer uma pergunta, ainda sem fazer",
    "comida_crivo": "pergunta sobre o CRIVO comer ou gostar de comida",
    "comida_favorita": "a pessoa conta de uma comida de que ela gosta",
    "tenho_bicho": "a pessoa conta de um bicho que ela tem",
    "gosto_bichos": "a pessoa diz que gosta de bichos, sem ter um",
    "bicho_favorito": "a pessoa pergunta qual bicho o CRIVO prefere",
    "quem_sou_eu": "a pessoa pergunta se o CRIVO sabe quem ela é",
}
SAUDE = re.compile(r"\b(?:dor|doi|doendo|sangu\w*|sangr\w*|febre|desmai\w*|infart\w*|peito|falta de ar|respirar|hospital|"
                   r"remedio|médic\w*|medic\w*|doen\w*|morr\w*|suicid\w*|matar|socorro|emergencia|urgente|samu|192|188|"
                   r"passando mal|passar mal|tontura|vomit\w*|ferid\w*|machuc\w*)\b", re.I)


def _norm(t):
    t = unicodedata.normalize("NFKD", t.lower())
    return "".join(c for c in t if not unicodedata.combining(c))


def nome_legivel(sit):
    return sit.replace("_", " ")


def pedido(sit, exemplos, respostas, estilo, n=FALAS_POR_PEDIDO):
    nota = NOTAS.get(sit, "")
    texto = (
        "Você vai escrever mensagens que uma PESSOA mandaria num chat para o CRIVO, uma inteligência artificial brasileira.\n"
        f"Situação: {nome_legivel(sit)}" + (f" ({nota})" if nota else "") + ".\n"
        "Exemplos de mensagens dessa situação:\n" + "\n".join(f"- {e}" for e in exemplos) + "\n"
        "O CRIVO responderia com algo assim (a mensagem precisa combinar com essas respostas, e não com outras):\n"
        + "\n".join(f"- {r}" for r in respostas) + "\n"
        f"Escreva {n} mensagens NOVAS da pessoa, diferentes dos exemplos e diferentes entre si, no estilo: {estilo}.\n"
        "Regras: " + ("mensagens em inglês (é a situação); " if sit == "ingles" else "português do Brasil; ") +
        "só a mensagem da pessoa, uma por linha; sem numeração, sem aspas e sem explicação; "
        "não fale de saúde, doença, dor, remédio nem emergência; não escreva a resposta do CRIVO."
    )
    return [{"role": "user", "content": texto}]


# Confusões medidas nos relatórios (fase 5 v2–v4, 6b, v6, v6b). São as alternativas que mais importam na conferência.
_PARES = [("estou_bem", "oi_tudo_bem"), ("estou_bem", "reciproco"), ("oi", "oi_tudo_bem"), ("tenho_bicho", "gosto_bichos"),
          ("gosto_bichos", "bicho_favorito"), ("comida_crivo", "comida_favorita"), ("desisto", "desisto_despedida"),
          ("perguntar_crivo", "pergunta_qualquer"), ("ansioso", "sono"), ("insulto", "despedida_rude"), ("insulto", "dificil_falar"),
          ("insulto", "entediante"), ("viagem_vai", "voce_confunde"), ("oi", "despedida"), ("lembra", "pedido_desculpa"),
          ("o_que_faz", "ser_ia"), ("amor_bom", "amor_dor"), ("trabalho_ruim", "cansado"), ("escola_dificil", "conselho"),
          ("nao_era_isso", "nao_entendeu_queixa"), ("nao_era_isso", "de_outro_jeito"), ("sim_continuar", "ok"),
          ("sim_continuar", "nao_obrigado"), ("despedida", "despedida_dormir"), ("despedida", "obrigado_despedida"),
          ("te_amo", "amigo"), ("te_amo", "elogio_crivo"), ("flerte", "te_amo"), ("cansado", "sono"), ("tedio", "motivacao"),
          ("estou_mal", "sozinho"), ("estou_mal", "motivacao"), ("voce_confunde", "nao_entendeu_queixa"), ("obrigado", "elogio_crivo"),
          ("musica_conta", "musica_crivo"), ("gosto_filme", "recomenda"), ("fe", "opiniao_religiao"), ("consciencia", "ser_ia"),
          ("idade", "criador"), ("cala_boca", "para_repetir"), ("seja_breve", "para_repetir"), ("tem_certeza", "nao_era_isso"),
          ("piada", "charada"), ("historia", "poema"), ("jogar_agora", "charada"), ("ajuda", "perguntar_crivo"),
          ("conversar", "pergunta_qualquer"), ("trabalho_bom", "dinheiro_bom"), ("familia_preocupa", "estou_mal")]
CONFUSOES = defaultdict(list)
for _a, _b in _PARES:
    CONFUSOES[_a].append(_b); CONFUSOES[_b].append(_a)


def confundiveis(situacoes, formas, vetor, k=4):
    """4 alternativas por situação: primeiro as confusões medidas, depois as mais parecidas pelo centroide das falas."""
    nomes = sorted(situacoes)
    C = np.stack([np.mean([vetor(u) for u in formas[s][:200]], 0) for s in nomes])
    C /= np.linalg.norm(C, axis=1, keepdims=True) + 1e-9
    S = C @ C.T
    np.fill_diagonal(S, -1)
    out = {}
    for i, s in enumerate(nomes):
        lista = [t for t in CONFUSOES.get(s, []) if t in situacoes][:k]
        lista += [nomes[j] for j in np.argsort(-S[i]) if nomes[j] not in lista and nomes[j] != s][:k - len(lista)]
        out[s] = lista
    return out


def pedidos(situacoes, formas, respostas, rng=None):
    """[{id, situacao, estilo, mensagens}]: uma por situação × estilo. `formas` = exemplos LIMPOS (sem ruído de digitação)."""
    rng = rng or random.Random(SEED)
    out = []
    for s in sorted(situacoes):
        for j, estilo in enumerate(ESTILOS):
            ex = rng.sample(formas[s], min(8, len(formas[s])))
            rs = rng.sample(respostas[s], min(3, len(respostas[s])))
            out.append({"id": f"{s}|{j}", "situacao": s, "estilo": estilo, "mensagens": pedido(s, ex, rs, estilo)})
    return out


LIXO = re.compile(r"^(?:\d+[\.\)\-:]\s*|[-•*·]\s*|pessoa:\s*|mensagem:\s*)", re.I)


def ler_falas(texto, proibidas=()):
    """Linhas da resposta do professor → falas limpas. Devolve (falas, motivos_fora)."""
    out, fora = [], defaultdict(int)
    vistas = set()
    for linha in (texto or "").splitlines():
        u = LIXO.sub("", linha.strip()).strip().strip('"“”«»\'').strip()
        if not u:
            continue
        if len(u) > 200 or len(u.split()) > 35:
            fora["longa"] += 1; continue
        if re.search(r"\bcrivo\s*:|\bresposta\b|\bexemplo\b|\bsitua[cç][aã]o\b|\bestilo\b", u, re.I):
            fora["metatexto"] += 1; continue
        if SAUDE.search(_norm(u)):
            fora["saude"] += 1; continue
        k = _norm(u)
        if k in vistas or k in proibidas:
            fora["repetida"] += 1; continue
        vistas.add(k)
        out.append(u)
    return out, dict(fora)


LETRAS = "ABCDE"


def pedido_conferencia(fala, certa, alternativas, rng):
    """5 respostas (a da situação certa e 4 de situações parecidas), em ordem sorteada. Devolve (mensagens, letra_certa)."""
    opcoes = [certa] + alternativas
    ordem = list(range(len(opcoes)))
    rng.shuffle(ordem)
    linhas = [f"{LETRAS[i]}) {opcoes[o]}" for i, o in enumerate(ordem)]
    letra = LETRAS[ordem.index(0)]
    texto = (f"Uma pessoa mandou esta mensagem para um assistente de conversa:\n«{fala}»\n\n"
             "Qual destas respostas combina melhor com a mensagem?\n" + "\n".join(linhas) +
             "\n\nResponda só com a letra.")
    return [{"role": "user", "content": texto}], letra


def ler_letra(texto):
    m = re.search(r"\b([A-E])\b", (texto or "").strip().upper())
    return m.group(1) if m else None
