# Intérprete contextual próprio — experimento concluído em 8 de outubro de 2026

**Candidato não aprovado para o chat.** Os pesos foram treinados e avaliados.
O piloto mostra avanço na cópia contextual dentro de uma gramática limitada,
mas falha com novas formulações e não produz conversa livre. O runtime do
Crivo permanece com os pesos anteriores.

## Resultado principal

| Medida no painel reservado | Candidato bruto | Mesmos pesos + cópia limitada |
| --- | ---: | ---: |
| Contratos com operação, argumentos, fontes, referente e escopo corretos | 184/400 (46%) | 342/400 (85,5%) |
| Sessões de quatro turnos inteiramente corretas | 19/100 | 65/100 |
| Requisitos, a família mais fraca | 6/56 | 24/56 (42,9%) |

O corpo é o transformer próprio existente de 2.612.352 parâmetros. Cabeças
autorais de operação, escopo e ponteiros elevam o total do candidato a
**2.947.216 parâmetros**. Não há arquitetura, tokenizer, pesos ou API de
modelos externos. Cada campo aponta para texto realmente presente nas falas.
Operações de custo/tempo/requisitos são executadas por código limitado, não
calculadas pelo transformer.

A variante de cópia limitada foi motivada por fragmentação observada em
**validação**, antes da avaliação final: “aprender foto” no lugar de “aprender
fotografia”, por exemplo. Um detector de gramática enumera trechos completos;
a rede escolhe entre esses candidatos. Isso acrescenta ajuda determinística
e seu ganho não pode ser atribuído apenas aos pesos. Resultados brutos e
limitados permanecem separados. As regras aceitas estão em
`decodificar_limitado.py`, e não cobrem toda linguagem natural.

Há **39 propostas executáveis com resultado incorreto** na variante limitada.
Uma conta pode estar aritmeticamente certa e usar os argumentos errados.
`executavel: true` não é aprovação semântica. Mesmo confiança alta na operação
não autoriza entregar a conclusão ao usuário.

## Dados, treino e seleção

| Partição | Prefixos distintos | Sessões | Maior contexto |
| --- | ---: | ---: | ---: |
| Treino | 3.000 | 750 | 136 tokens |
| Validação | 300 | 75 | 157 tokens |
| Avaliação | 400 | 100 | 175 tokens |

Cada sessão contém quatro falas do usuário. Os 3.000 exemplos são prefixos
de 750 cenários sintéticos, não 3.000 conversas humanas nem 3.000 formas
linguísticas independentes. São 36 formas de pergunta no treino, 12 na
validação e 18 na avaliação. Eventos de correção e hipótese compartilham
molduras entre partições. Nomes, números, objetivos, limites e objetos são
separados; o teste usa números de três dígitos, enquanto o treino usa dois.
Não há truncamento ou coincidência literal entre partições. Os controles
anteriores e conversas privadas não foram lidos pelo construtor.

Dois braços completaram 600 atualizações, lote 16, LR 0,0001 e a mesma
sequência de exemplos. Cada braço apresentou 692.524 tokens de entrada e
2.889 dos 3.000 prefixos distintos. O controle aprende cinco classes; o
candidato aprende operação, hipótese e oito limites de trecho. **Não houve
supervisão causal de redação**. Um alvo de classe correto não comprova que
o sistema sabe interpretar os argumentos ou conversar.

O controle tem 2.613.317 parâmetros e selecionou o passo 100 pela validação;
o candidato selecionou o passo 500. Ambos executaram todo o orçamento de
600 passos. Foram aproximadamente 706 e 653 segundos de treino em CPU,
respectivamente, com um thread por processo e execução simultânea no mesmo
ambiente. Esses tempos não estimam duração em Colab/GPU nem isolam eficiência
de arquitetura. Há uma única semente, 20261009.

O treino abriu apenas treino/validação. Manifestos e hashes foram fixados
antes da primeira avaliação dos pesos no teste. A variante limitada também
foi registrada antes desse teste, após examinar apenas erros de validação.
O primeiro avaliador, seu congelamento e o avaliador ampliado foram conservados.

## Famílias na variante limitada

| Família | Acertos |
| --- | ---: |
| Correção | 55/60 |
| Referência | 57/60 |
| Requisitos | 24/56 |
| Comparação | 52/56 |
| Duração | 45/56 |
| Objetivo/restrição | 53/56 |
| Esclarecimento | 56/56 |

O critério pré-definido exigia pelo menos 80% em cada família e aumento de
20 pontos percentuais nas sessões completas sobre o baseline medido. Requisitos
ficaram abaixo de 80%; **o piloto não passou**. A condição para três sementes
de confirmação não foi atingida, portanto não repetimos o treino buscando uma
semente melhor. Também não há painel independente para promoção.

## Comparação com o Crivo atual e limites de medição

O motor atual exportou os contratos esperados em 66/400 falas e 9/100 sessões.
O braço de cinco classes acertou 400/400 classes, mas, combinado ao mesmo
motor/extrator, continuou em 66/400 e 9/100. Isso ajuda a separar reconhecer
o domínio de resolver a conversa.

**Esses percentuais do motor atual não são uma nota semântica geral.** O
avaliador exige resultados estruturados e pode subestimar respostas equivalentes
sem os mesmos metadados. Consultas por pessoa e alguns esclarecimentos do motor
não oferecem esse contrato. O candidato também recebe histórico bruto, enquanto
o motor conserva estado e usa rotas diversas. A comparação não isola
causalmente arquitetura, dados, extrator ou alvo de aprendizado. Respostas
completas, IDs e erros estão em `avaliacao/crivo_atual.json`.

## Além das molduras do painel

Cinco sessões adicionais, com 20 falas, foram escritas e fixadas antes da
coleta: associação de lembranças, criação de história, sugestões a partir de
preferências, revisão de opinião e preços com outras formulações.

O candidato não tem cabeça de redação. Não atende aos quatro diálogos abertos.
Na transferência de preços, também errou **0/4 acertos**: confundiu os valores
dos planos e não aplicou a simulação corretamente. Esse resultado permanece
visível junto dos 85,5%. O motor atual também teve dificuldades nesses diálogos;
a leitura autoral registra uma resposta adequada, sete parciais e doze falhas.
Esse julgamento não é avaliação independente.

O principal limite observado é a dependência de formas e associações de
argumentos conhecidas. A regra de cópia reduz palavras cortadas, mas não garante
entender quais fatos são relevantes ou a que plano um número pertence.

## Próxima decisão

Preservar este candidato como laboratório. O próximo conjunto precisa variar
**relações e formulações das declarações**, além das perguntas: nomes arbitrários
de opções, ordens trocadas, cláusulas irrelevantes, correções indiretas e marcas
de hipótese diferentes. Aumentar números ou repetir a mesma moldura não basta.
Estudar representação de entidades e argumentos normalizados com vínculo à
fonte, conforme a pesquisa sobre abstração. Preparar outro painel antes de um
novo treino; os painéis desta rodada agora são diagnósticos conhecidos.

Também falta um currículo próprio de redação para diálogo aberto, com cobertura
linguística e avaliação manual. Não promover estas cabeças de interpretação
como se fossem um modelo gerativo, nem aumentar parâmetros esperando resolver
sozinho esses problemas.

## Reproduzir e inspecionar

Requer o repositório CRIVO e suas dependências de infraestrutura Torch, NumPy
e tokenizers. Usar pastas novas: os scripts recusam sobrescrever rodadas.
O notebook publicado facilita inspeção/reprodução; repetir o painel publicado
não cria uma avaliação independente nem um modelo automaticamente aprovado.

[Abrir notebook no Colab](https://colab.research.google.com/github/HROSONE/CRIVO/blob/codex/interpretador-contextual-20261008/notebooks/interpretador_contextual_crivo.ipynb).
Ele carrega `pesos_contextual/pesos.pt`, já treinado; o treino opcional começa
desligado. A branch conserva os relatórios dos dois braços e os pesos do
candidato. Para repetir a comparação inteira, treine os dois braços em uma
pasta nova, como faz a opção de reprodução do notebook.

```sh
python corpus.py /tmp/contextual-dados --tokenizer /caminho/CRIVO/artefatos/linguagem_profunda/tokenizer.json
python treinar.py controle /tmp/contextual-controle --raiz /caminho/CRIVO --dados /tmp/contextual-dados
python treinar.py contextual /tmp/contextual-candidato --raiz /caminho/CRIVO --dados /tmp/contextual-dados
python -m unittest testes_contratos -v
```

Para usar `avaliar.py`, conservar a organização desta pasta com `dados/`,
`controle/` e `contextual/`. A coleta abre o painel somente após os dois
relatórios confirmarem 600 passos completos. Não reexecutar sobre uma pasta
de avaliação existente nem apagar falhas.

`inferir.py` carrega somente o candidato próprio e o tokenizer correspondente,
recusa histórico acima de 256 tokens e oferece propostas/execuções para
inspeção. Ele não faz registro em conversas privadas nem integra o runtime.
O pacote local inclui pesos, tokenizer, arquitetura própria e scripts.

## Verificação

3.300 alvos de treino/dev passaram no roundtrip de caracteres/tokens e na
execução de referência. Oito contratos independentes conferiram Decimal,
déficit temporal, ausência/negação/contradição, rejeição de código/número com
texto, consulta sem referente e fonte que atravessa turnos. Um teste inicial
comparava formatação decimal; foi corrigido para comparar o valor exato,
preservando a implementação. Os oito passaram.

Nenhum arquivo do motor ou peso ativo foi alterado. Dados, scripts, logs,
resultados, checkpoint escolhido e hashes foram conservados. Nenhum candidato
foi aprovado ou ativado.
