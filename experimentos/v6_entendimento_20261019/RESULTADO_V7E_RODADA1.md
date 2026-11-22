# v7e — resultado da rodada 1 (28/10/2026)

T4, semente 20261019, commit `036c32e`. Treino completo: 2.859 passos. A guarda escolheu o **passo 951 (pesos crus)**, e
nenhuma versão passou a guarda. Pesos: `CRIVO/transformer-crivo-46m-conversa-v7e/rodada1/conversa_20261028_054107/pesos.pt`.
Resumo: `resumo_v7e_rodada1.json`. Professor: 4,6% das exposições de conversa. `ativo_no_chat: false`.

## A régua: não passou

| blind | v7c (chat) | v7e r1 | v7e − v7c [IC 95%] |
|---|---|---|---|
| v3 | 71,8 | 68,1 | **−3,8 [−5,2; −2,4]** |
| v1 | 72,7 | 73,1 | +0,0 [−1,6; +1,7] |
| paráfrases | 81,8 | 75,5 | **−6,4 [−7,7; −5,2]** |
| Grok | 74,4 | 72,0 | −2,4 [−3,8; −1,0] |
| v4 | 92,3 | 89,3 | −3,0 [−5,2; −0,8] |

| critério | v7e r1 | mínimo |
|---|---|---|
| blind v3 com IC > 0 contra o v7c | não | sim |
| outros blinds ≥ −1,5 | não | sim |
| frases reais | 12/15 | ≥ 12 |
| usa o fato | passou | ≥ 0,85 |
| urgência (acertos; chat 117) | 119 | ≥ 117 |

Como os critérios exigem as duas rodadas, **o v7e está reprovado**. O v7c continua no chat.

## O que o resultado mede (e o que não mede)

**A guarda do dev escolheu um passo cedo demais.** Nenhuma versão ficou com identidade igual ou acima do chat no dev
(61/75), e a regra fixada manda ficar com a de maior folga no pior grupo: a do passo 951 (60/75), um terço do treino. O
v7c, com a mesma regra, ficou com o passo 2.853. Nas medidas do dev, as versões mais tardias tinham mais sentido no total
(EMA 2219: 74,2% contra 72,7% do chat), mas identidade de 53 a 55/75.

**As maiores perdas são em situações que a limpeza quase não tocou:** escola_dificil −41,5 pontos (1 correção),
seja_breve −27,0 (1), gosto_bichos −27,6 (3), motivacao −18,9 (0), escola_boa −16,1 (1). Isso aponta para um modelo
pouco treinado, e não para um efeito da limpeza. **Ganhos em situações que a limpeza tocou ou vizinhas:** robo +20,9,
entediante +14,3, voce_aprende +8,1, opiniao_vida +6,9, conversar +9,3; e sono +22,4, saude_geral +14,1. Os blinds
somados por situação vêm de `linhas_rodada1.json`, pareados com a linha de base do v7c nas mesmas frases.

Então esta rodada **não responde** se limpar os rótulos ajuda. Ela mostra que a regra da guarda (identidade sem folga, num
grupo de 75 frases) escolhe pesos pouco treinados quando nenhuma versão empata com o chat em identidade. A mudança na
guarda (tirar as falas do professor do dev) foi decidida pelo assistente antes do treino e pode ter contribuído: o grupo
de identidade ficou com 75 frases, contra 84 no dev do v7c.

## Limites

- Uma rodada, uma semente. Só os pesos do passo 951 e o checkpoint final (passo 2.859, crus e EMA) existem; os passos
  intermediários não foram guardados.
- Qualquer medida do checkpoint final nos blinds, feita agora, seria **diagnóstico** (escolhido depois de ver o resultado)
  e não pode aprovar pesos.

## Próximo passo sugerido

Não rodar a rodada 2 com a mesma regra: ela não pode mais aprovar o v7e. Antes de qualquer novo treino, decidir e
fixar uma regra de escolha que não caia em pesos pouco treinados (por exemplo, só concorrem versões da segunda metade do
treino) como uma versão nova (v7f), com as duas rodadas de novo.
