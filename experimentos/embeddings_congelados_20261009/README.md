# Ablação da matriz compartilhada

Protocolo e código congelados em `a07ca8e`, antes dos treinos. Mesmos pesos
próprios 2,6M, currículo, replay, sorteios, LR e 30.000 tokens-alvo. Um braço
ajusta todos os parâmetros; o outro congela `embedding.weight`, também usado
na projeção de saída. Ambos concluíram 153 atualizações.

Leitura autoral dos mesmos 12 diálogos de desenvolvimento: **0/12 sessões
adequadas em ambos**. Trocam entidades e assuntos ou não executam o pedido.
Os casos já foram usados no desenvolvimento anterior; não são independentes.
O congelamento exato foi verificado nos tensores salvos; o controle alterou
a matriz. Congelar sozinho não resolve neste orçamento. Isso não refuta
combinações com cópia aprendida ou supervisão de fontes, nem aprova essas ideias.

`avaliacao/` conserva respostas, entradas reais e avaliação. Relatórios ficam
nos diretórios de cada condição. O treinador durável preserva também o último
estado, otimizador e RNG, além do checkpoint escolhido por validação. Pesos
ficam locais, ignorados no Git. Nenhum foi integrado ao chat.

Pesquisa e decisão em `docs/planos/crivo_conversa_20261009_resultados.md`.
