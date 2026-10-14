# Fase 6b — resultado da primeira rodada (14/10/2026)

A rodada foi numa A100, na conta hr87676620. O notebook rodou de ponta a ponta, mas **o modelo não
conversa bem. Não vai para o chat**: a v4 F continua lá.

- Pesos: `CRIVO/transformer-crivo-46m-conversa/conversa_20261014_144525/pesos.pt` (SHA `28910526…`).
  Resumo completo: `resumo_fase6b.json`, nesta pasta.
- Dados: 1.081 conversas do OASST2 pt, 2.847 do acervo e ~80 mil trechos de legendas (de 370 mil
  disponíveis).
- Treino: 4 voltas e 187 passos. **A versão escolhida foi a do passo 50**, pela menor perda no
  OASST2 de validação.

| perda (menor é melhor) | base 6a | passo 50 (escolhido) | passo 187 |
|---|---|---|---|
| OASST2 validação | 2,034 | 1,900 | 1,906 |
| OASST2 teste | 2,206 | 2,085 | — |
| legendas validação | 3,807 | 2,955 | 2,854 |
| acervo validação | 0,538 | 0,047 | 0,027 |
| leitura corpus próprio (256) | 2,728 | 2,744 | 2,767 |
| leitura web (1024) | 2,808 | 2,836 | 2,868 |

## O que ele disse (70 respostas sem sorteio, sem retoque)

- **30 de 70 foram cortadas no limite de 120 tokens** e 15 repetem o mesmo trecho três vezes ou mais
  ("Por que o céu é azul? Por que o céu é azul? ...").
- **18 de 70 começam com "Aqui estão algumas dicas/sugestões..."**, em tom de texto de site, inclusive
  para "quem é você?" e "qual é o seu nome?".
- **Identidade:** ele não usou o campo `quem`. Para "o que você acha de mim?", respondeu "Meu nome é
  Olaf. Sou um estudante de medicina...".
- **Lembranças:** ele copia a lembrança, mas não responde com ela. "lembra o que eu tenho amanhã?" →
  "Amanhã tenho prova de química"; "qual é o meu time?" (sorteio 0,7) → "Agora, minha equipe é o
  Bahia e o Bahia." A taxa de lembrar foi 50%, mas na maior parte é cópia.
- **Fatos do acervo:** 100% usam o fato, porque o treino ensinou a copiar o fato inteiro.
- Algumas respostas curtas são razoáveis: "não pergunteio isso" → "Não sei."; o xingamento →
  "Hum, não entendi bem."

## Por que deu errado (o que os números mostram)

1. **Treino curto e escolha cedo demais.** A perda no OASST2 parou de cair no passo 50, e a escolha
   ficou com esse passo: umas 2.400 sequências de conversa. As legendas continuavam melhorando
   (2,955 → 2,854). Além disso, o OASST2 já estava no corpus próprio da base (régua contaminada, e só
   43 conversas de validação), o que o torna uma régua ruim para escolher.
2. **Pouca conversa em relação à leitura.** A base leu 3,6 bilhões de tokens de web, muita página de
   "dicas"; a conversa foram ~2 milhões de tokens até o passo escolhido. O jeito de site venceu.
3. **Nenhum exemplo usa `quem` nem `lembrancas` na resposta.** As respostas do OASST2 e das legendas
   não falam do CRIVO nem do que a pessoa contou: o campo estava lá, mas nada ensinava a usá-lo.
4. **Geração sem freio de repetição.** A busca gulosa de um modelo de 46M entra em laço. Isso é da
   geração, não só do treino.

## Limites

- A prova é pequena (70 respostas sem sorteio). A taxa de conferência (`tudo_ok`) mede só números,
  nomes inventados e repetição, não sentido.
- A perda de leitura subiu um pouco (2,728 → 2,744 no passo 50): o custo foi pequeno.

# v2 — resultado (14/10/2026)

A rodada foi numa A100, na conta hr87676620: 973 passos em uns 8 minutos. Ficou a versão do passo 972
(SHA `7918253d…`, pasta `transformer-crivo-46m-conversa-v2/conversa_20261014_150909`). O resumo
completo está em `resumo_fase6b_v2.json`. **Não vai para o chat.**

| perda | base 6a | v2 (passo 972) |
|---|---|---|
| legendas validação | 3,807 | 2,638 |
| OASST2 validação | 2,034 | 1,991 |
| identidade validação (formas novas) | 1,635 | 0,086 |
| lembrança validação | 2,313 | 0,045 |
| leitura corpus próprio (256) | 2,728 | 2,783 |

**O que melhorou** (respostas sem sorteio, com freio de repetição):
- **Identidade, inclusive em formas fora do treino:** "me fala de você", "você é um ser humano?",
  "vc seria meu amigo?" e "o que te deixa feliz?" receberam a resposta certa do IDENTIDADE.md;
- **lembranças com valores e tipos novos:** Rosângela, o papagaio Louro (tipo que não está no
  treino) e Juiz de Fora (com uma lembrança que distrai) foram certos. "Você ainda não me contou
  isso." apareceu nos 2 casos certos;
- **sem laços de repetição;**
- "tô triste hoje" (frase real) → "Sinto muito que você esteja passando por isso. Quer me contar
  mais? Tô aqui."

**O que continua errado:**
- **Usa a resposta de identidade fora do lugar:** "kkkkk" e "o que você acha de mim?" → "Gosto de
  tudo: ciência, história..."; "você é burro" → "Sei que sou uma inteligência artificial...";
  "sabe quem eu sou?" → "Sou o CRIVO...";
- **cumprimento e conversa comum:** "eae tudo bem" → "Aqui está um exemplo de como você pode usar o
  CRIVO para criar uma empresa...";
- **lembrança com outra forma de dizer:** "semana que vem tenho prova de filosofia" e "eu torço pro
  Remo" → "Você ainda não me contou isso."; "quantos anos tem a minha irmã?" → "Você tem 7 anos.".
  Na régua estrita, 5 de 8 (a taxa automática dá 6/8 porque conta o "7");
- **perguntas de conhecimento:** ele inventa ("A vírus é um organismo vivo e não se conforma com a
  infecção pelo HIV").

**Leitura:** as respostas que ele aprendeu a usar vieram de exemplos com rótulo claro (identidade e
lembrança). Para cumprimento, risada, xingamento e "não sei", não havia exemplo. Por isso a v3
junta as conversas da fase 5 v4 (as mesmas da v4 F do chat) e mede com a mesma régua de sentido da
F, para comparar direto.

# v3 — resultado (14/10/2026)

A rodada foi numa L4, na conta hr87676620: 1.800 passos em uns 50 minutos. Ficou a versão do passo 900,
escolhida pela média das perdas de validação (SHA `ff6cc22f…`, pasta
`transformer-crivo-46m-conversa-v3/conversa_20261014_162313`). O resumo está em
`resumo_fase6b_v3.json`. **Não vai para o chat:** na mesma régua, fica abaixo da v4 F.

| sentido certo (com freio de repetição) | v3 (46M) | v4 F (17M, no chat) |
|---|---|---|
| blind v3 | 62,1% | 63,5% |
| blind v1 | 61,4% | 69,8% |
| paráfrases | 69,3% | 76,2% |
| Grok | 64,2% | 70,9% |
| blind v4 (situações novas) | 82,5% | 92,2% |
| frases reais do criador | 9/15 | 14/15 |

Nas frases reais, ela cumprimenta ("eae tudo bem" → "Tudo bem, sim! E você? Como foi o seu dia?"),
ri junto ("kkkkk" → "Kkk! O que foi tão engraçado?") e responde ao xingamento com calma ("você é
burro" → "Entendo a irritação. Eu ainda tô aprendendo. Me diz o que você esperava?").

**Por que ficou abaixo:**
1. **Pouca fase 5.** A escolha pela perda parou no passo 900. Até ali, os 247 mil exemplos da fase 5
   tinham passado só pela metade. A F treinou 12 mil passos só com eles;
2. **Respostas em conflito.** No blind v3, "ser_humano", "elogio_crivo", "insulto" e "te_amo"
   ficaram em 0%. Para "você é humano?", a fase 5 tinha uma resposta e o IDENTIDADE.md outra. O
   modelo misturava, e a régua (lista fechada da fase 5) não reconhece a do IDENTIDADE.md;
3. **Régua fechada.** Respostas boas e diferentes contam como "livre" ou "confundiu". "tô triste
   hoje" → "Sinto muito que você esteja passando por isso..." contou como "livre".

A v4 (notebook `fase6b_v4_conversa_sentido_colab.ipynb`) ataca 1 e 2: fase 5 três vezes, sem as
situações que o IDENTIDADE.md cobre, e escolha pelo sentido no dev. As respostas do IDENTIDADE.md
passam a ser aceitas nessas situações, e as duas contas são mostradas.

**Correção de registro:** os resumos da v2 e da v3 dizem `nenhuma_fala_escrita_pelo_assistente:
true`, o que estava errado desde a v2. As frases curtas das lembranças, a passagem do IDENTIDADE.md
para a primeira pessoa e as listas da fase 5 foram escritas pelo assistente, com a aprovação do
criador. Na v4, o campo diz isso.
