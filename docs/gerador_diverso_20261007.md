# Gerador próprio: preparação com diversidade verificável

Pedido: começar pelo gerador, com quantidade, variedade e qualidade de assuntos,
sem multiplicar o mesmo conteúdo. Trabalho isolado em `codex/gerador-diverso`,
sobre a main: não substitui nem fecha os PRs #105–#110.

## Rede

Transformer causal autoral, inicializado aleatoriamente:

| Característica | Valor |
| --- | --- |
| Parâmetros aprendíveis, conferidos na instância | 16.150.272 |
| Blocos / dimensão / cabeças | 8 / 384 / 8 |
| Vocabulário próprio | 4.096 tokens |
| Contexto total de entrada e saída | 1.024 tokens |
| Dropout | 0,1 |
| Entrada e saída | Embedding compartilhado |
| Pesos externos / promoção automática | Não / não |

A arquitetura reutiliza `linguagem_profunda.py`. A primeira rodada verifica o
ganho de dados e objetivo antes de aumentar a rede para dezenas de milhões de
parâmetros adicionais. A configuração anterior de diálogos tinha contexto 512
e 15.953.664 parâmetros. Nenhum checkpoint anterior foi redimensionado.
Os pesos ocupam aproximadamente 64,6 MB em FP32 ou 32,3 MB em FP16; isso não
inclui gradientes, Adam, ativações ou checkpoint de retomada. Contexto 1.024 não
permite analisar documentos arbitrariamente longos em uma única entrada.

## Currículo planejado e estado real

Meta inicial de SFT: **12.000 exemplos de treino, no mínimo 3.000 cenários**,
com até quatro exemplos por cenário; 12 domínios e seis tarefas. Os assuntos
são astronomia, biologia, ambiente, história, geografia, matemática,
programação, linguagem, economia, saúde, artes e cotidiano. As tarefas são
explicação, resumo, comparação, correção, padrões e limites da evidência.

Cada domínio precisa de pelo menos 400 exemplos e cada tarefa de 800 no
treino; nenhum domínio passa de 15% e nenhuma tarefa de 30% de uma partição.
Validação e teste precisam de cobertura própria: ao menos 20 exemplos por
domínio e 30 por tarefa. A meta de pré-treino é 30 milhões de tokens de textos
deduplicados, não repetir um corpus pequeno até o contador atingir esse valor.
Esses números são critérios de curadoria iniciais, não garantias de competência.

**Preparado agora:** 12 exemplos-semente, um cenário distinto por domínio,
cobrindo as seis tarefas. São exemplos sintéticos autorais identificados,
pendentes de revisão humana. Não são 12 mil exemplos nem um corpus final.
Não devem ser replicados trocando números, nomes ou sinônimos. O treino longo
não foi iniciado: a auditoria corretamente retorna código 1 e `apto=false`.

As conversas ampliadas anteriores têm famílias calculadas com centenas de
variações numéricas. Elas continuam preservadas para seus experimentos,
mas não são incorporadas automaticamente como milhares de assuntos novos.

## Qualidade e partições

O JSONL exige origem, licença, fonte, conteúdo-base, domínio, tarefa e revisão.
Corpus de treino completo exige revisão humana registrada. A revisão precisa
conferir coerência pedido/resposta, cálculos, atribuição das fontes e fidelidade
ao texto. O campo de revisão é um registro, não uma prova automática dessa
avaliação. Exemplos autorais sintéticos não contam como diálogos humanos.

A auditoria bloqueia pares ou respostas repetidos, conteúdo reutilizado sob
outro grupo, excesso de exemplos por cenário, concentração de domínios,
moldes numéricos repetidos e cobertura insuficiente. Quase duplicatas são
triadas por Jaccard de sequências de cinco palavras, normalizando números.
Essa triagem é lexical: paráfrases diferentes podem passar, portanto revisão
de diversidade semântica continua necessária. Conteúdo curto idêntico também
é detectado, mesmo sem cinco palavras.

Toda origem, conteúdo-base e cenário permanece em uma partição. Reformular a
pergunta não permite mandar a mesma passagem para treino e teste. A seleção
dos checkpoints usa apenas validação; o teste final não alimenta curadoria,
treino ou seleção. Fontes futuras precisam permitir o uso e ter proveniência
registrada. Conversas privadas não são incorporadas.

## Executado

- Oito testes da auditoria passaram, incluindo vazamento, repetições numéricas,
  textos curtos e caminho positivo com limites reduzidos somente na fixture.
- Sonda CPU de três passos na rede real, com tokenizer próprio já existente:
  perdas e gradientes finitos; embedding mudou em até 0,00045095384.
- O relatório marca `treino_completo=false` e `aprovado_para_chat=false`.

As três perdas pertencem a exemplos diferentes: sua redução não demonstra
convergência. Os pesos de sonda ficam em diretório separado e não alteram
`artefatos/` ou o chat. Nenhum modelo externo foi baixado ou executado.

```sh
python -m unittest testes_gerador_diverso -v
python scripts/auditar_gerador_diverso.py dados/gerador_diverso_semente.jsonl --saida /tmp/auditoria-gerador.json
# Código 1 acima é esperado: a semente ainda não satisfaz o currículo.
python scripts/sondar_gerador_diverso.py --saida /tmp/sonda-gerador --passos 3
```

Relatórios: `docs/resultados/gerador_diverso_auditoria_20261007.json` e
`docs/resultados/gerador_diverso_sonda_20261007.json`.

## Próxima entrega necessária

Curar o corpus completo e seus reservados, revisar qualidade e diversidade,
tokenizar os textos próprios e conferir o volume deduplicado do pré-treino.
A auditoria atual cobre o JSONL supervisionado; não audita ainda os 30 milhões
de tokens de pré-treino, que não foram preparados nesta etapa. Integrar esses
dados ao treinador retomável preservando sua seleção humana antes de iniciar
o treino longo. Avaliar respostas novas no chat completo, preservação de
fatos/números/negações, obediência ao pedido e latência antes de promover pesos.
