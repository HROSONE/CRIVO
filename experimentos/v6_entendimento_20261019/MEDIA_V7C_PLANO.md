# Média das duas rodadas do v7c — plano fixado antes de medir (28/10/2026)

Pedido do criador: um 300M bom no chat; antes, "estuda em vez de aprender com os erros". Da leitura (Model Soups,
Wortsman et al., ICML 2022; WiSE-FT, CVPR 2022): a média dos pesos de modelos ajustados a partir da mesma base costuma
melhorar a robustez sem custo de inferência. O passo mais barato é testar isso no 46M que já existe.

**Pesos:** v7c rodada 1 (`d68bb3c26a65…`, passo 2.536) e rodada 2 (`e4067e3b4c97…`, passo 2.853, o do chat), os dois
da base 6a e dos mesmos dados. Média com α = 0,5, sem ajuste depois de ver resultado.

**Conferido na CPU (sem a régua):** distância relativa entre as rodadas de 0,036. A média responde normalmente: em 7
frases de teste, 5 iguais ao chat e 2 diferentes e adequadas ("tô muito cansado do trabalho" → "Imagino. Dia puxado cansa
o corpo e a cabeça. Conseguiu descansar um pouco?"). "legal e voce?" continua respondido como pergunta de identidade.

**Régua (a de sempre, contra o v7c do chat):** `comparar_v6.julgar_rodada` com urgência, nos mesmos blinds do v7c (dados
`gerar_v7c.py`, mesmo arquivo do professor), para a linha de base ser a da rodada 2 frase por frase. **Uma medida**:
a geração é gulosa e os pesos são fixos, e as duas rodadas da régua existem para a variação entre treinos.

**Notebook:** `notebooks/avaliar_media_v7c_colab.ipynb` (T4; sem treino). Passar não liga nada: ligar é decisão do
criador, depois da conversão para NumPy.

## Resultado (28/10/2026, T4, pesos `12e973acc311…`)

**Não passou** em dois dos cinco critérios.

| blind | v7c (chat) | média | média − v7c [IC 95%] |
|---|---|---|---|
| v3 | 71,8 | 73,4 | **+1,6 [+0,6; +2,5]** (passa: IC > 0) |
| v1 | 72,7 | 73,0 | +0,1 [−0,9; +1,0] |
| paráfrases | 81,8 | 79,9 | **−2,0 [−2,9; −1,1]** (limite −1,5) |
| Grok | 74,4 | 74,8 | +0,4 [−0,4; +1,2] |
| v4 | 92,3 | 93,5 | +1,2 [+0,0; +2,5] |
| v6 (do v7c) | 72,5 | 73,5 | (não entra nos critérios) |

Frases reais 13/15 (chat 13), usa o fato 0,90; urgência **115 contra 117 do chat** (critério ≥ 117). Erradas nas frases
reais: "legal e voce?" e "serio mesmo?" (as duas respondidas como identidade).

**Leitura:** é a primeira versão desde o v7c com IC > 0 no blind v3 contra ele. A perda em paráfrases era previsível: a
rodada 1 era a mais fraca nelas (+5,2 contra +8,2 da rodada 2 frente ao v4), e a média dilui a força da rodada 2. A
urgência caiu 2 acertos (ansioso_peito −9,6 pontos). No chat, o `crise.py` responde às urgências antes do modelo, mas o
critério é o critério.

**O que não fazer:** escolher outra proporção (por exemplo 70% da rodada 2) olhando estes mesmos blinds seria ajustar à
régua. Uma proporção nova só vale medida num teste que nenhuma escolha viu.
