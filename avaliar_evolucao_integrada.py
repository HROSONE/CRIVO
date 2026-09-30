"""Contratos autorais de pedidos compostos, evidência e diálogo.

O oráculo é definido a partir de fatos de uma base fictícia, sem consultar
saídas do bot. Não participa do treinamento. É avaliação de desenvolvimento,
não um teste externo cego. O benchmark final anterior permanece reservado.
"""
import argparse
import json
import tempfile
from pathlib import Path

from crivo import Crivo


def base_sintetica():
    nomes = ("Vétron Q12", "anel de Savia", "ponte heliacal oblíqua", "módulo Zedrax",
             "câmara de Ivara", "espiral de Tembor", "prisma de Lúria", "rede não circular")
    base, itens = [], []
    for j, nome in enumerate(nomes):
        ident = "objeto_" + str(j)
        fatos = [
            {"texto": nome + " é um instrumento fictício de pesquisa.", "papel": "definicao", "fonte": "manual"},
            {"texto": "Ele recebe um pulso e registra " + str(7+j) + " marcas verdes.", "papel": "detalhe", "aspecto": "funcionamento", "fonte": "manual"},
            {"texto": "Sua função é medir pulsos luminosos.", "papel": "detalhe", "aspecto": "funcao", "fonte": "manual"},
            {"texto": "Um exemplo é registrar um pulso emitido por uma lâmpada.", "papel": "exemplo", "fonte": "manual"},
            {"texto": "Se não há luz, ele pode falhar; o resultado não garante precisão.", "papel": "limite", "fonte": "manual"},
        ]
        base.append({"id": ident, "topico": "clima", "perguntas": ["o que é " + nome], "resposta": fatos[0]["texto"]})
        itens.append({"id": "ficticio_" + str(j), "nome": nome, "aliases": ["dispositivo " + str(j)], "fatos": fatos})
    # Itens expandidos precisam de IDs distintos dos editoriais. Os aliases
    # preferidos declaram a substituição exata, sem depender de ordem.
    expandido = {"versao": 1, "fontes": {"manual": {"titulo": "Manual fictício de avaliação", "url": "https://example.org/manual-ficticio"}},
                 "itens": itens, "aliases_preferidos": [{"alias": i["nome"], "destino": i["id"], "substitui": b["id"]} for i,b in zip(itens,base)]}
    return base, expandido


def casos(itens):
    resultado = []
    for item in itens:
        nome = item["nome"]
        definicao, funcionamento, funcao, exemplo, limite = [f["texto"] for f in item["fatos"]]
        for texto, inclui in (
            ("Explique " + nome + "; depois dê um exemplo; ao final resuma", (definicao, exemplo, "Resumo")),
            ("O que é " + nome + "? E como funciona? Mostre as fontes", (definicao, funcionamento, "example.org/manual-ficticio")),
            ("Me explique " + nome + " e depois mostre para que serve e organize em tópicos", (definicao, funcao, "- ")),
            ("Explique " + nome + ", depois reformule e cite as fontes", ("instrumento fictício", "Reformulação", "example.org/manual-ficticio")),
        ):
            resultado.append(("pedidos_compostos", (), texto, inclui, ()))
        for texto, inclui in (
            ("Sobre " + nome + ", explique o registro de marcas verdes", (funcionamento,)),
            ("Sobre " + nome + ", me fale dos pulsos luminosos", (funcao,)),
        ):
            resultado.append(("busca_de_evidencias", (), texto, inclui, ()))
        resultado.append(("limites_no_resumo", (), "Explique " + nome + "; aprofunde; depois resuma", (limite, "Resumo"), ()))
        outro = itens[(itens.index(item)+1) % len(itens)]
        introducao = "Explique " + nome + "; explique " + outro["nome"]
        resultado.append(("referencias", (introducao,), "Resuma o segundo assunto", (outro["fatos"][0]["texto"],), (definicao,)))
        resultado.append(("referencias", (introducao,), "Qual é a função do primeiro?", (funcao,), (outro["fatos"][0]["texto"],)))
        resultado.append(("correcoes", ("Explique " + nome + "; depois resuma",), "Não, quis dizer " + outro["nome"], (outro["fatos"][0]["texto"],), (definicao,)))
        resultado.append(("ambiguidades", (introducao, "Resuma isso", "2"), "Dê um exemplo dele", (exemplo,), ()))
        for historico, texto in (
            ((), "Explique " + nome + " alienígena; depois dê um exemplo"),
            ((), "Explique " + nome + " se tiver capacidade infinita; depois resuma"),
            ((), "Não explique " + nome + "; depois resuma"),
            ((), 'Ele disse "explique ' + nome + '; depois resuma"'),
            ((introducao, "Oi!"), "Resuma o segundo assunto"),
            ((introducao, "Mudar de assunto"), "Resuma o primeiro"),
            ((introducao, "Resuma isso", "sim"), "Resuma isso"),
            ((), "Sobre " + nome + ", explique como cura doenças"),
        ):
            resultado.append(("controles", historico, texto, (), (definicao, funcionamento, exemplo)))
    return resultado


def avaliar(classe=Crivo):
    base, expandido = base_sintetica()
    grupos, falhas = {}, []
    with tempfile.TemporaryDirectory() as pasta:
        caminho = Path(pasta) / "conhecimento.json"
        caminho.write_text(json.dumps(base, ensure_ascii=False), encoding="utf-8")
        caminho.with_name("conhecimento_expandido.json").write_text(json.dumps(expandido, ensure_ascii=False), encoding="utf-8")
        for grupo, anteriores, texto, inclui, exclui in casos(expandido["itens"]):
            bot = classe(caminho)
            for q in anteriores:
                bot.responder(q)
            ident, resposta = bot.responder(texto)
            passou = all(t in resposta for t in inclui) and not any(t in resposta for t in exclui)
            g = grupos.setdefault(grupo, {"total": 0, "acertos": 0})
            g["total"] += 1
            g["acertos"] += passou
            if not passou:
                falhas.append({"grupo": grupo, "historico": anteriores, "pergunta": texto, "id": ident, "resposta": resposta})
    return {"total": sum(g["total"] for g in grupos.values()), "acertos": sum(g["acertos"] for g in grupos.values()),
            "grupos": grupos, "falhas": falhas,
            "limite": "152 contratos autorais sobre oito nomes fictícios repetidos. Desenvolvimento, não avaliação cega. Não alimenta treino; o teste final anterior não é lido."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--saida")
    parser.add_argument("--medir", action="store_true", help="Registrar também uma referência com falhas, sem reprovar")
    args = parser.parse_args()
    resultado = avaliar()
    if args.saida:
        Path(args.saida).write_text(json.dumps(resultado, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in resultado.items() if k != "falhas"}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if args.medir or resultado["acertos"] == resultado["total"] else 1)
