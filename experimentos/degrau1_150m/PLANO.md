# Degrau 1 — CRIVO de ~150M (plano, 20/10/2026)

Pedido do criador: "crescer ele aos poucos, com qualidade, deixando ele inteligente, eficiente […] até 1 bilhão ou
3 bilhões". Este é o primeiro degrau: **46M → ~150M**. Nada aqui vai para o chat sem passar na régua (seção 6).

## 1. Por que o degrau 1 é diferente dos próximos

Nos degraus seguintes (400M, 1B), o modelo **cresce a partir do anterior** (como a fase 6a fez de 17M para 46M,
`scripts/crescer_17m.py`, preservando a função). Neste degrau, duas mudanças valem mais se feitas agora, e as duas
impedem crescer a partir do 46M:

1. **Tokenizador de ~32 mil pedaços (hoje 8 mil).** A mesma frase vira menos tokens. Isso deixa o modelo mais rápido
   por palavra e faz caber mais conversa no contexto. Modelos maiores aproveitam bem um vocabulário maior. Trocar
   depois de 1B custaria muito mais.
2. **Arquitetura atual de modelos pequenos:**
   - RMSNorm;
   - posições por rotação (RoPE): o contexto pode crescer depois sem reaprender as posições;
   - MLP SwiGLU;
   - sem vieses;
   - embedding de saída amarrado à entrada.

   Rende mais inteligência pelo mesmo tamanho que a arquitetura GPT-2 de hoje.

Então o 150M é **treinado do zero, com os pesos próprios**. Os próximos degraus crescem a partir dele.

## 2. O modelo

| | hoje (46M) | degrau 1 |
|---|---|---|
| parâmetros | 46M | ~152M |
| dimensão × camadas × cabeças | 384 × 24 × 8 | 768 × 18 × 12 |
| vocabulário | 8.192 | 32.000 (BPE próprio, mesmos tokens especiais) |
| contexto | 1.024 | 1.024 (RoPE: dá para estender para 2.048 depois) |
| int8 no disco / na RAM do motor em C | 42 / ~63 MB | ~155 / ~230 MB |

## 3. Os dados

- **Pré-treino:** FineWeb-2 português (ODC-By, o mesmo da fase 6a) + corpus próprio + IDENTIDADE.md, na proporção da
  6a (70/30). São **3 bilhões de tokens** primeiro (≈ 20 por parâmetro). Se a perda ainda cair bem no fim,
  continua até 6 bilhões. A regra fica fixada antes de rodar (seção 6).
- **Tokens no Drive:** ~6 GB para 3 bi, ~12 GB para 6 bi. Os checkpoints têm ~1,8 GB cada. Precisa de espaço
  no Drive.
- **Conversa:** a receita que levou o v7c a passar, com o mesmo texto bruto re-tokenizado:
  - fase 6b (OASST2, legendas, acervo, identidade, lembranças);
  - fase 5 com substituição;
  - falas do v7c, incluindo as do professor, marcadas.

## 4. O que eu faço antes de você gastar GPU (sem GPU)

1. **Tokenizador:** treinar o BPE de 32 mil em amostra do FineWeb-2 + corpus próprio, e medir quantos tokens por
   palavra cai em relação ao de 8 mil. Os tokens especiais e o texto não podem injetar marcadores (o mesmo teste
   de hoje).
2. **Arquitetura** em `linguagem_profunda` (versão 2, sem mexer na versão 1, que está no chat). Teste de um modelo
   minúsculo na CPU: treina alguns passos, salva, carrega, gera.
3. **Motor em C** com a arquitetura nova. Conferir que dá as mesmas respostas do PyTorch, como no 46M (logits
   iguais e mesma escolha de palavra).
4. **Notebook de pré-treino** que retoma do checkpoint, ensaiado aqui com o modelo minúsculo.
5. **Teste novo de conversa de vários turnos** (seção 6), congelado antes de qualquer treino.

## 5. O que você faz

1. **(Opcional, mas é o que mais ajuda.)** Me mandar 3 a 5 conversas reais suas com o CRIVO, copiadas da tela como a
   do "Palarerepípedo". Elas viram o teste de vários turnos, nunca dados de treino.
2. **Pré-treino:** rodar o notebook em sessões de A100. Ele continua de onde parou.
3. **Conversa:** rodar o notebook de conversa, nas duas rodadas, como no v7c.

**Tempo estimado** (a partir da medida real da 6a: 46M leu 3,6 bi de tokens em 3h20 numa A100):

| etapa | A100 | L4 (~3× mais lenta) |
|---|---|---|
| pré-treino, 3 bi de tokens | ~9 a 12 h | ~30 h |
| pré-treino até 6 bi (se continuar) | +9 a 12 h | +30 h |
| conversa, 2 rodadas | ~3 a 4 h | ~10 h |

É uma estimativa, e o notebook mede o ritmo real logo nos primeiros minutos.

## 6. A régua (fixada antes de rodar)

**Depois do pré-treino** (sem conversa ainda):
- **Perda em bits por caractere**, que dá para comparar entre tokenizadores diferentes, no texto separado da web e
  do corpus próprio. Precisa ficar **abaixo do 46M da 6a** nas mesmas frases.
- Continuar de 3 para 6 bi: só se a perda ainda cair ≥ 0,01 bit/caractere nos últimos 10% dos passos.

**Depois da conversa**, contra o v7c que está no chat, nas mesmas frases e nas duas rodadas:
- os critérios do v7c: blind v3 com IC > 0, outros blinds ≥ −1,5, frases reais ≥ 12/15, usa o fato ≥ 0,85,
  urgência ≥ a do chat;
- **mais o teste novo de vários turnos:** conversas reais suas, com as respostas aceitáveis em cada turno marcadas
  antes. O degrau 1 precisa acertar mais turnos que o v7c, e não pode inventar nome ou fato que não foi dito
  (o "seu pai"). Hoje nenhuma régua mede isso, e é o que mais incomoda conversando com ele.

Se não passar, nada vai para o chat. O resultado fica registrado com os limites, como nos outros.

## 7. Riscos que já sei

- **Site (Vercel):** a função tem limite de tamanho (~225 MB). O 150M em int8 tem ~155 MB. Para caber, o site talvez
  precise tirar o 46M e a v4 F do pacote, e confiro isso antes. No app e no PC não há esse limite.
- **Celular:** o 150M faz ~3 vezes mais conta por palavra que o 46M. Com o motor em C, a estimativa é de alguns
  segundos por resposta num celular médio. Medir no aparelho faz parte do degrau. Se ficar lento, o próximo passo do
  motor é int8 também nas contas (não só nos pesos).
- **Do zero:** as primeiras horas de pré-treino ainda são piores que o 46M. A comparação justa é no fim.
- **Tamanho não resolve tudo:** 150M segue a conversa melhor que 46M, mas ainda erra bastante. O teste de vários
  turnos é o que diz se o degrau valeu.

## 8. Depois do degrau 1

- **Se passar:** degrau 2 (~400M), crescendo a partir do 150M (camadas e largura, preservando a função), mais texto.
- **Se não passar:** o resultado diz o porquê (leitura, conversa ou tamanho), e decidimos antes de gastar mais GPU.
