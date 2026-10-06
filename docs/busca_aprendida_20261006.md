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

## O que ainda não faz

- **Ainda não responde sozinha.** A busca ordena bem, mas não sabe quando a
  pergunta não tem resposta no acervo. Na validação, mesmo com confiança ≥ 0,9,
  7 dos 49 primeiros lugares eram perguntas sem resposta. Quem decide se fala
  continua sendo a leitura da ficha e o árbitro (`estado_interno.py`).
- **Ainda não melhora as respostas da leitura.** Como traço a mais da leitura
  (`scripts/treinar_leitura_ficha.py --com-busca`), entregou 79 fatos certos
  contra 77, com o mesmo erro. A margem exigida é 4, então não foi ligada.
  A leitura só afirma com todas as pistas cobertas, e esse filtro, não a
  ordem, é o que limita as entregas.
- **Erros vistos na validação:** "Que força faz a lagartixa grudar na parede?"
  vai para pressão arterial ("força… parede"), porque o nome "adesão da
  lagartixa" só aparece em parte na pergunta. "Que enzima copia o DNA na
  replicação?" fica na definição ("cópia"), e não no fato da DNA polimerase.

## Próximos passos

1. Usar a busca para achar o assunto quando a pergunta não cita o nome, e
   deixar a leitura decidir se há resposta. É aqui que ela substitui o
   classificador de lista fechada.
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
