"""Treino reproduzível de atos com contexto; não lê avaliações de conversa."""
import argparse
import json
from collections import Counter
from pathlib import Path

from dialogo_neural import DialogoNeural, atributos, assinatura_atributos, DIMENSAO
from rede_sequencial import RedeSequencial, assinatura


def avaliar(rede, casos):
    acertos, aceitos, por_ato = 0, 0, {}
    erros = []
    for c in casos:
        q = rede.analisar(c["texto"], c["estado"])
        correto = q["ato"] == c["ato"]
        aceito = q["confianca"] >= rede.limiar and q["margem"] >= .2
        acertos += correto
        aceitos += correto and aceito
        linha = por_ato.setdefault(c["ato"], dict(total=0, acertos=0, aceitos_corretos=0))
        linha["total"] += 1; linha["acertos"] += correto; linha["aceitos_corretos"] += correto and aceito
        if not correto:
            erros.append(dict(texto=c["texto"], estado=c["estado"], esperado=c["ato"], obtido=q))
    return dict(total=len(casos), acertos=acertos, aceitos_corretos=aceitos, por_ato=por_ato, erros=erros)


def treinar(caminho, destino, epocas=90, semente=73, acelerar=False):
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if dados.get("versao") != 1 or any(c["split"] not in ("treino", "validacao") for c in dados["exemplos"]):
        raise ValueError("Currículo inválido; teste final não entra no treino")
    treino = [c for c in dados["exemplos"] if c["split"] == "treino"]
    validacao = [c for c in dados["exemplos"] if c["split"] == "validacao"]
    if {c["familia"] for c in treino} & {c["familia"] for c in validacao}:
        raise ValueError("Famílias misturadas")
    if {c["texto"] for c in treino} & {c["texto"] for c in validacao}:
        raise ValueError("Falas repetidas entre as partições")
    lexico = dados["lexico"]
    rede = RedeSequencial(sorted({c["ato"] for c in treino}), dimensao=DIMENSAO, ocultos=40, semente=semente)
    rede.treinar([(atributos(c["texto"], c["estado"], lexico), c["ato"]) for c in treino],
                 epocas=epocas, semente=semente, acelerar=acelerar)
    checkpoint = dict(versao=1, assinatura_atributos=assinatura_atributos(),
                      assinatura_treino=assinatura(treino), lexico=lexico, rede=rede.dados(), limiar=.78,
                      treino=dict(epocas=epocas, semente=semente, exemplos=len(treino),
                                  atos=dict(Counter(c["ato"] for c in treino)),
                                  acelerador="numpy" if acelerar else "python"))
    modelo = DialogoNeural(checkpoint)
    resultado = dict(treino=avaliar(modelo, treino), validacao=avaliar(modelo, validacao),
                     assinatura_treino=checkpoint["assinatura_treino"],
                     limite="Validação autoral de atos; os assuntos e as famílias diferem do treino. Não mede geração livre, consciência nem compreensão universal.")
    Path(destino).write_text(json.dumps(checkpoint, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return resultado


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dados", default="curriculo_dialogo.json")
    p.add_argument("--saida", default="rede_dialogo.json")
    p.add_argument("--relatorio", default="avaliacao_dialogo_neural.json")
    p.add_argument("--epocas", type=int, default=90)
    p.add_argument("--semente", type=int, default=73)
    p.add_argument("--numpy", action="store_true")
    a = p.parse_args()
    resultado = treinar(a.dados, a.saida, a.epocas, a.semente, a.numpy)
    Path(a.relatorio).write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: {f: v[f] for f in ("total", "acertos", "aceitos_corretos")}
                      for k, v in resultado.items() if k in ("treino", "validacao")}, ensure_ascii=False))
