# Treino do mecanismo de saída lexical — 10/10/2026

Um único candidato. Mesmos dados, replay 1×, vocabulário, inicialização, arquitetura e hiperparâmetros do controle. A única mudança é a ponderação da loss **somente durante treino**: +0,75 nos três primeiros alvos e +0,75 nos alvos lexicais que não estão disponíveis por cópia. Validação e avaliação permanecem não ponderadas.

| Condição | CE antiga | Exatas antigas | CE nova | Exatas novas | NLL lexical | Erros token 0 |
|---|---:|---:|---:|---:|---:|---:|
| controle 1× | 0.943481 | 47/334 | 4.262217 | 1/94 | 6.0482 | 84 |
| loss ponderada | 0.837450 | 41/334 | 5.017282 | 0/94 | 7.0423 | 81 |

## Critério pré-congelado

- Reter antigo: **não**.
- Melhorar novo: **não**.
- Melhorar saída lexical: **não**.
- Melhorar abertura: **sim**.
- Sucesso conjunto: **não**.

## Integridade

- Holdout final conhecido do PR #137: **não lido**.
- Nenhum checkpoint público foi alterado.
- Nenhuma regra de diálogo, memória, acervo, modelo externo, arquitetura ou parâmetro foi adicionado.
- Este desenvolvimento é conhecido e não prova generalização; mesmo um candidato aprovado aqui não é promovido nesta fase.
