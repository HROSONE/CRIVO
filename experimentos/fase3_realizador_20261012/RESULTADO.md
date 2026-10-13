# Fase 3 — o 17M como realizador do quadro: resultado (13/10/2026)

**Passou em todos os gates do teste cego.** Isso aprova o realizador para a próxima etapa (a
porta conversacional), **não** para o chat: `ativo_no_chat=false`, `promovido=false`.

- Base: a exportação da fase 2 (sha256 `57e809f4…9573384`).
- Treino: 1.500 passos de ajuste fino completo com replay do pré-treino; o melhor passo pelo dev,
  entre os que preservam a linguagem, foi o 1.250. Uma T4, cerca de 1 hora.
- Pesos: `MyDrive/CRIVO/transformer-17m-fase3/fase3_…/pesos.pt`, sha256
  `745a2500615559d822f4fdb4d3d1c72850f64a9eac32a210bd6e5881f1d0b293`, commit `6d69dd9`.
- Resumo, falhas e amostras: `resultado_resumo_fase3.json`. O resultado completo (755 KB, todas as
  523 saídas) fica no Drive, com sha256 `eba6e999…39ff1fc` registrado no resumo.

## Gates no blind (523 casos com assuntos, nomes e uma formulação nunca vistos)

| Métrica | Base (sem ajuste) | Realizador | Gate | Passou? |
|---|---|---|---|---|
| tudo ok | 0,0% | **98,3%** | ≥ 85% | sim |
| fatos fiéis | 0,0% | **93,7%** | ≥ 90% | sim |
| nome exato | 0,7% | **98,8%** | ≥ 90% | sim |
| terminou em `<fim>` | 0,0% | **100%** | ≥ 95% | sim |
| sem nome inventado | 94,1% | **99,8%** | ≥ 95% | sim |
| pior ato (tudo ok) | — | **93,7%** (explicar) | ≥ 70% em cada | sim |
| perda de linguagem | 2,9645 | 3,0385 (+2,5%) | ≤ +5% | sim |

Por ato: aceitar correção 99%, acolher 100%, esclarecer 100%, explicar 93,7%, falar de si 100%,
não sei 99%, recordar 99%, recusar 100%, registrar 98%, saudar 100%.

## As 9 falhas (todas listadas no resumo)

- **Nome cortado ou trocado (5):** "Rufepe" saiu "Rufe" quatro vezes, e "Topati" saiu "Popati".
  É o mesmo ponto fraco da fase 2: copiar nomes inventados de três sílabas.
- **Fato com uma palavra alterada (4):** "fixa o centro" → "fixa a centro", "empurrar alguém para
  parar" → "empurrar alguém parar" e casos parecidos. A frase continua legível, mas não é cópia
  fiel; no chat, a guarda de fidelidade recusaria essas respostas.

## O que este resultado não mostra

- **Não mostra conversa livre.** As respostas-alvo vêm de modelos de frase no tom da identidade,
  e o blind usa os mesmos modelos com assuntos, nomes e uma formulação novos. O realizador
  aprendeu a preencher esses modelos de forma confiável. Nos atos sem nome nem fato, ele quase
  não varia: 12 casos de acolher deram só 2 frases diferentes, e saudar e recusar deram uma.
- **Nem sempre o tom combina com o conteúdo.** Ele usa "Achei bonito isso, né?" depois de explicar
  o resfriado comum, porque o fecho é sorteado sem olhar o assunto.
- **Não testa o quadro real.** O quadro aqui foi montado pelo gerador; o do CRIVO vem de
  `estado_interno.py`, que ainda não monta esse formato.

## Próximo passo: porta conversacional (fase 4)

1. Um adaptador que transforma a decisão real do CRIVO (ato, fatos com fonte, nome) no quadro
   da fase 3, sem nenhum fato novo.
2. Um conjunto prospectivo congelado de conversas reais, escrito antes de olhar as saídas,
   comparando o motor atual com o realizador. A guarda de fidelidade e a revisão continuam
   valendo: uma frase com fato alterado ou nome trocado volta para o texto de sempre.
3. Só então um opt-in experimental como o #168 (dupla trava, SHA exato dos pesos).
