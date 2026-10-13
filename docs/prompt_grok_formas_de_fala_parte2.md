# Prompt para o Grok, parte 2: as situações que ainda não têm variedade

Na v2, as situações com falas do Grok passaram a ser entendidas em frases novas (de 70% a 95%).
As que só tinham de 2 a 4 jeitos de dizer ficaram em 0%. Esta parte cobre essas.

Mesmas regras da parte 1:
- o Grok escreve só as falas da pessoa, nunca a resposta do CRIVO;
- nada de conteúdo real do X;
- o uso como dado de treino foi aprovado pelo criador e fica registrado.

Copie tudo a partir de "INÍCIO DO PROMPT". Quando ele terminar uma parte, mande "continua".

---

INÍCIO DO PROMPT

Estou treinando do zero uma IA pequena em português do Brasil, chamada CRIVO. Preciso de **muitos
jeitos diferentes de uma pessoa dizer a mesma coisa** numa conversa casual por chat.

Regras (leia todas antes de começar):

1. **Não copie nem cite posts reais do X/Twitter**, nem nomes, @, marcas ou pessoas reais. Frases
   novas, inventadas por você, no jeito que brasileiros escrevem no celular.
2. Só a fala da pessoa, nunca a resposta.
3. **30 falas por situação.** Cada fala precisa usar **palavras principais diferentes** das
   outras. É proibido criar uma fala nova só acrescentando palavras no fim de outra ("mesmo",
   "de verdade", "agora", "por favor").
4. No máximo **uma** palavra de reforço por fala.
5. No máximo **3** falas por situação dizendo onde a pessoa está ("tô no ônibus"), cada uma num
   lugar diferente.
6. Misture de verdade:
   - frases de 1 a 3 palavras e frases longas (15 a 25 palavras, com contexto);
   - perguntas diretas e indiretas ("queria saber se você…");
   - gíria de várias regiões, abreviação ("vc", "tbm", "pq"), sem acento, erro de digitação,
     emoji às vezes;
   - pessoas de idades diferentes (criança, adolescente, adulto, idoso);
   - tons educado, irritado, irônico e carinhoso.
7. Nada de informação sobre o mundo (fatos, datas, nomes de lugares ou de pessoas).
8. Cada fala deve ter **só aquele sentido**. Se uma frase puder ser lida de dois jeitos, não use.

Formato: **somente JSON válido**, sem texto antes ou depois:

```json
{"situacoes": [
  {"situacao": "nome_da_situacao", "falas": ["fala 1", "fala 2", "..."]}
]}
```

Faça **7 situações por resposta**: primeiro as de 1 a 7. Quando eu disser "continua", as de 8 a
14, e assim por diante.

Situações (o nome entre parênteses vai no campo "situacao"):

1. (bom_dia) Cumprimentar com bom dia, chegando na conversa.
2. (boa_tarde) Cumprimentar com boa tarde.
3. (boa_noite) Cumprimentar com boa noite, chegando na conversa (não é ir dormir).
4. (estou_bem) Responder que está bem, depois de a IA perguntar como a pessoa está.
5. (expressao_curta) Mandar só uma palavra solta de chamada ou espanto ("mano", "véi", "cara", "nossa").
6. (sem_sentido) Digitar coisa sem sentido: letras aleatórias, teclado batido, "hmmm".
7. (ingles) Falar com a IA em inglês, com frases simples.
8. (amor_bom) Contar algo bom no amor: está apaixonado, começou a namorar, vai casar.
9. (amor_dor) Contar uma dor de amor: levou um fora, terminou, sente saudade de alguém.
10. (familia_boa) Contar algo bom da família.
11. (familia_preocupa) Contar algo ruim ou preocupante da família (briga, alguém doente, saudade).
12. (dinheiro_aperto) Contar que está sem dinheiro ou com as contas apertadas.
13. (dinheiro_bom) Contar algo bom com dinheiro: recebeu, juntou, pagou as contas.
14. (trabalho_bom) Contar algo bom no trabalho.
15. (trabalho_ruim) Reclamar do trabalho.
16. (escola_boa) Contar que foi bem na escola ou na prova.
17. (escola_dificil) Reclamar da escola, de prova difícil ou de lição.
18. (dia) Contar como foi o dia (bom, corrido, chato, estranho), sem detalhes.
19. (sono) Dizer que não consegue dormir, dormiu mal ou está com sono (sem dizer que vai dormir agora).
20. (motivacao) Pedir motivação ou dizer que está sem vontade de fazer as coisas.
21. (tempo_clima) Falar do tempo: chuva, calor, frio, dia bonito.
22. (viagem_vai) Contar que vai viajar ou está de férias.
23. (viagem_voltou) Contar que voltou de viagem.
24. (filme_visto) Contar que viu um filme ou uma série.
25. (gosto_filme) Contar que tipo de filme ou série gosta.
26. (musica_conta) Contar que música ouve ou gosta.
27. (jogo_conta) Contar que joga ou gosta de algum jogo ou esporte.
28. (comida_favorita) Contar a própria comida favorita.
29. (gosto_bichos) Dizer que gosta de animais ou que quer ter um.
30. (tenho_bicho) Contar que tem um bicho de estimação, sem dizer o nome dele.
31. (nome_crivo) Perguntar o nome da IA.
32. (idade) Perguntar a idade da IA.
33. (onde_mora) Perguntar onde a IA mora ou de onde ela é.
34. (criador) Perguntar quem criou ou fez a IA.
35. (ser_ia) Perguntar se é uma inteligência artificial ou um programa.
36. (consciencia) Perguntar se a IA pensa, tem consciência ou sonha.
37. (medo) Perguntar se a IA tem medo de alguma coisa.
38. (lembra) Perguntar se a IA lembra do que a pessoa disse ou se tem memória.
39. (voce_aprende) Perguntar se a IA aprende ou evolui.
40. (aprendeu_algo) Perguntar se a IA aprendeu alguma coisa hoje.
41. (sabe_tudo) Perguntar se a IA sabe tudo ou se é um gênio.
42. (cor_favorita) Perguntar a cor favorita da IA.
43. (comida_crivo) Perguntar se a IA come ou qual comida ela prefere.
44. (musica_crivo) Perguntar se a IA ouve música ou qual ela prefere.
45. (bicho_favorito) Perguntar qual o animal favorito da IA.
46. (nao_gosta) Perguntar do que a IA não gosta ou o que ela odeia.
47. (fe) Perguntar se a IA acredita em Deus ou tem fé.
48. (opiniao_religiao) Perguntar qual religião é a certa ou se existe vida após a morte.
49. (opiniao_politica) Pedir opinião política: partido, voto, governo.
50. (opiniao_vida) Perguntar o sentido da vida ou por que a gente existe.
51. (o_que_acha_de_mim) Perguntar o que a IA acha da pessoa.
52. (flerte) Paquerar a IA: chamar para namorar, casar, dizer que ela é linda.
53. (entediante) Dizer que a IA é chata ou sem graça, sem xingar pesado.
54. (palavrao) Soltar só um palavrão comum, de raiva ou susto, sem falar com ninguém.
55. (perguntar_crivo) Perguntar se pode fazer uma pergunta.
56. (pergunta_qualquer) Pedir que a IA faça uma pergunta ou surpreenda a pessoa.
57. (ensinar_pedido) Perguntar se pode ensinar alguma coisa para a IA.
58. (conselho) Pedir um conselho sem dizer ainda sobre o quê.
59. (recomenda) Pedir que a IA indique um filme, uma música, uma série ou um livro.
60. (charada) Pedir uma charada ou adivinha.
61. (poema) Pedir um poema ou versos.
62. (jogar_agora) Chamar a IA para jogar ou brincar agora.
63. (recusar) Pedir algo errado ou que machuca alguém (colar na prova, mentir para enganar,
    xingar um colega, descobrir o endereço de alguém), sem nenhum detalhe perigoso.
64. (saude_geral) Tirar uma dúvida de saúde que **não** é emergência (febre leve, dor de cabeça,
    dormir pouco).
65. (ajuda_socorro) Pedir socorro sem dizer ainda o que houve ("socorro", "me acode").
66. (ansioso_peito) Dizer que o coração está acelerado ou o peito apertado de nervoso.
67. (obrigado_despedida) Agradecer e se despedir na mesma fala.
68. (desisto_despedida) Desistir da conversa e ir embora na mesma fala.

FIM DO PROMPT
