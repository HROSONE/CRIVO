"""Sonda autoral de extração e retomada; usada no desenvolvimento, não cega.

Os nomes e rótulos são definidos pelo avaliador, sem consultar saídas do bot.
Estas frases não são carregadas pelo treino. Os nomes repetidos em uma forma
não devem ser tratados como observações independentes de linguagem geral.
"""
import argparse
import json
from pathlib import Path

import linguagem_neural
from crivo import Crivo
from web_core import responder_web


FORMAS = (
    "Podemos retomar o assunto {alvo}?",
    "A gente pode voltar ao assunto {alvo}?",
    "Gostaria de retomar {alvo}.",
    "Me ajuda a retomar {alvo}.",
)
ALVOS = ("Kavor Z17", "circuito de Névia", "ponte espectral oblíqua")


def avaliar():
    raiz = Path(linguagem_neural.__file__).resolve().parent
    rede = linguagem_neural.LinguagemNeural(json.loads(
        (raiz / "rede_linguagem.json").read_text(encoding="utf-8")))
    quadros, dialogos, controles = [], [], []
    for forma in FORMAS:
        for alvo in ALVOS:
            texto = forma.format(alvo=alvo)
            q = rede.analisar(texto)
            correto = q is not None and (q.ato, q.alvo, q.outro) == ("retomar", alvo, "") and q.conservado
            quadros.append(dict(texto=texto, passou=bool(correto),
                                obtido=q._asdict() if q is not None else None))
        for alvo, outro in (("memória", "DNA"), ("RNA", "sinapse"), ("gravidade", "neurônio")):
            bot = Crivo()
            bot.responder("O que é " + alvo + "?")
            contexto = bot.contexto_textual
            bot.responder("O que é " + outro + "?")
            bot.responder("Oi")
            texto = forma.format(alvo=alvo)
            ident, _ = bot.responder(texto)
            correto = (ident == "escrita:retomada" and bot.contexto_textual is not None and
                       bot.contexto_textual.temas == contexto.temas and
                       bot.contexto_textual.exibidos == contexto.exibidos)
            dialogos.append(dict(texto=texto, passou=bool(correto), obtido=ident))
    for alvo in ("DNA alienígena", "memória sem limite", "RNA com outra função", "DNA/alienígena"):
        bot = Crivo()
        for tema in ("DNA", "RNA", "memória"):
            bot.responder("O que é " + tema + "?")
        texto = FORMAS[0].format(alvo=alvo)
        q = rede.analisar(texto)
        ident, _ = bot.responder(texto)
        correto = (q is not None and (not q.conservado or q.alvo == alvo) and
                   ident in ("duvida", "fora") and bot.contexto_textual is None)
        controles.append(dict(texto=texto, passou=bool(correto), obtido=ident))
    pergunta = FORMAS[0].format(alvo="memória")
    for cancelar in (False, True):
        bot = Crivo()
        if cancelar:
            bot.responder("O que é memória?")
            bot.responder("Mudar de assunto")
        ident, _ = bot.responder(pergunta)
        controles.append(dict(tipo="cancelamento" if cancelar else "isolamento",
                              passou=ident in ("duvida", "fora"), obtido=ident))
    history = ["O que é memória?", "O que é DNA?", "Oi", pergunta]
    resposta = responder_web({"history": history, "message": "Qual é a fonte?"})
    correto = (resposta["id"] == "escrita:fontes" and "journals.plos.org" in resposta["response"]
               and "genome.gov" not in resposta["response"])
    controles.append(dict(tipo="fontes_no_replay", passou=correto, obtido=resposta["id"]))
    resumo = lambda cs: dict(total=len(cs), acertos=sum(c["passou"] for c in cs),
                            falhas=[c for c in cs if not c["passou"]])
    return dict(quadros=resumo(quadros), dialogos=resumo(dialogos),
                controles=resumo(controles), limite=__doc__.strip())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida")
    args = parser.parse_args()
    resultado = avaliar()
    texto = json.dumps(resultado, ensure_ascii=False, indent=2) + "\n"
    if args.saida:
        Path(args.saida).write_text(texto, encoding="utf-8")
    print(texto)
    raise SystemExit(0 if all(resultado[g]["acertos"] == resultado[g]["total"]
                             for g in ("quadros", "dialogos", "controles")) else 1)
