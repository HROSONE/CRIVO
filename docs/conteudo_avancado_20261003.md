# Conteúdo avançado: física, biologia, sociologia e filosofia (2026-10-03)

## O que entrou

Foram acrescentados 206 conceitos e 537 fatos, em sínteses próprias em português de nível universitário. Cada
área tem um arquivo próprio, carregado pelo currículo do mundo (`curriculo_mundo.ler_curriculo`):

| área | arquivo | conceitos | fatos | exemplos |
|---|---|---|---|---|
| física | `conhecimento_fisica.json` | 59 | 172 | leis de Newton, entropia, relatividade restrita e geral, princípio da incerteza, equações de Maxwell, modelo padrão, bóson de Higgs |
| biologia | `conhecimento_biologia.json` | 50 | 127 | seleção natural, deriva genética, epigenética, meiose, ciclo de Krebs, teoria endossimbiótica, CRISPR, imunidade adaptativa |
| sociologia | `conhecimento_sociologia.json` | 47 | 113 | fato social, anomia, ação social, habitus, capital cultural, hegemonia, poder disciplinar, modernidade líquida, interseccionalidade |
| filosofia | `conhecimento_filosofia.json` | 50 | 125 | problema de Gettier, problema da indução, falseabilidade, imperativo categórico, utilitarismo, quarto chinês, existencialismo, véu da ignorância |

Cada conceito começa por uma definição e traz detalhes: autores, mecanismos, exemplos e limites. As perguntas de
treino seguem o padrão do currículo ("fale sobre X", "me explique X"…). O CRIVO responde também "O que é X?",
"Me explica X", "O que diz X?" e "Quais são as leis de X?".

## Fontes e licença

As referências são os livros abertos da OpenStax (Rice University):

| livro | licença registrada |
|---|---|
| Biology 2e (Clark, Douglas, Choi) | CC BY 4.0 |
| Introduction to Sociology 3e (Conerly, Holmes, Tamang) | CC BY 4.0 |
| Introduction to Philosophy (Nathan Smith e colaboradores) | CC BY 4.0 |
| University Physics vol. 1 (Ling, Sanny, Moebs) | CC BY 4.0 |
| University Physics vol. 2 e vol. 3 | **somente referência** (`reproducao_autorizada: false`) |

Os volumes 2 e 3 de física ficam só como referência porque as fontes consultadas divergiam sobre a licença
deles.

**Limite de verificação:** a rede deste ambiente bloqueia openstax.org e os espelhos da LibreTexts. Por isso,
cada livro, autor e licença foi confirmado por busca em catálogos (Open Textbook Library, eCampusOntario e outros),
mas o texto integral não pôde ser lido. Os fatos são conteúdo consolidado de manuais universitários, escrito com
palavras próprias e sem trechos, figuras ou exercícios dos livros. A atribuição a cada livro indica onde o tema é
tratado, não uma conferência linha a linha. O campo `escopo_uso` de cada fonte registra isso.

## Mudanças de código

- `curriculo_mundo.py`: carrega os quatro arquivos e aceita as naturezas `filosofico` e `social`. Filosofia e
  sociologia não são ciência natural; o teste de conhecimento só as aceita nessas áreas.
- `composicao_textual.py`: ao juntar fatos com "Além disso,", mantém a maiúscula de nomes próprios ("Além disso,
  Durkheim usou…"). Conta como nome próprio a palavra que o currículo escreve com maiúscula no meio da frase e
  nunca em minúscula, ou que vem antes de outra maiúscula ("Edmund Gettier").
- `crivo.py`: "O que diz o princípio da incerteza?" é lido como "O que é…", e "Quais são as leis de Newton?"
  como "O que são as leis…".
- `rede_crivo.json`: retreinada com a configuração de sempre (60 épocas, 48 neurônios ocultos, 512 dimensões,
  modo português, semente 42), agora com 447 intenções.
- Site: o menu lateral ganhou Física, Biologia, Sociologia e Filosofia, com perguntas conferidas por `testes_web`.

## Colisões evitadas

- "trabalho" da física passou a se chamar "trabalho mecânico". Antes, "Quero conversar sobre trabalho" ia para a
  física em vez da conversa sobre o emprego.
- "gene" e "cadeia alimentar" já existiam. A ficha nova de gene foi retirada e "cadeia alimentar" não é sinônimo
  da teia alimentar, para não criar ambiguidade.

- Nomes com " e " no meio ("solidariedade mecânica e orgânica", "status e papel social", "colisão elástica e
  inelástica" e outros) confundiam o pedido "Escreva um texto sobre X e Y". Viraram "solidariedade social",
  "papel social", "colisão mecânica", "genótipo", "dominância genética" e "ética protestante", e os nomes antigos
  ficaram como sinônimos quando não tinham " e ".
- `planejamento_conversa.py`: só o ordinal sozinho ("a segunda") retoma uma opção anterior. "Segunda lei da
  termodinâmica" é um conceito, não "a segunda" opção.

## Expectativas atualizadas

- `avaliacoes/bateria_v1/dev.json`: "O que é uma onda gravitacional?" era uma recusa esperada, porque o assunto
  não existia. Agora há ficha, e o caso exige o conteúdo certo ("ondulações do espaço-tempo"). O dev da bateria
  fica com 101 acertos de fato (eram 100) e nenhuma invenção.
- `testes_astronomia_avancada.py`: a base passa de 241 para 447 entradas, com a rede retreinada.

## Medição

`avaliacoes/conteudo_avancado_v1/casos.json` tem 42 perguntas em formas variadas. Cada resposta precisa conter uma
marca do conteúdo certo: 42/42, com e sem NumPy. `testes_conteudo_avancado.py` verifica:
- as perguntas;
- o tamanho mínimo de cada área;
- as licenças das fontes;
- a maiúscula de nomes próprios.

## Limites

- As respostas são as fichas: definição e um ou dois detalhes. O CRIVO não raciocina a partir delas nem compara
  conceitos que não tenham comparação cadastrada ("diferença entre mitose e meiose" ainda dá "não sei").
- Perguntas sobre aplicações ou opiniões ("o utilitarismo está certo?") seguem fora do alcance.
