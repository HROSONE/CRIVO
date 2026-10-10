# Conclusão da curva de replay — 10/10/2026

## Resultado do critério congelado

A dose 2× foi comparada contra 1× usando exatamente o critério registrado antes do treino. O holdout final conhecido do PR #137 permaneceu excluído.

| Dose | CE antiga | Exatas antigas | CE nova | Exatas novas | CE total |
|---:|---:|---:|---:|---:|---:|
| 0× | 1,265409 | 20/334 | 5,471622 | 0/94 | 1,828367 |
| 1× | 0,943481 | 47/334 | 4,262217 | 1/94 | 1,387659 |
| 2× | 0,799406 | 73/334 | 4,392715 | 1/94 | 1,280333 |

Critério pré-congelado 2× vs. 1×:

- reter desenvolvimento antigo: **passou**;
- não regredir correspondência literal nova: **passou**;
- melhorar CE nova: **falhou**;
- sucesso conjunto: **falhou**.

## O que aprendemos

Aumentar replay de 1× para 2× melhora fortemente a retenção antiga: a CE antiga cai de 0,943481 para 0,799406 e as correspondências literais antigas sobem de 47 para 73/334.

Porém isso não melhora a aprendizagem das famílias novas. As correspondências novas ficam em 1/94 e a CE nova piora de 4,262217 para 4,392715. Portanto o replay está funcionando como proteção contra esquecimento, mas aumentar sua dose desloca o treinamento ainda mais para o comportamento antigo sem resolver a generalização nova.

Isso encerra a hipótese de que a regressão do PR #137 possa ser resolvida simplesmente aumentando replay. O problema restante é de **estabilidade/plasticidade**: o gerador precisa aprender padrões novos sem apagar os antigos, e não apenas reapresentar mais exemplos antigos.

## Decisão

- Não aumentar replay além de 2× nesta frente.
- Não promover o checkpoint 2×.
- Não usar o holdout conhecido para escolher outra dose.
- Manter todos os checkpoints desta curva como `aprovado: false` e `ativo_no_chat: false`.
- Não alterar runtime, checkpoint público, memória, acervo, arquitetura ou número de parâmetros.

## Próximo trabalho único

Testar **ancoragem de pesos durante a adaptação**, mantendo o corpus, o léxico realocado, a dose 1× de replay, a arquitetura e os hiperparâmetros-base.

A próxima fase deve comparar, com protocolo congelado antes do treino:

1. **controle 1× já existente**;
2. **1× + ancoragem suave aos pesos anteriores**, penalizando deslocamento dos parâmetros que já carregavam comportamento útil.

A ancoragem deve ser aplicada como termo de regularização da atualização, não como uma nova regra de diálogo e não como congelamento total. O objetivo é testar se é possível conservar mais do desenvolvimento antigo **sem sacrificar a CE das famílias novas**.

Critério sugerido para a próxima fase, a congelar antes do treino:

- retenção antiga não pior que 1×;
- CE nova estritamente melhor que 1×;
- correspondência nova não pior que 1×;
- nenhum checkpoint é promovido com base apenas em desenvolvimento conhecido.

Se a ancoragem recuperar retenção sem bloquear o aprendizado novo, ela passa a ser candidata para uma avaliação inédita futura. Se também bloquear o novo, o problema deixa de ser principalmente esquecimento e passa a apontar para representação/capacidade de generalização do gerador atual.

## Limites

- 2× também executa mais atualizações por época; portanto esta curva mede a dose efetiva de replay no procedimento atual, não separa completamente peso estatístico de compute adicional.
- Correspondência literal não mede conversa natural nem compreensão semântica.
- O desenvolvimento é conhecido e autoral; esta fase é diagnóstica.
- O holdout final de 10 sessões do PR #137 continua regressão conhecida e não pode ser reapresentado como avaliação inédita.
