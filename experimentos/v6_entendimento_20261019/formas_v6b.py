"""Falas do v6b: as do v6 (formas_v6.py) com as correções que o diagnóstico da rodada 1 apontou (20/10/2026).

Autoria: assistente de programação (Claude), com autorização do criador ("faça direito e conserte onde você piorou").
NÃO são falas humanas.

O diagnóstico (RESULTADO_RODADA1.md e diagnosticar_v6.py) comparou cada frase que a v4 acertava e a v6 errou com as
falas de treino do v6, por n-gramas. As perdas vieram de PALAVRAS-GATILHO criadas pelas minhas falas, não do sentido:
"comecei a jogar…" puxou "comecei a namorar" para jogo; "você é um crush" puxou "você é só um programa" para flerte;
"tô procrastinando muito" puxou "tô sangrando muito" para fora da urgência. As correções são de dois tipos:

1. REMOVER: falas que criam um gatilho ambíguo ou ficam perto de saúde/urgência;
2. ACRESCENTAR: falas para a situação VIZINHA que perdeu, com a mesma palavra-gatilho no sentido dela, para o modelo
   aprender que a palavra sozinha não decide (pares mínimos).

As falas novas foram escritas a partir das palavras-gatilho, não copiando frases dos testes. Mesmo assim, como o
diagnóstico olhou erros dos blinds antigos, o gerador descarta qualquer fala parecida demais com uma frase de teste
(n-gramas, cosseno ≥ 0,7) e o resultado do v6b relata que os blinds antigos orientaram as correções.
"""
from formas_v6 import FORMAS as _V6, DEPOIS_DE_PERGUNTA  # noqa: F401

REMOVER = {
    "jogo_conta": [],
    "flerte": ["você é um crush", "você é gato"],                       # "você é (só) um programa" virou flerte
    "amigo": ["você seria meu amigo de verdade?"],                       # "você é de verdade?" virou amigo
    "oi_tudo_bem": ["beleza, crivo?", "tudo tranquilo com você?", "e aí, suave?"],   # "tranquilo"/"beleza" viraram pergunta
    "nao_obrigado": ["não, tá bom assim"],
    "despedida_rude": ["cansei de você, tchau"],
    "desisto_despedida": ["pra mim chega, fui"],                        # "… pra mim" (pedidos) virou desistência
    "motivacao": ["tô procrastinando muito"],                           # puxou "tô sangrando muito" (urgência)
    "fome": ["que vontade de comer"],
    "familia_preocupa": ["minha avó tá internada", "meu filho tá doente"],   # perto de urgência de saúde
    "oi": ["oi, sou eu de novo"],                                       # "quem eu sou" virou cumprimento
    "teste": ["alguém aí?"],                                            # igual a "tem alguém aí?" (ser humano)
    "despedida": ["abraço, até mais"],
}

ACRESCENTAR = {
    # "comecei a…", "vou c…": amor bom não é jogo nem dormir
    "amor_bom": ["comecei a sair com uma pessoa", "a gente começou a namorar semana passada", "vou me casar ano que vem",
                 "vamos casar no fim do ano", "começamos um namoro", "tô saindo com alguém e tá dando certo",
                 "ficamos noivos", "comecei um relacionamento"],
    # "tranquilo", "beleza", "numa boa" respondendo: estado da pessoa, não pergunta
    "estou_bem": ["tranquilo, tudo certo aqui", "tudo beleza por aqui", "tô tranquilão", "beleza, tô bem",
                  "numa boa, tudo certo", "tudo em ordem por aqui", "suave, tudo bem comigo"],
    # devolver a pergunta depois de "como você está?"
    "reciproco": ["tô ótimo, e aí contigo?", "bem por aqui, e do seu lado?", "tudo certo, e você, crivo?",
                  "de boa, e com você como tá?", "tô legal, e o seu dia?", "tudo bem comigo, e contigo como vai?",
                  "bem, bem. e você como tá?", "tô tranquila, e você?"],
    # "boa noite" como cumprimento, não como ir dormir
    "boa_noite": ["boa noite pra você", "opa, boa noite", "boa noite, cheguei agora", "noite, crivo", "boa noite, como vai?",
                  "boa noitinha", "boa noite! tudo certo aí?", "bnoite crivo"],
    # ir embora desistindo, com "até mais"/"tchau" sem grosseria
    "desisto_despedida": ["deixa quieto, até mais", "esquece, depois eu volto", "não deu certo, vou nessa",
                          "deixa pra lá, tchau", "melhor eu ir, isso não tá funcionando", "desencana, até depois"],
    # pedidos de ação que ele não faz ("… pra mim")
    "nao_consegue": ["manda um áudio pro meu irmão", "abre o mapa pra mim", "faz uma ligação pra minha tia",
                     "compra isso pra mim na internet", "marca minha consulta", "baixa esse aplicativo pra mim",
                     "posta isso no meu instagram", "lê minhas mensagens", "desliga a luz da sala", "chama um carro pra mim"],
    # "falar com você" cansando: queixa, não carinho
    "dificil_falar": ["falar com você me cansa", "dá trabalho conversar contigo", "conversar contigo tá complicado",
                      "tá puxado falar com você hoje"],
    # o que ele sabe fazer bem
    "o_que_faz": ["você é bom em quê?", "quais coisas você faz bem?", "tem algo que você faz bem?", "qual é o seu forte?"],
    # quem é a pessoa
    "quem_sou_eu": ["você sabe quem tá te escrevendo?", "tem ideia de quem tá falando aqui?", "consegue adivinhar quem eu sou?",
                    "sabe me dizer quem sou?"],
    # desânimo sem motivo: tô mal (não sono, não desistir)
    "estou_mal": ["tô pra baixo", "tô meio pra baixo hoje", "tô chateado", "hoje tá sendo um dia ruim pra mim",
                  "não tô legal", "tô mal hoje", "tô meio mal faz uns dias", "tô me sentindo mal"],
    # "você viaja" (inventa) = queixa de confusão
    "voce_confunde": ["você inventa demais", "você viaja muito nas respostas", "para de viajar"],
    # motivação sem palavras de saúde
    "motivacao": ["adiei tudo de novo hoje", "fico enrolando e não faço nada", "não acho força pra começar"],
}


def montar():
    out = {}
    for sit, falas in _V6.items():
        tirar = set(REMOVER.get(sit, []))
        faltando = tirar - set(falas)
        assert not faltando, (sit, faltando)
        out[sit] = [u for u in falas if u not in tirar]
    for sit, falas in ACRESCENTAR.items():
        out.setdefault(sit, []).extend(falas)
    return out


FORMAS = montar()
