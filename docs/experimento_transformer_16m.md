# Experimento CRIVO 16M

O candidato tem **15.855.360 parâmetros aprendíveis**: vocabulário próprio de
4.096 tokens, oito blocos causais, dimensão 384, oito cabeças e contexto de
256 tokens. A projeção de saída compartilha os pesos da entrada. A contagem
é conferida no modelo instanciado, não estimada pelo tamanho do arquivo.

O pré-treino começa aleatoriamente. O modelo anterior de 2.612.352 parâmetros
continua como referência e seus arquivos não são substituídos. O tokenizer
autoral é reutilizado; nenhum peso pré-treinado externo é importado. O SFT
carrega somente o pré-treino próprio **desta arquitetura**. Renomear os pesos
2,6M ou aumentar um número no relatório não cria uma rede 16M compatível.

## Dados e objetivos

O corpus usa a revisão pública fixada de Wikipedia em português e OASST2,
com licenças, hashes, curadoria e árvores de diálogo separadas por partição.
As demonstrações autorais sintéticas são identificadas e avaliadas à parte.
Conversas privadas e anexos do usuário não entram no corpus.

A preparação local selecionou 18.985 artigos para treino, 614 para validação
e 401 para teste. O treino tem 14.435.804 tokens de linguagem e 387 pares
humanos de diálogo; validação e teste têm 44 e 66 pares humanos. Essa escala
de diálogo ainda é pequena para conversar bem em situações abertas.

O currículo longo prevê 60.000 passos de pré-treino, lote 12, contexto 256:
até **184.320.000 tokens-alvo**, com repetição do corpus. O SFT prevê até
6.000 passos e preserva 15% de replay de linguagem. Metade dos exemplos
dos lotes SFT é humana; isso não significa metade dos tokens ou pessoas
diferentes em cada lote. Famílias sintéticas não ganham prioridade sobre
os humanos pela sua quantidade.

O pré-treino seleciona a menor perda de linguagem na validação. O SFT
seleciona a menor perda sobre **todos os tokens supervisionados dos diálogos
humanos de validação**. Os sintéticos não podem compensar uma piora humana.
Cinco validações consecutivas sem melhora encerram o SFT. O conjunto de
teste final, a sonda livre e os 72 contratos não selecionam checkpoints.

## Executar e retomar

Preferir o [notebook Colab](../notebooks/treinar_transformer_16m_colab.ipynb)
com GPU. Ele fixa a revisão do código no primeiro experimento, recupera essa
revisão nas próximas sessões e salva pesos, Adam, RNG, tokenizer e relatórios
diretamente no Drive. Reexecutar a célula de pré-treino retoma o checkpoint.
O notebook só inicia SFT depois de completar o horizonte de pré-treino.

O workflow `treinar-transformer-16m.yml` executa um **piloto em CPU** no
GitHub: até 6.000 segundos de pré-treino e 4.200 segundos de SFT. Isso
verifica o percurso completo e preserva o resultado em artifacts por 30 dias;
não conclui automaticamente o currículo longo. O relatório registra os
passos e tokens efetivamente executados, que precisam ser conferidos.
Um artifact intermediário preserva o pré-treino antes de começar o SFT.
Esse treino é independente do run anterior de conversa 2,6M.

Com as dependências de treino instaladas e o corpus preparado:

```sh
python scripts/experimento_transformer_16m.py --etapa config
python scripts/experimento_transformer_16m.py --etapa pretreino --corpus /caminho/corpus --saida /caminho/ensaio --dispositivo cuda --max-segundos 7200
python scripts/experimento_transformer_16m.py --etapa dialogo --corpus /caminho/corpus --saida /caminho/ensaio --dispositivo cuda --max-segundos 7200
python scripts/experimento_transformer_16m.py --etapa avaliar --corpus /caminho/corpus --saida /caminho/ensaio
```

O CLI permite SFT sobre pré-treino pausado para o piloto CPU. O operador
precisa distinguir isso de um currículo completo. `--max-segundos` pausa e
salva; não é um critério de qualidade. Retomada preserva Adam, RNG e horizonte
da taxa de aprendizado, recusando alterações de dados, arquitetura, código
ou política. A equivalência numérica exata foi testada no mesmo ambiente
CPU; trocar backend GPU/CPU ou versão das bibliotecas pode mudar os cálculos.

## Avaliação e ativação

O avaliador preserva respostas completas e separa loss humana/sintética na
validação e no teste. O contrato de 72 turnos compara o motor atual e o
candidato integrado, distinguindo respostas geradas das recuperadas pela
base factual. A exportação NumPy confere paridade com Torch.

Os arquivos para revisão são `baseline_2m6.json`, `candidato_16m.json`,
`contrato_72.json` e os relatórios em `pretreino/` e `dialogo/`, incluindo
`melhor/`. Os checkpoints de retomada são diferentes dos pesos de inferência.
Não apagar o checkpoint mais recente ao escolher o melhor para avaliação.

O modelo 2,6M já recebeu treino anterior, enquanto o 16M começa aleatoriamente.
A comparação verifica se o novo candidato serve melhor ao produto; não
isola o efeito do número de parâmetros. Uma ablação científica posterior
precisaria treinar ambos do zero com os mesmos dados e orçamento de tokens.
Perda menor e palavras esperadas numa resposta não certificam raciocínio.

Não há promoção automática ao site. Antes de ativar, exigir melhora humana,
seguir instruções e correções em diálogos novos, revisar afirmações factuais
e medir latência/memória no ambiente real. Os pesos usam aproximadamente
31,7 MB em FP16 ou 63,4 MB em FP32; Adam, ativações, caches e arquivos de
checkpoint aumentam o consumo total.

O experimento amplia o componente de linguagem, mantendo o mesmo contexto.
Não liga automaticamente o workspace cognitivo estruturado da PR #85, nem
cria memória episódica persistente. O passo seguinte, após avaliar a linguagem,
é treinar a extração de objetivos, entidades, condições, evidências e dúvidas
para conectar a entrada natural ao workspace com supervisão e avaliação
próprias. Hipóteses e respostas geradas não viram fatos por repetição.
