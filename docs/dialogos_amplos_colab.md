# Diálogos ampliados para o Colab

O corpus v2 amplia a variedade de conversa e reduz a predominância dos exercícios
com uma única fórmula de resposta. É uma preparação de dados e treinamento, não
um candidato já treinado. A rodada usa pesos próprios aleatórios e não importa
modelos pré-treinados externos.

Abra [o notebook de diálogos ampliados](https://colab.research.google.com/github/HROSONE/CRIVO/blob/codex/dialogos-colab-amplos/notebooks/treinar_dialogos_amplos_colab.ipynb),
selecione GPU e execute na ordem. O notebook anterior continua disponível para
retomar sua rodada original; não misture seu checkpoint com este corpus.

## Dados preparados e conferidos

| Medida | Corpus anterior | Corpus v2 |
| --- | ---: | ---: |
| Pares de treino | 2.512 | 4.031 |
| Pares humanos de treino | 387 | 461 |
| Pares humanos de validação | 44 | 51 |
| Pares humanos de teste | 66 | 75 |
| Tokens supervisionados de diálogo no treino | 203.866 | 309.108 |
| Pares de treino com histórico | — | 2.459 |
| Pares totais, incluindo reservas | 3.174 | 5.026 |
| Contexto | 256 | 512 |

Os 3.570 pares não humanos de treino são sintéticos e identificados dessa forma.
O material autoral inclui **119 conversas distintas, 257 pares**, mais exercícios
calculados e explicações. Nem todos os pares autorais vão para treino: cenários
completos são separados por hash; duplicatas entre partições e contextos que
não cabem são recusados. Não se deve chamar cada variação de uma conversa humana
nova nem confundir pares, janelas, pessoas e cenários.

As 20 famílias cobrem conversa, esclarecimento, contexto, memória, correção,
restrição, hipótese, incerteza, evidência, compreensão, raciocínio, planejamento,
decisão, diagnóstico, aprendizado, ideias, escrita, resumo e programação,
além da família de diálogos humanos. Há perguntas indiretas, mudanças de objetivo,
referentes ambíguos, pedidos com informações insuficientes, correções de valores,
planos sob restrições, distinção entre causa e coincidência e casos JS/TS.

### Fontes e curadoria

OASST2 `ready` e a exportação `all` estão fixados na mesma revisão pública,
`179dd21fc55192153d94adb0e0ce8f69e222bf75`, licença Apache-2.0. A exportação
completa tem SHA-256 `820146830e78634170f5a33d79d0b3e5022a7f169ce054886ad1f16e1d53a764`.
As mensagens comuns precisam coincidir integralmente e não são contadas duas
vezes. OASST1 já está incluído; concatená-lo não criaria diálogos novos.

Todo o caminho até a resposta precisa ser humano, revisado e compatível com os
filtros de qualidade existentes. Contatos, identidades de outros assistentes,
alvos duplicados e erros identificados são recusados. A curadoria adicional
registra problemas de conteúdo e também recusa descendentes que dependem deles.
Os rótulos públicos não constituem verificação independente de todos os fatos.

Wikipedia permanece na revisão e nos artigos anteriormente verificados.
Nenhuma conversa privada, anexo do usuário ou saída do CRIVO é usada como dado.
Sondas e respostas esperadas de avaliação não são lidas pelo preparador.

O [relatório reproduzível](../avaliacoes/linguagem_profunda/corpus_dialogos_amplos_v2.json)
registra contagens, hashes, fontes e verificações. As reservas humanas anteriores
continuam fora do novo treino. IDs, árvores, entradas com histórico e alvos
normalizados são disjuntos entre treino, validação e teste.

## Amostragem e capacidade

O novo modelo tem **15.953.664 parâmetros**: a mudança é a tabela de posições
para contexto 512. Os oito blocos, dimensão 384, oito cabeças e tokenizer próprio
4096 continuam. É uma nova arquitetura incompatível com os pesos de contexto 256;
o notebook cria um experimento independente e preserva os anteriores.

No SFT, 75% das escolhas são humanas. Primeiro se escolhe um par humano e depois
uma de suas janelas, evitando prioridade automática para respostas longas.
Os demais exemplos são escolhidos primeiro por família sintética, depois por
par e janela. Uma família numerosa não domina só por ter mais linhas.
Essa distribuição é registrada no manifesto e na assinatura do checkpoint.
As porcentagens descrevem escolhas, não proporções garantidas de tokens.

30.000 passos × lote 12 × contexto 512 mantém o orçamento anterior de
**184.320.000 tokens-alvo** de pré-treino, com repetição dos aproximadamente
14,54 milhões de tokens de linguagem do corpus. Não são 184 milhões de textos
novos. O SFT continua com até 6.000 passos, replay de linguagem de 15%, seleção
pela validação humana completa e parada após cinco validações sem melhora.

O contexto maior permite incluir mais histórico, mas não cria memória permanente
nem garante compreensão. As conversas autorais que excedem a janela inteira são
recusadas. Respostas humanas longas mantêm janelas mascaradas: tokens do usuário
não são alvos, mas janelas posteriores podem perder parte do contexto anterior.

## Execução, retomada e avaliação

Os resultados ficam em `MyDrive/CRIVO/dialogos-amplos-v2`, separados do experimento
antigo. O ponteiro guarda a revisão exata do código. Retomada mantém Adam, RNG e
horizonte; mudança de corpus ou política exige uma nova rodada.

No celular, use `BLOCOS_POR_EXECUCAO = 1`. Com uma sessão estável pode aumentar
esse número para continuar por vários blocos. Cada bloco avança até 500 passos
ou aproximadamente 900 segundos e salva a cada 50 passos. Escrita e validação
podem ultrapassar o orçamento; uma queda pode perder trabalho desde o último
checkpoint completo. O notebook não mantém a sessão ativa nem contorna cotas.

O pré-treino precisa completar os 30.000 passos antes do SFT. Uma etapa que já
parou por validação não volta a treinar ao reexecutar a célula. O teste final só
é liberado após concluir o SFT ou encerrá-lo pela validação. Os relatórios
registram separadamente conclusão, pausa e parada por validação.

A comparação com o modelo anterior reconstrói as janelas no contexto menor
sem perder os tokens supervisionados. Exige o mesmo tokenizer verificado e
registra no relatório os dois contextos e a reconstrução.

Os testes locais verificam dados, matemática, amostragem, execução JavaScript,
retomada exata em CPU, preservação dos alvos na comparação e parada.
45 testes passaram, além de forward/backward em CPU com o modelo real de
15.953.664 parâmetros e contexto 512 em linguagem e diálogo. Não houve execução CUDA neste ambiente nem
medição de velocidade/memória numa T4. Menor perda precisa ser acompanhada de
respostas corretas em conversas novas; palavras esperadas não bastam para
aprovar uma resposta factual contraditória.

Compartilhe `baseline_2m6.json`, `candidato_16m.json`, `contrato_72.json` e os
relatórios de `pretreino/` e `dialogo/`. O candidato é exportado para `numpy/`,
sem ativação automática no site. A referência 2,6M já foi treinada antes, então
a comparação mede utilidade para o produto, não isola o efeito da arquitetura.
