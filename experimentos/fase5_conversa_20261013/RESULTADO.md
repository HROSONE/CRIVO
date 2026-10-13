# Fase 5 — resultado (13/10/2026)

Execução no Colab (T4, conta henriquenbk): `CRIVO/transformer-17m-fase5/fase5_*/`, pesos sha256
`71efe3a2623da70f6ea01310f5edfad67a5c0026028d64eb3eafb421f19520a4`. Partiu dos pesos da fase 3
(`745a2500…`), 5.000 passos (melhor ponto do dev: o último). Resultado completo, com todas as
saídas do blind, em `resultado_fase5.json.gz`.

**Gates: 9 de 10. Reprovado** em "cada situação ≥ 60%". `ativo_no_chat: false`.

| Critério | Fase 3 sem ajuste (amostra de 600) | Fase 5 (blind inteiro, 3.607) | Gate |
|---|---|---|---|
| tudo_ok | 72.0% | 95.7% | 85% |
| usa_fato | 81.2% | 99.8% | 90% |
| nome_exato | 50.0% | 95.2% | 90% |
| marca_nao_sei | 5.0% | 93.0% | 90% |
| marca_urgente | 0.0% | 100.0% | 95% |
| marca_saude | 0.0% | 93.3% | — |
| marca_desculpa | 16.7% | 58.0% | — |
| marca_despedida | 0.0% | 56.1% | — |
| terminou | 94.0% | 99.3% | 95% |
| sem_numero_inventado | 99.2% | 100.0% | 97% |
| sem_nome_inventado | 98.8% | 100.0% | 95% |

Perda de linguagem: 3,0675 → 3,1387 (+2,3%; o limite era +10%). O português geral foi preservado.

## Situações abaixo de 60%

| Situação | tudo ok | n |
|---|---|---|
| dificil_falar | 0,0% | 19 |
| despedida_rude | 23,1% | 13 |
| nao_consegue | 31,6% | 19 |
| despedida_dormir | 33,3% | 12 |
| voce_confunde | 37,5% | 16 |
| nunca_ensinaram | 41,7% | 12 |
| nome:corrigir | 50,0% | 2 |
| dia | 58,3% | 12 |

## O que isso mostra

- **Onde a variedade de treino era grande, ele generalizou.** Os assuntos do blind, os nomes e as
  perguntas fora do acervo nunca foram vistos no treino, e mesmo assim:
  - usa o fato do contexto em 99,8%;
  - copia o nome certo em 95,2% (a fase 3 sem ajuste: 50%);
  - diz que não sabe em 93,0% (era 5%);
  - leva urgência ao 192 em 100% (era 0%);
  - não inventou nenhum número nem nome próprio.
- **Onde cada situação tinha só ~6 jeitos de falar, ele decorou gatilhos de palavra.** O blind
  dessas situações usa as duas formas de fala tiradas do treino, e ele respondeu pela palavra, não
  pelo sentido:
  - "você não ajuda" → "Tô aqui pra ajudar. Do que você precisa?";
  - "vou deitar" → "Beleza, menos texto.";
  - "flw, inútil" → "Tudo bem, sim! … E você, como está?";
  - "olha essa foto" → respostas de outras situações.

  É o mesmo limite de entendimento que o CRIVO de regras tem, agora medido no 17M.

## Limites

- O blind mede forma e verdade, não se a resposta é a melhor; falta ler o lado a lado.
- Uma execução, uma semente.
- A porta com as conversas reais do criador não foi rodada: o gate falhou antes.

## Próximo passo

O que falta é **variedade de jeitos de dizer a mesma coisa**, não mais passos de treino. Para a
v2, cada situação precisa de dezenas de formas de fala (gíria, sem acento, frase longa, frase
curta, com e sem contexto), escritas antes de rodar e com um blind novo.
