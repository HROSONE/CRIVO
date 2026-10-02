# Noções ampliadas (2026-10-02)

A base de noções do dia a dia passou de 107 para 175 noções
(`dados/nocoes_pt.json`), com a mesma política: noção não é fato com fonte,
é dita como noção ("costuma", "em geral") e nunca responde pergunta técnica
ou de saúde.

## O que entrou

Temas que a base antiga não cobria: música e instrumentos, futebol e outros
esportes, videogame, dança, show, teatro, museu, desenho e pintura,
caminhada, natação, yoga, viagem, hotel, pôr do sol, trilha e serra,
fazenda, cavalo, galinha; chuveiro, louça, roupa, mudança, aluguel, reforma,
vazamento, jardim e horta, cozinhar, cabelo, roupa e calçado novos, presente,
fim de semana, datas comemorativas; entrevista, emprego, reunião,
apresentação, salário, lição de casa, aula; vergonha, nervosismo, ciúme,
orgulho, alegria; avós, tios e primos, irmã, esposa e namorado; chá, leite,
sushi, lanche, doce, açaí, arroz e feijão, suco, padaria; dentista, farmácia,
dor nas costas; metrô, estrada, aeroporto, mecânico, táxi e aplicativo;
computador travado e mensagens.

Formas que estavam numa noção mais geral foram para a específica
("reunião" saiu de "trabalho"; "flor", "jardim" e "horta" saíram de
"planta"; "voo" e "aeroporto" saíram de "avião").

Avaliação do que aconteceu ("o show foi incrível", "a festa foi chata")
passou a contar como relato, com uma lista fechada de adjetivos.

## Medição

Conjunto novo `amplo` em `avaliacoes/conversa_cotidiana_v1`, escrito antes
da ampliação, com temas que a base não cobria; o retido usa temas
diferentes do dev.

| | antes | depois | sem analisador |
|---|---|---|---|
| amplo dev | 18/30 | 30/30 | 24/30 |
| amplo retido (agregado) | 18/25 | 23/25 | 20/25 |
| conversa cotidiana retido2 | 12/15 | 14/15 | 12/15 |

Sem perda: conversa cotidiana dev 36/36 e retido 23/24, diálogos 6/6, 4/4,
3/3, nenhum fato errado. Auditorias: definições, regras mistas, entrada do
usuário e programação adversarial passam; coorte histórica 192 acertos e
43 erradas (limites ≥192 e ≤44).

## O que ficou para depois

Fichas novas **com fonte** (conhecimento verificado em áreas além de
astronomia) não entraram nesta rodada: cada ficha precisa de fonte
conferida, e isso pede uma rodada própria.
