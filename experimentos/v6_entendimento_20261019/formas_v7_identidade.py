"""Falas v7b: identidade (20/10/2026).

No v7, as situações de identidade ficaram sem falas novas e caíram 1 ponto (e "robo" caiu 62 → 48). Aqui ganham falas
novas, com as respostas que já são as delas: as do IDENTIDADE.md (extras_fase6b.RESPOSTAS), como na 6b v4. As chaves são
as situações da fase 5 que o IDENTIDADE.md cobre (extras_fase6b.FASE5_SUBSTITUIDAS); a régua já aceita essas respostas.

Autoria: assistente de programação (Claude), com autorização do criador. NÃO são falas humanas.
"""
# situação da fase 5 → grupos de resposta do IDENTIDADE.md (extras_fase6b.RESPOSTAS)
RESPOSTAS_DE = {"quem_e": ["quem"], "nome_crivo": ["quem"], "ser_humano": ["pessoa", "humano"], "robo": ["robo"],
                "sente": ["sentir"]}

F = {}
F["quem_e"] = [
    "me diz quem você é", "você é o quê, afinal?", "quem é esse que tá falando comigo?", "pode se apresentar?",
    "conta um pouco sobre você", "quem é você, crivo?", "que tipo de coisa você é?", "como você se descreveria em uma frase?",
    "quem é o crivo?", "me explica o que é você", "você é quem mesmo?", "se apresenta aí",
]
F["nome_crivo"] = [
    "como é seu nome?", "qual é o teu nome?", "você tem um nome?", "te chamam de quê?", "como eu te chamo?",
    "qual o nome dessa ia?", "tu se chama como?", "como posso te chamar?",
]
F["ser_humano"] = [
    "tem uma pessoa do outro lado?", "você é gente de verdade?", "você é humano ou máquina?", "é alguém digitando aí?",
    "você é uma pessoa real?", "quem responde é humano?", "você existe de verdade?", "você é de carne e osso?",
    "tô falando com uma pessoa?", "tem humano aí?",
]
F["robo"] = [
    "você não passa de um robô", "você é só uma máquina de responder", "você é um robozinho", "isso aqui é só um bot",
    "você é só um programa de computador", "você é um robô qualquer", "no fim você é só código", "você é uma máquina, né",
    "robozinho", "você é só um bot mesmo",
]
F["sente"] = [
    "você tem emoções de verdade?", "você consegue sentir alegria?", "você fica chateado?", "você sente saudade?",
    "você sente raiva?", "você tem sentimentos de verdade?", "você fica feliz quando alguém conversa contigo?",
    "você se emociona?",
]
