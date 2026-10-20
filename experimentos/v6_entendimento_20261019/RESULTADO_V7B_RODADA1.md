# v7b — resultado da rodada 1 (20/10/2026)

A100 80 GB, semente 20261019, desde a base 6a com substituição. 2.856 passos; escolhido o 2.219 pelo dev (71,5%). Pesos:
`CRIVO/transformer-crivo-46m-conversa-v7b/rodada1/conversa_20261020_042646/pesos.pt`, sha256 `cb8d59e0d0db…`. Resumo:
`resumo_v7b_rodada1.json`. **Professor: 5,2% das exposições de conversa** (falas da pessoa; respostas das listas).
`ativo_no_chat: false`.

**Reprovado em 3 dos 5 critérios.** O entendimento geral ficou igual ao do v7. A urgência melhorou muito, mas não o
bastante. A primeira leitura culpou as falas de identidade; a comparação frase por frase com o v7 não sustenta isso (item 1).

| blind | v4 (chat) | v7 r1 | v7b r1 | v7b − v4 [IC 95%] | critério |
|---|---|---|---|---|---|
| v3 | 65,4 | 71,4 | 71,2 | **+5,8 [+4,3; +7,3]** | ✅ |
| v1 | 65,7 | 75,0 | 73,4 | **+7,7 [+6,1; +9,4]** | ✅ |
| paráfrases | 73,7 | 80,6 | 80,8 | **+7,1 [+5,8; +8,4]** | ✅ |
| Grok | 73,4 | 74,6 | 73,5 | +0,1 [−1,1; +1,4] | ✅ |
| v4 | 92,5 | 91,5 | 90,8 | −1,7 [−3,5; +0,2] | ❌ (mínimo −1,5) |

- Frases reais: **11/15** ❌ (v4: 12). Contra o v7: recuperou "ea tranquilo", perdeu "serio mesmo?" e "tá vendo claude?…".
  "legal e voce?" errava nos dois, com "Sou uma IA, não uma pessoa…".
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

1. **Identidade e "e você?" — correção (20/10/2026, depois de comparar com o v7 frase por frase).** A primeira leitura
   culpou as falas novas de identidade. Os números não sustentam isso:
   - só ~60 casos de identidade entraram depois dos filtros, uns 10% do peso que o IDENTIDADE.md já tem;
   - "legal e voce?" **já errava no v7** com a mesma resposta ("Sou uma IA, não uma pessoa…"), e o v7 não tinha falas
     de identidade;
   - `reciproco` no blind v4 já caía no v7 (−4), e no v7b caiu −9;
   - entre o v7 e o v7b, com a mesma semente, situações sem nenhuma mudança nos dados variaram muito: voce_confunde
     +18 → −10, dificil_falar +7 → −15.

   Boa parte da diferença entre os dois é **variação de um treino para outro**, que numa situação passa de 10 pontos.
   O "e você?" respondido como pergunta de identidade é um erro do jeito de treinar desde a 6a (o treino de identidade
   tem "e você, quem é?"), não das falas do v7b. Uma regra de qualidade do professor apareceu na análise:
   nas situações que perguntam algo AO CRIVO, parte das falas do professor fala da própria pessoa
   ("Tenho medo de que…" em medo, "Não gosto de…" em nao_gosta). São ~105 falas, que o v7c tira.
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
- O v7c (registrado no README antes de rodar) ataca a variação e as causas medidas: média móvel dos pesos e escolha com
  guarda no dev (nenhum grupo abaixo do chat), falas incoerentes do professor fora, saúde em pares mínimos, identidade sem
  ganhar peso.
