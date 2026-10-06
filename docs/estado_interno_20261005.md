# Estado interno do turno e leitura da ficha (05/10/2026)

## O problema

O diagnóstico do CRIVO apontou que ele tem muitos órgãos e nenhum sistema
nervoso. A compreensão, a memória, o conhecimento e a geração vivem em peças
separadas, e cada peça decide sozinha.

Os conjuntos de desenvolvimento mostraram isso de forma concreta. Em 25 falhas
da bateria e da troca de assunto, cerca de 12 eram recusas como "Reconheci o
assunto Titã, mas não tenho evidência cadastrada", com a ficha de Titã dizendo
que há "nuvens, chuva, rios e lagos". O conhecimento estava lá, mas a busca
factual exige as palavras exatas no mesmo fato ("chove" ≠ "chuva"), e nenhuma
outra parte via a recusa nem o que já tinha sido entendido.

Nas 226 perguntas que o tutor escreveu para 62 fichas fora da astronomia, o
CRIVO de antes respondia certo a 39 das 161 perguntas com resposta na ficha e
recusava 114.

## O que mudou

### 1. Estado interno (`estado_interno.py`)

Cada fala monta um estado único que as espécies leem e escrevem:

| Parte | Conteúdo |
|---|---|
| compreensão | tipo de pergunta (quem, quando, quanto, onde, por que, como, qual, sim/não), entidades da fala ou do contexto, pistas de conteúdo, negação |
| memória | assunto da conversa, turno anterior, oferta pendente |
| conhecimento | quantos fatos e ligações cada entidade tem |
| propostas | o que cada espécie propõe (responder, recusar, afirmar, aproximar, calar) e com que evidência |
| decisão | quem falou e por quê |

A API devolve o estado em `internal_state`, e a leitura em `card_reading`.

O estado não é uma representação neural de ponta a ponta. É o contrato comum
que permite a regras, redes e acervo operarem sobre o mesmo entendimento do
turno. É o primeiro passo do caminho descrito no diagnóstico: as peças deixam
de só passar mensagens e começam a trabalhar sobre um estado compartilhado.

### 2. Leitura da ficha (`leitura_ficha.py`, nova espécie do reino neural)

Para a entidade da pergunta, a leitura mede em cada fato da ficha:

- pistas iguais (mesma raiz), sinônimos do léxico curado e relações
  pergunta→fato (`dados/relacoes_pergunta_fato.json`, por exemplo "chove" → "chuva",
  "olho nu" → "telescópio", "suga" → "aspirador");
- proximidade nos vetores próprios (skip-gram treinado do zero). Eles não
  passam no controle de equivalência e por isso entram só como traço fraco,
  com peso aprendido;
- compatibilidade com o tipo de pergunta: quem → nome próprio, quando → data,
  quanto → número, onde → lugar, por que → linguagem causal;
- quantas pistas ficaram sem cobertura.

Um modelo logístico em NumPy (`scripts/treinar_leitura_ficha.py`), treinado
com as perguntas do tutor (`dados/leitura_ficha_tutor.json`), combina os traços
numa probabilidade.

### 3. Árbitro

Depois da cascata de sempre, o árbitro lê as propostas. Ele só revê recusas
por falta de evidência (`fora`, "não entendi"). Dúvidas lógicas deliberadas
(`duvida`, `logica:desconhecido`) ficam como estão.

- **afirmar:** a pergunta cita um único conceito com ficha; não há negação,
  relação entre conceitos, pedido de escrita nem pergunta pessoal; a leitura
  cobre **todas** as pistas, e o fato é compatível com o tipo de pergunta. A
  resposta é o fato inteiro, com fonte, e a voz própria dá a forma;
- **aproximar:** todas as pistas cobertas, mas o tipo não fecha (por exemplo,
  "quanto" sem número no fato). A resposta começa com "Não tenho uma
  resposta exata para essa pergunta. O que a ficha de X traz de mais próximo
  é:";
- **calar:** sem isso, a recusa de antes fica.

**Aproximação parcial (ligada por decisão do dono do projeto, 05/10/2026).**
Com `LeituraFicha.aproximar_parcial`, a leitura também aproxima quando falta
apoio para uma única pista, desde que outra esteja coberta. Ela nunca aproxima:

- perguntas com qualificador absoluto ("memória infinita", "vida eterna",
  "perfeita", "mágica");
- pedidos imperativos de um detalhe ("Sobre X, explique o registro de marcas
  ultravioletas"), em que o "mais próximo" seria outro detalhe.

Nesses casos, a recusa continua. A resposta sempre começa
avisando que não é exata. A versão estrita (V3) fica disponível desligando a
chave.

## Como foi treinado e decidido

- 226 perguntas do tutor; 192 viram exemplos (34 não identificam a ficha ou são
  recusadas pelo quadro). Validação cruzada agrupada por assunto: nenhum
  assunto aparece no treino e na validação ao mesmo tempo.
- **Versão 1** (decide só pela probabilidade): na validação, 67 afirmações
  certas e 5 erradas.
- **Versão 2**, depois de olhar as previsões fora da amostra do tutor (não o
  teste congelado). Com todas as pistas cobertas: 49 certas e 1 errada. Com
  cobertura parcial: 18 certas e 5 erradas. Afirmar passou a exigir cobertura
  total; a cobertura parcial virou aproximação com ressalva.
- **Versão 3**, depois da suíte de testes do projeto. Quatro testes antigos
  falharam, e com razão: eles protegem recusas deliberadas.
  - "O gato é um mamífero e orbita o Sol?" é consulta lógica composta.
  - "Como o cérebro tem memória infinita?" e "Por que Marte tem cor de
    ferrugem quântica alienígena?" têm premissa falsa.
  - "Dê um exemplo de melatonina." pede um detalhe que a ficha não tem.

  Um desses testes se chama "ausência de evidência não aproximada". Por isso
  o árbitro deixou de rever dúvidas lógicas, e a aproximação também passou a
  exigir cobertura total. Na validação do tutor: afirma 40 (39 certas),
  aproxima 12 (11 certas) e cala 140.

**Achado honesto.** Com cobertura total exigida, o modelo aprendido quase
empata com a regra simples (39/40 contra 38/40 na validação). A diferença real
estava na aproximação parcial, que esbarra no princípio do projeto de não
aproximar o que não tem evidência. O gargalo não é o árbitro nem o modelo
logístico. É vocabulário e sentido: o CRIVO não sabe que "o quadro mais
famoso" de uma pintora corresponde a "pintou Abaporu". A lista de relações é
pequena, e os vetores próprios são ruidosos demais para afirmar.

## Resultados

Bateria de astronomia. Nenhuma pergunta de astronomia entrou no treino da
leitura. Algumas relações pergunta→fato foram escritas olhando falhas do
conjunto dev, então o dev deixa de ser medida limpa da leitura. O retido nunca
foi olhado.

| Conjunto | Sem leitura | V3 estrita | **V3 + parcial (ligada)** |
|---|---|---|---|
| dev: acertos (126 fatos) | 103 | 115 | **116** |
| dev: inventou / assunto errado | 0 / 0 | 0 / 0 | 0 / 0 |
| retido: acertos (81 fatos) | 48 | 49 | **54** |
| retido: inventou / assunto errado | 0 / 1 | 0 / 1 | 0 / 1 |

A bateria conta como acerto qualquer resposta que contenha o trecho esperado,
inclusive uma aproximação.

Teste congelado da leitura (`avaliacoes/leitura_ficha_v1`): 72 perguntas
escritas pelo tutor depois do treino, sobre 22 fichas que não estão nos dados
de treino. Foi medido a cada versão. As mudanças entre versões vieram da
análise do tutor e dos testes antigos, não dos casos do teste. Como o tutor
que escreveu o teste também ajusta a leitura, as próximas melhorias precisam
de um teste novo, escrito depois delas.

| | Sem leitura | V1 | V2 | V3 estrita | **V3 + parcial (ligada)** |
|---|---|---|---|---|---|
| respondíveis (50): afirmou certo | 22 | 34 | 23 | 24 | **24** |
| respondíveis: aproximou com o fato certo | 0 | 2 | 16 | 0 | **13** |
| respondíveis: afirmou errado | 0 | 1 | 0 | 0 | **0** |
| respondíveis: recusou | 28 | 13 | 11 | 26 | 13 |
| sem resposta (22): recusou | 20 | 15 | 13 | 19 | 16 |
| sem resposta: aproximou | 0 | 2 | 6 | 0 | 3 |
| sem resposta: afirmou (erro grave) | 2 | 5 | 3 | 3 | **3** |

As travas de qualificador absoluto e de pedido imperativo entraram depois
dessa medição, por causa de testes antigos do projeto ("Como o cérebro tem
memória infinita?"; "Sobre X, explique …"). A remedição do teste congelado e
da bateria deu os mesmos números.

## Limites

- A leitura escolhe um fato; não resume nem combina fatos, e não deduz.
- Só age sobre uma entidade citada na fala. O contexto ("e ele tem chuva?")
  entra no estado como entidade, mas a leitura ainda não responde por ele.
- A aproximação parcial entrega o fato certo em 37 de 50 perguntas (eram 22),
  mas em 3 de 22 perguntas sem resposta mostra um fato próximo, sempre com o
  aviso de que não é exato. Premissas falsas sem qualificador absoluto ainda
  podem receber uma aproximação em vez da recusa.

## O Transformer como leitor (preparado em 06/10/2026)

O resultado acima aponta onde o Transformer próprio deve entrar: como
**leitor**. Dado o estado (pergunta, entidade e fatos da ficha), ele diz se e
qual fato responde, entendendo paráfrases ("o quadro mais famoso" ↔ "pintou
Abaporu"). É o que a lista de relações e os vetores não conseguem. Prever a
próxima palavra solto já foi testado (16M parâmetros: 33/72 contra 42/72 do
motor híbrido) e não vira conversa.

O que ficou pronto:

| Peça | O que faz |
|---|---|
| `leitor_transformer.py` | executor NumPy (sem PyTorch no site): `<documento> fato <usuario> pergunta <fim>` passa pelo Transformer causal, e o estado da última posição vai para uma camada linear que dá P(o fato responde) |
| `scripts/treinar_leitor_transformer.py` | ajuste em PyTorch a partir de um pré-treino próprio (`--base`) |
| `scripts/perguntas_sinteticas.py` | perguntas tiradas das próprias fichas, com variações (sinônimos, palavras retiradas) e perguntas sem resposta (nome de outra ficha) |
| `scripts/treinar_leitura_ficha.py --com-transformer` | prova 1: o leitor entra como traço a mais da leitura e só é aprovado se entregar pelo menos 4 fatos certos a mais, sem mais erros, na validação do tutor |
| `avaliacoes/leitura_ficha_v2` | prova 2: teste congelado novo (70 perguntas, 24 fichas), escrito antes de qualquer código do leitor; o leitor só fica ligado se melhorar aqui |
| `notebooks/treinar_leitor_colab.ipynb` | treino com GPU a partir do pré-treino de 16M guardado no Drive, as duas provas e um zip com o resultado |

Os dados de treino do leitor nunca incluem as fichas das perguntas do tutor,
dos testes v1 e v2, nem a astronomia da bateria. Assim, todas essas medidas
continuam limpas.

**Piloto em CPU** (base de 2,6M, `artefatos/linguagem_profunda`, 3.000 passos,
cerca de 25 minutos):

- treino: a perda cai de 0,45 para cerca de 0,1, ou seja, o modelo decora as
  perguntas sintéticas;
- validação do tutor: acerto do fato de 27% para 35% (com cerca de 3 fatos
  por ficha, o acaso fica perto de 33%); separação entre perguntas com e sem
  resposta (AUC) 0,56, quase o acaso de 0,5;
- prova 1 (com a margem antiga, de 1 fato): 79 contra 77 fatos certos
  entregues. Isso é ruído, e por isso a margem passou a ser de 4;
- prova 2, teste congelado v2: igual à linha de base (19 fatos certos e 6
  erros, com ou sem o leitor). **Não fica ligado.**

Conclusão: o caminho funciona de ponta a ponta. A paridade NumPy × PyTorch é
exata até a sexta casa. Mas o Transformer de 2,6M, com pouco pré-treino, não
transfere para paráfrases reais. O teste que importa é o de 16M no Colab.
Linha de base para ele no teste v2, com a leitura atual: 12 afirmadas certas,
7 aproximadas certas, 2 afirmações erradas e 4 afirmações em perguntas sem
resposta. Sem leitura nenhuma: 9 certas.

Depois do leitor, o próximo papel é o de **realizador**: receber o estado com
os fatos escolhidos e escrever a resposta, com a guarda de fidelidade
descartando o que não estiver nos fatos.

## Reproduzir

```bash
python scripts/treinar_leitura_ficha.py          # treino e validação (~1 min)
python scripts/avaliar_leitura_ficha.py teste    # teste congelado (~1 min)
python scripts/avaliar_leitura_ficha.py teste --sem-leitura
python scripts/avaliar_bateria.py todos
python -m unittest testes_leitura_ficha
# leitor Transformer (piloto em CPU; o de verdade vai pelo caderno do Colab)
python scripts/treinar_leitor_transformer.py --base artefatos/linguagem_profunda --passos 3000
python scripts/treinar_leitura_ficha.py --com-transformer artefatos/leitor_transformer
python scripts/avaliar_leitura_ficha.py teste_v2
```
