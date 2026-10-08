# Leitor revisado v2

Este experimento continua o leitor próprio de 17.428.609 parâmetros. Ajusta
somente os **385 parâmetros da cabeça linear**. As oito camadas, os embeddings
e o tokenizador ficam idênticos aos pesos anteriores. Nenhum modelo de terceiro
foi utilizado.

O papel do leitor é escolher qual fato de uma ficha responde a uma pergunta e
separar perguntas respondíveis de perguntas sem resposta. Não é um gerador de
conversa.

## Problema do ajuste anterior

O treino anterior executou 1.000 passos, mas nenhum candidato cumpriu o critério
de seleção. O ZIP conservou os 86 conjuntos de parâmetros anteriores, verificados
por igualdade de arrays. Isso não permite concluir que os pesos do último passo
não tenham mudado: esse checkpoint tem 98 MB e não foi inspecionado localmente.

Foram encontradas perguntas sintéticas malformadas e exemplos negativos gerados
por troca aleatória de assunto. Esses rótulos não garantem ausência de resposta.
São hipóteses de causa, não uma ablação que comprove por que o treino falhou.

## Protocolo novo

As 226 perguntas revisadas do tutor, sobre 62 assuntos, fornecem supervisão.
Cinco blocos externos separam os assuntos entre ajuste e validação. A intensidade
da regularização é escolhida em quatro blocos internos também separados por
assunto. O modelo original é o mesmo em todas as comparações.

A representação do Transformer é extraída uma vez e armazenada com assinatura
dos pesos, corpus, tokenizador, código e versão do PyTorch. A cabeça aprende
competição entre fatos da mesma ficha e uma opção sem resposta, com penalização
do afastamento da cabeça anterior. A regularização final é a mediana das
seleções internas, não uma escolha baseada nos controles congelados.

Os controles v1 e v2 não compartilham assuntos nem perguntas com a supervisão.
Só foram medidos depois de congelar os candidatos. Publicam-se agregados;
perguntas ou erros individuais desses controles não orientaram alterações.

## Resultados do leitor isolado

| Controle | Original | Cabeça revisada |
| --- | --- | --- |
| Desenvolvimento por assunto, acertos | 89/161 (55,28%) | 97/161 (60,25%) |
| Desenvolvimento por assunto, AUC | 0,714 | 0,757 |
| Congelado v1, acertos | 22/50 (44%) | 30/50 (60%) |
| Congelado v1, AUC | 0,509 | 0,659 |
| Congelado v2, acertos | 17/48 (35,42%) | 25/48 (52,08%) |
| Congelado v2, AUC | 0,573 | 0,745 |

No desenvolvimento, 26 respostas foram corrigidas e 18 regrediram. O intervalo
de 95% do ganho, reamostrando assuntos, inclui zero (-1,19 a +11,04 pontos).
Por isso o primeiro controle, sozinho, foi tratado como preliminar. Os dois
controles independentes mostram ganho de acerto e AUC, mas são amostras pequenas
e a acurácia absoluta ainda exige evolução.

Também foram ajustadas as duas últimas camadas com a mesma supervisão. Esse
candidato alcançou 101/161 acertos, mas baixou a AUC de desenvolvimento de 0,714
para 0,686. Foi rejeitado antes de decidir pela cabeça revisada. Seus agregados
nos controles constam do relatório, sem selecionar novamente pelo teste.

## Limite para uso no chat

O combinador foi avaliado com cabeças treinadas dentro de cada bloco, sem usar
uma cabeça ajustada no assunto que estava sendo validado. Com o leitor anterior,
entregou 78 fatos certos e cometeu 1 erro nas afirmações. Com a cabeça revisada,
entregou 76 e cometeu 0. O ganho isolado do leitor **ainda não atende o critério
de promoção do Crivo**, que exige maior cobertura sem mais erros.

Os pesos ficam com `controle.aprovado: false`. A avaliação do chat é isolada em
memória e não instala pesos experimentais nem muda os artefatos ativos. O caderno
reproduz o ajuste em CPU; não exige repetir o pré-treino nem os 1.000 passos
anteriores. Relatórios registram as versões e assinaturas efetivamente usadas.

No chat completo, o congelado v1 permaneceu em 33 respostas certas; o v2 caiu
de 22 para 21. Os erros permaneceram iguais. **O leitor isolado melhorou, mas a
integração atual não entrega esse ganho ao usuário.** Nenhum artefato ativo foi
alterado. O modo padrão do Colab monta os novos pesos já treinados; a reprodução
do treino e das avaliações é opcional.
