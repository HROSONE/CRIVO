# Pointer Copy Causal v1

Objetivo: testar se o gargalo de preservação de identidade do CRIVO está na ausência de uma via explícita de cópia, sem alterar os pesos do Transformer base.

## Intervenção única

- Base: checkpoint `05_05_dialogo_estado` do treino curricular longo.
- Transformer congelado.
- lm_head congelado (no CRIVO ele é tied com `embedding.weight`).
- Única parte treinável: pointer low-rank (rank 32) + gate geração↔cópia.
- O pointer só pode copiar tokens não-especiais da mensagem-fonte.
- Sem pesos externos e sem modelos de terceiros.
- `ativo_no_chat=false` e `promovido=false` durante todo o experimento.

A distribuição de saída usada na inferência experimental é:

`P(y) = g * P_vocab(y) + (1-g) * P_copy(y)`

onde `P_vocab` continua sendo a saída congelada do CRIVO e `P_copy` soma a atenção do pointer nas posições-fonte que contêm o token candidato.

## Treino

- 1.000 passos.
- Base completamente congelada.
- 25% do batch contém exemplos cujo alvo não requer copiar a entidade, para evitar colapso do gate em `copy`.
- Nomes de treino usam múltiplas famílias lexicais e não compartilham um prefixo fixo.
- Checkpoint escolhido pelo desenvolvimento prioriza cópia exata e usa semântica como desempate.

## Holdout congelado

- 100 entidades nunca vistas.
- Nomes entre 1 e 4 tokens segundo o tokenizer do CRIVO.
- 100 casos de cópia pura.
- 500 casos semânticos: categoria, função, invariância, composição e negação.
- Grupos `close` e `distant` por família lexical.
- Definição varia entre início, meio e fim do prompt.
- Métricas: exact copy, distância de edição, desempenho por comprimento, grupo lexical e posição, além das tarefas semânticas.

## Gates congelados

- Exact copy geral >= 70%.
- Exact copy em `distant` >= 65%.
- Diferença `close` vs `distant` <= 10 p.p.
- Spread início/meio/fim <= 10 p.p.
- Regressão em função <= 5 p.p. contra o baseline do mesmo holdout.
- Regressão semântica geral <= 2 p.p. contra o baseline do mesmo holdout.
- Hash dos pesos base deve ser idêntico antes e depois do treino.

Passar tecnicamente ou reduzir loss não autoriza promoção para o chat. O resultado precisa ser analisado antes de qualquer integração.
