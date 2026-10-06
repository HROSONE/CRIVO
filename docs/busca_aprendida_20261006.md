# Busca aprendida (06/10/2026)

## O problema

O CRIVO procurava como um bibliotecário. Primeiro achava a etiqueta, isto é, o
nome do conceito na pergunta ou o classificador de assuntos (`rede_crivo.json`),
que só conhece uma lista fechada de ids. Depois achava o fato. Cada ficha nova
exigia retreinar o classificador. E, com o assunto achado, quem decidia o fato
era a palavra repetida: "Quantos códons existem no código genético?" caía na
definição de código genético, porque ela repete "código genético", e não no
fato que diz "64 códons".

## O que muda

`busca_semantica.py` procura direto nos 4.100 fatos do acervo. Para cada fato
candidato, mede evidências de que ele responde:

| Evidência | O que mede |
|---|---|
| palavras | BM25 sobre palavras e radicais, no acervo todo e na ficha |
| resto | BM25 só com o que a pergunta pede além do nome do assunto ("QUANTOS CÓDONS existem no código genético?") |
| sentido | proximidade nos vetores próprios (skip-gram treinado do zero); aproxima "igual em todos" de "universal" |
| forma | o tipo da pergunta casa com o fato: quem → nome, quando → data, quanto → número, por que → causa, como → funcionamento |
| aspecto | "para que serve", "como surgiu", "como se sabe" casam com a marca do fato |
| ficha | o nome do assunto aparece na pergunta; pergunta de definição → primeiro fato |

Um modelo de ordenação aprendeu quanto vale cada evidência: um softmax entre os
candidatos, com 18 pesos. Ele não vê ids nem palavras, só evidências. Por isso
um fato novo é achado sem retreinar nada. O teste
`test_fato_novo_e_achado_sem_retreinar` mostra isso com um catálogo inventado.

## Como foi treinado

- **Dados:** perguntas sintéticas tiradas dos próprios fatos
  (`scripts/perguntas_sinteticas.py`), com variação por sinônimo, mais "O que é
  X?" ligado ao primeiro fato. São 1.962 perguntas.
- **Fichas fora do treino:** as do tutor, que servem de validação; as dos testes
  congelados de leitura v1 e v2, que servem de teste; e a astronomia.
- **Escolhas:** a regularização foi escolhida só pela validação. O teste
  congelado foi medido no fim, só em agregados.
- **Custo:** o treino leva menos de um minuto na CPU (`python
  scripts/treinar_busca_semantica.py`) e é reproduzível, com o mesmo `meta.json`
  a cada execução.

## Resultado

O "fato certo" é o fato que o tutor marcou como resposta.

| | Só palavras (BM25) | Busca aprendida |
|---|---|---|
| **Validação (tutor, 161 perguntas)** | | |
| fato certo em 1º, assunto dado | 55% | 81% |
| fato certo em 1º, acervo inteiro | 40% | 75% |
| fato certo entre os 5 primeiros, acervo inteiro | 68% | 97% |
| **Teste congelado v1 (50)** | | |
| fato certo em 1º, assunto dado | 44% | 76% |
| fato certo em 1º, acervo inteiro | 34% | 74% |
| fato certo entre os 5 primeiros | 62% | 98% |
| **Teste congelado v2 (48)** | | |
| fato certo em 1º, assunto dado | 29% | 67% |
| fato certo em 1º, acervo inteiro | 23% | 67% |
| fato certo entre os 5 primeiros | 46% | 98% |

O modelo foi aprovado, porque ganhou da busca por palavras na validação e nos
dois testes congelados. Os pesos que mais pesam são proximidade de sentido
relativa à ficha, nome do assunto citado, pergunta de definição, força da
ficha, e "por que" casado com linguagem causal.

Uma ressalva de método: o teste congelado foi lido duas vezes. Na segunda,
depois de fixar a semente do sorteio das perguntas sintéticas para o treino
ficar reproduzível, os números foram os mesmos e nada foi escolhido por eles.

## Ligada no CRIVO

A busca sozinha não sabe quando a pergunta não tem resposta no acervo. Na
validação, mesmo com confiança ≥ 0,9, 7 dos 49 primeiros lugares eram
perguntas sem resposta. Por isso ela não fala sozinha: entra no árbitro
(`estado_interno.py`) como a espécie `busca_aprendida`, e a leitura da ficha
confere o fato que ela achou.

Quando entra: a espécie que respondeu recusou por falta de evidência, e

- a pergunta não cita o nome de nenhum conceito; ou
- cita dois conceitos numa pergunta aberta (qual, quem, quanto…), e a resposta
  está numa terceira ficha ("Qual organela produz ATP nas células?"); ou
- cita um conceito cuja ficha não tem a resposta, numa pergunta aberta.

Quando fala:

- **afirma** se a leitura cobre todas as pistas do fato achado, com pelo menos
  duas pistas e probabilidade de busca ≥ 0,5;
- **aproxima** ("Não tenho uma resposta exata… o mais próximo é…") se a
  leitura aprovaria a aproximação, com pelo menos duas pistas e probabilidade
  de busca ≥ 0,7.

Quando não entra:

- "O que é X?" sem ficha de X: a pergunta pede a identidade de algo
  desconhecido, e um fato que só cita o nome não é a resposta;
- perguntas de sim ou não sobre relação ("A memória ajuda o sono?");
- negação.

Exemplos:

| Pergunta | Antes | Agora |
|---|---|---|
| Quem pintou a Mona Lisa? | "não entendi" | "Pintou a Mona Lisa e A Última Ceia." (ficha de Leonardo da Vinci) |
| Qual organela produz ATP nas células? | "não entendi" | aproxima com o fato da mitocôndria |
| Qual molécula carrega a informação genética? | recusa | aproxima com a ficha de RNA |
| Quem propôs a teoria da relatividade? | "não entendi" | continua recusando: a busca acha Darwin e a leitura não confirma |

Medição com a ligação: a bateria ficou igual (dev 116, retido 54, nenhuma
invenção, recusas esperadas 13/13 e 12/12). Ela é quase toda de astronomia e
cita o nome do assunto, então não mede o caso novo. Falta um teste congelado
de perguntas que não citam o nome do assunto.

Como traço a mais da leitura (`scripts/treinar_leitura_ficha.py --com-busca`),
a busca entregou 79 fatos certos contra 77. A margem exigida é 4, então esse
uso continua desligado.

Erros vistos na validação: "Que força faz a lagartixa grudar na parede?" vai
para pressão arterial ("força… parede"), porque o nome "adesão da lagartixa"
só aparece em parte na pergunta. "Que enzima copia o DNA na replicação?" fica
na definição ("cópia"), e não no fato da DNA polimerase.

## Próximos passos

1. Teste congelado de perguntas sem o nome do assunto, com e sem resposta no
   acervo.
2. Acrescentar a evidência de nome citado em parte e dar à busca um sinal
   de "não há resposta", treinado com as perguntas sem resposta.
3. Pôr o Transformer próprio (16M, ajustado no Colab) como mais uma
   evidência, com a mesma interface.

## Reproduzir

```bash
python scripts/treinar_busca_semantica.py            # treina, mede e grava artefatos/busca_semantica/meta.json
python scripts/treinar_busca_semantica.py --sem-teste # ajuste: só validação, sem gravar
python -m unittest testes_busca_semantica
```
