# Média das duas rodadas do v7c — plano fixado antes de medir (28/10/2026)

Pedido do criador: um 300M bom no chat; antes, "estuda em vez de aprender com os erros". Da leitura (Model Soups,
Wortsman et al., ICML 2022; WiSE-FT, CVPR 2022): a média dos pesos de modelos ajustados a partir da mesma base costuma
melhorar a robustez sem custo de inferência. O passo mais barato é testar isso no 46M que já existe.

**Pesos:** v7c rodada 1 (`d68bb3c26a65…`, passo 2.536) e rodada 2 (`e4067e3b4c97…`, passo 2.853, o do chat), os dois
da base 6a e dos mesmos dados. Média com α = 0,5, sem ajuste depois de ver resultado.

**Conferido na CPU (sem a régua):** distância relativa entre as rodadas de 0,036. A média responde normalmente: em 7
frases de teste, 5 iguais ao chat e 2 diferentes e adequadas ("tô muito cansado do trabalho" → "Imagino. Dia puxado cansa
o corpo e a cabeça. Conseguiu descansar um pouco?"). "legal e voce?" continua respondido como pergunta de identidade.

**Régua (a de sempre, contra o v7c do chat):** `comparar_v6.julgar_rodada` com urgência, nos mesmos blinds do v7c (dados
`gerar_v7c.py`, mesmo arquivo do professor), para a linha de base ser a da rodada 2 frase por frase. **Uma medida**:
a geração é gulosa e os pesos são fixos, e as duas rodadas da régua existem para a variação entre treinos.

**Notebook:** `notebooks/avaliar_media_v7c_colab.ipynb` (T4; sem treino). Passar não liga nada: ligar é decisão do
criador, depois da conversão para NumPy.
