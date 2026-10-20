"""Gera os pedidos para o professor (modelo com licença Apache 2.0 ou MIT), no formato do rodar_modelo.py.

Cada pedido pede 10 mensagens de um tipo de pergunta sobre um alvo, com um estilo de escrita.
Os rótulos vêm do pedido e são conferidos depois por validar_saida.py (regras + revisão humana).
Uso: python compreensao_semantica/geracao/gerar_pedidos.py
"""
import gzip
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
TIPOS = {
    "quem": "pergunta sobre uma pessoa ou sobre a identidade de alguém (quem é, quem foi, quem escreveu)",
    "o_que": "pergunta por definição ou por uma ação (o que é, o que você faz, o que significa)",
    "qual": "pergunta por uma escolha ou um atributo (qual é, qual a capital, qual o seu nome)",
    "quanto": "pergunta por quantidade ou duração (quanto é, quantos anos, quanto tempo leva)",
    "quando": "pergunta por tempo ou data (quando foi, quando é, quando você…)",
    "onde": "pergunta por lugar (onde fica, aonde, em que lugar)",
    "como": "pergunta por modo ou procedimento (como faço, como funciona, como você…)",
    "por_que": "pergunta por causa (por que, porque)",
    "para_que": "pergunta por finalidade (para que serve, pra que serve)",
    "se": "pergunta condicional ou hipotética (se…, e se…, você faria isso se…)",
    "pedido": "pedido ou comando (me explica…, escreve…, pode me ajudar?, me conta…)",
    "nenhum": "afirmação ou relato, sem pergunta e sem pedido (eu gosto de…, hoje eu fui…)",
}
ALVOS = {
    "sobre_o_crivo": "sobre o assistente com quem a pessoa conversa (você, seu nome, sua idade, seu funcionamento)",
    "sobre_o_usuario": "sobre a própria pessoa que escreve (eu, meu, minha, o que eu quero, o que eu fiz)",
    "sobre_o_mundo": "sobre um assunto externo: fatos, conceitos, lugares, pessoas históricas, ciência",
    "sobre_pratica": "pedido prático: código, receita, procedimento, conta, texto para escrever",
    "outro": "não se encaixa nos anteriores (conversa do dia a dia, dúvida sobre a conversa, pedido de ajuda vago)",
}
# Combinações que fazem sentido (tipo, alvo).
COMBOS = {
    "quem": ["sobre_o_crivo", "sobre_o_mundo", "sobre_o_usuario"],
    "o_que": ["sobre_o_mundo", "sobre_o_crivo", "sobre_pratica"],
    "qual": ["sobre_o_mundo", "sobre_o_crivo", "sobre_o_usuario"],
    "quanto": ["sobre_o_mundo", "sobre_pratica", "sobre_o_crivo"],
    "quando": ["sobre_o_mundo", "sobre_o_crivo", "sobre_o_usuario"],
    "onde": ["sobre_o_mundo", "sobre_o_usuario", "sobre_o_crivo"],
    "como": ["sobre_pratica", "sobre_o_mundo", "sobre_o_crivo"],
    "por_que": ["sobre_o_mundo", "sobre_o_crivo"],
    "para_que": ["sobre_o_mundo", "sobre_pratica"],
    "se": ["outro", "sobre_pratica", "sobre_o_crivo"],
    "pedido": ["sobre_pratica", "sobre_o_mundo", "outro"],
    "nenhum": ["sobre_o_usuario", "outro", "sobre_o_mundo"],
}
VARIACOES = [
    "curtas e diretas",
    "informais, com gíria e sem pontuação",
    "com erro de digitação e tudo em minúsculas",
    "um pouco mais longas, com um pouco de contexto do dia a dia",
]
PEDIDOS_POR_COMBO = 3  # cada pedido gera 10 mensagens: 34 combinações x 3 x 10 = 1.020 candidatos


def pedido(tipo, alvo, k):
    variacao = VARIACOES[k % len(VARIACOES)]
    prompt = (
        "Escreva 10 mensagens diferentes que uma pessoa brasileira mandaria num chat de texto.\n"
        f"Tipo da mensagem: {TIPOS[tipo]}.\n"
        f"Sobre: {ALVOS[alvo]}.\n"
        f"Estilo: {variacao}.\n"
        "Uma mensagem por linha, sem numeração, sem aspas e sem explicação. "
        "Não use nomes de pessoas famosas, marcas ou números. Não repita a mesma estrutura."
    )
    return {
        "id": f"{tipo}__{alvo}__{k}",
        "mensagens": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperatura": 0.9,
    }


def principal():
    linhas = [pedido(t, a, k) for t, alvos in COMBOS.items() for a in alvos for k in range(PEDIDOS_POR_COMBO)]
    saida = AQUI / "entrada_professor.jsonl.gz"
    with gzip.open(saida, "wt", encoding="utf-8") as f:
        f.write("\n".join(json.dumps(x, ensure_ascii=False) for x in linhas) + "\n")
    print(len(linhas), "pedidos em", saida)


if __name__ == "__main__":
    principal()
