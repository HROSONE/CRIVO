# Teste: um só modelo de 46 milhões classifica e escreve

## Pergunta do teste
O modelo de 46 milhões (v4, do repositório) aprende a dizer o tipo e o alvo de uma pergunta
quando isso faz parte da própria resposta, e continua conversando bem?

## Ponto de partida (19/10/2026)
- Modelo: `artefatos/conversa46m_v4_pt/pesos_numpy.npz` (v4, 24 camadas, contexto 1024).
- Régua de classificação (12 exemplos da semente, nunca usados para ajustar): **0/12**.
  O modelo atual não produz o rótulo.
- Velocidade em CPU: carrega em ~2 s e responde em ~0,1 s por pergunta.

## Formato de treino
Mesmo formato da conversa do 46M, com o rótulo como resposta:

    <documento> nada <fim> <usuario> {pergunta} <fim> <assistente> tipo: {tipo}; alvo: {alvo} <fim>

Assim o modelo aprende a classificar no mesmo passo em que conversa.

## Mistura de dados (evita esquecer a conversa)
- Exemplos de classificação: os exemplos gerados com status `ok` (divisão `treino`).
- Conversa original da fase 6b (a mesma usada na v4), na mesma proporção que a v4 usou.
- Nenhum exemplo da régua (semente `regua`, e a divisão `regua_gerada`) entra no treino.

## Medidas
1. **Classificação:** acerto do tipo e do alvo na régua da semente (12) e na `regua_gerada` (cerca de 10% dos exemplos gerados).
2. **Conversa (regressão):** a régua de compreensão (`avaliacoes/regua_compreensao_v1`, 55 casos) e as frases reais do criador.
   O modelo não pode piorar nelas.
3. **Resposta completa:** o rótulo e a resposta em português devem sair juntos. Medida à parte.

## Regra de decisão
- Passa se: classificação ≥ 0,90 na régua de classificação, e a régua de conversa não cair mais de 2 casos em relação ao baseline.
- Não passa: qualquer queda grande na conversa, mesmo com boa classificação. Nesse caso o modelo não vai para o chat.
- Em qualquer caso, a decisão de levar ao chat exige a régua própria e o ok do criador.

## O que ainda falta para rodar
1. Gerar os exemplos no Colab (pedidos em `compreensao_semantica/geracao/`).
2. Validar e revisar uma amostra (`validar_saida.py`).
3. Treinar no Colab, adaptando o caderno de treino da v4 (`notebooks/fase6b_v4_conversa_sentido_colab.ipynb`),
   com a mistura acima. O treino precisa de PyTorch e de GPU; o modelo aqui roda só em NumPy, para medir.
