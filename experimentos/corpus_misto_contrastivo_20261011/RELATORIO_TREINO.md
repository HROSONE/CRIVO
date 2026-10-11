# Treino misto-contrastivo — resultado

Um único candidato; mesma rede de 81.433 parâmetros, vocabulário 720, inicialização e 3.699 exemplos totais.

## Preservação

| Recorte | Controle 1× | Fatorial puro | Misto |
|---|---:|---:|---:|
| old334 CE | 0.943 | 0.723 | 0.798 |
| old334 exatas | 47/334 | 64/334 | 77/334 |
| known94 CE | 4.262 | 7.125 | 4.896 |
| known94 exatas | 1/94 | 0/94 | 0/94 |
| fatorial96 CE | 3.367 | 0.658 | 0.932 |
| fatorial96 operações | 5.2% | 38.5% | 38.5% |

## Prospectivo 120 — não usado na seleção

| Medida | Controle 1× | Fatorial puro | Misto |
|---|---:|---:|---:|
| CE | 3.444 | 1.300 | 1.258 |
| Exatas | 0/120 | 10/120 | 11/120 |
| Primeiro token | 10.8% | 16.7% | 23.3% |
| Operações | 11.7% | 16.7% | 17.5% |

## Gate pré-congelado

- old334_exatas: **PASSOU**.
- old334_ce: **PASSOU**.
- known94_exatas: **FALHOU**.
- known94_ce: **FALHOU**.
- fatorial_operacoes: **PASSOU**.
- fatorial_ce: **PASSOU**.
- prospectivo_ce: **FALHOU**.
- prospectivo_primeiro: **FALHOU**.
- prospectivo_operacoes: **FALHOU**.
- prospectivo_total: **FALHOU**.
- prospectivo_por_operacao: **FALHOU**.

**Sucesso conjunto: NÃO.**

Checkpoint permanece experimental e `ativo_no_chat=false`.
