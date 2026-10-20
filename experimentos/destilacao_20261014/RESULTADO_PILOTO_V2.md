# Destilação v2: piloto (15/10/2026)

40 pedidos (os primeiros da grade), conta hr87676620, A100. Professor Qwen3-32B-AWQ (Apache 2.0,
revisão 0499c3ac). Juízes: Phi-4 (MIT, 2db69c1c) e Qwen3-32B-AWQ; só entra o que os dois dão 4 ou 5.
Manifesto: `CRIVO/dados-professor-v2/piloto/manifesto.json` (dados sha256 b18d7449…).

| | |
|---|---|
| falas novas aceitas | 384 (de 400; 5 idioma, 5 tamanho, 2 repetidas) |
| turno 1 / ok no filtro | 384 / 364 |
| turno 2 / ok no filtro | 357 / 342 |
| fora no filtro | inventou 30, repetição 3, cortada 1, idioma 1 |
| notas (mín. dos dois juízes) | 5: 439, 4: 250, 3: 3, 1: 14 |
| **respostas trocadas aprovadas** | **8,3%** (limite 10%) |
| treino / prova | 604 / 85 (293 de dois turnos) |
| treino por pedido | 15,1 → a meta de 87 mil pede ~5.800 pedidos |

## O que deu errado no caminho (e foi corrigido antes deste resultado)

1. Juiz Mistral Small 3.1 w4a16 sem modelo de conversa: travava. Saiu da lista.
2. Phi-4 sozinho aprovou 20% das respostas trocadas, mesmo perguntando antes se tinha a ver. Entrou
   o segundo juiz (Qwen3-32B); os dois juntos: 8,3%.
3. Segunda fala da pessoa com "PESSOA: PESSOA:" (o professor repetia o rótulo): tirado.
4. Professor fingindo ser gente ("Eu tô dormindo razoável"): filtro novo.

## O que a leitura de 25 conversas mostrou

- Português natural, do jeito pedido, e responde o que a pessoa disse (vaca na calçada, matemática
  2x+3=7, avó mandando receita, encanador).
- Defeitos que ainda passaram: uma "fala" que era o professor explicando ("A pessoa pode
  responder:") — filtro novo para o caderno completo; 76% das respostas terminam com pergunta
  (o Crivo pode aprender a sempre perguntar de volta); algumas oferecem ajuda física ("posso ajudar
  com o café"); muitas começam com "Entendo, às vezes" (o teto de 1% por começo vale no caderno
  completo).
- O juiz aprova quase tudo que passou no filtro (98%). A trava das trocadas é a única medida de que
  ele reprova lixo; o criador lê a amostra antes do caderno completo.

## Medida final do juiz (15/10/2026, commit 603bfc4)

As trocadas da primeira medida eram 60, e algumas do mesmo tema (que podem servir de verdade): a
mesma amostra deu 8,3% numa rodada e 21% na seguinte só por sortear outras. Agora são 120, sempre de
outro tema. **Os dois juízes juntos aprovaram 6,7% (8 de 120)**, abaixo do limite de 10%. Caderno do
piloto: 598 de treino, 85 de prova, 14,95 por pedido (dados sha256 abfc5648…). Liberado para o
caderno completo com o ok do criador.
