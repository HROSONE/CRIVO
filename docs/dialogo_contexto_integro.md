# Ajuste de diálogo com contexto inteiro

Este experimento reaproveita o Transformer próprio de 15.953.664 parâmetros.
Não repete o pré-treino, não importa pesos externos e não consulta respostas
cadastradas na geração. A preparação seleciona dados para aprendizado; o modelo
continua gerando token por token a partir dos seus pesos.

## Problema medido

No corpus anterior, 259 dos 461 pares humanos não cabiam integralmente no
contexto de 512 tokens. As janelas preservavam os tokens supervisionados da
resposta, mas uma continuação podia deixar de enxergar partes do pedido ou do
histórico. Isso não prova sozinho a causa de toda a incoerência; é um problema
de supervisão verificável para o ajuste de diálogo.

O novo preparador exige que histórico, pedido e resposta, incluindo o fim,
caibam em uma única janela. Não corta a resposta nem acrescenta um fim falso.
Separa também os exercícios calculados deste ajuste de conversa, porque suas
respostas numéricas estavam aparecendo indevidamente em perguntas abertas.

Resultado da derivação: **481 pares**, sendo 202 humanos e 279 demonstrações
sintéticas autorais; 141 pares têm histórico, e há 53.216 tokens-alvo
por passagem pelo conjunto. Os 3.291 exemplos calculados permanecem no corpus
original, assim como os pares longos excluídos deste ajuste. Menos exemplos não
significa um corpus geral suficiente: o conjunto continua pequeno.

As matrizes e textos de validação e teste, assim como o replay de linguagem,
são cópias byte a byte do corpus anterior. A origem e cada arquivo são
identificados por SHA-256. Os dados reservados não entram no SFT.

## Comparação de conversa

`avaliar_dialogo_integro.py` percorre oito cenários de validação, com 17 turnos.
Cada modelo recebe suas próprias respostas anteriores. Os alvos de referência
ficam somente no relatório, para revisão, e nunca são fornecidos ao gerador.
Todos usam temperatura zero, limite de 128 tokens por turno e os mesmos cenários.

A comparação separa término, repetição de sequências de quatro palavras e revisão
de pertinência/correção. Término e ausência de repetição não provam compreensão.
Esses cenários são desenvolvimento/validação, não uma certificação independente.
O teste reservado anterior não foi usado para escolher dados ou ajustar pesos.

## Reproduzir sem refazer o pré-treino

Use diretórios locais novos. O `corpus-anterior` deve conter o corpus verificado
já preparado; `pretreino/melhor` deve conter os pesos e tokenizer próprios.

```bash
python scripts/preparar_dialogo_integro.py \
  --origem corpus-anterior --saida corpus-integro
python scripts/treinar_linguagem_profunda.py \
  --corpus corpus-integro --saida piloto-integro \
  --fase dialogo --inicial pretreino/melhor --ajustar-proprio \
  --dimensao 384 --camadas 8 --cabecas 8 --contexto 512 \
  --passos 300 --parar-em 150 --lote 8 --lr 0.00008 \
  --semente 20261004 --threads 2 --dispositivo cpu \
  --avaliar-a-cada 50 --salvar-a-cada 50 \
  --selecionar-melhor --selecao-humana --podar-padding \
  --perda-por-resposta --repeticao-linguagem 0.1 \
  --paciencia-validacoes 4 --max-segundos 1200
python scripts/avaliar_dialogo_integro.py \
  --modelo piloto-integro/melhor --corpus corpus-anterior \
  --saida respostas-validacao.json
```

O orçamento de tempo pode pausar antes dos 150 passos. Para retomar o mesmo
experimento, preserve código, corpus e configuração; troque `--inicial ...` e
`--ajustar-proprio` por `--retomar`. O horizonte de 300 mantém a mesma curva de LR.
Nenhum desses comandos ativa o candidato no chat do site. Para backups no Drive,
use snapshots verificados entre blocos; não aponte a saída de treino diretamente
para a montagem do Drive.

## Resultado observado

Foram executados 150 passos em CPU, com 263.778 tokens-alvo supervisionados.
O melhor ponto pela validação humana continuou sendo o passo 50: CE 2,836599,
contra 2,842532 do SFT anterior. No passo 150, a CE foi 2,844909.

| Modelo / geração | Turnos terminados / 17 | Respostas repetitivas / 17 |
|---|---:|---:|
| Pré-treino, temperatura 0 | 0 | 17 |
| SFT anterior, temperatura 0 | 10 | 12 |
| Novo passo 50, temperatura 0 | 12 | 5 |
| Novo passo 150, temperatura 0 | 8 | 12 |
| SFT anterior, temperatura 0,7 | 8 | 11 |
| Novo passo 150, temperatura 0,7 | 12 | 9 |

**A redução de repetição no passo 50 não virou compreensão adequada.**
A revisão qualitativa pelo assistente encontrou falhas de pertinência, referência,
negação e condições. Por exemplo, ao perguntar sobre a necessidade de autorização
para abrir uma sala, o modelo ainda produziu frases sem resolver a condição.
O passo 150 não corrigiu isso. Nenhum candidato foi aprovado para produção.

Os resultados completos, incluindo respostas ruins, estão em
[`avaliacoes/linguagem_profunda/dialogo_integro_20261004`](../avaliacoes/linguagem_profunda/dialogo_integro_20261004/).
A rodada mudou também lote e LR: não constitui uma ablação que isole causalmente
o efeito do contexto inteiro. O painel é de desenvolvimento, não uma avaliação
independente. Os resultados não justificam repetir uma rodada longa no mesmo
conjunto ou promover pesos com base somente na perda de validação.

A preparação corrigida e a avaliação de trajetórias ficam disponíveis para os
próximos experimentos. O diagnóstico desta rodada é negativo para conversação:
melhorar supervisão foi necessário, mas insuficiente. O próximo investimento
precisa aumentar a diversidade de diálogos e medir compreensão durante o treino,
com orçamento curto e critérios de interrupção, antes de ampliar a duração.

O pacote `crivo-dialogo-integro-50-experimental-nao-aprovado.zip` contém os pesos,
o tokenizer, o relatório e as avaliações. Serve para inspeção/inferência ou
inicialização de outro ajuste próprio; não contém Adam/RNG para retomada exata.
O checkpoint completo do experimento permanece no workspace de treinamento.
