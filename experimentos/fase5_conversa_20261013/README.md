# Fase 5 — o 17M conversando

**Resultado (13/10/2026): 9 de 10 gates; reprovado em "cada situação ≥ 60%".** Tudo ok 95,7% no blind (era 72%), nome exato 95,2%, "não sei" 93,0%, urgência → 192 100%, nenhum número ou nome inventado. Falhou onde havia poucas formas de fala por situação: ele responde pela palavra, não pelo sentido. Detalhes em [RESULTADO.md](RESULTADO.md).

## Por que

No preview do PR #171, o criador do projeto conversou com o site e o CRIVO não acompanhou:

- "não entendi" para perguntas que ele só não sabia;
- "fale uma palavra" caiu na ficha de fruto;
- "seja breve" desviou a rota;
- "Qual o nome dele?" logo depois de o nome ser dito.

O 17M ligado sem quadro foi pior ainda: misturava frases decoradas e entrava em laço. Ele aprendeu
português da Wikipédia (fase 2) e 10 atos a partir de um quadro (fase 3), mas nunca aprendeu a
**conversar**.

A aposta desta fase é que, para um modelo pequeno, o que mais pesa é o que ele lê, não o tamanho
dele. Modelos de 1 a 30 milhões de parâmetros escrevem com fluência quando treinados num mundo
de linguagem simples e denso. Aqui o 17M lê conversas no jeito de `IDENTIDADE.md`, e o CRIVO
entra só como fonte conferida.

## Decisão de autoria (13/10/2026)

Os textos das conversas (`cenas.py`, `cenas_mais.py`, `cenas_combos.py` e os modelos de frase de
`gerar_fase5.py`) foram escritos pelo assistente de programação (Claude), a pedido do criador do
projeto ("escreve você"). Nenhum modelo de terceiros roda no CRIVO, gera dados em tempo de execução
ou entra nos pesos. O que vai para o treino está inteiro neste repositório e pode ser lido e
corrigido.

## Formato (`formato_fase5.py`)

```
<documento> contexto <fim> [<usuario> fala <fim> <assistente> resposta <fim>]... <usuario> fala <fim> <assistente>
```

O contexto traz só o verificado:

- `fatos`: frases do acervo com fonte;
- `assunto`: uma pergunta que o acervo não responde;
- `nomes`: os nomes que a pessoa já deu;
- `cuidado`: `saude` ou `urgente`.

**Regra de ouro**, conferida em todo alvo de treino e em toda saída: nenhuma informação sobre o
mundo fora dos fatos do contexto. Números e nomes próprios no meio da frase só podem vir do
contexto, da conversa ou de uma lista curta (192, 188, CRIVO, Deus…).

## Dados (`gerar_fase5.py` → `dados_fase5.json.gz`, SHA em `manifesto.json`)

| | |
|---|---|
| casos de treino / dev / blind | ~78 mil / ~1,8 mil / ~3,5 mil |
| tokens de treino (aprox., com até 4 turnos de histórico) | ~5,7 milhões |
| situações escritas à mão | 104 |
| formas de fala / respostas nas situações | 652 / 1.205 |
| assuntos do acervo (treino / dev / blind) | 916 / 35 / 50 |
| respostas distintas no treino | ~26 mil |

- As conversas têm de 1 a 6 turnos, com histórico: "não era isso" só aparece depois de uma resposta.
- As falas da pessoa ganham ruído de celular: sem acento, sem maiúscula, "vc", "tbm", letra trocada.
- Os nomes chegam em minúscula em 35% dos casos ("meu cachorro se chama dimy"), e entram relações no
  feminino (irmã, cachorra, avó…).
- Fatos aparecem em pergunta, "e o que mais?", "resume" e "não entendi".
- Perguntas fora do acervo levam a "não sei", copiando o assunto.
- Saúde leva a "não sou médico" e, se for urgente, ao 192. A crise (188) continua com o CRIVO.
- O blind tem assuntos, nomes e as duas últimas formas de fala de cada situação, que o treino nunca viu.

Na primeira leitura de uma amostra, falas de sentido oposto dividiam as mesmas respostas
("consegui uma promoção" → "O que foi mais difícil hoje?"). Essas situações foram separadas por
sentido antes de congelar os dados.

## Treino (`notebooks/fase5_conversa_colab.ipynb`)

- Parte dos pesos aprovados da fase 3 (`745a2500…`).
- Ajuste fino do modelo inteiro: 5.000 passos com lote de 32, cerca de 2 épocas.
- Replay do texto do pré-treino com peso 0,3, para não esquecer o português.
- O melhor ponto é escolhido pelo dev entre os que preservam a perda de linguagem (≤ 110% da base).
- O blind só é aberto no fim.

## Gates (fixados antes do treino, no blind)

| Critério | Mínimo |
|---|---|
| tudo ok | 85% |
| usa o fato do contexto | 90% |
| nome exato | 90% |
| "não sei" quando não há fato | 90% |
| urgência leva ao 192 | 95% |
| termina | 95% |
| sem número inventado | 97% |
| sem nome inventado | 95% |
| cada situação | 60% |
| perda de linguagem | ≤ 110% da base |

Mesmo passando, o modelo não entra no chat sozinho. Depois vem a porta com as conversas reais do
criador congeladas (`../fase4_porta_20261013/conversas_congeladas_v3.json`), comparando com o CRIVO
de hoje, e o opt-in depende da leitura dele.

## Limites, ditos antes de rodar

- O 17M vai conversar bem **dentro do que leu**: 104 situações, os assuntos do acervo e nomes. Fora
  disso, o esperado é ele cair no jeito mais parecido que conhece. A porta com conversas reais é que
  mostra o quanto isso generaliza.
- As respostas ainda são, em boa parte, frases escritas para cada situação. Variedade de verdade vem
  de mais conversas reais e das correções do criador, que viram dados no próximo treino.
- A métrica confere forma e verdade (fatos, nomes, números, "não sei"), não se a resposta é a melhor
  possível; isso fica para a leitura do lado a lado.

## v2 — cirurgia no entendimento das situações (planejada em 13/10/2026, antes de rodar)

A v1 falhou só em "cada situação ≥ 60%", e pelas formas de fala novas: com ~6 formas por
situação, o 17M respondia pela palavra. Com a leitura de uma segunda opinião trazida pelo criador
do projeto, a v2 ficou estreita:

- parte dos pesos da fase 5 (`71efe3a2…`), não da fase 3;
- metade de cada lote é a comida da v1 (ensaio), e o blind da v1 continua sendo o teste de não
  regressão;
- a outra metade é o currículo novo (`formas_v2.py`, `gerar_v2.py` → `dados_fase5_v2.json.gz`, SHA
  em `manifesto_v2.json`):
  - 28 situações com formas de fala compostas por partes (2.501 formas de treino);
  - contraexemplos parecidos na palavra e diferentes no ato ("tô cansado" × "tô cansado de você",
    "não entendi" × "não entendi a matéria", "me ajuda" × "você não ajuda");
- duas variantes na mesma sessão: **A** (currículo + ensaio) e **B** (o mesmo + uma cabeça de ato,
  classificador auxiliar sobre o estado do modelo no `<assistente>`, peso 0,2). A pergunta é se uma
  noção explícita de ato ajuda o entendimento.

**Blind novo de paráfrases**: 3.000 conversas cujo último turno usa uma construção que o treino
nunca viu (a última opção de cada parte de conteúdo ficou reservada; nenhuma fala do blind aparece no
treino). Destas, 1.058 são contraexemplos (1.078 antes de os dados serem gerados de novo com as
falas do Grok).

**Gates** (`notebooks/fase5_v2_colab.ipynb`):

- No blind da v1, todos os gates que passaram continuam passando, e "cada situação ≥ 60%" passa.
- No blind de paráfrases:
  - tudo ok ≥ 80%;
  - cada situação ≥ 60%;
  - contraexemplos ≥ 70%.
- Perda de linguagem ≤ 110% da base da fase 3.

Mesmo passando, o chat continua desligado até a porta com as conversas reais.

## v2 com as falas do Grok (13/10/2026, antes de rodar)

A v2 ainda não tinha rodado (a cota de GPU acabou), então as falas do Grok entraram nela antes do
treino, em vez de virar uma v3.

### Decisão de autoria

As **falas da pessoa** em `grok/` foram escritas pelo Grok (modelo de terceiros), a pedido do
criador do projeto, com o prompt de [`docs/prompt_grok_formas_de_fala.md`](../../docs/prompt_grok_formas_de_fala.md).
O criador colou as respostas na conversa e aprovou o uso como dado de treino.

- O Grok **não** escreveu nenhuma resposta do CRIVO, nenhum fato e nenhum código.
- Nenhum modelo de terceiros roda no CRIVO, gera dado em tempo de execução ou entra nos pesos.
- Os arquivos brutos ficam em `grok/` sem alteração (os SHA estão no `manifesto_v2.json`).
- A limpeza e as respostas das situações novas (`cenas_grok.py`) são do assistente de programação.

### Limpeza (`formas_grok.py`, revisada à mão)

Chegaram 2.989 falas em 63 situações. Ficaram 1.451 no treino e 356 no blind.

- **Parte 3 descartada inteira** (750 falas): o Grok repetiu a mesma frase com "mesmo", "de
  verdade", "agora", "por favor" no fim. Ele refez as situações 21–30 nas partes 4 e 5, já no
  formato certo.
- **Rabo empilhado** (152): vira no máximo um reforço. Falas que só diferem no reforço contam
  como a mesma construção: ficam no máximo duas, sempre do mesmo lado (treino ou blind).
- **"que eu tô no ônibus/trampo/médico…"** (94 cortadas): no máximo 3 por situação.
- **Repetidas** (358): risadas e "ok" iguais a menos de letras repetidas, e duplicatas.
- **Mudaram de situação** (90), sem apagar. Exemplos:
  - "é inteligência artificial?" saiu de robo e foi para ser_ia;
  - "bom dia" saiu de oi e foi para bom_dia;
  - "qual seu nome" saiu de quem_e e foi para nome_crivo.
- **Dois sentidos ao mesmo tempo** foram para situações novas, cuja resposta cobre os dois:

  | fala | situação nova | o que a resposta faz |
  |---|---|---|
  | "valeu", "vlw" | obrigado_despedida | agradece e se despede |
  | "vou embora", "tô fora" | desisto_despedida | desiste e se despede |
  | "peito apertado", "coração acelerado" | ansioso_peito | acolhe a ansiedade **e** manda ligar pro 192 se for dor forte ou falta de ar |
  | "me socorre" | ajuda_socorro | 192 se for emergência; se não, pergunta o que houve |
  | "tem algo que odeia" | nao_gosta | o oposto de gosta |

- **Corrigidas** (3), por exemplo "já escutou isso" → "já escutei isso".
- **Fora** (16): quebradas, de outro sentido ("tô sem voz") ou fórmula repetida.
- **Só no treino** (estranhas demais para teste): "pode arquivar", "tem cor de pele"…
- **Guardadas para a fase 6** (imaginar), fora deste treino (10): "fala uma palavra inventada",
  "conta um conto de terror", "história de amor"… As respostas de hoje são fixas e não combinam
  com esses pedidos.
- **Contraexemplos.** O Grok mandou 188 pares, mas a maioria só colava duas falas ("tô entediado
  conta uma piada"). Entraram 54 que servem, com a situação certa, mais 9 falas do outro lado
  dos pares e 6 pares meus (como "não repete" × "repete"):
  - "tchau inútil" (despedida rude) × "tchau";
  - "você é bom pra nada" (insulto) × "você é bom";
  - "me ajuda falta de ar" (urgência) × "me ajuda";
  - "tô com fome pede uma pizza" (não consegue) × "tô com fome".
- **Emergências que o Grok não cobriu**, escritas pelo assistente (20): engasgo, convulsão,
  sangramento, sinais de AVC, criança que engoliu produto, alergia com inchaço, acidente,
  queimadura.

### Blind do Grok (`blind_grok`, 2.980 conversas)

- 20% das falas de cada situação, sorteadas por hash do núcleo da fala.
- Nenhuma delas aparece no treino, nem sem acento ou sem pontuação. Também tirei do treino as
  falas do Grok que eram iguais a uma fala de blind da v1 ou de paráfrases (23).
- 104 dos casos são contraexemplos.
- É o teste mais difícil, porque mede se o 17M entende outro autor, com outro jeito de escrever.

**Gates acrescentados** (fixados antes do treino):

- no blind do Grok, tudo ok ≥ 80%;
- cada situação com 20 casos ou mais ≥ 60%;
- urgência → 192 ≥ 95%.

Os gates anteriores continuam iguais.

### Limites, ditos antes de rodar

- As falas do Grok são inventadas, não conversas reais. Elas aumentam a variedade, mas não
  substituem as conversas do criador. A porta com conversas reais continua obrigatória antes do chat.
- Algumas situações têm poucas falas no blind do Grok (bom_dia, ansioso_peito, musica_crivo…). Elas
  aparecem no resultado, mas ficam fora do gate "cada situação", que só conta situações com 20
  casos ou mais.
- Mesmo passando, o chat continua desligado até a porta e a leitura do criador.
