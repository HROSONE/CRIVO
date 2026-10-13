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
treino). Destas, 1.078 são contraexemplos.

**Gates** (`notebooks/fase5_v2_colab.ipynb`):

- No blind da v1, todos os gates que passaram continuam passando, e "cada situação ≥ 60%" passa.
- No blind de paráfrases:
  - tudo ok ≥ 80%;
  - cada situação ≥ 60%;
  - contraexemplos ≥ 70%.
- Perda de linguagem ≤ 110% da base da fase 3.

Mesmo passando, o chat continua desligado até a porta com as conversas reais.
