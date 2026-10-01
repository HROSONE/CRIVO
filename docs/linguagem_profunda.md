# Pré-treino de linguagem e adaptação a diálogos

O novo candidato aprende a prever texto português antes de aprender a responder.
É um Transformer causal de **2.612.352 parâmetros**, com quatro blocos, seis
cabeças de atenção, dimensão 192 e contexto de 256 tokens. Embeddings de entrada
e projeção de saída compartilham pesos. A tokenização BPE de 4.096 tokens aprende
apenas o treino, com alfabeto de bytes para representar palavras e Unicode novos.
Nenhum peso, vocabulário ou modelo externo pré-treinado é carregado. PyTorch e
Tokenizers fornecem cálculo e algoritmos, sem conteúdo aprendido previamente.

## Corpus e separação

São 20.000 artigos íntegros em português, escolhidos por hash entre 185.375
registros do shard da Wikipedia; 35.061 não atendem limites de comprimento e
uma duplicata foi removida antes da amostragem. Há 14.229.426 tokens no treino,
421.610 na validação e 354.429 no teste. O conteúdo não amplia automaticamente
o grafo factual: o modelo aprende linguagem e pode produzir informações erradas.

A seleção de diálogo amplia os 62 pares humanos anteriores para **497 pares
em 137 árvores**: 387/44/66 pares em treino/validação/teste. Mantém mensagens e
respostas completas, com histórico. Também usa os 10.478 exemplos sintéticos
autorais de treino, identificados como tal; não são novos diálogos humanos.
O SFT tem 11.895 janelas no treino, sendo 1.417 humanas, e 455.403 tokens de
resposta distintos por passagem pelo corpus de janelas. Janelas sobrepostas
preservam cada token do alvo e aplicam perda nele exatamente uma vez por
passagem. Perguntas e histórico não recebem perda de resposta.

Cada lote de SFT contém metade das janelas de origem humana e metade de origem
sintética. Vinte por cento dos passos continuam o pré-treino para reduzir
esquecimento. Árvores e documentos inteiros ficam em uma só partição. Alvos
humanos normalizados repetidos entre partições são recusados; nenhum caso das
sondas congeladas de diálogo ou astronomia foi adicionado ao corpus.

[Manifesto com hashes e contagens](../avaliacoes/linguagem_profunda/corpus_20261001.json).
[Origem, licenças, atribuição e critérios](../dados/NOTICE_linguagem_profunda.md).

## Reproduzir dados e treino

O download inicial soma cerca de 267 MB. Dados preparados, fontes e Adam devem
ficar fora do checkout para não versionar centenas de megabytes a cada rodada.
O ambiente atual tem três CPUs e nenhuma GPU. Use um diretório persistente em
sua máquina; os comandos abaixo usam `../crivo-linguagem` como exemplo.

```bash
python -m pip install 'torch>=2.2,<3' --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements-treino.txt -r requirements.txt
python scripts/baixar_fontes_linguagem.py --saida ../crivo-linguagem/fontes
python scripts/preparar_linguagem_profunda.py \
  --wikipedia ../crivo-linguagem/fontes/wikipedia.pt.parquet \
  --origem-wikipedia dados/origem_wikipedia_20261001.json \
  --oasst2 ../crivo-linguagem/fontes/oasst2.pt.jsonl \
  --saida ../crivo-linguagem/corpus --documentos 20000 --vocabulario 4096 --contexto 256
python scripts/treinar_linguagem_profunda.py \
  --corpus ../crivo-linguagem/corpus --saida ../crivo-linguagem/treino/pretreino \
  --fase linguagem --passos 2000 --lote 12 --lr 0.0008 --threads 3
python scripts/treinar_linguagem_profunda.py \
  --corpus ../crivo-linguagem/corpus --saida ../crivo-linguagem/treino/dialogo \
  --fase dialogo --inicial ../crivo-linguagem/treino/pretreino \
  --passos 2000 --lote 12 --lr 0.0003 --threads 3
python scripts/avaliar_linguagem_profunda.py \
  --corpus ../crivo-linguagem/corpus --modelo ../crivo-linguagem/treino/dialogo \
  --saida ../crivo-linguagem/avaliacao_teste.json
```

A primeira etapa de 2.000 passos processa 6.144.000 tokens. A segunda tem o
mesmo orçamento de posições de entrada, mas apenas os tokens das respostas e
dos passos de repetição de linguagem recebem supervisão: conferir o relatório
real, sem chamar todas as posições de tokens de diálogo aprendidos.
O ciclo local usa Python 3.12, PyTorch 2.14.1+cpu, NumPy 2.3.5, Tokenizers
0.23.2 e PyArrow 25.0.1. A reprodução byte a byte do corpus foi verificada nesse
ambiente; equivalência numérica exata de retomada pressupõe o mesmo ambiente.
O script permite modelos/contextos maiores; prepare o corpus com o mesmo
contexto e ajuste dimensão/cabeças/camadas ao hardware, começando do zero.

## Retomada e extensão

`checkpoint.pt` preserva pesos, Adam, RNG NumPy/PyTorch/CUDA, passo, horizonte
da taxa de aprendizado, origem da etapa anterior e contagens acumuladas.
`pesos.pt` é a versão de inferência sem Adam. A escrita usa arquivo temporário
e substituição atômica. O checkpoint é salvo a cada cem passos; se o processo
for interrompido à força, a retomada começa no último checkpoint salvo.

```bash
python scripts/treinar_linguagem_profunda.py \
  --corpus ../crivo-linguagem/corpus --saida ../crivo-linguagem/treino/pretreino \
  --fase linguagem --passos 12000 --lote 12 --lr 0.0008 --threads 3 --retomar
```

Para continuar o SFT, use sua pasta, `--fase dialogo --lr 0.0003 --retomar`,
sem `--inicial`. Código do modelo/treinador, corpus, tokenizer e configurações
devem coincidir com os do checkpoint. A retomada não reinicia Adam nem o LR;
ampliar `--passos` mantém o horizonte original e o LR final para continuidade.
`--parar-em N` pausa em um passo planejado sem alterar o horizonte. O teste de
retomada compara pesos, momentos de Adam e RNG com uma execução contínua.
Há uma única migração explícita da primeira versão do treinador: carregar o
checkpoint em CPU mantém estados RNG no dispositivo exigido, enquanto pesos e
Adam são movidos ao dispositivo do modelo. A equivalência de pesos/Adam/RNG
foi verificada em CPU entre as versões; CUDA não foi testada neste ambiente.
Nenhuma alteração de corpus ou código do modelo é aceita nessa migração.

O workflow **Pré-treino amplo e diálogos do zero**, executado manualmente no
GitHub Actions ou por um merge marcado `[treino-linguagem]` que altere seu arquivo,
prepara o corpus e treina 12.000 + 3.000 passos por padrão:
46.080.000 posições de entrada, cerca de 36,9 milhões no pré-treino. Publica
corpus, checkpoints e avaliação como artefato por 30 dias. Esses são orçamentos
configuráveis; consultar a execução para saber o que de fato foi processado.
Um merge comum não repete o treino automaticamente. Em CPUs lentas o limite de tempo
do runner pode interromper o treino; o artefato preserva checkpoints para
continuar localmente com o mesmo commit e configurações.

## Conversar e avaliar o candidato

O modelo permanece experimental. O CLI direto permite examinar gerações
integrais, inclusive incompletas; `/sair` encerra a conversa interativa:

```bash
python -m dialogo_linguagem_profunda --modelo artefatos/linguagem_profunda
python web_local.py --modelo-linguagem-profunda artefatos/linguagem_profunda
# Para examinar um treino posterior salvo fora do repositório:
python -m dialogo_linguagem_profunda --modelo ../crivo-linguagem/treino/dialogo
python -m dialogo_linguagem_profunda --modelo ../crivo-linguagem/treino/dialogo \
  --mensagem "Estou inseguro com uma decisão. Podemos conversar?"
python web_local.py --modelo-linguagem-profunda ../crivo-linguagem/treino/dialogo
```

Os pesos de inferência publicados ficam em `artefatos/linguagem_profunda`.
O chat e a avaliação usam cache de chaves/valores da atenção. Os testes conferem
logits contra a implementação de referência, inclusive ao reiniciar as posições
quando a janela desliza. A referência continua em `linguagem_profunda.py`;
os pesos e o cálculo de treino não foram alterados por essa otimização.
Os checkpoints completos com Adam/RNG e o corpus da execução atual ficam em
`../crivo-linguagem`, fora do checkout; conserve essa pasta para continuar
o treinamento. Os pesos de inferência sozinhos não contêm estado do otimizador.

Na integração ao chat, a geração pode atender conversas sem reconhecer um dos
23 atos antigos. Pedidos que o motor factual/escrita já reconhece conservam sua
prioridade. Só uma opção do servidor escolhe o checkpoint; o navegador não pode
enviar caminho ou ativar candidatos. A memória pertence à conversa, sem cache
de mensagens globais e sem transformar texto gerado em fatos/provas. O quadro
de compreensão permanece recusado: não inventa spans ou objetivos interpretados.

O contexto neural de 256 tokens limita o histórico útil, mesmo que a memória
externa tenha doze turnos. Turnos antigos são descartados inteiros; uma mensagem
atual que não cabe é recusada, sem corte silencioso. A guarda existente exige
resposta encerrada, pontuação e ausência de repetição; não verifica coerência
ou verdade. Gerações reprovadas voltam ao motor anterior.

O teste reservado mede todos os tokens dos textos e alvos humanos. As amostras
livres preservam pedido, histórico, resposta humana e erro do modelo. A sonda
de conversa de 72 turnos já foi consultada em trabalhos anteriores: permanece
diagnóstico de regressão, não teste externo cego. Não se deve promover o
candidato apenas porque a perplexidade caiu ou o modelo ficou maior.


## Resultados do piloto de 1 de outubro de 2026

O piloto terminou 2.000 passos em cada fase. Foram 6.144.000 tokens no pré-treino
mais 2.501.548 tokens supervisionados na adaptação (respostas e repetição de
linguagem). O Transformer tem 2.612.352 parâmetros. Os relatórios integrais,
pedidos e respostas livres estão em [avaliacoes/linguagem_profunda](../avaliacoes/linguagem_profunda/).

| Medida reservada | Resultado |
| --- | ---: |
| Perplexidade de textos Wikipedia, teste | 106,60 |
| Perplexidade de respostas humanas, teste | 62,08 |
| Acurácia dos tokens de respostas humanas | 25,63% |
| Sonda de conversa, candidato | 10/72 turnos, 0/18 conversas completas |
| Sonda de conversa, motor padrão anterior | 31/72 turnos, 2/18 conversas completas |

As gerações livres ainda são incoerentes. O candidato piorou a sonda de conversa
em relação ao motor padrão e permanece desligado por padrão. A queda da perda
mostra aprendizado estatístico de linguagem; não demonstra compreensão ou uma
melhoria efetiva de conversa. O cache preservou exatamente as respostas e os
resultados dos 72 turnos, reduzindo a duração de 414,66 para 9,30 segundos.

## Corpus do próximo ciclo maior

O ciclo de 12.000 + 3.000 passos prepara um corpus novo: acrescenta até 50.000
conversas sintéticas públicas de Tucano-SFT, filtrando exclusivamente a fonte
GPT4-500k-Augmented-PTBR-Clean cuja licença declarada é MIT. A curadoria por hash
preserva textos e procedência, agrupa pedidos iniciais iguais e recusa alvos
repetidos entre partições e textos presentes na avaliação humana reservada.
Esses são dados gerados externamente; os pesos e o BPE do Crivo começam do zero.
Os registros públicos reservados ficam separados da avaliação humana.

Para preparar esse corpus, acrescente `--dialogos-publicos` ao downloader e
`--dialogos-publicos CAMINHO/tucano-sft.parquet` à preparação. Sem essas opções,
a preparação mantém o corpus do piloto, inclusive a reprodução dos seus hashes.
A ampliação muda o tokenizer/manifesto: não retome os checkpoints do piloto com
esse corpus. O workflow inicia um modelo novo e publica seus resultados como
candidato; não substitui automaticamente os pesos do chat.

A seleção realizada contém 48.074 conversas públicas: 45.658 no treino e 2.416
reservadas. Somando o currículo autoral e os humanos, há 56.523 pares de treino,
116.419 janelas e 10.644.061 tokens-alvo distintos por passagem completa. O
pré-treino dispõe de 14.565.841 tokens em 18.985 documentos. Essas contagens
medem o corpus disponível, não o que já foi processado; a amostragem de lotes
não garante visitar todos os exemplos. O manifesto separado é
[corpus_massivo_20261001.json](../avaliacoes/linguagem_profunda/corpus_massivo_20261001.json).
