# v7b — resultado da rodada 1 (20/10/2026)

A100 80 GB, semente 20261019, desde a base 6a com substituição. 2.856 passos; escolhido o 2.219 pelo dev (71,5%). Pesos:
`CRIVO/transformer-crivo-46m-conversa-v7b/rodada1/conversa_20261020_042646/pesos.pt`, sha256 `cb8d59e0d0db…`. Resumo:
`resumo_v7b_rodada1.json`. **Professor: 5,2% das exposições de conversa** (falas da pessoa; respostas das listas).
`ativo_no_chat: false`.

**Reprovado em 3 dos 5 critérios.** O entendimento geral ficou igual ao do v7. A urgência melhorou muito, mas não o
bastante, e as falas novas de identidade criaram um erro novo.

| blind | v4 (chat) | v7 r1 | v7b r1 | v7b − v4 [IC 95%] | critério |
|---|---|---|---|---|---|
| v3 | 65,4 | 71,4 | 71,2 | **+5,8 [+4,3; +7,3]** | ✅ |
| v1 | 65,7 | 75,0 | 73,4 | **+7,7 [+6,1; +9,4]** | ✅ |
| paráfrases | 73,7 | 80,6 | 80,8 | **+7,1 [+5,8; +8,4]** | ✅ |
| Grok | 73,4 | 74,6 | 73,5 | +0,1 [−1,1; +1,4] | ✅ |
| v4 | 92,5 | 91,5 | 90,8 | −1,7 [−3,5; +0,2] | ❌ (mínimo −1,5) |

- Frases reais: **11/15** ❌ (v4: 12). Recuperou "ea tranquilo", que o v7 tinha perdido. Perdeu "legal e voce?" e "serio
  mesmo?": as duas foram respondidas com "Sou uma IA, não uma pessoa…".
- Urgência: **97 acertos contra 102** ❌ (v7: 79).
- Usa o fato: 1,0 ✅. Sem o freio de repetição: blind v3 71,7%, frases reais 11.

## Por grupo de situações (soma dos blinds antigos)

| grupo | v4 | v7 | v7b |
|---|---|---|---|
| com falas novas no v7 (10.743) | 71,1 | 77,0 | 76,6 |
| identidade (597) | 75,4 | 74,4 | **69,5** |
| saúde e urgência (224) | 59,4 | 49,1 | 47,8 |

Urgência por situação (acertos v4 → v7b): saude_urgente 84 → 78, ansioso_peito 16 → 16, ajuda_socorro 2 → 3.

## O que explica a reprovação

1. **As falas novas de identidade puxaram o "e você?".** Toda a queda no blind v4 vem de `reciproco` (−9 frases); as
   outras situações somam +4 e −5. As duas frases reais perdidas são do mesmo tipo: depois de o CRIVO perguntar
   "E você, como está?", a pessoa devolve a pergunta e o modelo responde como se ela perguntasse se ele é humano.
   As falas de `ser_humano` ("você é gente de verdade?", "tem humano aí?"…) entraram **sem substituir nada**,
   porque a fase 5 não tem casos de identidade. Assim aumentaram o peso da identidade, e 30% delas vieram depois de uma
   pergunta do CRIVO. É a lição do v6 ("acrescentar desloca peso") que voltou por essa porta. `robo` também caiu
   (38 → 27): "é sistema sem vida" e "é código andando" não se parecem com as falas novas, que começam por "você é…".
2. **Saúde comum: as falas novas eram quase todas perguntas.** `saude_geral` caiu de 49 para 16 acertos, mas 19 das 23
   perdas são duas frases repetidas com ruído: "minha barriga tá estranha desde ontem" (12) e "tem alguma dica pra
   aliviar dor de cabeça" (7). As falas escritas para o v7b eram perguntas ("é normal…?", "o que é bom pra…?"), e
   um relato de sintoma sem pergunta ficou sem cobertura.
3. **Urgência: as falas novas ajudaram (+18 sobre o v7), mas não bastaram.** Perdas contra a v4: "tô passando mal" (4),
   "meu rosto tá inchando e tá difícil respirar" (3), "não consigo pegar ar" (2), "meu filho tá com muita falta de ar" e
   "tô sangrando muito". **Todas são pegas pelo `crise.py`** (conferido nesta data), que responde antes do modelo no chat.

## Decisão

- Pela regra fixada, o v7b não vai para o chat: o chat continua com o 46M da fase 6b v4.
- **A rodada 2 não muda a reprovação** (as duas rodadas precisam passar), então não vale gastar GPU com ela.
- Para um v7c, com base nos itens acima:
  - a identidade deve entrar **substituindo** exemplos de identidade, para manter o peso;
  - o "e você?" depois de uma pergunta do CRIVO precisa de falas de `reciproco` em número igual;
  - saúde comum precisa de relatos de sintoma, não só de perguntas.
