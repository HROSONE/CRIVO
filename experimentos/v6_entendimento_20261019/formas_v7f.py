"""Falas da v7f (06/11/2026): os casos que reprovaram o 300M v7c, no formato em que ele errou.

Origem: escritas pelo assistente de programação (Claude), com autorização do criador; não são humanas.
As respostas vêm das listas existentes (dados_v7c), nunca daqui.

- RECIPROCO_2T: a pessoa devolve a pergunta DEPOIS de o Crivo cumprimentar (o v7c repetia a saudação).
- QUEIXA_2T: a pessoa reclama da resposta anterior, com e sem erro de digitação (o v7c tratava como desabafo).
- INSULTO: insulto com palavrão (o v7c caía no "Respira!" do palavrão).
- NUNCA_ENSINARAM: pergunta do dia a dia sem fato no contexto (o v7c caía em cenas de saúde ou clima).
- QUEM_E: "como você se descreveria" e parecidas (o v7c respondia como "o que acha de mim").
"""
SAUDACOES = ["eae tudo bem", "oi td bem?", "e aí, beleza?", "opa, tudo certo?", "olá, como vai?", "oi crivo, tudo bem?",
             "bom dia, tudo bem?", "e ai blz", "salve, tudo certo?", "oi, como você está?"]
PERGUNTAS_ANTES = ["como faz pra economizar no mercado?", "o que é fotossíntese?", "me fala sobre o sistema solar",
                   "qual a capital do canadá?", "como eu organizo minha semana?", "o que significa empatia?",
                   "me explica o que é inflação", "qual o maior planeta?"]
F = {
    "cena:reciproco": ["legal e vc?", "tô bem e vc", "bem tb, e tu?", "td certo, e contigo?", "suave, e vc?",
                       "tô ótimo e você?", "de boa, e aí vc?", "bem graças a deus e vc?", "tranquilo, e você?",
                       "beleza, e tu como tá?", "to bem sim e vc", "melhor agora, e vc?", "tudo ótimo por aqui, e com você?",
                       "bem demais, e vc como tá?"],
    "cena:nao_era_isso": ["não perguntei isso", "nao foi isso q eu perguntei", "não era isso", "n foi isso que eu quis dizer",
                          "pera, não perguntei isso não", "nao perguntei isso kkk", "naoo, n era isso",
                          "não é isso que eu falei", "nada a ver com o que eu perguntei", "nao pergunteio isso nao"],
    "cena:nao_entendeu_queixa": ["vc não entendeu", "isso não responde nada", "cadê a resposta?", "e a resposta?",
                                 "vc nao entendeu oq eu falei", "não entendeu nada né", "cade a resposta certa?",
                                 "você não respondeu minha pergunta", "nao respondeu o que eu perguntei"],
    "cena:insulto": ["vc é burro demais porra", "que merda de resposta", "caralho, vc não entende nada",
                     "porra crivo, que resposta ruim", "vc é inútil pqp", "resposta lixo mano", "que bosta, hein",
                     "tá uma merda isso aí", "puta que pariu, que resposta horrível"],
    "cena:nunca_ensinaram": ["como faço arroz?", "por que o céu é azul?", "me dá uma dica pra estudar melhor",
                             "como troco o pneu do carro?", "qual a receita de bolo de cenoura?", "como funciona um motor de carro?",
                             "por que o mar é salgado?", "quem inventou a lâmpada?", "como se planta tomate?",
                             "como faço pra aprender a nadar?", "quanto tempo leva pra ferver um ovo?", "como funciona a internet?"],
    "cena:quem_e": ["como você se descreveria?", "como vc se descreve?", "se descreve pra mim", "me fala como você é",
                    "quem é você de verdade?", "como você se definiria?", "me conta quem você é", "descreve você mesmo"],
}
# Situações que vêm DEPOIS de um turno do Crivo, e qual turno anterior faz sentido.
DEPOIS_DE = {"cena:reciproco": "saudacao", "cena:nao_era_isso": "pergunta", "cena:nao_entendeu_queixa": "pergunta",
             "cena:insulto": "pergunta"}
