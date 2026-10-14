# Fase 6b — conversar com falas de pessoas

Decisão do criador (14/10/2026): "eu não quero que tu faça as falas dele, ele quem deve falar do
jeito que ele quiser". Por isso nenhum alvo de treino desta fase foi escrito pelo assistente nem
por modelo de linguagem.

## Dados (`gerar_fase6b.py`)

| origem | o que é | licença |
|---|---|---|
| OASST2 pt | conversas inteiras de voluntários (sem sintéticas, apagadas ou reprovadas); só as que terminam numa resposta, porque os começos já entram nelas | Apache-2.0 |
| legendas pt-BR | 2 a 8 falas seguidas de filmes e séries (OpenSubtitles v2018, OPUS), sem linhas de crédito e música | uso não comercial, crédito a opensubtitles.org |
| acervo do CRIVO | "me fala sobre X" e, como resposta, os fatos do acervo que o CRIVO entrega no contexto | próprio |

- **Contexto** (`formato_fase6.py`): `quem` (o resumo do IDENTIDADE.md: ele se apresenta do jeito
  dele) e `lembrancas` (em conversas de 6 turnos ou mais, as primeiras falas da pessoa saem do
  histórico e viram "a pessoa disse: ..."), além de `fatos`, `assunto`, `nomes` e `cuidado`, como na
  fase 5.
- **Perda:** em todas as falas do assistente da janela de 1024 tokens.
- **Separação:** teste 3% e validação 3%, por árvore do OASST2, item do acervo ou trecho das legendas.
- **Leitura:** um quarto de cada lote continua sendo leitura (FineWeb-2 da 6a, corpus próprio e o
  IDENTIDADE.md inteiro), para ele não esquecer o que leu.

## Treino (`notebooks/fase6b_conversa_humana_a100_colab.ipynb`)

Base: a 6a terminada (SHA no `resumo_fase6a.json`). Quatro voltas no OASST2; a cada volta, uma
amostra nova do acervo (mesmo número de tokens) e legendas novas (o dobro). O número de passos sai do
tamanho real dos dados. LR 1e-4 → 1e-5. Fica a versão com a menor perda no OASST2 de validação.

**Medidas:** perda nas conversas separadas antes e depois, perda de leitura (para ver se esqueceu) e
as respostas dele, sem retoque, às 15 frases reais do criador, a perguntas de identidade, a
perguntas livres, a fatos do acervo e a testes de lembrança.

## Limites, ditos antes de rodar

- **OASST2 em português é pequeno** (alguns milhares de mensagens): quatro voltas podem decorar
  respostas. A escolha pela validação limita isso, mas não elimina.
- **Nas legendas, quem é "pessoa" e quem é "CRIVO" é uma convenção** (falas alternadas). Duas falas
  seguidas podem ser do mesmo personagem. Elas ensinam o ritmo da conversa em português, não um
  jeito de ser.
- **Não há exemplo de "não sei" escrito por pessoas** nos dados. Nas perguntas sem fatos, ele vai
  responder com o que leu, e pode errar. A conferência do chat (números e nomes fora do contexto)
  continua marcando isso.
- Nada desta fase entra no chat sem a 6c, que mede de novo na CPU e mostra o resultado ao criador.

## v2 (14/10/2026, depois da primeira rodada)

A primeira rodada falhou (RESULTADO.md). O criador aprovou que entrem respostas tiradas do
IDENTIDADE.md ("faça essa desgraça direito [...] inventa essa merda"). Mudanças
(`extras_fase6b.py` e o mesmo notebook):

- **identidade:** ~100 formas de perguntar quem ele é, com respostas do IDENTIDADE.md, literais
  (os exemplos que o arquivo dá) ou passadas para a primeira pessoa;
- **lembrança:** 20 mil perguntas sobre o que a pessoa contou. A resposta curta devolve o que está
  nas lembranças ("Seu nome é Gabi."), e 20% das perguntas são sobre algo que ela não contou
  ("Você ainda não me contou isso."). Essas frases curtas foram escritas aqui;
- **OASST2:** saem as conversas em que o assistente diz ser outro sistema;
- **mais conversa:** legendas 2 vezes, OASST2 6, acervo 2, identidade 4, até 2.500 passos;
- **escolha da versão** pela média da perda nas legendas e no OASST2 separados;
- **freio de repetição** na geração (penalidade 1,3 nos tokens já ditos e nenhum trecho de 3
  tokens repetido);
- **a prova usa outras formas:** perguntas de identidade e lembranças com valores e tipos que não
  estão no treino; "Voce é o crivo certo?" e "tô triste hoje" (frases reais do criador) ficam fora
  do treino.

Saída: `CRIVO/transformer-crivo-46m-conversa-v2/`.

## v3 (14/10/2026)

O mesmo da v2 mais as **conversas da fase 5 v4** (~247 mil, geradas no Colab por `gerar_v4.py` e
conferidas por SHA), com `quem` no contexto. A prova acrescenta o **sentido da v4 F** (`sentido.py`,
blinds v3, v1, paráfrases, Grok e v4, e as 15 frases reais), com o mesmo contexto que o chat monta
e o freio de repetição. A escolha da versão usa a média das perdas de validação da fase 5, das
legendas e do OASST2. Notebook: `notebooks/fase6b_v3_conversa_completa_a100_colab.ipynb`. Saída:
`CRIVO/transformer-crivo-46m-conversa-v3/`.

Limite: a régua de sentido reconhece as respostas das listas da fase 5. Uma resposta boa e
diferente conta como "livre", não como "certo".
