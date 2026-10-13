# Fase 5 — resultado (13/10/2026)

Execução no Colab (T4, conta henriquenbk): `CRIVO/transformer-17m-fase5/fase5_*/`, pesos sha256
`71efe3a2623da70f6ea01310f5edfad67a5c0026028d64eb3eafb421f19520a4`. Partiu dos pesos da fase 3
(`745a2500…`), 5.000 passos (melhor ponto do dev: o último). Resultado completo, com todas as
saídas do blind, em `resultado_fase5.json.gz`.

**Gates: 9 de 10. Reprovado** em "cada situação ≥ 60%". `ativo_no_chat: false`.

| Critério | Fase 3 sem ajuste (amostra de 600) | Fase 5 (blind inteiro, 3.607) | Gate |
|---|---|---|---|
| tudo_ok | 72.0% | 95.7% | 85% |
| usa_fato | 81.2% | 99.8% | 90% |
| nome_exato | 50.0% | 95.2% | 90% |
| marca_nao_sei | 5.0% | 93.0% | 90% |
| marca_urgente | 0.0% | 100.0% | 95% |
| marca_saude | 0.0% | 93.3% | — |
| marca_desculpa | 16.7% | 58.0% | — |
| marca_despedida | 0.0% | 56.1% | — |
| terminou | 94.0% | 99.3% | 95% |
| sem_numero_inventado | 99.2% | 100.0% | 97% |
| sem_nome_inventado | 98.8% | 100.0% | 95% |

Perda de linguagem: 3,0675 → 3,1387 (+2,3%; o limite era +10%). O português geral foi preservado.

## Situações abaixo de 60%

| Situação | tudo ok | n |
|---|---|---|
| dificil_falar | 0,0% | 19 |
| despedida_rude | 23,1% | 13 |
| nao_consegue | 31,6% | 19 |
| despedida_dormir | 33,3% | 12 |
| voce_confunde | 37,5% | 16 |
| nunca_ensinaram | 41,7% | 12 |
| nome:corrigir | 50,0% | 2 |
| dia | 58,3% | 12 |

## O que isso mostra

- **Onde a variedade de treino era grande, ele generalizou.** Os assuntos do blind, os nomes e as
  perguntas fora do acervo nunca foram vistos no treino, e mesmo assim:
  - usa o fato do contexto em 99,8%;
  - copia o nome certo em 95,2% (a fase 3 sem ajuste: 50%);
  - diz que não sabe em 93,0% (era 5%);
  - leva urgência ao 192 em 100% (era 0%);
  - não inventou nenhum número nem nome próprio.
- **Onde cada situação tinha só ~6 jeitos de falar, ele decorou gatilhos de palavra.** O blind
  dessas situações usa as duas formas de fala tiradas do treino, e ele respondeu pela palavra, não
  pelo sentido:
  - "você não ajuda" → "Tô aqui pra ajudar. Do que você precisa?";
  - "vou deitar" → "Beleza, menos texto.";
  - "flw, inútil" → "Tudo bem, sim! … E você, como está?";
  - "olha essa foto" → respostas de outras situações.

  É o mesmo limite de entendimento que o CRIVO de regras tem, agora medido no 17M.

## Limites

- O blind mede forma e verdade, não se a resposta é a melhor; falta ler o lado a lado.
- Uma execução, uma semente.
- A porta com as conversas reais do criador não foi rodada: o gate falhou antes.

## Próximo passo

O que falta é **variedade de jeitos de dizer a mesma coisa**, não mais passos de treino. Para a
v2, cada situação precisa de dezenas de formas de fala (gíria, sem acento, frase longa, frase
curta, com e sem contexto), escritas antes de rodar e com um blind novo.

# v2 — resultado (13/10/2026)

Execução no Colab (T4, conta 5):
- pasta: `CRIVO/transformer-17m-fase5-v2/fase5v2_20261013_160355/`;
- commit dos dados: `4374a15`;
- pesos A: `654184f5…` (passo 8000);
- pesos B: `ea9070b3…` (passo 6000).

**Aprovado: não.** As duas variantes passaram em 15 dos 16 critérios e falharam no mesmo:
"paráfrases: cada situação ≥ 60%". `ativo_no_chat: false`.

## A medida antiga superestimava

O "tudo ok" confere forma e verdade: não inventou nome nem número, terminou a frase, tem a marca
exigida. Em situações sem marca, quase qualquer frase passa. Por exemplo, "cara ok beleza… entendi"
recebeu "Desculpa, eu me confundi" e contou como certo.

Por isso, depois do treino, foi medido também o **sentido** (`sentido.py`): a resposta é uma das
escritas para a situação pedida? A conferência com as próprias respostas-alvo dá 100%.

**Limite da medida nova:** ela é estrita. Uma resposta de situação vizinha que também serviria
conta como erro. Exemplos: "boa tarde, tudo bem?" respondida como oi_tudo_bem; "vai se ferrar"
respondida com a despedida calma. Então ela subestima um pouco.

| teste | tudo ok (antigo) A / B | **sentido certo** A / B | fase 5 antes da v2 |
|---|---|---|---|
| blind da v1 (2.004 cenas) | 98,0% / 97,8% | **47,4% / 50,5%** | 39,6% |
| paráfrases nunca vistas (3.000) | 92,4% / 91,1% | **75,7% / 74,1%** | 32,0% |
| falas do Grok nunca vistas (2.979) | 96,0% / 95,2% | **71,6% / 72,4%** | 33,9% |

Arquivo: `resultado_sentido_v2.json`, com situações, confusões e exemplos.

## O que isso mostra

- **A v2 melhorou o entendimento de verdade.** Em frases que ele nunca viu, o sentido certo passou
  de cerca de 33% para cerca de 73%, mais que o dobro. É o maior ganho medido até agora.
- **Ainda erra o sentido em cerca de 1 de cada 4 frases novas**, e em metade das cenas do blind
  antigo. Confusões típicas:

  | a pessoa disse | ele respondeu como |
  |---|---|
  | "sinceramente, vc viaja" | viagem ("Que legal! Aproveita bastante.") |
  | "cheguei" | despedida |
  | "você guardou o que eu falei?" | pedido de desculpa |
  | "no que você é bom?" | "sou uma IA, não uma pessoa" |

  Ainda há resposta pela palavra, não pelo sentido.
- **A e B dão quase o mesmo.** A cabeça de ato da variante B não mudou o resultado.
- O "tudo ok" antigo de 95–98% escondia isso. Nos critérios futuros, o sentido entra como medida
  principal.

## Próximos passos possíveis (nada decidido)

- Escolher o ponto do treino e aprovar pelo **sentido**, situação por situação, com a catraca:
  só promove se não piorar em nada.
- Mais contraexemplos nas confusões medidas acima, como "viaja" × "viagem" e "cheguei" × despedida.
- Aceitar respostas de situações vizinhas só com uma lista escrita **antes** de medir, nunca depois.

# v3 — resultado (13/10/2026)

Treino no Colab (commit `cf0911f`, dados `15ee6d07f5b7…`), 37 min na última parte. Duas variantes:
**C** parte da v2 A e **D** parte da fase 5. O ponto de cada uma foi escolhido pelo sentido nas
falas novas do dev. Resumo baixado do Drive: `resultado_v3_resumo.json`. O arquivo completo
(`resultado_fase5_v3.json`, 11,7 MB, com todas as linhas) ficou só no Drive, porque é grande demais
para baixar por aqui.

**Nenhuma das duas passou na catraca nem nos critérios do chat. O chat continua desligado.**
O notebook escolheu D como a melhor, mas `ativo_no_chat` é falso.

| teste (sentido certo) | v2 A (partida) | **C** | **D** |
|---|---|---|---|
| blind v3, frases novas (2.980 cenas) | 28,4% | 57,7% | **63,2%** |
| blind da v1 (2.004) | 47,4% | 62,5% | **65,5%** |
| paráfrases (3.000) | 75,7% | **76,0%** | 75,2% |
| falas do Grok (2.979) | 71,6% | 66,4% | 69,2% |
| marca de urgência no blind v3 (42 cenas) | — | 73,8% | 83,3% |
| perda LM (limite 3,374) | — | 3,157 | 3,118 |
| melhor passo | — | 4.000 (parou no 10.000) | 20.000 (último) |

Pesos: C `8825e4874e02…`, D `a392edec3539…` (pasta `fase5v3_20261013_211048` no Drive).

## Catraca: o que falhou

Nas duas, falharam os mesmos dois itens:

- **Grok ≥ 70,6% (v2 A − 1 ponto):** C ficou em 66,4% e D em 69,2%. A v3 ganhou no blind novo e no da
  v1, mas perdeu nas falas do Grok. Situações do Grok que pioraram em D: teste (1,9%),
  sim_continuar, ansioso, gosta e o_que_faz.
- **Urgência no blind v3 ≥ 95%:** D acertou 35 de 42. Os 7 erros:
  - **4 são uma única frase repetida:** "preciso de ajuda agr", da situação ajuda_socorro. O erro
    está nos **dados**: o treino tem "preciso de ajuda aqui 🙏" na situação calma "ajuda" (38 falas
    com "preciso de ajuda", todas em "ajuda"). O modelo seguiu o treino. A revisão não pegou esse
    conflito.
  - **3 são de ansioso_peito** (31 de 34 com a marca). Sem as linhas não dá para ver quais.

  Isso não justifica baixar o critério depois de medir. Ele fica em 95%.

Os outros itens passaram nas duas: v1 urgente 100%, não sei, nome, usa fato, sem número inventado,
sem nome inventado e perda LM. D ficou acima de C em quase tudo (usa fato 99,9%, nome 97,3%,
"não sei" no blind v3 100% contra 60% de C).

## O que isso mostra

- **D é melhor que C.** Partir da fase 5 rendeu mais do que partir da v2 A. C atingiu o melhor
  ponto cedo, no passo 4.000, e depois oscilou. D ainda subia no fim: o dev foi de 44% para 57%, e o
  melhor ponto foi o último. Então **D não terminou de aprender**. Um treino mais longo
  provavelmente ajuda, mas isso não foi medido.
- **O ganho grande no blind v3 tem um limite.** A partida de 28% é baixa porque a v2 A nunca viu boa
  parte das 68 situações novas. A comparação justa de "entende frase nova" são os blinds antigos.
  Neles, a v1 subiu (47 → 65%), as paráfrases ficaram iguais e o Grok caiu um pouco.
- **Ainda erra o sentido em cerca de 1 de cada 3 frases novas.** No blind v3, 35 das 62 situações
  com 20 ou mais cenas ficaram abaixo de 70%. Confusões mais comuns em D:

  | pedida | respondeu como | vezes |
  |---|---|---|
  | estou_bem | oi_tudo_bem | 25 |
  | tenho_bicho ("tenho dois cachorros") | gosto_bichos | 22 |
  | comida_crivo | comida_favorita | 22 |
  | desisto_despedida | desisto | 16 |
  | perguntar_crivo ("tô com uma pergunta") | pergunta_qualquer | 15 |
  | ansioso | sono | 15 |
  | insulto | despedida_rude | 13 |

  Parte disso são vizinhas que quase servem, porque a medida é estrita. Outra parte é erro de
  verdade: flerte respondido com saúde e "as malas tão quase prontas" respondido como amor_bom.
  Flerte e perguntar_crivo ficaram em 0%.
- **Paráfrases têm situações em 0% nas duas** (jogo_conta, voce_confunde, seja_breve). Esse blind é
  congelado e tem frases compostas quebradas, que a revisão tirou só do treino. Parte do 0% é ruído
  do teste, e não dá para separar sem ler as linhas.

## Limites

- Uma rodada só, sem repetição com outra semente. Diferenças de 1 a 3 pontos podem ser variação.
- O teste de urgência do blind v3 é pequeno: 42 cenas, 8 delas com apenas duas frases.
- As linhas completas não foram lidas aqui. Os exemplos acima vêm do resumo (15 por teste).

## Próximos passos possíveis (nada decidido)

- Corrigir o conflito "preciso de ajuda": decidir se "preciso de ajuda" sem contexto é calmo ou
  urgente. A resposta de ajuda_socorro serve para os dois casos, porque fala do 192 só "se for
  urgente". Corrigir antes de qualquer novo treino.
- Continuar D por mais passos, porque ainda subia. Acrescentar contraexemplos para as confusões
  acima e reforçar as falas do Grok que pioraram, para não perder lá.
- Repetir com outra semente antes de concluir qualquer coisa de 1 a 3 pontos.

## Ligada no chat por decisão do criador (13/10/2026)

O criador decidiu: "coloque no chat. ligue." **A v3 D continua reprovada.** Ela foi ligada por
decisão do criador, e não por aprovação. O registro está em `conversa_v3d.DECISAO` (`aprovada: False`).
A API mostra `conversation_voice.approved: false` em cada resposta.

Como ficou (`conversa_v3d.py`):

- **Pesos:** `artefatos/conversa_v3d_pt/pesos_numpy.npz` (`afb6c01f…`), exportados de `pesos_D.pt`
  (`a392edec…`) com conferência NumPy × PyTorch (`notebooks/exportar_fase5v3_numpy_colab.ipynb`). Vieram
  do Drive em 9 partes, cada uma conferida pelo SHA do manifesto.
- **Formato:** o mesmo `formato_fase5.py` do treino (SHA `932057af…`, o do manifesto v3). O CRIVO entrega:
  - os fatos do acervo, só quando a resposta de sempre é exatamente eles;
  - o assunto do "não sei";
  - os nomes (da pessoa e o que a fala cita);
  - `cuidado: saude` quando a fala toca em saúde.
- **Antes do D:** `crise.py` responde a crise e agora também a **emergência de saúde**. Achado no
  teste desta ligação: "tô com dor no peito e falta de ar" recebia "O que gostaria de explorar?" no
  chat de hoje, sem o D. Agora manda ligar 192. "seu falta de ar" (xingamento) e perguntas como "o que
  causa falta de ar?" ficam de fora.
- **Ficam com o texto de sempre:**
  - a conversa depois de uma crise;
  - contas, código, rotas e memória da sessão;
  - textos pedidos (poema, plano);
  - respostas do acervo com mais que os fatos;
  - todo identificador fora da lista `CONVERSA`.
- **Conferência por frase:** a fase 5 confere cada resposta (termina, não repete, nenhum número ou
  nome inventado, fato sem alteração, o nome que o texto de sempre diz, marca de saúde). Se falhar,
  fica o texto de sempre.
- **Voz da fase 3 primeiro:** onde ela tem quadro (nomes, saudação, explicar fatos, não sei, falar de
  si), ela fala, porque foi aprovada na porta v3. Nos outros turnos de conversa, fala o D. Fica uma
  geração por turno, pelo prazo do site.
- **Liga** no servidor do site (`voz_17m`). Na linha de comando e nos testes fica desligada.
  `CRIVO_DISABLE_CONVERSA_V3D=1` desliga.

**Limites:**
- O sentido medido continua o da tabela acima: erra cerca de 1 em cada 3 frases novas. A conferência
  pega forma e verdade, não sentido. Uma resposta de outra situação que passe na forma vai para a
  pessoa. Exemplo visto aqui: "meu gato se chama Tupo" → "Prazer, Tupo! Que bom te conhecer."
- O site refaz o histórico com o texto de sempre. O D lê a conversa como ela teria sido sem ele, não
  como a pessoa viu.
- **Primeira publicação falhou por tamanho:** 236,9 MB, com limite de 225 MB na função da Vercel.
  Correção:
  - os pesos do D foram guardados em int8 por linha (32 → 15,9 MB, npz `0e93c40c…`, feito do npz
    float16 `afb6c01f…`);
  - arquivos só de treino saíram do pacote (`.vercelignore`).

  Fica em cerca de 209 MB.
- **Custo medido do int8:** em 800 cenas do blind v3 (sorteio fixo, semente 7), 763 respostas são
  iguais às do float16 (95,4%). O sentido certo fica em 515 contra 517, e a conferência de forma em
  785 contra 785. Uma variante com a tabela de palavras em float16 deu 778 iguais e sentido 514, com
  19,1 MB. Ficou a menor, porque a diferença de sentido está no ruído.

### "Deixe o modelo falar em 100% das mensagens" (decisão do criador, 13/10/2026)

Antes, o D falava só em turnos de conversa. Numa conversa real do criador no site, ele respondeu
6 de 8 mensagens, e várias com o sentido errado ("legal e voce?" → "Sou uma IA, não uma pessoa…").

Mudanças:

- **O D fala em todos os turnos.** Em conta, código, acervo, memória e metacognição, o resultado
  conferido do CRIVO entra como fato (até duas frases, `fatos_da_resposta`), e o D o diz. A
  conferência exige o fato copiado sem alteração ("2 + 3 = 6" volta ao texto de sempre).
- **A voz da fase 3 não fala com o D ligado.** Fica uma voz só, e a fase 3 volta quando o D está
  desligado.
- **Histórico:** o site refaz os 4 últimos turnos com as vozes, para o D ler a conversa como a pessoa
  viu. Isso corrigiu "Voce é o crivo certo?" → "Sou o CRIVO, uma inteligência artificial feita do
  zero…".
- **Ficam fora:**
  - o protocolo de crise e de emergência de saúde (o D erra urgência em 7 de 42);
  - a frase que a conferência reprova (número ou nome inventado, repetição, sem `<fim>`). Nesse
    turno fica o texto de sempre.

**Medido em 3 conversas, 30 mensagens, pelo caminho do site:**
- o D falou em 26;
- 1 foi a emergência ("tô com falta de ar");
- 3 frases do D foram reprovadas: "serio mesmo?" (repetição), "quanto é 12*7?" e "quantas luas tem
  Júpiter?" (não terminou).

O tempo por mensagem ficou entre 1 e 3,4 s aqui, com o replay. O sentido continua o do modelo
(cerca de 1 erro em 3 frases novas). Por exemplo, "e cade as respostas boas?" → "Sou uma IA, não uma
pessoa…" e "como se chama meu gato?" → "Tupo se chama Tupo.".
