# v7c — resultado da rodada 1 (20/10/2026)

L4, semente 20261019, desde a base 6a com substituição. 2.856 passos; escolhido o passo 2.536 (pesos crus). Pesos:
`CRIVO/transformer-crivo-46m-conversa-v7c/rodada1/conversa_20261020_071157/pesos.pt`. Resumo: `resumo_v7c_rodada1.json`.
**Professor: ~5% das exposições de conversa** (falas da pessoa; respostas das listas). `ativo_no_chat: false`.

**A primeira rodada que passa nos 5 critérios.** Não passou com folga, então a rodada 2 continua obrigatória
(regra fixada antes, `comparar_v6.FOLGA_UMA_RODADA`).

| blind | v4 (chat) | v7b r1 | v7c r1 | v7c − v4 [IC 95%] | critério |
|---|---|---|---|---|---|
| v3 | 65,4 | 71,2 | 71,6 | **+6,3 [+4,9; +7,7]** | ✅ |
| v1 | 65,7 | 73,4 | 74,8 | **+9,0 [+7,3; +10,7]** | ✅ |
| paráfrases | 73,7 | 80,8 | 78,9 | **+5,2 [+3,8; +6,5]** | ✅ |
| Grok | 73,4 | 73,5 | 75,8 | **+2,5 [+1,2; +3,7]** | ✅ |
| v4 | 92,5 | 90,8 | 91,0 | −1,5 [−3,8; +0,8] | ✅ exatamente no limite (−1,5) |

- **Urgência: 118 acertos contra 102** ✅ (v7: 79; v7b: 97). saude_urgente 84 → 99, ansioso_peito 16 → 17.
- Frases reais: **12/15** ✅ (v4: 12). Ganhou "serio mesmo?" ("É comigo mesmo! Sou o CRIVO."); errou "legal e voce?"
  (identidade de novo), "e cade as respostas boas?" e "tá vendo claude?…".
- Usa o fato: 0,95 ✅.

## Por grupo (soma dos blinds antigos)

| grupo | v4 | v7b | v7c |
|---|---|---|---|
| com falas novas (10.743) | 71,1 | 76,6 | 76,7 |
| saúde e urgência (224) | 59,4 | 47,8 | **65,2** |
| identidade (597) | 75,4 | 69,5 | 71,0 |

43 de 113 situações melhoraram ≥ 5 pontos; 14 pioraram ≥ 5 (as maiores: estou_bem 77 → 63, nao_era_isso 58 → 44,
confirma_crivo 98 → 85, medo 71 → 61). No blind v4, toda a perda vem de confirma_crivo (−20 frases; reciproco +7).

## Guarda do dev

O 46M do chat no dev: sentido 0,622; grupos urgência 63/85, identidade 62/84, conversa 179/242, saúde 44/78.
**Nenhuma versão passou a guarda**: em todas, a identidade ficou de 1 a 4 frases abaixo do chat no dev. Pela regra, ficou
a de maior folga no pior grupo: passo 2.536, pesos crus (sentido 0,704; urgência 71/85; identidade 60/84; conversa
187/242; saúde 52/78). A média móvel (EMA) teve mais sentido no total, mas folga pior na urgência ou na identidade.

## Leitura e limites

- É a primeira rodada aprovada pelos critérios fixados, mas com o blind v4 **exatamente** no limite e a identidade
  abaixo do chat (blinds −4,4; dev −2 frases). A rodada 2 diz se isso se repete com outra semente.
- A saúde e a urgência, que derrubavam as versões anteriores, agora ficam **acima** do chat.
- Promover para o chat continua sendo decisão do criador, depois das duas rodadas.
