# Arquitetura Cognitiva do CRIVO

## Diretriz de longo prazo para agentes e desenvolvedores

Este documento define uma bússola arquitetural do CRIVO. Ele não declara que o
software atual já implementa um cérebro humano e não autoriza alegações de
equivalência biológica, consciência ou cognição humana.

A inspiração é **funcional e sistêmica**: estudar princípios úteis da organização
do cérebro e do sistema nervoso e transformá-los, quando houver benefício
mensurável, em mecanismos computacionais próprios, testáveis e auditáveis.

## Objetivo

Evoluir o CRIVO de uma coleção de capacidades especializadas para um sistema
cognitivo integrado capaz de:

1. perceber e interpretar entradas;
2. manter um estado mental de trabalho;
3. recuperar experiências e conhecimento;
4. formular hipóteses;
5. planejar;
6. escolher ferramentas/capacidades;
7. agir;
8. observar o resultado;
9. detectar erro ou incerteza;
10. replanejar;
11. responder;
12. registrar experiência útil;
13. consolidar aprendizagem sem destruir capacidades anteriores.

O ciclo desejado é:

```text
percepcao
   |
   v
representacao / workspace
   |
   +--> memoria de trabalho
   +--> memoria episodica
   +--> memoria semantica
   +--> memoria procedural
   |
   v
controle executivo
   |
   +--> hipoteses
   +--> planejamento
   +--> selecao de ferramenta
   |
   v
acao
   |
   v
observacao
   |
   v
critica / verificacao
   |
   +--> replanejar, se necessario
   |
   v
resposta + aprendizagem
```

## Analogia funcional, nao copia literal

Algumas inspirações possíveis:

| Sistema biologico (analogia) | Papel computacional desejado |
|---|---|
| sistemas sensoriais | codificar texto, voz, imagem e outros sinais |
| memoria de trabalho | estado pequeno e ativo do problema atual |
| hipocampo | registrar e recuperar episodios/experiencias rapidamente |
| memoria semantica cortical | conhecimento consolidado e relações gerais |
| cortex associativo | representações distribuídas e associação entre conceitos |
| cortex pre-frontal | metas, planejamento, controle e replanejamento |
| ganglios da base | seleção entre ações/capacidades concorrentes |
| cerebelo (analogia funcional) | previsão, comparação entre resultado esperado e observado, correção |
| atenção | selecionar informação relevante sob capacidade limitada |
| consolidação | transformar experiências repetidas/validadas em conhecimento durável |

Essas correspondências são metáforas de engenharia. Não se deve presumir que um
módulo computacional reproduz a neurobiologia da estrutura citada.

## Principio central: integrar, nao acumular ilhas

Uma nova capacidade não deve virar automaticamente mais um módulo isolado.

Antes de criar um componente, o agente deve perguntar:

- qual estado compartilhado ele lê?
- qual evidência produz?
- como o executivo decide quando usá-lo?
- como seu resultado retorna ao workspace?
- como erros e incerteza são representados?
- como a experiência pode ser lembrada?
- como ele será avaliado fora dos exemplos usados para construí-lo?

Módulos especializados existentes continuam úteis. Lógica formal, recuperação de
conhecimento, programação, classificadores, verificadores e redes neurais devem
poder funcionar como circuitos/ferramentas especializadas de uma arquitetura
cognitiva comum.

## Workspace cognitivo

O CRIVO deve caminhar para uma representação explícita e compartilhada do estado
atual. Ela pode conter, conforme a tarefa:

- objetivo;
- contexto;
- entidades;
- fatos/evidências;
- hipóteses;
- relações;
- restrições;
- plano atual;
- ações já tentadas;
- observações;
- conflitos;
- incerteza;
- perguntas ainda abertas.

O workspace não deve ser confundido com um grande prompt textual. Estruturas
tipadas e representações aprendidas podem coexistir.

## Memorias em velocidades diferentes

O projeto deve distinguir pelo menos:

**Memoria de trabalho** — informação ativa da tarefa/conversa.

**Memoria episodica** — experiências: o que aconteceu, contexto, ação tomada,
resultado e confiabilidade.

**Memoria semantica** — conceitos, fatos, relações, modelos do mundo e suas
fontes/versões.

**Memoria procedural** — habilidades e procedimentos: como executar, diagnosticar,
programar, verificar e corrigir.

Aprender uma experiência não exige necessariamente alterar pesos imediatamente.
A consolidação pode ocorrer depois, somente com dados validados.

## Controle executivo

O sistema deve evoluir além de mapear pedido -> módulo -> resposta.

O comportamento-alvo é:

```text
objetivo
 -> decompor problema
 -> recuperar memoria/conhecimento
 -> gerar hipoteses
 -> estimar incerteza
 -> escolher proxima acao
 -> executar
 -> observar
 -> verificar previsao
 -> atualizar estado
 -> continuar ou concluir
```

O planejador deve futuramente conseguir criar planos não cadastrados
explicitamente, acompanhar dependências, interromper caminhos improdutivos e
replanejar a partir de evidência nova.

## Raciocinio

Não tratar "raciocínio" como uma única função.

O CRIVO pode combinar:

- associação aprendida;
- raciocínio causal;
- raciocínio temporal;
- lógica formal;
- raciocínio probabilístico;
- analogia;
- decomposição;
- simulação de consequências;
- busca;
- cálculo;
- verificação externa.

Solucionadores determinísticos existentes podem ser preservados como ferramentas
confiáveis. A rede central não precisa reaprender aritmética ou prova lógica se
puder reconhecer quando delegar e interpretar corretamente o resultado.

## Aprendizado e plasticidade

Inspirado funcionalmente em plasticidade em escalas diferentes:

```text
segundos/minutos -> workspace
horas/dias       -> episodios persistentes
repeticao + validacao -> consolidacao semantica/procedural
treino controlado -> alteracao de pesos
avaliacao cega    -> promocao ou rejeicao
```

Nunca promover pesos apenas porque a loss diminuiu. A aprendizagem precisa ser
medida no comportamento livre e em testes não usados para escolher a solução.

O sistema deve proteger-se contra esquecimento catastrófico, contaminação de
avaliação, memórias falsas e consolidação de experiências incorretas.

## Modelo neural

A contagem de parâmetros não é o objetivo arquitetural.

Modelos maiores podem aumentar capacidade, mas escalar somente depois de
demonstrar que a receita de dados, objetivo de treino, contexto e avaliação
produz ganho real de generalização.

O núcleo neural deve progressivamente assumir funções de representação,
linguagem, associação e generalização. Conhecimento verificável não precisa
estar todo memorizado nos pesos: memória externa estruturada e recuperação são
partes do cérebro computacional.

## Sistema nervoso computacional

A analogia com sistema nervoso significa também comunicação entre subsistemas.

É desejável definir protocolos comuns para:

- eventos;
- observações;
- intenções;
- ações;
- evidências;
- erros;
- confiança/incerteza;
- memória;
- feedback.

Um componente não deve fingir que executou uma ação. Ação produz observação
verificável. Falha produz estado de falha. Incerteza permanece explícita.

## Programacao como habilidade procedural

Para tornar programação uma capacidade real, o alvo não é apenas recuperar
explicações. O ciclo desejado é:

```text
entender repositorio
 -> representar arquitetura
 -> localizar simbolos relevantes
 -> propor mudanca
 -> editar
 -> executar testes/compilar
 -> observar erros
 -> diagnosticar
 -> corrigir
 -> testar novamente
 -> revisar regressao
 -> guardar experiencia
```

Conhecimento de programação, geração neural e ferramentas verificáveis devem
cooperar.

## Avaliacao obrigatoria

Toda afirmação de nova capacidade deve distinguir:

1. recuperação de conteúdo conhecido;
2. paráfrase;
3. composição;
4. execução de procedimento;
5. generalização para exemplo novo;
6. tarefa adversarial;
7. conversa/tarefa livre;
8. retenção após novas aprendizagens.

Acertar exemplos de desenvolvimento não prova generalização.

Métricas internas como entropia cruzada, similaridade ou confiança de
classificador não substituem avaliação comportamental.

## Regras para futuros agentes

Ao trabalhar no CRIVO:

1. preserve evidência e reprodutibilidade;
2. não confunda benchmark com capacidade geral;
3. prefira corrigir causas a cadastrar respostas para testes específicos;
4. não copie literalmente o cérebro humano nem faça alegações biológicas sem
   evidência;
5. integre capacidades ao ciclo cognitivo comum sempre que isso for tecnicamente
   justificável;
6. preserve módulos especializados que sejam verificáveis e úteis;
7. represente incerteza e falha explicitamente;
8. mantenha avaliação reservada separada do treino e do desenvolvimento;
9. não aumente parâmetros ou duração de treino como substituto automático para
   diversidade de dados e arquitetura;
10. faça mudanças incrementais e mensuráveis na implementação, mesmo que a visão
    de longo prazo seja ampla;
11. não promova uma arquitetura apenas porque parece mais "humana": exija ganho
    mensurável;
12. documente quando uma analogia neurobiológica é apenas inspiração.

## Norte arquitetural

O CRIVO não deve evoluir para uma coleção infinita de respostas e regras.

O norte é um sistema em que capacidades diferentes compartilham estado,
memória e feedback:

```text
PERCEBER
  -> REPRESENTAR
  -> LEMBRAR
  -> ASSOCIAR
  -> FORMULAR HIPOTESES
  -> PLANEJAR
  -> AGIR
  -> OBSERVAR
  -> VERIFICAR
  -> CORRIGIR
  -> APRENDER
```

A pergunta principal para cada nova etapa passa a ser:

> Esta mudança aproxima o CRIVO de um sistema que consegue formar um estado
> interno útil, usar experiência e conhecimento, escolher ações, verificar
> consequências e aprender — ou apenas adiciona mais uma resposta especializada?

Essa pergunta é uma diretriz, não um teste suficiente. Decisões finais continuam
dependendo de experimentos, métricas e regressões.
