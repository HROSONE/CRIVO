"""Treinamento CANDIDATO da rede autoral com o currículo de Astronomia.
Não atualiza main, nem publica pesos como produção. Relatório de desenvolvimento.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from crivo import Crivo
from curriculo_mundo import carregar_base, ler_curriculo
from rede_neural import RedeCrivo, treinar_base

def principal():
    base_path = ROOT / "conhecimento.json"
    curriculo = ler_curriculo(ROOT / "conhecimento_mundo.json")
    conceitos = [x for x in curriculo["itens"] if x["area"] == "astronomia"]
    assert len(conceitos) >= 20
    base = carregar_base(base_path)
    ids = {e["id"] for e in base}
    assert len(ids) == len(base)
    checkpoint = ROOT / "rede_crivo.json"  # arquivo temporário do runner, não é commit
    rede = treinar_base(base_path, checkpoint, epocas=60, ocultos=48,
                        dimensao=512, modo="portugues", semente=42)
    bot = Crivo()
    assert bot.rede is not None and bot.erro_rede is None, bot.erro_rede
    assert set(rede.rotulos) == ids
    # As formulações abaixo não fazem parte das três perguntas editoriais
    # geradas automaticamente por conceito. É avaliação de desenvolvimento,
    # NÃO avaliação externa cega.
    treino_normalizado = {" ".join(q.lower().split()) for e in base for q in e["perguntas"]}
    casos = []
    for item in conceitos:
        q = "Defina " + item["nome"] + "."
        assert " ".join(q.lower().split()) not in treino_normalizado, q
        rotulo, confianca = rede.prever(q)
        resposta_id, resposta = bot.responder("O que é " + item["nome"] + "?")
        casos.append({
            "conceito": item["nome"], "esperado": item["id"],
            "predito_rede": rotulo, "confianca": round(confianca, 5),
            "acerto_rede": rotulo == item["id"],
            "resposta_hibrida": resposta_id,
            "acerto_hibrido": resposta_id == "conhecimento:" + item["id"],
            "texto_hibrido": resposta[:180],
        })
    controles = []
    for q in ("O que é o planeta Zorvax-913?",
              "O que é a estrela inventada Drelon-Q?"):
        resposta_id, resposta = bot.responder(q)
        controles.append({"pergunta": q, "id": resposta_id,
                          "absteve": resposta_id == "fora"})
    relatorio = {
        "tipo": "avaliacao_de_desenvolvimento_neural_e_hibrida",
        "distincao": "Atualiza realmente pesos do classificador autoral. Não treina compreensão causal nem geração livre.",
        "base": "conhecimento.json + conhecimento_mundo.json na branch candidata",
        "configuracao": {"epocas": 60, "dimensao": 512, "ocultos": 48,
                         "modo": "portugues", "semente": 42},
        "rotulos_totais": len(rede.rotulos),
        "astronomia": {
            "conceitos": len(conceitos),
            "classificador": {"acertos": sum(c["acerto_rede"] for c in casos),
                               "total": len(casos)},
            "hibrido": {"acertos": sum(c["acerto_hibrido"] for c in casos),
                        "total": len(casos)},
            "casos": casos,
        },
        "controles_desconhecidos": controles,
        "observacoes": [
            "Rede isolada sempre escolhe uma classe: a abstenção é do motor híbrido.",
            "Casos de desenvolvimento não servem para certificar 100% da skill.",
            "O modelo treinado é um artefato candidato; não foi integrado à main."
        ],
    }
    destino = ROOT / "avaliacao_treino_astronomia.json"
    destino.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    print(json.dumps({
        "labels": len(rede.rotulos), "conceitos": len(conceitos),
        "acertos_rede": relatorio["astronomia"]["classificador"]["acertos"],
        "acertos_hibrido": relatorio["astronomia"]["hibrido"]["acertos"],
        "abstencoes": sum(c["absteve"] for c in controles),
        "controles": len(controles),
    }, ensure_ascii=False))
    assert all(c["absteve"] for c in controles), "Falha de abstenção após treinamento"

if __name__ == "__main__":
    principal()
