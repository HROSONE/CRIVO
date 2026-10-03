# Ajuste de contratos, lógica e reparo

A rodada `37115525535` terminou com 16/16 respostas que compilavam e executavam,
mas 0/16 tarefas corretas. A inspeção das gerações mostrou confusão de operações
(somar no lugar de multiplicar, dobrar no lugar de calcular fatorial), ordem,
seleção de algoritmo e tipos exigidos pelo contrato. Não houve uma única resposta
literal repetida em todas as tarefas.

Os relatórios foram extraídos sem repetir o treino pela execução de diagnóstico
`37129435890`. Os pesos próprios selecionados foram baixados e conferidos por
SHA-256 `bbcba4725f62e136967f81581bb4fa66f247a41cd5a64c6e213868d117aa1349`.
Não há ativação desse candidato no site.

## Dados

`gerar_logica_programacao.py` reproduz `dados/programacao/logica.json`:
2.304 exemplos autorais em 144 famílias de composição. São variantes e exercícios
de reparo, não 2.304 problemas independentes. Os contratos contrastam:

- Filtrar antes ou depois de transformar a lista.
- Maior/maior ou igual/menor/menor ou igual; par e ímpar.
- Somar, subtrair, escalar ou negar cada elemento; constantes positivas e negativas.
- Retornar a lista, sua soma ou a quantidade de elementos; listas vazias e limites.

Cada referência tem seis casos calculados por um oráculo Python. Cada reparo
mostra código autoral com um predicado errado e um contraexemplo concreto com
entrada, resultado esperado e obtido. Metade dos contratos limpos fornece dois
exemplos; a outra metade não fornece resultados. Avaliação usa somente contratos
limpos sem exemplos; soluções e contraexemplos do teste antigo não entram no treino.

Uma família inteira (idiomas, constantes, versões e reparos) fica em uma partição.
Alvos textualmente iguais não cruzam partições. Isso não garante independência
semântica: composições distintas podem ser equivalentes. O benchmark é sintético.

Corpus resultante: 2.768 instruções de treino, 536 de validação e 240 de teste,
com as mesmas seis fontes reais e licenças. A validação das referências, incluindo
os programas autorais defeituosos e seus resultados observados, aprovou 33.248
casos em JS/TS; isso valida os dados, não a capacidade do modelo.

## Treino

- Inicializar a nova etapa com os pesos próprios anteriores, mantendo o tokenizer
  byte a byte. Conferir o hash; registrar linhagem. O corpus muda e Adam começa
  novo: não apresentar isso como retomada exata do checkpoint antigo.
- Amostrar famílias/linguagens com a mesma probabilidade em SFT, para variantes
  repetidas de poucos padrões não dominarem o treinamento.
- Remover somente posições finais sem alvos supervisionados do lote, preservando
  todos os tokens-alvo e o contexto necessário. Teste verifica equivalência da
  perda sem dropout; a nova política consta da assinatura da execução.
- Ponderar operadores, constantes e termos de controle por fator 4 no objetivo
  de SFT. Marcadores especiais e posições do prompt não ganham esse peso.
  A entropia de validação continua comum; resultados funcionais têm prioridade.

## Verificação

TypeScript compila o candidato junto de um arquivo separado que verifica chamadas
com entradas e tipos de retorno exigidos. Esse arquivo não executa nem fornece
valores esperados ao programa avaliado. JS continua verificado pelo parser e pelos
casos em VM isolada. Saídas, mutações de entradas e protocolo continuam verificados.

Os relatórios agora preservam contraexemplos e acertos por caso. Casos parciais
não aprovam uma tarefa nem contam como pass@1. O checkpoint é escolhido por:
soluções completas corretas, média de acerto de casos por tarefa/linguagem,
compilação, término e perda, nessa ordem. A seleção usa somente validação.

Além das 16 tarefas antigas, um teste separado contém 28 composições reservadas
(14 famílias x JS/TS), sem exemplos no prompt. O candidato anterior acertou 0/28
nesse novo teste local. Não usar resultados do teste para escolher checkpoints.
Compilação agora também exige o contrato TS; comparar rodadas com o mesmo
verificador e não confundir esse indicador com a métrica antiga de sintaxe.

## Execução

O workflow `treino-codigo-real.yml` tem modo `diagnostico` (extração de relatórios)
e `treino`. `aproveitar_anterior=true` usa o artefato pequeno de pesos próprios da
execução de diagnóstico e dedica o orçamento ao ajuste. Com `false`, faz novo
pré-treino. Artefatos têm retenção de 30 dias: preservar uma cópia permanente.
Se o artefato inicial faltar ou o hash divergir, parar; não reiniciar do zero silenciosamente.

```sh
python scripts/treinar_codigo_real.py --saida /tmp/ciclo-logica \
  --cache /tmp/fontes-codigo --tsc /tmp/ts/node_modules/typescript/lib/tsc.js \
  --perfil codigo6m --inicial /tmp/modelo-anterior \
  --inicial-sha256 bbcba4725f62e136967f81581bb4fa66f247a41cd5a64c6e213868d117aa1349 \
  --sft-passos 8000 --threads 2 --max-segundos 9600
```

Testes e uma execução curta verificam o novo processo; não demonstram melhoria
na geração de soluções. Nenhuma promoção automática. Uma nova rodada longa é
necessária para medir aprendizado, e aprovação exige os critérios existentes de
regressão, cobertura e avaliação independente.
