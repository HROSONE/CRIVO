# Compreensão neural própria (05/10/2026)

## O problema

O CRIVO tinha um classificador neural de 611 intenções ligado, mas ele **nunca
decidia nada sozinho**: só confirmava a escolha do recuperador por palavras.
Quando as regras não entendiam, a rede era ignorada e o CRIVO dizia "não entendi".

Medi o que aconteceria se esse classificador pudesse decidir. Ele não acertaria
nenhuma das perguntas que hoje recebem "não entendi" e inventaria respostas
confiantes para perguntas fora do acervo. "Quanto custa um apartamento em São
Paulo?" iria para Grandes Navegações (82%), e "Como trocar o pneu da bicicleta?"
para reciclagem (81%). O motivo é que ele nunca aprendeu a recusar: só viu
perguntas que têm resposta.

Os motores que **escrevem** (o Transformer próprio de 16 M e o diálogo contextual)
continuam desligados. Eles já foram medidos e pioram a conversa: o contrato cai
de 42/72 para 33/72 com o Transformer.

## O que foi feito

`entendimento_neural.py` traz uma rede nova, treinada do zero em NumPy por
`scripts/treinar_entendimento.py`, sem pesos ou vocabulário externos.

- **Entrada:** n-gramas de palavras, pares de palavras e n-gramas de 3 a 5 letras,
  com hash (2¹⁵ posições). Isso tolera erros de digitação e fala informal ("vc",
  "pra", "ap").
- **Arquitetura:** soma das características, camada oculta ReLU de 128 neurônios e
  softmax sobre **664 rótulos**. São 611 intenções da base, os conceitos do
  acervo expandido e a classe **`fora`**, para perguntas que o CRIVO não sabe
  responder.
- **Dados:** gerados do próprio acervo, de forma determinística.
  - Positivos: perguntas da base com variações, erros de digitação e cortesias, e
    nomes e apelidos dos conceitos em modelos de pergunta.
  - Classe `fora`: preços, lugares, esportes, receitas, documentos e serviços, e
    **quase-acertos** que citam um conceito conhecido mas pedem outra coisa
    ("quanto custa {conceito}", "qual o telefone de {pessoa}").
  - Regularização: descarte aleatório de 25% das características, suavização de
    rótulos de 0,05 e 6 épocas.
- **Guarda de vocabulário:** quando o nome do assunto aparece na pergunta, o resto
  precisa caber no vocabulário desse assunto ou em palavras genéricas de pergunta.
  "Qual o signo de Isaac Newton?" cita Newton, mas "signo" não aparece em nada
  sobre ele, então a rede não decide.
- **Integração:** a rede só é consultada quando o CRIVO responderia "não entendi"
  (`fora`, `social:nao_entendido`, `conversa:esclarecer`), nunca em perguntas com
  negação, e só decide acima do limiar validado. Ela não escreve a resposta:
  aponta o assunto, e o CRIVO responde pela pergunta canônica dele, com as fontes
  e verificações de sempre. A API informa `mechanism: "compreensao_neural"` e
  `neural_understanding` (assunto, pergunta canônica e confiança).
- **Sem NumPy ou sem pesos aprovados**, a rede fica desligada e o CRIVO segue
  como antes.

## Medição

**Validação**, gerada com modelos e preenchimentos próprios e usada para escolher
o limiar:

- 1232 de 1514 perguntas conhecidas certas (81%) e 23 assuntos errados (1,8% das
  aceitas);
- **0 de 96** perguntas fora do acervo aceitas.

O controle exige no máximo 3% de erro entre as aceitas, no máximo 2% de fora
aceitas e pelo menos 50% de cobertura. A primeira rodada foi reprovada: "signo
de Newton" passava com 100% de confiança. A guarda de vocabulário e os
quase-acertos corrigiram isso.

**Teste congelado** (`avaliacoes/entendimento_v1/teste.json`), escrito à mão antes
do treino e nunca usado nele:

| | CRIVO sem a rede | Com a compreensão neural |
|---|---|---|
| Perguntas conhecidas em formulações novas | 45/75 | **53/75** |
| Perguntas fora do acervo recusadas | 49/55 | 49/55 |

- A rede decidiu 9 vezes e acertou 8. O erro: "como faço uma condição se senão
  em python" foi para `while` em vez de `if`.
- Ela não aceitou nenhuma pergunta fora do acervo. As 6 falhas de recusa são do
  recuperador antigo ("onde fica a farmácia mais perto" → planeta mais quente) e
  já existiam.
- As 467 perguntas de exemplo da base vão para o mesmo destino de antes.
- Depois dessa medição, testei deixar a rede agir também em pedidos de
  esclarecimento (`duvida`, `contexto:sem_referencia`). Não mudou nada (53/75), e
  a mudança foi desfeita.

`testes_entendimento_neural.py` inclui uma catraca no teste congelado: os números
só podem melhorar.

## Limites

- A rede reconhece **qual assunto** foi pedido; não compreende a frase como um
  modelo de linguagem grande nem escreve respostas. A conversa livre continua
  dependendo do gerador, que segue desligado até passar nos critérios dele.
- Ela só ajuda quando as regras dizem "não entendi". Quando as regras respondem
  errado ("sujei a camisa de molho de tomate" → regar plantas), ela não é
  consultada.
- Paráfrases sem nenhuma palavra em comum com o acervo ("bicho mais veloz" para
  "animal mais rápido") seguem difíceis: as características são de forma, não de
  significado. Vetores de palavras melhores seriam o próximo passo; os atuais estão
  desligados no controle de qualidade.
- A validação é sintética, gerada por modelos. O número que vale é o do teste
  congelado, que é pequeno (130 perguntas).

## Reproduzir

```bash
python scripts/treinar_entendimento.py --saida artefatos/entendimento_pt   # ~5 min em CPU
python scripts/avaliar_entendimento.py --detalhes
```
