# Experimento de raciocínio modular — 07/10/2026

## Pergunta e hipótese

O piloto conjunto anterior não produziu nenhuma das 28 provas necessárias no
seu teste. A inspeção das saídas também encontrou erros de seleção de regra e
apoios; simplesmente substituir a conclusão pelo consequente da regra não
resolvia essas seleções. Não bastava presumir que o único problema era redação.

A pesquisa do [FaiRR, ACL 2022](https://aclanthology.org/2022.acl-long.77/)
acrescentou uma alternativa operacional: decompor seleção de regra, seleção de
fatos e composição. Isso mudou o experimento: medir e supervisionar componentes
separadamente, em vez de pedir uma saída conjunta com regra, apoios e conclusão.
O artigo usa três Transformers distintos. Este experimento é uma adaptação com
um Transformer próprio compartilhado e quatro tarefas identificadas no prompt;
não é reprodução dos resultados publicados nem demonstração de sua causa.

## Método pré-definido

- Base própria `artefatos/geracao_pt`: Transformer causal de 17.428.224 parâmetros,
  vocabulário 8.192, dimensão 384, oito camadas, oito cabeças e contexto 256.
  Nenhum modelo ou peso externo foi utilizado.
- Quatro tarefas: aplicabilidade de regra (0/1); correspondência entre condição
  e fato, incluindo polaridade (0/1); estado A–E (sustentado, refutado,
  indeterminado, conflito, continuar); redação textual do consequente.
- 640 problemas de treino, 56 de validação e **84 de teste novo**. Sementes
  8201/8202/8203; treino 8204. O teste usa oito literais diferentes dos anteriores
  e de treino/validação; 36 problemas têm estruturas reservadas, incluindo
  cadeias de quatro/cinco passos e diamante. Os dados foram gravados e tiveram
  seus hashes calculados antes da otimização.
- 2.720 exemplos de regra, 12.800 de apoio, 1.280 de estado e 640 de redação.
  São exemplos sobre estados intermediários produzidos por professor simbólico
  apenas para construir os alvos supervisionados e avaliar etapas isoladas.
- 800 atualizações, lote 8, AdamW, taxa 0,00015; tarefas alternadas, 200
  atualizações por tarefa, classes balanceadas dentro das tarefas classificatórias.
  Perda somente nos tokens de resposta e fim. Não equivale a quatro treinos
  independentes nem a um orçamento controlado contra o piloto anterior.
- Avaliação em validação a cada 200 atualizações. Seleção lexicográfica:
  provas neurais completas, respostas neurais corretas, provas do controle
  simbólico e soma de acurácias das etapas. O teste nunca seleciona o checkpoint.
- Exportação float16; execução NumPy independente dos pesos selecionados.
  Redação greedy de até 40 tokens, exige fim, sem máscara lexical, prefixo da
  fonte ou penalidades de repetição. Classificação escolhe entre códigos válidos.

## Fronteira entre modelo e verificador

O parser enumera todas as regras e todos os fatos disponíveis. O modelo pontua
cada regra e, para cada antecedente da escolhida, todos os fatos disponíveis.
A maior pontuação deve ser pelo menos 0,5. Não há filtro simbólico prévio de
aplicabilidade, busca pela próxima opção nem reparo após um veto. Esse limiar
sobre probabilidades restritas às classes não representa confiança calibrada.

O verificador testa apenas a proposta escolhida, exige os antecedentes e a
conclusão corretos e pode interromper a execução. Status positivo/negativo
exige o literal correspondente entre premissas ou passos previamente aceitos.
Indeterminação e conflito são previsões classificatórias; não são provas
formais desses dois estados. Logo, o total de respostas corretas precisa ser
lido junto do número de provas completas e dos erros por etapa.

Há duas execuções separadas: **neural**, em que o modelo escreve cada conclusão,
e **simbólica**, em que o controle copia o consequente da regra escolhida. A
segunda mantém as escolhas neurais, mas sua composição textual é simbólica;
seu sucesso não conta como geração aprendida. Mesmo a redação neural aqui é uma
tarefa estreita de extração/composição de um consequente presente na regra,
não criação de conhecimento, resumo livre ou raciocínio geral.

## Resultados

Checkpoint selecionado: **400**. Tempo total do treino e avaliações originais:
**472 segundos** em CPU. Os 20 contratos de dados/protocolo passaram sem NumPy
ou PyTorch (`python -S`). A avaliação NumPy independente, com o mesmo greedy
de 40 tokens do Torch, não teve divergência de status, passos ou motivo nos
84 casos, em nenhuma das duas composições. A primeira avaliação NumPy usada
pelo processo de treino herdava penalidades de repetição e limite 70 do executor
existente; foi verificada novamente com o decodificador uniforme. Os resultados
por caso permaneceram iguais; isso não alterou a seleção do checkpoint.

| Execução no mesmo teste novo | Respostas corretas | Provas completas | Provas em estruturas reservadas |
|---|---:|---:|---:|
| Piloto conjunto anterior, pesos já congelados | 44/84 | 3/42 | 0/18 |
| Modular, redação neural | **30/84** | **5/42** | **0/18** |
| Modular, composição simbólica explícita | 40/84 | 15/42 | 0/18 |

A comparação no mesmo teste evita atribuir melhora a diferenças entre os dois
conjuntos reservados. Ainda assim, os orçamentos e tarefas de treino diferem;
não é uma comparação controlada que prove superioridade da arquitetura.
Os pesos do piloto anterior não foram reajustados para esta comparação.
Seu relatório está em `docs/resultados/controle_conjunto_no_teste_modular_20261007.json`.

As cinco provas neurais completas são três de profundidade 1, uma de
profundidade 2 e uma de profundidade 3. Foram aceitos **27 passos neurais** e
**53 seleções válidas**. No controle simbólico, 66 passos e 74 seleções válidas.
Nas 36 estruturas reservadas, ambos acertaram 11 respostas, mas nenhuma prova
completa das 18 necessárias. O piloto anterior acertou 17 respostas nesse grupo.

Diagnósticos de etapas no teste, em estados do professor: regra **43/48**,
apoio **48/48**, estado **82/108**. Para indeterminação, o classificador acertou
somente **4/21** nessa amostra; para continuar, **22/24**. Acertos locais altos
não se traduziram em execução confiável de cadeias.

A execução neural terminou por: 31 términos previstos (30 corretos), 22
rejeições de regra abaixo do limiar, 16 conclusões incorretas, sete redações
inválidas, quatro apoios abaixo do limiar, três passos repetidos e um término
positivo sem prova. As conclusões propostas estão registradas no relatório
NumPy independente. Exemplo real: `modular-teste-0052` propôs **“o rádio tensão”**
quando a regra exigia **“o rádio toca”**; o verificador vetou a conclusão.

**Resultado: não aprovado.** Surgiram algumas provas válidas, porém a acurácia
global caiu frente ao piloto anterior e a generalização estrutural continua
sem demonstração. Trocar apenas a redação por composição simbólica também não
resolveu as cadeias reservadas. O próximo diagnóstico precisa distinguir
aplicabilidade, prioridade de regras e término na trajetória livre. Separar
pesos/adaptadores pode ser uma hipótese futura, mas interferência entre tarefas
não foi causalmente demonstrada neste experimento.


## Limites e interpretação

Os problemas são sintéticos, com gramática proposicional restrita. O teste
reservado mede transferência entre literais e alguns grafos, não linguagem
natural irrestrita. Os diagnósticos de etapas usam no máximo os primeiros 24
exemplos de cada classe, numa amostra fixa estratificada de estados do professor;
não medem todas as decisões da execução livre. A prova completa é o critério
mais exigente para os casos sustentados/refutados.

Os resultados não sustentam integrar automaticamente estes pesos ao chat.
`controle.aprovado` permanece falso. Código, dados, resultados individuais,
checkpoint e metadados ficam isolados em `experimentos/raciocinio_generativo`.
Não ajustar estes pesos a partir deste teste e continuar chamando-o de reservado.

## Reprodução

Treino requer PyTorch CPU e NumPy; avaliação requer apenas NumPy. A raiz precisa
estar disponível para os módulos próprios:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 python experimentos/raciocinio_generativo/treinar_modular.py --saida /tmp/crivo-modular --passos 800 --avaliar-a-cada 200
OPENBLAS_NUM_THREADS=1 PYTHONPATH=. python experimentos/raciocinio_generativo/avaliar_modular.py --pesos experimentos/raciocinio_generativo/pesos_modulares --casos experimentos/raciocinio_generativo/dados_modulares/teste.json --saida /tmp/crivo-modular-avaliacao.json
PYTHONPATH=experimentos/raciocinio_generativo python -S -m unittest testes_piloto testes_modular -v
```

Resultados integrais e hashes em
`docs/resultados/raciocinio_modular_20261007.json`; avaliação NumPy independente
em `docs/resultados/raciocinio_modular_numpy_20261007.json`.
