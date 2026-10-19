# v6b — resultado da rodada 1 (19/10/2026)

L4, conta henriquenbk18, semente 20261019. 3.059 passos; escolhido o 2.373 pelo dev (67,6%). Pesos:
`CRIVO/transformer-crivo-46m-conversa-v6b/rodada1/conversa_20261019_230539/pesos.pt`, sha256 `8e1a9c686455…`. Resumo:
`resumo_v6b_rodada1.json`. `ativo_no_chat: false`. Linha de base: os blinds antigos foram reaproveitados do v6, e só o
blind v6b foi medido de novo.

**Reprovado: passou só em "usa o fato".** A rodada 2 não foi rodada: ela não mudaria a reprovação.

| blind | v4 (chat) | v6 r1 | **v6b r1** | v6b − v4 [IC 95%] |
|---|---|---|---|---|
| v3 | 65,4 | 68,7 | 66,6 | +1,2 [−0,3; +2,6] ❌ |
| v1 | 65,7 | 69,8 | 72,2 | **+6,5 [+4,9; +8,0]** |
| paráfrases | 73,7 | 79,0 | 74,4 | +0,7 [−0,5; +1,8] |
| Grok | 73,4 | 72,8 | 74,0 | +0,6 [−0,7; +1,8] |
| v4 | 92,5 | 89,8 | 89,5 | −3,0 [−5,3; −0,8] ❌ |
| v6b (não decide) | 57,1 | — | 62,8 | +5,7 [+2,1; +9,4] |

Frases reais: 11/15 ❌ (v4: 12). Urgência: 79 acertos contra 102 do v4 ❌ (pior que a rodada 1, 88). Usa o fato: 0,95.

## As pioras corrigidas, situação por situação (soma dos blinds antigos)

| situação | v4 | v6 r1 | v6b |
|---|---|---|---|
| amor_bom | 41,9 | 3,2 | **61,3** |
| boa_noite | 90,0 | 66,2 | **97,7** |
| estou_bem | 77,5 | 57,7 | **80,3** |
| desisto_despedida | 83,7 | 51,0 | 75,5 |
| quem_sou_eu | 92,0 | 87,3 | 96,7 |
| estou_mal | 79,8 | 74,7 | 86,5 |
| robo | 62,3 | 50,8 | 63,9 |
| reciproco | 80,7 | 76,0 | 76,7 (não resolveu) |
| motivacao | 45,8 | 25,0 | 16,7 (piorou mais) |
| saude_urgente | 71,8 | 59,8 | **53,0 (piorou mais)** |

As correções por pares mínimos funcionaram onde foram aplicadas. A urgência piorou mais.

## A causa nova: quem não ganha casos perde

Agrupando as situações pelo que receberam no v6b:

| grupo | frases | v4 → v6b |
|---|---|---|
| com falas novas | 6.881 | 65,0 → 68,8 (+3,8) |
| com equilíbrio (falas antigas) | 3.222 | 81,6 → 81,9 (+0,3) |
| identidade (fora do treino v6) | 597 | 75,4 → 73,4 (−2,0) |
| situações da v4 sem casos novos (confirma_crivo, nao_sabe_entao…) | 640 | 84,1 → 77,8 (−6,2) |
| **saúde e urgência (fora do treino v6)** | 224 | **59,4 → 43,3 (−16,1)** |

O equilíbrio deixou de fora justamente saúde/urgência, identidade e as situações da v4. Com mais casos para todas as
outras, essas ficaram relativamente menores no treino e perderam. É a mesma causa do blind v4 e da urgência. A rodada 1
já mostrava isso em menor escala.

## Leitura

- **Ganho real de entendimento onde há falas novas:** +3,8 nessas situações, e o blind v1 +6,5 com IC longe de zero. Com
  o filtro de parecença, isso não vem de cópia.
- O ganho das paráfrases da rodada 1 (+5,2) caiu para +0,7 sem as quase-cópias. Parte dele era cópia.
- **Acrescentar casos muda o peso de quem não recebe nada.** É preciso preservar a proporção de cada situação.

## Próximo passo sugerido (não decidido): v6c por substituição

Em vez de ACRESCENTAR casos, cada caso novo de uma situação SUBSTITUI um caso antigo da fase 5 da mesma situação. Assim:
- a proporção de cada situação no treino fica igual à da v4 (saúde, urgência, identidade e v4 intactas);
- muda só a variedade das falas dentro de cada situação, que é exatamente a hipótese;
- não há equilíbrio artificial.

Os critérios continuam os mesmos, inclusive o de urgência.
