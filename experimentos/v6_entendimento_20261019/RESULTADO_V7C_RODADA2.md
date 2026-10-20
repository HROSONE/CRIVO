# v7c — resultado da rodada 2 e decisão das duas rodadas (20/10/2026)

L4, semente 20261020. 2.856 passos; escolhido o passo 2.853 (pesos crus), que **passou a guarda do dev** (folga de +1,2
pontos no pior grupo). Pesos: `CRIVO/transformer-crivo-46m-conversa-v7c/rodada2/conversa_20261020_122214/pesos.pt`.
Resumo: `resumo_v7c_rodada2.json`. Professor: ~5% das exposições de conversa. `ativo_no_chat: false`.

## As duas rodadas passaram nos 5 critérios fixados

| blind | v4 (chat) | r1 − v4 [IC 95%] | r2 − v4 [IC 95%] |
|---|---|---|---|
| v3 | 65,4 | **+6,3 [+4,9; +7,7]** | **+6,4 [+5,0; +8,0]** |
| v1 | 65,7 | +9,0 [+7,3; +10,7] | +7,4 [+5,8; +8,9] |
| paráfrases | 73,7 | +5,2 [+3,8; +6,5] | +8,2 [+6,8; +9,5] |
| Grok | 73,4 | +2,5 [+1,2; +3,7] | +1,0 [−0,2; +2,2] |
| v4 | 92,5 | −1,5 [−3,8; +0,8] | −0,2 [−2,0; +1,8] |

| critério | r1 | r2 | mínimo |
|---|---|---|---|
| urgência (acertos; chat 102) | 118 | 117 | ≥ 102 |
| frases reais | 12/15 | 13/15 | ≥ 12 |
| usa o fato | 0,95 | 0,85 | ≥ 0,85 |

`comparar_v6.principal(..., com_urgencia=True)`: **"AS DUAS RODADAS PASSARAM: candidata a ser mostrada ao criador (não
liga sozinha)."** É a primeira versão desde o v6 que passa nas duas.

## Por grupo (soma dos blinds antigos)

| grupo | v4 | r1 | r2 |
|---|---|---|---|
| com falas novas (10.743) | 71,1 | 76,7 | 76,9 |
| saúde e urgência (224) | 59,4 | 65,2 | 66,1 |
| identidade (597) | 75,4 | 71,0 | 71,9 |

Na rodada 2, 47 de 113 situações melhoraram ≥ 5 pontos e 12 pioraram ≥ 5: estou_bem 77 → 59, robo 62 → 46,
gosta 61 → 49, nao_era_isso 58 → 48, obrigado 94 → 86, entre outras.

## Limites (o que não é vitória)

- **A identidade fica abaixo do chat nas duas rodadas** (−3,5 a −4,4 pontos), e algumas situações caem mais de 10 pontos
  (estou_bem e robo nas duas). Os critérios fixados medem os blinds inteiros; estas perdas estão registradas e não somem.
- "legal e voce?" continua respondido como pergunta de identidade nas duas rodadas.
- Rodada 1: blind v4 exatamente no limite (−1,5). Rodada 2: usa o fato exatamente no limite (0,85).
- Na rodada 1, nenhuma versão passou a guarda do dev; na rodada 2, a escolhida passou.
- O `crise.py` continua respondendo às urgências antes de qualquer modelo no chat.

## Decisão

Candidata ao chat pela régua própria, nas duas rodadas. **Ligar é decisão do criador.** Para ligar, falta:
1. exportar os pesos para NumPy (int8 por linha, como o 46M atual) com conferência NumPy × PyTorch;
2. ligar no `conversa_v3d.py` com o SHA novo;
3. rodar os testes do site e do APK.
