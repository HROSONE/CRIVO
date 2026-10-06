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
| Quem propôs a teoria da relatividade? | "não entendi" | ainda recusa, mas é um erro: o acervo tem Einstein na ficha de relatividade restrita |

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

## Perguntas sem o nome do assunto (07/10/2026)

A bateria não mede o caso para o qual a busca existe: quase todas as perguntas
dela citam o nome do assunto. Por isso há um conjunto novo,
`avaliacoes/busca_sem_nome_v1`, em que nenhuma pergunta cita o nome nem os
apelidos da ficha que responde.

- **Fichas:** 80, sorteadas com semente fixa, fora das fichas do tutor, dos
  testes de leitura e da astronomia.
- **dev:** 33 perguntas com resposta e 10 sem. Pode ser olhado caso a caso.
- **teste:** 43 perguntas com resposta e 12 sem. Congelado, medido só em
  agregados.
- **Perguntas sem resposta:** conferidas no acervo e na base antiga antes de
  rodar o CRIVO. Uma pergunta do dev ("animal terrestre mais rápido") tinha
  resposta na base antiga e foi trocada.

`scripts/avaliar_busca_sem_nome.py` classifica cada resposta:

- **certo:** mostrou o fato esperado, afirmando ou aproximando;
- **errado:** respondeu com outro fato;
- **recusou:** recusou, embora o acervo tenha a resposta;
- **inventou:** respondeu a uma pergunta sem resposta no acervo.

O que mudou, sempre ajustado olhando só o dev:

- **Entrada da busca:** a rota passa a valer também para perguntas longas
  (mais de 6 pistas ou de 16 palavras) e para "quem escreveu…", que antes
  era lido como pedido de escrita.
- **Pistas:** palavras vazias ("se", "joga") deixam de contar como pistas. Antes,
  "Como se joga xadrez?" virava aproximação com a ficha de soluções.
- **Aproximar em pergunta longa:** pede 3 ou mais pistas cobertas, pelo
  menos metade do total. Antes, a leitura exigia que faltasse no máximo uma.
- **Duas propostas:** a busca aprendida e a busca só por palavras propõem
  cada uma seu fato, e a leitura confere as duas. Sem nome nenhum na pergunta,
  as palavras sozinhas acertam mais (no dev, 91% contra 85% em 1º lugar).
- **Aproximar com leitura forte:** com 3 ou mais pistas cobertas, a
  aproximação aceita uma probabilidade de busca menor (≥ 0,2). Na ficha com
  muitos fatos parecidos, essa probabilidade cai.

Duas tentativas ficaram de fora porque fizeram o CRIVO responder uma pergunta
que ele deve recusar no teste congelado de compreensão
(`testes_entendimento_neural`, de 49 para 48 recusas certas):

- deixar **afirmar** com 3 pistas cobertas mesmo com a busca pouco confiante;
- **retreinar a busca** com duas evidências novas (nome citado em parte e
  palavras quando nenhum nome é citado) e com perguntas sem o nome.

A causa foi achada desligando uma mudança por vez e olhando só o total do
teste, sem ver casos.

Também não entrou o **decisor aprendido** (`decisor_resposta.py`), um modelo
único no lugar dos limiares da rota, treinado com perguntas sintéticas e com
a ficha que responde retirada do acervo (para aprender a calar). Na validação
que imita a rota, ele entregou 13 fatos certos contra 21 das regras. As
perguntas sintéticas copiam as palavras do fato, e as reais não: sem exemplos
de formulação real, ele não calibra. O código fica no repositório, desligado,
para quando houver esses dados ou o Transformer (`scripts/treinar_decisor.py`).

Em 07/10, o tutor escreveu 400 perguntas de formulação real
(`dados/decisor_tutor.json`): 320 sem o nome do assunto e com outras palavras,
sobre fichas fora de todos os testes, e 80 sem resposta no acervo (conferidas
no texto do acervo). Com elas, o decisor passou a acertar sem errar na
validação: 18 fatos certos, nenhum errado e nenhuma pergunta sem resposta
respondida. Ligado no lugar das regras, porém, o dev das perguntas sem nome
cai de 20 para 15 acertos, com o mesmo 1 erro e nenhuma invenção. A bateria
e a catraca de compreensão ficam iguais. Continua desligado. Quando o leitor
Transformer for instalado (`scripts/instalar_leitor.py`), a probabilidade
dele entra pela leitura da ficha e o decisor é medido de novo.

Teste congelado, perguntas sem o nome: lido uma vez antes dos ajustes e uma
depois.

| | Sem a busca | Busca de 06/10 | Agora |
|---|---|---|---|
| fato certo (de 43) | 3 | 16 | **27** |
| aproximou com o fato certo | 0 | 7 | 17 |
| respondeu com outro fato | 5 | 6 | 8 |
| recusou tendo a resposta | 35 | 21 | 8 |
| inventou (de 12 sem resposta) | 0 | 0 | **0** |

A tabela é a mesma com as duas tentativas revertidas (medida de novo, terceira
leitura do teste, sem escolher nada por ela). As respostas com outro fato
subiram de 6 para 8. A maioria delas vem como
aproximação, que avisa que não é a resposta exata. A bateria ficou igual (dev
116, retido 54, nenhuma invenção). `testes_busca_semantica` guarda a catraca:
pelo menos 27 certos, no máximo 8 errados e nenhuma invenção.

## Próximos passos

1. Reduzir as respostas com outro fato: a leitura ainda aceita um fato da
   ficha certa que não é o que a pergunta pede.
2. Dar à busca um sinal de "não há resposta", treinado com as perguntas sem
   resposta.
3. Pôr o Transformer próprio como mais uma evidência, com a mesma interface.
   O caderno `notebooks/treinar_transformer_leitor_colab.ipynb` pré-treina a
   base (~17M, Wikipédia em português inteira) e ajusta o leitor com
   exercícios do acervo e da Wikipédia; grava no Drive um único checkpoint a
   cada 10.000 passos.

## Reproduzir

```bash
python scripts/treinar_busca_semantica.py            # treina, mede e grava artefatos/busca_semantica/meta.json
python scripts/treinar_busca_semantica.py --sem-teste # ajuste: só validação, sem gravar
python -m unittest testes_busca_semantica
python scripts/avaliar_busca_sem_nome.py dev --detalhes   # o teste congelado só em agregados
```
