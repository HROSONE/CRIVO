# Primeira investigação de conversa — resultados de 9 de outubro de 2026

**Decisão: nenhum peso novo aprovado para o chat.** O diagnóstico, a auditoria,
os pilotos e a avaliação de desenvolvimento foram executados. A integração,
as três sementes e a bateria final de 60 sessões não foram iniciadas porque
os candidatos falharam no desenvolvimento. Não apresentar esta rodada como
melhora da conversa livre.

O [PR 116](https://github.com/HROSONE/CRIVO/pull/116) teve os 19 checks verdes e
foi mesclado em `93b3f0a`, às 03:29:51 UTC. Esse PR melhora tratamento de
hipóteses no motor; não promove os geradores deste experimento.

## O que foi medido

Casos e rubricas do diagnóstico foram congelados antes da inferência. Mesmos
12 pedidos em quatro apresentações: reunido, multiturno, recapitulação e estado
manualmente organizado. As entradas reais, tokens, respostas e omissões estão
em `experimentos/diagnostico_pareado_20261009/`.

| Condição | Motor: respostas adequadas / 12 | Gerador próprio 2,6M / 12 |
| --- | ---: | ---: |
| Reunido | 1 | 0 |
| Multiturno | 2 | 0 |
| Recapitulação | 2 | 0 |
| Estado assistido | 1 | 0 |

O motor tem respostas parciais adicionais, registradas separadamente. Citar
fatos e devolver uma pergunta genérica não recebeu aprovação completa. O
estado assistido do motor ainda passa pelo interpretador, portanto não isola
seu executor. No gerador, apenas uma das 48 entradas finais omite histórico;
duas perdem prefixo durante geração. O fracasso nas condições curtas, completas
e assistidas enfraquece a hipótese de resolver tudo apenas com memória.

O gerador ancorado maior, de 17.428.224 parâmetros, também foi sondado com
estados corretos no formato de fatos em que foi treinado. Produziu frases
em geral mais claras, mas nenhuma das 12 executou completamente o pedido.
Por exemplo, repete as despesas em vez de calcular o saldo. A saída crua ficou
apenas no laboratório; a guarda do chat não foi alterada. Essa comparação usa
outro tokenizer e treinamento, e não isola o efeito do número de parâmetros.

## Dados disponíveis e intervenção

O arquivo humano compacto tem 62 pares de 26 árvores: 56 de treino, dos quais
27 cabem inteiros em 256 tokens. Somente seis pares humanos, somando partições,
têm histórico completo dentro desse limite. O aviso geral registra outro
corpus humano de 497 pares; seus binários não estavam disponíveis localmente.
Não confundir as duas seleções.

Os 119 cenários autorais estáticos têm 257 pares. Nenhum arquivo disponível
nessa preparação tinha exemplo inteiro com seis mensagens anteriores.
Também foi encontrado o piloto causal anterior: 242 pares e 600 atualizações,
com sobreajuste e 0/20 respostas adequadas. Ele já supervisionava respostas;
não seria correto propor o mesmo treino como uma novidade.

A intervenção adicionou trajetórias procedurais de oito mensagens, com seis
famílias: vínculo, correção, referência, hipótese/causa, condição e intenção.
São 4.770 entradas de treino e 271 de validação após deduplicação, com 1.548
entradas de treino contendo seis mensagens anteriores. São formas compartilhadas
com permutações e contrastes, não novas conversas humanas nem diversidade
independente. Tudo cabe integralmente no contexto; perda apenas nas respostas.

Uma primeira execução foi interrompida após revisão de concordância de gênero.
Os registros e dados originais foram preservados; a versão corrigida foi
congelada antes do reinício. Essa execução interrompida não é contada como
piloto concluído.

## Resultados dos treinos

As 12 sessões de desenvolvimento foram redigidas e congeladas antes dos treinos.
Cada sessão usa quatro falas de usuário e quatro respostas do próprio modelo,
que retornam ao histórico. A avaliação foi leitura autoral, sem cegamento ou
independência; exige continuidade e execução dos pedidos, sem trocar os dados.

| Experimento | Orçamento efetivo de tokens-alvo | Sessões adequadas / 12 | Decisão |
| --- | ---: | ---: | --- |
| Base causal 2,6M | Sem ajuste novo | 0 | Referência |
| 2,6M: currículo antigo | 180.000 | 0 | Rejeitado |
| 2,6M: currículo relacional | 180.000 | 0 | Rejeitado |
| Base maior, antes do ajuste | Sem ajuste novo | 0 | Referência |
| Maior: currículo antigo | 30.000 | 0 | Rejeitado |
| Maior: currículo relacional | 28.582 / 30.000 | Não avaliado em pesos novos | Teto; comparação incompleta |
| 2,6M relacional: matriz ajustável | 30.000 | 0 | Rejeitado |
| 2,6M relacional: matriz congelada | 30.000 | 0 | Rejeitado |

O primeiro par 2,6M usou a mesma inicialização, tokenizer, replay humano e
orçamento de tokens-alvo. O currículo novo reduziu a perda relacional até
0,305, mas aumentou a perda nos exemplos antigos. Nas sessões, substituiu
Nora/Caio e mochila/garrafa por Eva/Cora e objetos do treino. Até respostas
com uma cor coincidente falham quando trocam o objeto ou a pessoa. Nas 48
condições do diagnóstico original, o candidato continuou sem resposta adequada.

O controle antigo voltou a sobreajustar. Seu checkpoint selecionado foi o
passo 104, enquanto o braço novo selecionou o passo 933. O gerador ancorado
maior foi convertido dos tensores próprios para Torch, com igualdade após
recarga e paridade de tokenização em 53 textos, antes de qualquer ajuste.

O braço relacional maior atingiu o teto em 156 atualizações, antes do intervalo
de avaliação. O treinador v1 exportou o estado inicial (passo selecionado zero)
e não preservou os pesos intermediários ajustados. **Não houve avaliação de
pesos novos desse braço e isso não prova que a arquitetura maior falhou com
o currículo novo.** Os resultados não compõem uma comparação de orçamento
igual. A implementação posterior `piloto_duravel.py` salva estado atual,
Adam e RNG, e avalia o ponto parcial. Um teste de teto antes da primeira
avaliação confirmou essa persistência. Isso não recupera os pesos da execução
anterior.

Não houve GPU: Torch CPU, afinidade de três CPUs, mas cota efetiva de duas.
O maior mediu 25,56 tokens-alvo/s no currículo novo e 42,50 no controle, nas
100 primeiras atualizações. A rodada não deixou treinos pendentes e não
alterou os arquivos dos modelos ativos. Pesos experimentais continuam locais;
somente textos, métricas e hashes entram no Git, sem novos artefatos Actions.

## Nova pesquisa e consequência

Skill usada: `.claude/skills/insight-entidade-internet/SKILL.md`.

**Antes eu acreditava:** melhorar a supervisão relacional poderia fazer o
gerador usar fatos e correções. Os novos resultados mostram frases aprendidas,
com identidades trocadas. Não sabemos quanto vem de representação lexical,
seleção da fonte ou mecanismo de cópia.

**A pesquisa mostrou:** um preprint de lógica simbólica descreve dificuldade
com símbolos novos, convergência dos vetores de saída de tokens ausentes e
atenção de cópia. Testa diversidade e intervenções na matriz compartilhada,
mas observa limitações para linguagem geral e símbolos com várias subpalavras.
Isso oferece uma hipótese testável, não uma explicação confirmada do Crivo.
[Lazić et al., 2026](https://arxiv.org/html/2604.21632v1).

**Eu não sabia:** esse mecanismo e desenho de ablação. No código do Crivo,
entrada e saída compartilham `embedding.weight`. A similaridade média entre
mil pares de IDs ausentes nos alvos do novo ajuste passou de 0,145 para 0,339.
Esses IDs não são necessariamente inéditos no pré-treino, e nomes podem usar
subpalavras presentes no ajuste. A correlação não estabelece causalidade.

**Isso muda:** foi feita a ablação de 30 mil tokens, com os mesmos dados,
sorteios e pesos, congelando ou ajustando a matriz. A igualdade da matriz
congelada com a base foi verificada. Ambas as condições ficaram em 0/12;
portanto congelar sozinho não resolveu neste orçamento.

A arquitetura pointer-generator combina produção de texto e cópia da fonte,
em tarefas de resumo. Seu ganho de fidelidade não garante interpretação da
fonte ativa ou raciocínio de diálogo. É uma possibilidade de implementação
própria para investigar, sem baixar modelos ou usar inferência externa.
[See et al., ACL 2017](https://aclanthology.org/P17-1099/).

**Próxima hipótese operacional:** separar reprodução fiel de campos da
seleção de qual campo/fonte está ativo. Antes de outro treino longo, criar um
teste de cópia e vínculo com nomes e objetos reservados, distrações, correções
e fala de terceiros; comparar um caminho de cópia aprendido com o decoder
atual. Só ampliar diálogos após ganho comportamental nessa base. Não repetir
180 mil tokens do mesmo currículo nem aprovar por entropia cruzada.

Essa hipótese ainda precisa de implementação e treino. Nenhuma arquitetura
nova foi apresentada como já treinada ou aprovada. A primeira investigação
se encerra com resultados negativos registrados e uma pergunta mais específica;
a meta de conversa livre permanece aberta.
