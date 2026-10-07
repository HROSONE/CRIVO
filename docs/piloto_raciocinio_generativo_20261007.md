# Piloto treinado de raciocínio por passos — 07/10/2026

**Resultado: não aprovado para o chat.** O piloto não demonstrou o ganho de
raciocínio pretendido. O modelo de resposta direta superou a geração iterativa
de passos nas classificações. Não há justificativa para anunciar capacidade
generativa geral nem substituir os pesos de produção.

## O que foi realmente executado

Dois ajustes dos mesmos pesos próprios de 17.428.224 parâmetros, sem modelos
externos, em CPU com PyTorch 2.14.1+cpu. Cada variante recebeu 400 atualizações,
lote de seis e AdamW com taxa 0,00015. Semente 8104. O alvo da perda é somente
a resposta, mantendo o contexto sem truncar evidências.

- **Direto:** aprende a produzir uma das quatro classificações: sustentado,
  refutado, indeterminado ou conflito. Não escreve uma prova.
- **Passos:** aprende a gerar `regra|apoios|conclusão` e depois uma classificação.
  O modelo propõe os passos. O verificador aceita ou veta cada um, sem escolher
  uma inferência substituta nem responder pelo modelo.

Os dois treinos compartilham problemas e orçamento de atualizações/lote, mas
não têm o mesmo número de tokens supervisionados ou contextos intermediários.
Os respectivos orçamentos de tokens estão nos metadados do resultado. Não é
uma comparação com custo computacional ou tokens perfeitamente igualados.

480 problemas de treino; 32 de desenvolvimento; 56 de teste. A variante de
passos tem 960 exemplos, incluindo estados intermediários e término. Os
problemas usam cadeias, conjunções, negação, condições ausentes, conflitos,
distratores e permutação de premissas. Cada partição usa um vocabulário próprio.
24 casos de teste incluem profundidades 4/5 ou um grafo de diamante, ausentes
no treino. Os outros 32 medem transferência lexical em estruturas conhecidas.
Os termos podem existir no pré-treino anterior: a separação lexical diz respeito
a este ajuste, não a tudo que os pesos viram na vida.

Dados e manifesto foram gravados antes de otimizar. Nenhum conjunto congelado
anterior do CRIVO entrou no piloto. Os rótulos vêm do resolvedor proposicional
existente: são supervisão de um domínio sintético restrito, não anotação
independente de textos livres. Todos os exemplos de passos do professor passam
pelo verificador, com contrato executado na suíte.

## Seleção e resultados

O checkpoint é escolhido no desenvolvimento, a cada 100 atualizações. No
controle direto, o critério é classificação correta; nos passos, conclusão
com contrato completo, seguida de classificação correta. O teste não escolhe
checkpoint. Os pesos exportados em FP16 são recarregados para a avaliação.

| Variante | Checkpoint | Classificação no teste | Classificação nas estruturas inéditas | Provas completas necessárias |
|---|---:|---:|---:|---:|
| Direto | 300 | 50/56 (89,3%) | 18/24 (75,0%) | Não gera provas |
| Passos | 200 | 27/56 (48,2%) | 11/24 (45,8%) | 0/28 |

Antes dos ajustes, os pesos originais acertavam 0/32 casos de desenvolvimento
no protocolo de cada variante. Esse número mede incompatibilidade/capacidade
na tarefa nova, não qualidade geral do CRIVO.

No desenvolvimento, o checkpoint 300 de passos produziu uma prova completa
e o 400 produziu duas, mas perderam em contratos totais para o 200. A seleção
escolheu o 200 conforme o critério fixado. Essas provas isoladas não justificam
trocar o checkpoint depois de olhar o teste nem anunciar inferência multissalto.

No teste do modelo selecionado, houve 41 términos sem gerar passo; dez falhas
de apoio ausente/futuro; duas de regra; uma de antecedente; uma de premissas
em conflito; e uma de protocolo. Nenhum passo foi aceito. Quase todos os
acertos vêm de indeterminação ou conflito. Uma resposta «indeterminado» pode
ser um término prematuro errado em um problema que possui conclusão.

O executor NumPy reproduziu 27/56 classificações, 11/24 no subconjunto inédito,
zero passos aceitos e zero provas completas, sem PyTorch. Os pesos permanecem
marcados `controle.aprovado: false`.

[Resultado de treino e avaliação](resultados/piloto_raciocinio_generativo_20261007.json).
[Avaliação NumPy e diagnóstico de seleção](resultados/piloto_raciocinio_generativo_numpy_20261007.json).

## Nova fronteira de ignorância e pesquisa

**Dúvida:** a falha está somente em redigir nomes/negativos inéditos ou também
em selecionar regra e fatos? Uma frase de teste chegou a dizer «a chave
primária», embora a premissa tratasse de «a chave entra». Mas isso não basta
para atribuir todos os erros à geração de texto.

**Experimento diagnóstico:** para cada primeira proposta, substituímos somente
a redação pela conclusão da regra citada, fora da execução, e verificamos as
referências. Nenhuma seleção virou um passo válido. Essa proposta modificada
não entrou na resposta nem na contagem de acertos. Portanto, neste checkpoint
e nestes casos, corrigir apenas a cópia da conclusão não resolveria as escolhas.

**Pesquisa adicional:** [FaiRR, ACL 2022](https://aclanthology.org/2022.acl-long.77/)
separa seleção de regra, seleção de fatos e composição da inferência em
componentes treinados. A inferência depende dos apoios escolhidos, e os erros
de cada estágio são observáveis. O artigo fundamenta uma alternativa para
investigação; não transfere seus resultados automaticamente ao CRIVO.

[Pointer-generator, ACL 2017](https://aclanthology.org/P17-1099/) combina cópia
de conteúdo da entrada com geração de palavras, ajudando a preservar detalhes.
Isso pode ser útil para a redação de entidades, mas nosso diagnóstico mostra
que cópia seletiva, sozinha, não basta para este piloto.

**Antes:** aprendíamos escolha de regra, apoios, redação e término em uma mesma
sequência de saída, esperando que o ajuste conjunto bastasse.

**Depois:** a hipótese operacional passa a separar supervisão e avaliação de
seleção de regra, seleção de apoios, término e redação. Há evidência local de
falha na seleção; a arquitetura modular encontrada fornece uma maneira de
isolar esse estágio. Ainda não conhecemos a causa única: poucos exemplos,
orçamento, configuração da perda, formato e generalização podem contribuir.

**Consequência:** o próximo experimento deve medir seleção independentemente
da fluência, comparar alvos/recompensas de cada estágio e usar um novo teste
retido para decisões posteriores. Reutilizar este teste para ajustar o modelo
e continuar chamando-o de teste cego seria incorreto. Não implementamos FaiRR
nem novos seletores neste piloto; esta é a proposta derivada do resultado.

## Código, pesos e reprodução

Tudo fica em `experimentos/raciocinio_generativo/`. Os pesos selecionados de
passos e seu tokenizer estão em `pesos_piloto/`; corpus e manifesto em
`dados_piloto/`. Os pesos do controle direto permanecem na pasta local de
execução; seu treino e metadados são reproduzíveis pelo script.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 python \
  experimentos/raciocinio_generativo/treinar_piloto.py \
  --saida /tmp/crivo-piloto --passos 400 --avaliar-a-cada 100

OPENBLAS_NUM_THREADS=1 python \
  experimentos/raciocinio_generativo/avaliar_numpy.py \
  --pesos experimentos/raciocinio_generativo/pesos_piloto \
  --casos experimentos/raciocinio_generativo/dados_piloto/teste.json \
  --saida /tmp/avaliacao-piloto-numpy.json

PYTHONPATH=experimentos/raciocinio_generativo python -S -m unittest testes_piloto -v
```

O executor `responder_piloto.py` permite uma consulta por CLI com `--premissa`
repetido e `--objetivo`; ele não está integrado à linguagem natural do chat.
Uma classificação positiva/negativa sem prova é vetada. Indeterminação e
conflito continuam sendo previsões neurais, sem prova gerada neste protocolo.

Validação: oito contratos passaram sem dependências opcionais; todas as
sequências do professor cabem no contexto de 256 tokens; gravação na pasta de
produção é bloqueada; inferência NumPy executada nos 56 casos; sintaxe e
`git diff --check` passaram. Workflow específico cobre os contratos, sem
reexecutar um treino pesado no CI. Publicação dos artefatos não é aprovação
dos pesos ou confirmação do CI remoto.
