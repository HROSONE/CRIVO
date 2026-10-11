# Auditoria pareada do Transformer 17,43M — V1 × V4 × V5

Esta frente é **diagnóstica**. Não treina, não seleciona checkpoint, não altera pesos e não autoriza promoção para o chat.

## Pergunta causal

As avaliações V4 e V5 originais usaram holdouts prospectivos diferentes. Antes de propor outra arquitetura, esta auditoria coloca V1, V4 e V5 diante dos **mesmos 120 casos novos**, congelados antes da execução.

Além de operação/slot/primeiro token/CE, a sonda mede:

- acurácia token a token sob teacher forcing;
- posição da primeira divergência na geração greedy;
- se o token esperado na divergência já existia na fonte;
- se a divergência ocorre dentro de uma entidade requerida;
- pointer no início exato e em qualquer token do span da entidade;
- comprimento BPE dos slots e taxa de slots multi-token;
- estabilidade do pointer nos quatro primeiros tokens gerados.

## Checkpoints imutáveis

- V1: run `38112043184`, pesos `849bc4655820f8cd1f445539a1bd0f01959f03ce38145ece460c0fe27568c661`.
- V4: run `38154299065`, checkpoint composto `c53981fda15f31fcc22b3355a8eb75551ce85907926960c1776774db0d9f2cda`.
- V5: run `38160159893`, checkpoint composto `03a0bdc2241d01029df2ff34e2dc2aace1209bf90e6303ce50c9bb9b41758a89`.

## Holdout diagnóstico

- 120 casos, 20 por operação, 5 famílias novas;
- gerador SHA-256 `58807e8fb9b6ce00aec82a491f19a6fdfceb0da8c389f68ac74c32e6ec224ef5`;
- holdout canônico SHA-256 `55fab7f65ded87c721fe44bf84d6b69a1153c32caa3675feb95ce1a7887707f0`.

Os resultados desta auditoria servem somente para escolher **uma** próxima intervenção causal. Os gates de promoção existentes não são alterados.
