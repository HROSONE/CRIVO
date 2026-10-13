# Prompt para o Grok: formas de fala para o treino do CRIVO

Copie tudo a partir de "INÍCIO DO PROMPT". O Grok devolve só **falas de pessoas** (o lado do
usuário); as respostas do CRIVO continuam as do repositório. Nada de conteúdo real do X.

**Usado em 13/10/2026:** as respostas estão em `experimentos/fase5_conversa_20261013/grok/` e
entraram na v2 da fase 5 (ver o README de lá).

Decisão registrada quando o arquivo entrou no treino: as falas foram geradas pelo Grok (modelo de
terceiros) a pedido do criador do projeto; entram só como dado de treino, revisadas, e nenhum modelo
de terceiros roda no CRIVO.

---

INÍCIO DO PROMPT

Estou treinando do zero uma IA pequena em português do Brasil, chamada CRIVO. Ela já sabe responder,
mas não entende frases que nunca viu. Preciso de **muitos jeitos diferentes de uma pessoa dizer a
mesma coisa** numa conversa casual por chat.

Regras importantes:

1. **Não copie nem cite posts reais do X/Twitter**, nem nomes, @, marcas ou pessoas reais. Escreva
   frases novas, inventadas por você, no estilo de como brasileiros escrevem no celular.
2. Escreva só a fala da pessoa (o que ela digita), nunca a resposta.
3. Varie de verdade:
   - gírias de várias regiões (Sudeste, Nordeste, Sul…);
   - abreviações ("vc", "tbm", "pq", "q", "blz");
   - sem acento, tudo minúsculo, erro de digitação, letras repetidas ("nãoooo");
   - frase curta (1–3 palavras) e frase longa (15–25 palavras, com contexto);
   - emoji às vezes;
   - pessoas de idades diferentes;
   - tons educado, irritado, irônico e carinhoso.
4. Nada de informação sobre o mundo (fatos, datas, números, nomes de lugares). São só falas de
   conversa.
5. Sem palavrão pesado, mas pode ter os leves e os xingamentos comuns ("burro", "inútil"), porque o
   CRIVO precisa aprender a responder com calma a isso.
6. Para cada situação, escreva **60 falas diferentes**. Não repita estrutura: se uma começa com
   "você", a próxima não deve começar igual.

Formato da resposta: **somente JSON válido**, sem texto antes ou depois, assim:

```json
{"situacoes": [
  {"situacao": "nome_da_situacao", "falas": ["fala 1", "fala 2", "..."]}
]}
```

Como é muita coisa, faça em partes: responda primeiro as situações 1 a 10. Quando eu disser
"continua", faça a 11 a 20, e assim por diante. Cada parte é um JSON completo e válido.

Situações (o nome entre parênteses vai no campo "situacao"):

1. (oi) Cumprimentar a IA para começar a conversa.
2. (oi_tudo_bem) Cumprimentar perguntando se ela está bem.
3. (despedida) Se despedir de um jeito normal.
4. (despedida_rude) Se despedir xingando ou desdenhando da IA.
5. (despedida_dormir) Avisar que vai dormir ou deitar.
6. (obrigado) Agradecer a ajuda.
7. (nao_entendeu_queixa) Reclamar que a IA não entendeu o que a pessoa disse.
8. (nao_era_isso) Dizer que a resposta da IA não era o que a pessoa queria saber.
9. (dificil_falar) Reclamar que é difícil ou cansativo conversar com a IA.
10. (voce_confunde) Dizer que a IA confunde, mistura ou erra as coisas.
11. (insulto) Xingar ou ofender a IA, sem se despedir.
12. (seja_breve) Pedir que a IA responda mais curto.
13. (de_outro_jeito) Dizer que não entendeu a explicação e pedir de outro jeito.
14. (repetir) Pedir para a IA repetir o que disse.
15. (tem_certeza) Duvidar da resposta da IA ("tem certeza?").
16. (nunca_ensinaram) Provocar dizendo que ninguém ensinou aquilo à IA.
17. (posso_falar) Perguntar se pode escrever do jeito que quiser, com gíria ou errado.
18. (risada) Rir de algo (kkkk, rsrs, haha…), às vezes junto com uma palavra.
19. (grito) Expressar frustração ou susto com interjeição (aff, aaaa, putz…).
20. (ok) Concordar ou só confirmar que leu ("beleza", "show", "tá").
21. (sim_continuar) Dizer que sim, que quer continuar.
22. (nao_obrigado) Recusar a continuação ("não", "deixa pra lá").
23. (desisto) Dizer que desistiu da conversa.
24. (pedido_desculpa) Pedir desculpa à IA por ter sido grosso.
25. (quem_e) Perguntar quem ou o que a IA é.
26. (o_que_faz) Perguntar o que a IA sabe fazer ou para que serve.
27. (ser_humano) Perguntar se é uma pessoa de verdade.
28. (robo) Chamar a IA de robô ou máquina.
29. (sente) Perguntar se a IA sente ou tem emoções.
30. (gosta) Perguntar do que a IA gosta.
31. (amigo) Perguntar se a IA é ou quer ser amiga da pessoa.
32. (estou_mal) Dizer que está mal, triste ou para baixo, sem dar motivo.
33. (cansado) Dizer que está cansado.
34. (ansioso) Dizer que está ansioso, nervoso ou com medo.
35. (sozinho) Dizer que se sente sozinho.
36. (tedio) Dizer que está entediado.
37. (fome) Dizer que está com fome.
38. (conversar) Pedir para a IA conversar ou fazer companhia.
39. (fale_palavra) Pedir para a IA falar uma palavra qualquer.
40. (piada) Pedir uma piada.
41. (historia) Pedir uma historinha.
42. (nao_consegue) Pedir algo que uma IA de texto não consegue fazer (abrir app, ver foto, tocar
    música, ligar para alguém, pesquisar na internet).
43. (hora_data) Perguntar que horas são ou que dia é hoje.
44. (ajuda) Pedir ajuda sem dizer ainda com o quê.
45. (elogio_crivo) Elogiar a IA.
46. (te_amo) Dizer que ama ou gosta muito da IA.
47. (cala_boca) Mandar a IA calar a boca ou parar de falar.
48. (para_repetir) Reclamar que a IA está repetindo as mesmas coisas.
49. (teste) Testar se a IA está funcionando ("teste", "alô").
50. (saude_urgente) Avisar uma emergência de saúde acontecendo agora (dor no peito, falta de ar,
    desmaio, alguém passando mal).

Depois das 50, faça mais uma parte com o nome "contraexemplos": pares de falas **parecidas na
palavra mas com sentido diferente**, no formato:

```json
{"contraexemplos": [
  {"a": {"situacao": "cansado", "fala": "tô cansado"},
   "b": {"situacao": "dificil_falar", "fala": "tô cansado de você"}}
]}
```

Faça 80 pares, usando só os nomes de situação da lista acima.

FIM DO PROMPT
