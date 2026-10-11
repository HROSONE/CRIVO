# Resultado da Escola Cognitiva v1 — Transformer 17,43M

Execução: GitHub Actions run `38112043184`, job `treino-candidato`.

## Base

- Transformer próprio do CRIVO: 17.428.224 parâmetros
- Pré-treino: 20.000 passos
- Pesos base SHA-256: `16102a72b21031b8bee2b4edfa633a359f7f08c5beab552b05f294e656b0cc67`
- Checkpoint candidato SHA-256: `849bc4655820f8cd1f445539a1bd0f01959f03ce38145ece460c0fe27568c661`
- `ativo_no_chat=false`

## Resultado prospectivo (120 casos)

| métrica | base | candidato |
|---|---:|---:|
| CE | 4.5628 | 1.8071 |
| primeiro token | 0.0% | 55.8% |
| operação correta | 4.2% | 44.2% |
| slot correto | 7.5% | 44.2% |
| exata | 0.0% | 0.0% |

Preservação relativa de CE em português: `0.9544` (passou o gate <= 1.05).

### Operação por operação

- corrigir_pessoa: 55%
- guardar_hipotese: 45%
- mensagem_sem_horario: 15%
- pedir_detalhe: 100%
- recordar_objeto: 0%
- recordar_pessoa: 50%

## Gates

Passaram:
- ganho de primeiro token >= 10 pp;
- melhora de CE >= 5%;
- preservação de português <= 5% de regressão.

Falharam:
- operação total >= 60%;
- cada operação >= 35%;
- slot >= 70%.

## Conclusão

A Escola Cognitiva sobre o Transformer é causalmente útil e muito superior à base crua para diálogo. O candidato, porém, ainda não é promovível. O próximo experimento deve manter replay de todas as operações e reforçar de forma contrastiva `recordar_objeto` e `mensagem_sem_horario`, usando um holdout novo congelado antes do treino. Não reutilizar este holdout como certificação inédita.
