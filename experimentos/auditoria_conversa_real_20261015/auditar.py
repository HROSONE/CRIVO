#!/usr/bin/env python3
"""Conversa diagnóstica com o CRIVO real (web_core.responder_web).

Não é benchmark de promoção: registra saídas, mecanismo e sinais esperados para
leitura humana. Não altera conhecimento, pesos, configuração nem memória externa.
"""
import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from web_core import responder_web


CASOS = [
    {
        "id": "saudacao",
        "mensagem": "Oi, Crivo!",
        "historico": [],
        "proposito": "conversa social e identidade",
        "sinais": [],
    },
    {
        "id": "conhecimento_virus_bacteria",
        "mensagem": "Qual é a diferença entre vírus e bactéria?",
        "historico": [],
        "proposito": "recuperar e explicar conhecimento factual",
        "sinais": ["vírus", "bactéria"],
    },
    {
        "id": "desconhecido",
        "mensagem": "O que é plimbo?",
        "historico": [],
        "proposito": "calibrar abstenção quando não há evidência",
        "sinais": ["não sei", "não conheço", "não tenho", "não encontrei", "não reconheci"],
    },
    {
        "id": "memoria_nome",
        "mensagem": "Como eu me chamo?",
        "historico": ["Meu nome é Henrique."],
        "proposito": "recuperar dado pessoal explícito do histórico",
        "sinais": ["henrique"],
    },
    {
        "id": "memoria_pet",
        "mensagem": "Qual é o nome da minha cachorra?",
        "historico": ["Minha cachorra se chama Mel."],
        "proposito": "resolver referente e gênero com memória contextual",
        "sinais": ["mel"],
    },
    {
        "id": "acolhimento_contextual",
        "mensagem": "O que posso fazer agora?",
        "historico": ["Estou triste porque meu pai está doente."],
        "proposito": "responder ao seguimento preservando o contexto emocional",
        "sinais": ["pai", "doente", "triste"],
    },
    {
        "id": "plano_com_contexto",
        "mensagem": "Como posso organizar isso?",
        "historico": ["Quero aprender fotografia.", "Só tenho 30 minutos por dia."],
        "proposito": "usar objetivo e restrição de turnos anteriores",
        "sinais": ["fotografia", "fotografar", "30 minutos", "30 min"],
    },
    {
        "id": "correcao_memoria",
        "mensagem": "Como ela se chama?",
        "historico": [
            "Minha cachorra se chama Mel.",
            "Na verdade, ela se chama Nina.",
        ],
        "proposito": "aplicar correção recente sem recuperar o valor antigo",
        "sinais": ["nina"],
    },
    {
        "id": "deducao",
        "mensagem": (
            "Se todos os mamíferos respiram e a baleia é um mamífero, "
            "o que podemos concluir?"
        ),
        "historico": [],
        "proposito": "dedução relacional simples, sem depender de frase decorada",
        "sinais": ["baleia", "respir"],
    },
    {
        "id": "identidade",
        "mensagem": "Quem é você e o que consegue fazer?",
        "historico": [],
        "proposito": "resposta de identidade sem desviar para assunto alheio",
        "sinais": ["crivo"],
    },
]


def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.casefold())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto).strip()


def executar():
    parser = argparse.ArgumentParser()
    parser.add_argument("--saida", default="/tmp/auditoria-conversa-crivo.json")
    args = parser.parse_args()

    resultados = []
    for caso in CASOS:
        entrada = {"message": caso["mensagem"], "history": caso["historico"]}
        item = {
            "caso": caso["id"],
            "proposito": caso["proposito"],
            "historico": caso["historico"],
            "pergunta": caso["mensagem"],
        }
        try:
            resposta = responder_web(entrada)
            texto = resposta.get("response", "")
            normalizada = normalizar(texto)
            item.update({
                "id_resposta": resposta.get("id"),
                "resposta": texto,
                "tem_prova": resposta.get("has_proof"),
                "rede_neural_ativa": resposta.get("neural_active"),
                "dialogo_experimental": resposta.get("experimental_dialogue"),
                "voz_conversa": resposta.get("conversation_voice"),
                "sinais_encontrados": [
                    sinal for sinal in caso["sinais"]
                    if normalizar(sinal) in normalizada
                ],
                "sinais_esperados": caso["sinais"],
                "erro": None,
            })
        except Exception as exc:  # o relatório precisa preservar a falha e os próximos casos
            item.update({
                "id_resposta": None,
                "resposta": None,
                "tem_prova": None,
                "rede_neural_ativa": None,
                "dialogo_experimental": None,
                "voz_conversa": None,
                "sinais_encontrados": [],
                "sinais_esperados": caso["sinais"],
                "erro": f"{type(exc).__name__}: {exc}",
            })
        resultados.append(item)
        print(f"\n[{item['caso']}] {item['pergunta']}")
        print(f"ID: {item['id_resposta']}")
        print(f"CRIVO: {item['resposta'] or item['erro']}")
        print(f"Sinais: {item['sinais_encontrados']} / {item['sinais_esperados']}")

    relatorio = {
        "tipo": "auditoria diagnóstica; não é benchmark de promoção",
        "criado_em_utc": datetime.now(timezone.utc).isoformat(),
        "base": "runtime do repositório via web_core.responder_web, configuração padrão",
        "casos": resultados,
        "resumo": {
            "total": len(resultados),
            "falhas_de_execucao": sum(bool(x["erro"]) for x in resultados),
            "casos_com_algum_sinal": sum(bool(x["sinais_encontrados"]) for x in resultados),
        },
        "limites": [
            "Sinais textuais são pistas para inspeção, não uma avaliação semântica completa.",
            "A execução usa a configuração padrão do runtime; não presume que pesos experimentais estejam ligados.",
            "Nenhum peso, dado de conhecimento ou configuração é alterado.",
        ],
    }
    destino = Path(args.saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nRelatório salvo em {destino}")
    print(json.dumps(relatorio["resumo"], ensure_ascii=False))
    if relatorio["resumo"]["falhas_de_execucao"]:
        raise SystemExit(1)


if __name__ == "__main__":
    executar()
