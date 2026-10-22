# v6 entendimento — resultado da rodada 1 (19/10/2026)

A100 80 GB, conta henriquenbk18, commit `68d5b6c`, semente 20261019. 3.018 passos; escolhido o passo 2.345 pelo sentido
no dev (68,9%). Pesos: `CRIVO/transformer-crivo-46m-conversa-v6/rodada1/conversa_20261019_200853/pesos.pt`, sha256
`59db0066daa6…`. Resumo: `resumo_v6_rodada1.json` (cópia do Drive). Linhas frase a frase ficam no Drive
(`linhas_rodada1.json`, `linhas_v4_base.json`). `ativo_no_chat: false`. Dados do professor: 0%.

**Não passou nos critérios fixados antes de rodar** (falhou "outros blinds sem piorar", por causa do blind v4). Por isso,
qualquer que seja a rodada 2, esta versão não é candidata ao chat.

## Comparação pareada com o 46M v4 do chat (mesmas frases, mesmo freio)

| blind | v4 (chat) | v6 r1 | diferença [IC 95%] | critério |
|---|---|---|---|---|
| v3 (2.980) | 65,4% | 68,7% | **+3,3 [+1,9; +4,7]** | IC > 0 ✅ |
| v1 (2.004) | 65,7% | 69,8% | +4,0 [+2,2; +5,7] | ≥ −1,5 ✅ |
| paráfrases (3.000) | 73,7% | 79,0% | +5,2 [+3,9; +6,5] | ≥ −1,5 ✅ |
| Grok (2.980) | 73,4% | 72,8% | −0,6 [−1,9; +0,6] | ≥ −1,5 ✅ |
| v4 (600) | 92,5% | 89,8% | **−2,7 [−4,3; −1,0]** | ≥ −1,5 ❌ |
| v6 (525, não decide) | 59,4% | 64,8% | +5,3 [+2,1; +8,8] | — |

Frases reais: 12/15 nas duas (v6 errou "legal e voce?", "serio mesmo?" e "e cade as respostas boas?"). Usa o fato: 0,9.
Sem o freio de repetição, blind v3 69,5%.

Leitura fixada antes: blind v3 subiu com IC acima de zero, mas menos de 5 pontos → **apoio fraco** à hipótese.

## Onde ganhou e onde perdeu (soma dos blinds antigos)

Nas situações que o v6 reforçou, o ganho foi grande; nas outras, houve perda:

| blind | situações reforçadas | outras situações |
|---|---|---|
| v3 | 56,4 → 61,4 | 76,5 → 77,6 |
| v1 | 57,4 → 70,9 | 73,8 → 68,7 |
| paráfrases | 59,1 → 69,6 | 95,6 → 93,0 |
| Grok | 74,6 → 76,7 | 71,9 → 68,0 |

Maiores ganhos (v4 → v6, situações com ≥ 30 frases): oi 37 → 84, perguntar_crivo 35 → 81, pedido_desculpa 38 → 79,
risada 26 → 54, escola_dificil 39 → 64, desisto 36 → 60, nao_era_isso 58 → 80, teste 25 → 46.

Maiores perdas: amor_bom 42 → 3, desisto_despedida 84 → 51, boa_noite 90 → 66, motivacao 46 → 25, estou_bem 77 → 58,
medo 71 → 51, tem_certeza 87 → 70; no blind v4, reciproco caiu (76% contra 81% da v4).

Hipóteses para as perdas, **não conferidas** (as linhas compactas não guardam as saídas):
- "boa noite, vou descansar" (despedida_dormir) pode ter puxado "boa noite" para dormir;
- desisto ganhou frases fortes ("deixa pra lá, não vai dar") e pode ter engolido desisto_despedida;
- estou_bem ganhou casos depois de "como você está?", o mesmo turno anterior de reciproco ("tô bem, e você?");
- amor_bom × amor_dor: o contraste "a pessoa que eu gosto (não) gosta de mim" pode ter confundido as duas.

## Limites

- Uma rodada, uma semente. A rodada 2 só confirmaria a variação; ela não muda a reprovação.
- O blind v6 é do mesmo autor do treino.
- A régua continua de listas fechadas.

## Próximo passo sugerido (não decidido)

Um v6b com as mesmas falas e correções das perdas acima: contraexemplos para boa_noite, desisto_despedida, estou_bem ×
reciproco e amor_bom, e mais falas nas situações "outras" que caíram. Depois, de novo duas rodadas com os mesmos critérios.

## Diagnóstico depois do resultado (20/10/2026)

`diagnosticar_v6.py` comparou cada frase que a v4 acertava e a v6 errou com as falas de treino do v6 (n-gramas). As
perdas vieram de **palavras-gatilho criadas pelas falas do v6**, não de sentido:

| frase do teste (v4 certo, v6 errado) | fala de treino do v6 mais parecida | situação que puxou |
|---|---|---|
| "comecei a namorar" (amor_bom) | "comecei a jogar xadrez online" | jogo_conta |
| "você é só um programa" (robo) | "você é um crush" | flerte |
| "você é de verdade?" (ser_humano) | "você seria meu amigo de verdade?" | amigo |
| "tranquilo" (estou_bem) | "tudo tranquilo com você?" | oi_tudo_bem |
| "esquece isso, até mais" (desisto_despedida) | "abraço, até mais" | despedida |
| "entra no meu email pra mim" (nao_consegue) | "pra mim chega, fui" | desisto_despedida |
| **"tô sangrando muito" (saude_urgente)** | "tô procrastinando muito" | motivacao |
| **"minha avó passou mal" (saude_urgente)** | "minha avó tá internada" | familia_preocupa |

**Urgência piorou:** somando os blinds, as situações de urgência caíram de 102 para 88 acertos. No chat, o crise.py
responde antes do modelo, mas o modelo não pode piorar nisso.

**Parte do ganho era quase cópia.** 97 frases do blind v3 (3%) têm cosseno de n-gramas ≥ 0,7 com uma fala de treino do v6.
Nelas, o acerto subiu 43 pontos. Sem elas:

| blind | ganho total | ganho nas frases distantes do treino v6 |
|---|---|---|
| v3 | +3,3 | +1,9 (n = 2.883) |
| v1 | +4,0 | +4,0 (n = 1.882) |
| paráfrases | +5,2 | +4,1 (n = 2.729) |
| Grok | −0,6 | −0,8 |
| v4 | −2,7 | −2,1 |

O efeito existe nas frases distantes (v1 e paráfrases), mas é menor do que a primeira tabela sugeria. Correção: o
ganho do blind v3 atribuível a entendimento novo é de cerca de +1,9 ponto, não +3,3.

A correção é o v6b (README, seção v6b).
