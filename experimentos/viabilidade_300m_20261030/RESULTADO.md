# Um 300M cabe no chat? Medida de velocidade e memória (30/10/2026)

Pedido do criador: "um 300m bom no chat". Antes de gastar A100 treinando, medi se o motor do chat consegue rodar um
modelo desse tamanho. A velocidade só depende das formas dos pesos, então o 300M foi medido com pesos aleatórios no
formato do 7a (40 camadas, largura 768, 16 cabeças, vocabulário 8.192, contexto 1.024, 290,5M parâmetros), no mesmo
formato do chat (int8 por linha). O 46M é o v7c real (`artefatos/conversa46m_v7c_pt`).

Máquina: PC de mesa, 4 núcleos x86 (a do criador). Motor NumPy (`conversa_v3d.Conversa46mNumpy._passo`, o do site e
do celular hoje) e motor em C (`android/app/src/main/cpp/motor_crivo.c`, compilado com `-O3 -fopenmp`, 4 threads; no
celular ARM ele está desligado desde o #201). Resposta de 40 tokens, gulosa. Script: `medir_velocidade.py`.

| | prompt 150 tokens | prompt 400 tokens | por token gerado | memória (pico) | arquivo |
|---|---|---|---|---|---|
| 46M, NumPy | 1,9 s | 3,1 s | 0,034–0,042 s | 292 MB | 42 MB |
| 46M, C | 0,9 s | 2,0 s | 0,007–0,008 s | 140 MB | 42 MB |
| **300M, NumPy** | **7,0 s** | **12,3 s** | 0,13–0,16 s | **1.393 MB** | **291 MB** |
| **300M, C** | **4,6 s** | **11,6 s** | 0,034–0,040 s | 443 MB | 291 MB |

(tempos = ler o prompt + gerar 40 tokens)

## O que isso diz

- **O 300M é uns 4 vezes mais lento que o 46M no NumPy:** de 7 a 12 segundos por resposta neste PC, sem contar as novas
  tentativas que o chat faz quando a conferência reprova uma frase.
- **Site:** a função do Vercel tem limite de 20 s por resposta (`vercel.json`), e o pacote já leva ~205 MB de
  artefatos. O 300M acrescentaria 291 MB (o limite das funções Python é 500 MB; acima disso só com Fluid Compute) e
  1,4 GB de RAM no NumPy. A velocidade da CPU do Vercel não foi medida aqui.
- **Celular:** sem o motor em C (desligado no ARM), o NumPy precisaria de 1,4 GB de RAM e seria mais lento que neste
  PC. Mesmo com o motor em C, ler um prompt de 400 tokens leva 10 s aqui.
- **O motor em C lê o prompt devagar:** no 300M, 10 s para 400 tokens, mais lento que o NumPy (6 s). Ele gera bem (4
  vezes mais rápido que o NumPy por token), mas lê o prompt token a token. Ler o prompt em bloco (matriz × matriz) é a
  melhoria de engenharia que mais rende.

## Conclusão

Um 300M **não cabe no chat como ele é hoje**, nem no site nem no celular, sem antes:
1. ler o prompt em bloco no motor em C e validar o motor no ARM;
2. resolver o tamanho do pacote do site (o 300M sozinho ocupa mais que todos os artefatos de hoje);
3. ou mirar num modelo menor e mais profundo (o MobileLLM mostra que profundidade rende mais que largura nesse tamanho),
   que fique entre o 46M e o 300M em custo.

## Motor em C melhorado (30/10/2026)

Pedido do criador: "eu não posso treinar nada ainda. melhore o motor em c e faça caber". Três mudanças, todas com as
**mesmas contas** (logits idênticos, diferença 0,0, e as mesmas respostas nos testes):

1. **Ler o prompt em blocos** (`motor_crivo.c`, `tarefa_blocos`): cada thread passa 16 linhas de peso para float uma vez
   e as usa contra quatro posições por vez. Antes, cada linha de peso relia o prompt inteiro.
2. **Threads simples do sistema (pthreads) no lugar do OpenMP**: as threads nascem uma vez e esperam trabalho. O
   OpenMP estático dentro de uma biblioteca aberta pelo Python é um gatilho conhecido de queda ao criar threads no
   Android (possível causa da queda que desligou o motor no ARM; não confirmada sem um aparelho), e a biblioteca deixa
   de depender da libgomp (só libc, libm e libpthread), o que também abre caminho para usar o motor no servidor.
   Compilação: `-O3 -fopenmp-simd` (só vetoriza as somas, sem biblioteca).
3. **Não reler o começo da conversa** (`conversa_v3d.py`): o motor em C guarda quais palavras estão em cada posição
   do cache e, numa mensagem nova, só calcula a partir do primeiro ponto em que o texto muda. O NumPy reaproveita o
   cache do prompt anterior. A atenção de cada posição só olha as anteriores, então as contas são as mesmas.

**Medidas** (PC de 4 núcleos com a CPU disputada: Chrome e o controle térmico do Linux, `kidle_inject`, forçando pausas;
antes × depois alternados no mesmo processo, melhor de 4; `comparar_motores.py`):

| | antes | depois |
|---|---|---|
| 46M, ler 400 palavras | 2,9 s | 1,6 s |
| 46M, cada palavra gerada | 0,056 s | 0,017 s |
| 300M, ler 150 palavras | 3,7 s | 2,1 s |
| 300M, ler 400 palavras | 14,0 s | 7,0 s |
| 300M, cada palavra gerada | 0,049 s | 0,037 s |

Com a CPU disputada, o motor antigo ficava **mais lento com 4 threads que com 1** (0,061 contra 0,031 s por palavra no
46M); o novo acelera 3,1× no prompt e 1,4× por palavra com 4 threads.

**Conversa real de 6 turnos (46M v7c, exato, não depende do calor):** o motor calculou 143 palavras de prompt em vez de
972 (6,8× menos). Do segundo turno em diante, só a mensagem nova (10 a 13 palavras), mesmo com o prompt crescendo de 86
para 236. As respostas não mudaram.

**O 300M por mensagem, estimado com isso:** primeira mensagem ~86 palavras de prompt (~1,2 s) + 40 geradas (~1,5 s);
seguintes ~12 palavras + 40 geradas, uns 2 s. Antes: 7 a 12 s.

**Testes:** `testes_motor_nativo` 7/7 (com dois novos: a conversa que reaproveita o começo dá as mesmas respostas que
calcular do zero, no motor em C e no NumPy; um erro no motor esquece o cache). Estresse em C: 240 chamadas aleatórias
com 2, 3, 4 e 8 threads contra 1 thread, diferença 0; 200 aberturas e fechamentos sem travar. O ThreadSanitizer não
está instalado nesta máquina.

**O que ainda falta para o 300M caber de verdade:**
- **Celular:** o motor em C continua desligado no ARM (`crivo_app.py`) até ser conferido num aparelho. O teste é ligar
  `CRIVO_MOTOR_ARM=1`; a marca de abertura faz o app voltar ao NumPy se o motor derrubar o processo.
- **Site:** o site segue no NumPy (1,4 GB para o 300M). Com o motor sem libgomp, dá para levar a biblioteca compilada
  ao Vercel, mas isso precisa de um teste de publicação.
- **Pacote do site:** o 300M soma 291 MB aos ~205 MB de hoje (limite de 500 MB das funções Python).
