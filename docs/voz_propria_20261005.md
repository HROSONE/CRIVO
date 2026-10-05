# Voz própria (05/10/2026)

## O problema

As respostas de conhecimento do CRIVO eram corretas e tinham fonte, mas soavam
como ficha lida: os fatos vinham colados com "Além disso,", sem retomar o
assunto e sem oferecer um próximo passo.

> Inflação é o aumento geral e contínuo dos preços, que reduz o poder de compra
> do dinheiro. Além disso, no Brasil, o índice oficial é o IPCA, calculado pelo
> IBGE.

Os geradores livres já tinham sido medidos e desligados: escreviam com
gramática, mas inventavam ou fugiam do assunto. Com o Transformer de 16M, o
contrato caiu de 42/72 para 33/72.

## A ideia

Separar o que é dito de como é dito.

- **O conteúdo continua com o CRIVO:** as fichas com fonte, as travas e as
  recusas.
- **A voz só escolhe a forma:**
  - como abrir: com artigo, com sujeito quando a definição começa direto pelo
    núcleo, ou como está;
  - como ligar cada frase: nada, "Por exemplo,", "Na prática,", pronome,
    "Antes disso,", "Depois," ou "Vale lembrar que";
  - como fechar: um limite importante que não foi mostrado, a oferta de
    continuar, ou nada.

Quem decide cada escolha é um pequeno modelo treinado do zero
(`artefatos/voz_pt`): um softmax linear por tipo de decisão sobre
características do texto com hash.

## Quem ensinou

Com autorização do responsável pelo projeto, o tutor (o assistente que
desenvolve o CRIVO) escreveu 110 respostas em `dados/voz_tutor.json`. Cada uma
usa só os fatos verificados do assunto. Nenhuma IA roda dentro do CRIVO.

O treino (`scripts/treinar_voz.py`) segue estes passos para cada resposta:

1. monta todas as combinações de escolhas da voz;
2. toma como gabarito a combinação mais próxima do tutor (chrF);
3. aprende a reproduzir essas escolhas a partir do texto.

## Contrapeso

A voz é parte da espécie `composicao_factual` no ecossistema e passa por três
travas:

- **Guarda de fidelidade:** qualquer palavra de conteúdo que não esteja nos
  fatos do assunto, na pergunta ou no vocabulário de conversa (`voz.DISCURSO`)
  descarta a frase, e o texto de sempre volta.
- **Alcance limitado:** ela só reescreve a composição pura de um assunto. Notas
  ("não tenho esse aspecto"), comparações, listas, recusas e pedidos de escrita
  com forma definida ("em duas frases", resumo, roteiro) ficam como estão.
- **Cuidado com perguntas de aspecto:** "Como se formou Júpiter?" não ganha
  sujeito inventado nem um limite que não responde ao aspecto pedido.

A API informa `voice: "voz_propria"` quando a voz falou.

## Medição

**Validação** (22 assuntos separados do treino, com as respostas do tutor):

| | Texto atual | Voz |
|---|---|---|
| chrF contra o tutor | 82,8 | 96,1 |
| Fidelidade | — | 22/22 |

**Teste congelado** (`avaliacoes/voz_v1/teste.json`): 36 perguntas com
respostas do tutor escritas antes de qualquer treino, sobre assuntos disjuntos.

| | Texto atual | Voz |
|---|---|---|
| chrF médio contra o tutor | 86,4 | 87,4 |
| Fidelidade | 36/36 | 36/36 |
| Marcas mecânicas ("Além disso,") | 34 | 0 |
| Casos mais próximos / mais distantes do tutor | — | 14 / 19 (3 iguais) |

A diferença entre validação e teste é grande. A causa principal é uma
inconsistência do tutor:

- nas respostas de treino, ele usou muito a oferta genérica "Se quiser, conto
  mais sobre X.";
- nas do teste, ofereceu pouco, e de forma específica ("posso contar sobre o
  Código de Hamurábi"), o que a voz ainda não sabe fazer.

Por isso o ganho no teste é pequeno e misto. O que é certo: a voz tirou todas as
marcas mecânicas sem perder nenhum fato.

Depois de ver o teste congelado, foram corrigidas só regras gerais de
gramática:

- pronome antes de verbo impessoal ("Ela existem");
- artigo com nome de pessoa ("o Albert Einstein");
- concordância de número ("os neutrino");
- gênero pelo próprio nome, não pela palavra da definição;
- sigla de uma letra ("A") tratada como nome próprio.

Nenhuma resposta do teste foi usada para treinar.

**Catracas:** contrato 45/72 com e sem a voz; troca de assunto 25/27 e 12/14;
bateria sem inventar (dev e retido); presença 35/35 e `fatos_novos` 0.

## Ofertas específicas e cumpridas (atualização)

Até o PR #96, a voz oferecia "Se quiser, conto mais sobre X.", mas um "sim" na
fala seguinte caía na confirmação social ("Certo! Quer saber mais…?"): a
oferta não era cumprida. Agora toda oferta é uma promessa com ação guardada, e
um "sim", "quero" ou "pode ser" na fala seguinte a executa:

| Oferta | De onde vem | O que o "sim" faz |
|---|---|---|
| "Se quiser, conto mais sobre a inflação." | Fatos ainda não mostrados | Continua com eles |
| "Se quiser, conto como o neurônio se liga à sinapse." | Ligação cadastrada | Responde à relação |
| "Se quiser, explico como Júpiter se formou." | Aspecto marcado nos fatos | Responde ao aspecto |
| "Se quiser, conto também sobre o Código de Hamurábi." | Nome próprio, com duas palavras ou mais, no início de um fato não mostrado | Mostra esse fato |

Os textos de todas as ofertas vêm do acervo e passam pela guarda de
fidelidade. A oferta vale só para a fala seguinte, e a resposta à relação não
repete a mesma oferta. Como tutor, revisei 5 respostas de treino: quando havia
oferta específica, ela substituiu a genérica.

Teste congelado depois da mudança: chrF 87,6 (antes 87,4; sem voz, 86,4),
fidelidade 36/36, marcas mecânicas 0. Caso a caso: 13 casos mais próximos do
tutor, 19 mais distantes e 4 iguais. A maior parte das respostas do teste
ainda pede ofertas que o acervo não marca, como "posso contar sobre a imprensa
de Gutenberg", cujo fato começa com palavra minúscula.

## Limites

- A voz muda a forma, não o conteúdo: não explica com outras palavras nem
  resume um fato.
- Ofertas específicas só aparecem quando o acervo tem nome próprio, ligação ou
  aspecto marcado.
- O gênero e o número vêm de regras e de pistas nos fatos, e podem errar em
  nomes raros.
- O ciclo de retorno (sinais de "sim", "não" e "não era isso") ainda não
  alimenta a voz. O próximo passo é usar esses sinais, com consentimento, como
  novos exemplos.

## Reproduzir

```bash
python scripts/treinar_voz.py                 # ~1 min
python scripts/avaliar_voz.py --sem-voz       # texto atual
python scripts/avaliar_voz.py                 # com a voz
python -m unittest testes_voz
```
