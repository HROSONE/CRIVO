# Integração candidata — CRIVO conversa V6 r0

Estado: **preparação; não promovida para o chat, site ou APK**.

## Artefatos identificados

- Notebook de treino: `fase6b_v6_r0_colab_corrigido.ipynb`.
- Pasta no Drive: `CRIVO/transformer-crivo-46m-conversa-v6-r0/conversa_20261015_201812/`.
- Checkpoint: `pesos.pt`; passo escolhido: **1890**.
- SHA-256 do checkpoint registrado no resumo: `673359b6342a2263c7d1f005de7591add76246fa63b155f02c7b5ee03a4d827f`.
- Configuração: vocabulario 8192, dimensão 384, 24 camadas, 8 cabeças, contexto 1024.
- Tokenizador e `formato_fase6.py` são copiados para a pasta do checkpoint.
- O resumo declara `ativo_no_chat: false`.

## Validação disponível no resumo do treino

Os resultados são sinais de pesquisa, não uma aprovação para produção:

- Sentido no blind v3: **63,49%** (2.980 casos).
- Paráfrases: **70,43%** (3.000 casos).
- Blind Grok: **70,77%** (2.980 casos).
- Blind v4: **90,0%** (600 casos).
- Frases reais do criador: **10/15 corretas**.
- Sem freio, blind v3: **64,33%**; frases reais: **10/15**.

Os resultados existentes do CRIVO e da V6 precisam ser comparados com os **mesmos casos, o mesmo contexto, o mesmo gerador, o mesmo freio e o mesmo avaliador** antes de qualquer decisão. O resumo do treino, sozinho, não comprova superioridade sobre a versão atualmente servida.

## Regras de integração

1. Não substituir os pesos, tokenizador, realizador ou voz atuais.
2. Não habilitar a V6 por variável de ambiente nem por detecção automática de arquivos.
3. Obter os bytes do checkpoint diretamente do Drive e verificar o SHA-256 acima antes de exportar.
4. Exportar os pesos para o formato NumPy compatível com o site e com o empacotamento offline do APK; verificar equivalência de logits/top-1 contra PyTorch numa amostra fixa e registrar tolerâncias.
5. Implementar o carregador V6 como candidato isolado, com validação de SHA, configuração, tokenizador e formato; em qualquer falha, manter o caminho atual.
6. Rodar a comparação cega pareada e testes de regressão do site, endpoint, crise/urgência, memória, respostas factuais e APK offline.
7. Promover somente se os critérios de aceitação forem satisfeitos. Caso contrário, manter a V6 disponível apenas para avaliação.

## Bloqueio atual

O resumo e o notebook de treino estão disponíveis, mas o arquivo binário `pesos.pt` e o tokenizador real da pasta de saída do Drive não estão acessíveis nesta execução. Sem esses bytes não é possível verificar o SHA no conteúdo real, exportar os pesos, testar a equivalência NumPy/PyTorch nem empacotar a V6 no site/APK. **Este documento não afirma que a integração foi concluída.**
