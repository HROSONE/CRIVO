# Escola Cognitiva do CRIVO

Esta fase ensina organização interna antes de aumentar Transformer, RAG, acervo ou parâmetros.

## Regra principal

Os professores existem **somente durante o treino**. Eles aplicam perdas auxiliares ao estado interno da GRU para forçar representações mais úteis, mas não recebem mensagens em produção, não escolhem respostas e não são serializados no checkpoint final.

## Primeira turma

A primeira ablação separa o rótulo monolítico usado no PR #146 em duas dimensões:

- **AÇÃO**: recordar, corrigir, avaliar, escrever, perguntar;
- **FOCO**: pessoa, objeto, estado, atividade, detalhe.

Exemplos:

- `recordar_pessoa` -> `AÇÃO=recordar`, `FOCO=pessoa`;
- `recordar_objeto` -> `AÇÃO=recordar`, `FOCO=objeto`;
- `corrigir_pessoa` -> `AÇÃO=corrigir`, `FOCO=pessoa`.

O peso auxiliar total permanece **0,25**, igual ao PR #146: `0,125 + 0,125`. Assim, esta rodada testa a fatoração, e não uma simples mudança de intensidade da supervisão.

## Disciplina experimental

1. congelar prova prospectiva nova;
2. auditar sobreposição e gerabilidade;
3. só depois adicionar workflow de treino;
4. treinar um único candidato;
5. selecionar época apenas por CE de geração conhecida;
6. abrir a prova prospectiva somente após seleção;
7. manter checkpoint `ativo_no_chat=false` até passar preservação + generalização;
8. não aumentar RAG, acervo, Transformer ou parâmetros nesta fase.

## Próximos professores possíveis

Somente depois de validar a fundação: estado factual, referência, temporalidade, causalidade, certeza/hipótese, objetivo e continuidade. Eles não entram todos de uma vez; cada professor precisa provar ganho causal antes de permanecer na escola.
