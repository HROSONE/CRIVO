# Diagnóstico de transferência — 10/10/2026

Sem treino e sem alteração de pesos. Usa o checkpoint 1× e somente os 94 exemplos novos de desenvolvimento já conhecidos; o holdout final do PR #137 não foi lido.

- CE média com histórico: **4.1516**
- CE média sem histórico: **5.9147**
- Exatas com histórico: **1/94**
- Exatas sem histórico: **1/94**

## Por família

| Família | N | CE full | CE sem hist | Δ sem-full | Exatas full | Vizinho treino |
|---|---:|---:|---:|---:|---:|---:|
| correcao_autoria | 24 | 3.9386 | 6.6204 | 2.6818 | 0 | 0.360 |
| esperar_sem_garantia | 24 | 3.8856 | 5.8633 | 1.9777 | 0 | 0.386 |
| moradia_e_tarefas | 22 | 4.4024 | 5.4196 | 1.0172 | 1 | 0.439 |
| pessoa_silencio | 24 | 4.4006 | 5.7142 | 1.3136 | 0 | 0.335 |

## Por posição do turno

| Turno | N | CE full | CE sem hist | Δ sem-full | Exatas | Primeiro erro médio |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 14 | 4.0547 | 4.0547 | 0.0000 | 1 | 0.15 |
| 2 | 16 | 4.6108 | 5.8494 | 1.2386 | 0 | 0.25 |
| 3 | 16 | 5.0005 | 6.4921 | 1.4916 | 0 | 0.00 |
| 4 | 16 | 4.1693 | 6.9197 | 2.7504 | 0 | 0.25 |
| 5 | 16 | 3.2972 | 5.7926 | 2.4954 | 0 | 0.25 |
| 6 | 16 | 3.7648 | 6.1471 | 2.3824 | 0 | 0.00 |

## Por categoria de token

| Categoria | Tokens | NLL média | NLL mediana |
|---|---:|---:|---:|
| copia_oov | 66 | 4.3367 | 3.7068 |
| eos | 94 | 0.3287 | 0.0761 |
| geracao_lexical | 371 | 6.0482 | 5.5414 |
| vocab_e_fonte | 315 | 3.3170 | 3.2262 |

## Flags pré-congeladas

- Histórico prejudica materialmente: **não** (full − sem histórico = -2.0717 nos turnos 2–6).
- Gap geração lexical vs. tokens disponíveis na fonte: **sim** (Δ NLL = 2.5546).
- Divergência muito cedo: **sim** (100.0% das não-exatas divergem até índice 2).
- Erro cresce nos turnos finais: **não** (Δ CE turnos 5–6 − 1–2 = -0.8203).

## Limites

Desenvolvimento conhecido serve somente para diagnóstico. Jaccard usa apenas entradas, nunca o alvo. CE token a token usa teacher forcing. Nenhuma capacidade nova é alegada e nenhum checkpoint é promovido.
