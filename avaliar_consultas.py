"""Sonda de desenvolvimento de consultas, fixada antes do novo motor.

Mede respostas reais (inclusive histórico e recusas), não um teste cego
de inteligência. Não adiciona perguntas ou fatos ao conhecimento.
"""
import json

from crivo import Crivo


CASOS = [
    ([], "Quem orbita a Terra?", "logica:consulta", ["Lua"], []),
    ([], "Quem orbita o Sol?", "logica:consulta", ["Terra", "Marte"], ["Lua"]),
    ([], "O que faz parte do Sistema Solar?", "logica:consulta", ["Sol", "Terra", "Lua"], ["Via Láctea"]),
    ([], "Quais animais têm penas?", "logica:consulta", ["pinguim", "tucano"], ["gato"]),
    ([], "Quais animais são vertebrados e têm penas?", "logica:consulta", ["pinguim", "tucano"], ["abelha"]),
    ([], "Quais astros orbitam o Sol e fazem parte da Via Láctea?", "logica:consulta", ["Terra", "Marte"], ["Lua"]),
    ([], "Quais seres vivos têm coluna vertebral e têm respiração aérea?", "logica:consulta", ["gato", "baleia"], ["tucano"]),
    ([], "Quais animais não são insetos?", "logica:consulta", ["aranha"], ["gato", "sapo"]),
    ([], "Quais animais não são répteis?", "logica:consulta", ["sapo"], ["aranha", "gato"]),
    ([], "Quais planetas são orbitados pela Lua?", "logica:consulta", ["Terra"], ["Marte"]),
    ([], "A Lua orbita o quê?", "logica:consulta", ["Terra"], ["Sol"]),
    ([], "Quais planetas a Lua orbita?", "logica:consulta", ["Terra"], ["Marte"]),
    ([], "De que a Terra faz parte?", "logica:consulta", ["Sistema Solar", "Via Láctea", "Universo"], ["Lua"]),
    ([], "O que é orbitado pela Terra?", "logica:consulta", ["Sol"], ["Lua"]),
    ([], "Liste os mamíferos que têm coluna vertebral", "logica:consulta", ["gato", "golfinho"], ["pinguim"]),
    ([], "Mostre os astros que têm luz própria", "logica:consulta", ["Sol"], ["Lua"]),
    ([], "Por favor, quais animais possuem oito patas?", "logica:consulta", ["aranha"], ["abelha"]),
    ([], "Eae, Crivo. Quem gira em torno da Terra?", "logica:consulta", ["Lua"], ["Sol"]),
    ([], "A Terra é um planeta e faz parte da Via Láctea?", "logica:conjuncao", ["Sim.", "Terra"], []),
    ([], "O pinguim é uma ave e tem penas?", "logica:conjuncao", ["Sim.", "penas"], []),
    ([], "A aranha é um inseto e tem oito patas?", "logica:conjuncao_falsa", ["Não.", "incompat"], []),
    ([], "O gato é um mamífero e orbita o Sol?", "logica:desconhecido", ["não", "prova"], []),
    ([], "Quais planetas têm penas?", "logica:desconhecido", ["não prova"], []),
    ([], "Quem orbita Marte?", "logica:desconhecido", ["não prova"], []),
    ([], "Quais animais têm penas e pilotam aviões?", "duvida", ["condi"], []),
    ([], "Quais animais têm penas ou oito patas?", "duvida", ["condi"], []),
    ([], "Quais animais não têm penas?", "duvida", ["nega"], []),
    ([], "Quais animais têm penas e não orbitam o Sol?", "duvida", ["nega"], []),
    ([], "Quais animais têm penas falsas?", "duvida", ["condi"], []),
    ([], "Quais animais são aves quânticas?", "duvida", ["condi"], []),
    (["Quais astros fazem parte do Sistema Solar?"], "Desses, quais orbitam o Sol?", "logica:consulta", ["Terra", "Marte"], ["Lua", "Sol"]),
    (["Quais animais são vertebrados?"], "E quais têm penas?", "logica:consulta", ["pinguim", "tucano"], ["gato"]),
    (["Quais animais têm penas?", "Oi"], "Desses, quais são aves?", "duvida", ["anterior"], []),
    ([], "Desses, quais têm penas?", "duvida", ["anterior"], []),
    (["Quais animais têm penas?"], "Desses, quais são mamíferos?", "logica:desconhecido", ["não prova"], []),
    (["Quais animais têm penas?"], "Desses, quais sabem programar?", "duvida", ["condi"], []),
]


def executar_caso(caso):
    historico, pergunta, esperado, contem, ausentes = caso
    bot = Crivo()
    for turno in historico:
        bot.responder(turno)
    ident, resposta = bot.responder(pergunta)
    # Nas listas, conferir os nomes na lista de resultados, não nas provas
    # (a prova da órbita de Marte, por exemplo, necessariamente cita o Sol).
    lista = resposta.split("\n", 1)[0]
    texto = lista if esperado == "logica:consulta" else resposta
    ok = (ident == esperado and all(t in texto for t in contem)
          and all(t not in lista for t in ausentes))
    return {"pergunta": pergunta, "historico": historico,
            "esperado": esperado, "obtido": ident, "passou": ok,
            "resposta": resposta}


def avaliar():
    resultados = [executar_caso(caso) for caso in CASOS]
    return {"total": len(resultados),
            "acertos": sum(r["passou"] for r in resultados),
            "limite": "Sonda de desenvolvimento usada para orientar a implementação; não é teste cego nem mede inteligência geral.",
            "casos": resultados}


if __name__ == "__main__":
    print(json.dumps(avaliar(), ensure_ascii=False, indent=2))
