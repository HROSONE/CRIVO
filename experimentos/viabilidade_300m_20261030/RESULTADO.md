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
