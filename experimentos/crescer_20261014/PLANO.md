# Fase 6 — o CRIVO crescer de verdade (14/10/2026)

**Pedido do criador:** "treine o crivo, mas não substitua ele. faça o que quiser para ele crescer de
verdade. menos deixar ele impossível de rodar na minha máquina com CPU e 8 GB de RAM [...] menos
colocar qwen, gemma, etc."

**Regras desta fase:**
- **Não substituir:** o CRIVO cresce a partir dos próprios pesos e do próprio tokenizador. Nenhum
  modelo de linguagem de terceiros entra: nem como peça, nem como professor, nem gerando dados.
- **Dados de texto abertos são permitidos,** como sempre foram (a Wikipédia já era usada).
- **Limite físico:** rodar em CPU com 8 GB de RAM.

## Diagnóstico que orienta tudo (análise de 14/10)

- O 17M é generativo no mecanismo, mas na prática escolhe: 98% das frases dele são cópias exatas
  de respostas do treino.
- O erro típico é ler errado (35% respondem com a situação errada), não falar mal.
- Três causas:
  - leu pouco: ~1 bilhão de tokens, com 17M parâmetros;
  - estuda listas fechadas de respostas;
  - a régua de sentido só aceita respostas da lista.
- Contexto de 256 tokens: lembra 2 a 3 turnos.

## Quanto cabe numa CPU (medido aqui, 4 núcleos, NumPy, KV cache)

| modelo | tokens/s | memória (pico) | int8 no disco |
|---|---|---|---|
| 17M (hoje) | 355 | 116 MB | 17 MB |
| 42M (d512, L12) | 193 | 222 MB | 42 MB |
| 84M (d640, L16) | 68 | 392 MB | 84 MB |
| 148M (d768, L20) | 54 | 650 MB | 148 MB |

Até ~150M roda folgado em 8 GB. No celular deve ser umas 3 a 5 vezes mais lento.

## Etapas

### 6a — crescer e ler (`notebooks/fase6a_crescer_ler_a100_colab.ipynb`)
- **Crescer:** a base de linguagem da fase 2 (`57e809f4…`) ganha 2 blocos novos depois de cada um
  dos 8 (`scripts/crescer_17m.py`). Os blocos novos começam como identidade: projeção da atenção e
  última camada do MLP em zero.
- **Contexto** de 256 para 1024: as posições novas começam como a última aprendida.
- **Conferido na CPU:** o modelo crescido (24 camadas, 46,1M) dá exatamente os mesmos logits que o
  original (diferença 0,00e+00).
- **Ler:** ~2,5 bilhões de tokens do FineWeb-2 português (ODC-By; texto da web escrito por pessoas,
  já filtrado), mais o corpus próprio em 30% dos lotes. ~55 mil passos de 64 × 1024 tokens,
  ~3,6 bilhões no total.
- **Medidas a cada 2 mil passos:** perda no corpus próprio (janelas de 256, a régua da base), perda
  na web separada, sonda de cópia.
- **Custo estimado:** 6 a 8 horas de A100, em sessões que retomam do checkpoint. Os tokens ficam no
  Drive (~5 GB).
- **Sucesso:** a perda no corpus próprio fica abaixo da base (2,946 na fase 2) e a cópia sobe dos
  ~51%. Essas são as metas fixadas antes de rodar.

### 6b — conversa que compõe, não que escolhe (a fazer, depois de 6a)
- **Respostas compostas no treino:** cada resposta montada de partes (reação, eco do que a pessoa
  disse, pergunta), com muitas combinações por situação. O modelo aprende a combinar, e não só a
  escolher entre 4 frases.
- **Uma régua que aceite resposta nova certa:**
  - um classificador próprio de "a que situação esta resposta serve" (treinado nas respostas
    compostas) substitui a lista exata;
  - a conferência de verdade continua (números, nomes, fatos).
- **Dados:** os da v4 (situações novas, correções e as conversas reais do criador como teste),
  reaproveitados no modelo crescido, com contexto de 1024.
- **Proteção:** o critério de segurança do dev passa a usar dezenas de casos, não 9 (lição da v4).

### 6c — entrar no CRIVO sem quebrar nada
- **Formato:** NumPy int8 (~46 MB), lido pelo mesmo `ConversaNumpy`, que já usa o número de camadas
  e o contexto do arquivo.
- **Site:** o pacote tem limite de 225 MB. O modelo novo cabe trocando a voz atual (16 MB) e
  passando as outras redes de 17M (geração, sentido, realizador) para int8, o que libera ~48 MB.
- **App:** cabe (o APK passa de ~210 para ~240 MB) e continua offline.
- **Entrada no chat:** pela catraca, ou por decisão do criador registrada como tal, como foi com a
  D e a F.
