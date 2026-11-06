# v6c com PARTIDA = "v4" — resultado (20/10/2026)

A100 80 GB, semente 20261019, 1.259 passos de ajuste leve (LR 3e-5 → 3e-6) a partir do 46M do chat (`45825352…`), com
substituição. Resumo: `resumo_v6c_partida_v4.json`.

**A catraca ficou com o próprio 46M do chat** (`escolhida_e_o_chat: true`). Sentido no dev de escolha (1.150 frases):

| passo | 0 (chat) | 139 | 278 | 417 | 556 | 695 | 834 | 973 | 1.112 | 1.251 |
|---|---|---|---|---|---|---|---|---|---|---|
| dev | **67,5%** | 66,8 | 66,4 | 66,0 | 66,8 | 65,9 | 66,3 | 65,8 | 66,2 | 66,5 |

Os blinds deram diferença 0,0 em tudo, porque a versão medida é a do chat. Isso confirma que a régua e a linha de base
pareada estão consistentes. Os critérios "sem piorar" passaram trivialmente; o do blind v3 (IC > 0) não.

## Leitura

- Uma volta a mais na fase 5, mesmo com as falas novas no lugar das antigas, **piorou** um pouco o dev (−0,7 a −1,7
  ponto). O 46M do chat já tinha visto a fase 5 três vezes; mais uma passagem decora mais do que ensina, como a auditoria
  tinha visto na perda de validação (mínima no passo ~330 da 6b v4).
- Com ~10% de casos novos por situação, o ajuste leve não muda o entendimento. Os ganhos do v6 e do v6b (dev 68,9% e
  67,6%) apareceram treinando desde a base 6a.
- Nada piorou: a catraca funcionou como planejado.

## Próximo passo

O mesmo notebook com `PARTIDA = "6a"`: a receita longa desde a base, em que as falas novas deram ganho, agora com a
substituição que corrige a causa medida das perdas (o peso das situações sem casos novos). A medida do 46M do chat é
reaproveitada inteira (o blind v6c é o mesmo). Saída separada: `CRIVO/transformer-crivo-46m-conversa-v6c-6a/`.
