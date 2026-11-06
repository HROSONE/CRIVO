# Auditoria do treino do CRIVO: qual é o melhor próximo treino (19/10/2026)

Pedido do criador: "faz uma auditoria do crivo para descobrirmos o melhor treinamento para ele".

Esta auditoria lê os resultados registrados desde a fase 2 do 17M (12/10) até a destilação v2
(15/10) e acrescenta três medições feitas aqui, na CPU, sem treinar nada. Nenhum peso foi
alterado, promovido ou ligado. Nenhum modelo de terceiros foi baixado ou executado.

## Resposta curta

**O gargalo não é ler mais nem crescer. É a variedade de jeitos de falar com o CRIVO nos dados de
conversa, e a régua que decide entre treinos.** O próximo treino que mais promete é a partir da
mesma base da 6a (46M), com **muito mais formas de fala da pessoa por situação** (inclusive
conversas de vários turnos e contraexemplos das confusões medidas), **mantendo as respostas que já
existem**, treino curto (cerca de uma volta) e escolha por uma régua maior, com intervalo de
confiança e duas sementes. Antes de treinar, a régua precisa ser consertada, senão nenhuma diferença
de 1 a 3 pontos pode ser lida.

A medição nova mais importante: uma sonda linear no 46M do chat acerta a situação em 69,2% das
frases nunca vistas, só 3,5 pontos acima do que ele acerta respondendo (65,7%). Então o limite é
o que ele entende, e isso vem dos dados, não da forma de gerar.

## 1. O que os resultados já registrados mostram

### 1.1 Seis treinos diferentes param no mesmo platô

Sentido certo no blind v3 (2.980 frases nunca vistas), tirado dos relatórios:

| modelo | tamanho | o que mudou | blind v3 |
|---|---|---|---|
| fase 5 v3 D | 17M | +variedade v3 | 63,2% |
| fase 5 v4 E | 17M | +reforço das 35 situações fracas | 62,6% |
| fase 5 v4 F (reserva) | 17M | recomeça da fase 5 | 63,5% |
| 6b v3 | 46M, leu 3,6 bi de tokens | +OASST2, legendas | 62,1% |
| 6b v4 (no chat) | 46M | fase 5 ×3, escolha por sentido | 65,7% |
| 6b v5 médio | 46M | +10% de professor (Qwen3-8B) | 64,3% |

Crescer de 17M para 46M e ler 3,6 bilhões de tokens a mais mudou o blind v3 em cerca de 2 pontos,
e o blind v1 piorou (69,8% → 65,3%). Reforçar as situações fracas (v4 E) não subiu o teste limpo.

### 1.2 O único salto grande veio da variedade das falas da pessoa

A fase 5 v2 trocou ~6 jeitos de dizer por situação por dezenas: paráfrases de 32% → 75,7% e Grok
de 33,9% → 71,6%, no mesmo modelo de 17M. Nenhuma outra mudança (passos, tamanho, mistura,
cabeças, professor) chegou perto disso.

### 1.3 Dentro do treino, ele decora cedo

No histórico da 6b v4 (`resumo_fase6b_v4.json`), a perda de validação da fase 5 é mínima no
**passo 327** (0,528) e depois **sobe** até 0,634. O sentido no dev já está em 56% no passo 327 e
depois oscila entre 55,5% e 66% sem tendência clara. Os 247 mil exemplos repetidos 3 vezes não
ensinam mais nada depois de menos de uma volta: só decoram as respostas.

### 1.4 Conflitos de alvo sempre custaram caro

- 6b v3: "você é humano?" com uma resposta na fase 5 e outra no IDENTIDADE.md → 0% nessas situações.
- Fase 5 v3: "preciso de ajuda" calmo no treino e urgente no teste → 4 erros de urgência.
- Destilação v5 médio: o professor respondeu as mesmas falas da fase 5 com outra resposta → risada
  nas paráfrases 11,4% → 0,8%; e reescreveu fatos → "usa o fato" 0,9 → 0,7, com fatos errados.

### 1.5 Escolhas de versão erradas por réguas pequenas

- 6b v1: escolheu o passo 50 pela perda num OASST2 de 43 conversas que já estava no pré-treino.
- Fase 5 v4 E/F: pararam com 0,39–0,49 bi de tokens (de 1 bi planejado) porque o critério "seguro"
  usava 9 casos de nome.

### 1.6 O que funcionou de verdade

- Ler com replay de 25%: a perda de linguagem subiu só 2–3% em todos os ajustes.
- Fase 3 (quadro → frase): 98,3% no blind, porque a tarefa é fechada e a cópia de fatos é exata.
- Pensador v2: recursão + conferência, aprovado nos gates.
- Fatos copiados literalmente: 99,8% "usa o fato". Reescrever fatos piora.

## 2. Medições novas desta auditoria (CPU, sem treinar)

Scripts nesta pasta. Dados: `experimentos/fase5_conversa_20261013/dados_fase5_v3.json.gz`.

### 2.1 Os dados (`auditar_dados.py`)

| medida | valor |
|---|---|
| exemplos de treino | 194.016 |
| situações | 134 |
| mensagens distintas sem histórico | 16.683 |
| repetição média de cada forma | 5,3 vezes |
| formas distintas por situação | mediana 119, mínimo 2 |
| respostas distintas por situação (cenas) | mediana 8 |
| mesma mensagem com duas situações | 2 (0,0%) |
| dev usado na escolha (`frase_nova`, 750) idêntico ao treino | 0 |
| blind v3 idêntico ao treino | 0 |

Situações com menos formas: `fato:sem_mais` 2, `nome:meu_lembrar` 7, `fato:de_novo` 13,
`fato:resume` 20, `fato:mais` 22, `nome:corrigir` 26, `cena:sem_sentido` 41.

Leitura: os dados da v3 estão limpos (sem conflito literal, sem vazamento para o dev de escolha nem
para o blind). O problema é de quantidade de formas: são 194 mil linhas, mas só ~17 mil frases
diferentes, e as respostas são poucas (8 por situação). O modelo aprende uma escolha entre 134
situações, com cerca de 120 exemplos de cada.

### 2.2 Linha de base sem rede profunda (`baseline_ngramas.py`)

Um centróide de n-gramas de caracteres e palavras, só da mensagem, treinado com as 36.773 formas
distintas do treino, acerta a situação em **43,9%** do blind v3 (top-5: 69,6%). O 46M no chat
acerta 65,7% respondendo. O 46M entende mais que a superfície das palavras, mas um terço do
caminho de 0 a 65,7% já sai só de n-gramas, o que confirma que o treino atual ensina muito
"responder pela palavra".

### 2.3 Sonda linear no 46M do chat (`sonda_linear.py`)

Pergunta: o 46M "entende" a situação por dentro e só erra ao falar, ou já entende errado?
Pegamos o estado final do 46M v4 (o do chat, NumPy int8) no ponto em que ele começaria a
responder, com o mesmo prompt do chat. Treinamos uma regressão logística com 25 formas de treino
por situação (3.329) e medimos no blind v3 inteiro (2.980), em 20 minutos de CPU.

| | blind v3 top-1 | top-5 |
|---|---|---|
| centróide de n-gramas (só a mensagem) | 43,9% | 69,6% |
| 46M respondendo (régua de sentido, registrado) | 65,7% | — |
| **sonda linear no estado do 46M** | **69,2%** | **88,3%** |

Leitura:
- A sonda passa a fala em só 3,5 pontos. **O limite está no entendimento**, não em como ele
  escolhe as palavras da resposta. Mexer na decodificação, no freio ou em cabeças de saída não
  vai buscar mais que alguns pontos.
- No top-5 a situação certa aparece em 88%: a maior parte dos erros é entre situações próximas.
  É o que contraexemplos e mais formas por situação atacam, e é o que a lista de vizinhas
  aceitas precisa separar na régua.

## 3. Diagnóstico

1. **Pré-treino não é o gargalo agora.** A base leu ~78 tokens por parâmetro (bem acima do ponto
   ótimo de ~20 do Chinchilla) e a perda ainda cai devagar (−0,003 nos últimos 2 mil passos).
   Ler mais vai custar horas de A100 para ganho pequeno na conversa.
2. **Tamanho não é o gargalo agora.** 17M e 46M empatam na régua. Até ~150M cabe na CPU de 8 GB,
   mas não há medida que indique falta de capacidade.
3. **Dados de conversa são o gargalo**: poucas formas da pessoa por situação, quase nada de
   vários turnos (o "legal e você?" ainda falha), e respostas repetidas que o modelo decora em
   menos de uma volta.
4. **A régua limita as decisões.** Com 2.980 frases, o intervalo de 95% é ±1,7 ponto; com o dev de
   400, ±4,7; com 15 frases reais, 12/15 contra 14/15 não é diferença significativa. Escolher o
   melhor de ~10 medidas no dev de 400 dá um viés otimista de alguns pontos (v4: dev 66%, blind
   65,7%). Sempre uma semente. A lista fechada conta resposta boa de situação vizinha como erro.
   O juiz, já autorizado, nunca rodou.

## 4. O melhor treinamento, em ordem

### Passo 0: consertar a régua (CPU, antes de qualquer GPU)

- **Frases reais:** juntar 150 a 300 mensagens reais do criador no site (com permissão),
  congeladas antes do treino, com a situação aceita escrita antes. Hoje são 15.
- **Vizinhas aceitas:** lista escrita antes de medir (ex.: estou_bem × oi_tudo_bem), relatada ao
  lado da conta estrita.
- **Intervalo de confiança** (bootstrap) em toda tabela; promover só quando a melhora passa do
  intervalo, em duas sementes.
- **Dev de escolha maior:** ≥ 1.500 frases novas, para a escolha não ser sorte.
- **Rodar o juiz** já planejado (v4 × v5 médio, pares com ordem trocada). Responde, sem treinar,
  se o professor ajudou fora da lista. O juiz relata; a régua própria decide (AGENTS.md).

### Passo 1: o treino "v6 entendimento" (o mais promissor)

- **Base:** a mesma da 6a (`fcf396b9…`). Sem ler mais, sem crescer.
- **Variedade de entrada, não de resposta.** Meta de ≥ 500 formas distintas por situação,
  começando pelas que ficaram em 0–10% (cansado, insulto, seja_breve, sem_sentido, ser_humano,
  trabalho_ruim, flerte, perguntar_crivo) e pelas com < 30 formas. As formas podem vir:
  - do criador e de pessoas (melhor fonte, rotular a situação);
  - do professor autorizado (Qwen3-32B, Apache 2.0), **só escrevendo o que a pessoa diz**, com
    origem marcada em pasta própria, nunca chamado de humano, e rótulo conferido pelo juiz de outra
    família. As respostas continuam as das listas: assim não nasce conflito de alvo, o erro que
    derrubou a v3 e a v5 médio.
- **Contraexemplos das confusões medidas:** viaja × viagem, cheguei × despedida, tenho_bicho ×
  gosto_bichos, insulto × despedida_rude, estou_bem × oi_tudo_bem, ansioso × sono.
- **Vários turnos:** casos em que a mesma frase muda de situação pelo turno anterior
  ("legal e você?" depois de "E você, como está?").
- **Fatos copiados literalmente**, como na v4. Professor não reescreve fato.
- **Treino curto:** cerca de 1 a 1,5 volta nos dados novos, não 3 repetições; 25% de leitura de
  replay; escolha pelo sentido no dev grande, a cada ~300 passos.
- **Duas sementes.** Uma L4 dá conta (a v4 levou ~95 min).

**Previsão testável:** se a hipótese estiver certa, o blind v3 sobe como subiram as paráfrases na
v2 (dezenas de pontos, não 1 a 3). Se ficar em 63–66% com 5× mais formas, a hipótese cai e o
próximo suspeito é a forma da tarefa (escolher entre respostas decoradas).

### Passo 2 (depois): correção sobre a própria fala

O 46M responde a falas novas e reais, o juiz e o criador marcam as erradas, e elas voltam ao
treino com a resposta certa das listas (destilação "on-policy" só em texto, como no plano da
destilação). É o que ataca os erros que ele de fato comete, não os que imaginamos.

### O que não fazer agora

- Ler mais 1 bilhão de tokens ou crescer para 84–148M: sem sinal de que ajuda a conversa.
- Professor escrevendo **respostas** para falas que a fase 5 já tem, ou reescrevendo fatos.
- Cabeças pointer sobre base congelada (v2–v4 quebraram a preservação; o v5 com âncora KL é
  barato, mas resolve cópia de nome, que já está em 95–97%).
- Mais passos na mesma mistura: a validação da fase 5 piora depois do passo ~330.
- Escolher versão por réguas de 9 ou 43 casos.

## Limites desta auditoria

- As conclusões da seção 1 vêm dos relatórios, não de reexecução dos treinos.
- A sonda usa o 46M que já foi ajustado nessas situações; ela mede o que esse modelo separa, não o
  que a base da 6a separaria.
- A linha de base de n-gramas usa só a mensagem; o blind v3 tem histórico em 2.620 dos 2.980 casos.
- Nada aqui foi treinado; as previsões da seção 4 são hipóteses a testar, não resultados.
