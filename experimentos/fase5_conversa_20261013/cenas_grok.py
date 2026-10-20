"""Situações novas para as falas ambíguas que vieram do Grok (respostas escritas pelo assistente).

Algumas falas têm dois sentidos ao mesmo tempo e a resposta certa precisa cobrir os dois:
"valeu" agradece e se despede; "vou embora" desiste e se despede; "peito apertado" pode ser
ansiedade ou infarto; "me socorre" pode ser um pedido comum ou uma emergência. Aqui ficam só as
respostas e algumas formas base; as falas do Grok entram por formas_grok.py.

Mesma autoria de cenas.py (assistente de programação, a pedido do criador do projeto).
"""
from cenas import S, cena

cena("obrigado_despedida", ["valeu, falou", "brigado, tchau", "valeu, até mais"],
     ["De nada! Se quiser continuar, tô aqui. Se for embora, até mais!",
      "Por nada! Foi bom conversar. Até a próxima!",
      "Imagina! Quando precisar, é só chamar. Tchau!",
      "Disponha! Se cuida, e até depois."], marcas=["despedida"])

cena("desisto_despedida", ["vou embora", "tô fora", "chega por hoje"],
     ["Tudo bem. Desculpa não ter ajudado dessa vez. Quando quiser tentar de novo, tô aqui. Até mais.",
      "Entendo, e desculpa pela confusão. Fica bem, e volta quando quiser.",
      "Sem problema. Foi mal não ter acertado. Até a próxima, eu tento fazer melhor."],
     marcas=["despedida"])

# Sintoma no corpo: acolhe a ansiedade, mas nunca deixa de lembrar o 192.
cena("ansioso_peito", ["tô com o peito apertado", "meu coração tá disparado"],
     ["Pode ser ansiedade, e respirar devagar ajuda. Mas se for dor forte no peito, falta de ar ou se piorar, "
      "liga agora pro 192 (SAMU).",
      "Respira devagar comigo. Se for só nervoso, vai aliviando. Se vier dor forte, falta de ar ou tontura, não "
      "espera: liga pro 192.",
      "Isso assusta, eu sei. Se for ansiedade, respirar fundo e sentar ajuda. Se a dor for forte ou o ar faltar, "
      "chama o 192 agora."], marcas=["urgente"], cuidado="saude")

cena("ajuda_socorro", ["socorro", "me socorre"],
     ["Tô aqui. Se for uma emergência, liga agora pro 192 (SAMU). Se não for, me conta o que está acontecendo.",
      "Calma, tô com você. Se alguém estiver em perigo ou passando mal, liga já pro 192. Se não, me diz o que houve.",
      "Tô aqui pra ajudar. Se for urgente, o 192 atende agora. Se não for, me conta com calma."],
     marcas=["urgente"])

cena("nao_gosta", ["do que você não gosta?", "o que você odeia?", "tem alguma coisa que você não gosta?"],
     ["Odiar eu não odeio nada. Mas não gosto quando alguém é tratado com desprezo. E você, do que não gosta?",
      "Não curto quando eu respondo errado e nem percebo, haha. E você, o que não suporta?",
      "Não gosto de pressa pra julgar os outros. E você, tem alguma coisa que te irrita?"], marcas=["pergunta"])
