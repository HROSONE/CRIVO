# Diagnóstico e decisão antes da correção

O conjunto foi congelado no commit adb6017, antes de mudar o consumidor.
No main ef2fafd, motor e API obtiveram 0/12 sessões e 2/25 solicitações.
Os dois acertos automáticos são recusas genéricas: também precisam ser lidos.
O roteador anterior recusou os oito primeiros pedidos de ajuda pessoal.
Suas 16 classes não incluem pedidos fora do escopo; o gerador antigo não
recebe as declarações nominais da memória atual.

Aplicação da skill insight-entidade-internet: havia uma lacuna concreta no
roteamento, não uma necessidade de ampliar o acervo. O estudo de
[Larson et al. (2019)](https://aclanthology.org/D19-1131/) distingue a
classificação de intenções conhecidas da detecção de pedidos fora do escopo.
Bom desempenho na primeira não assegura a segunda. A separação por cenários
também informa a avaliação: variações superficiais da mesma frase não são
um teste independente. Usaremos exemplos negativos e famílias separadas,
sem baixar dados ou pesos desse trabalho.

[Geifman e El-Yaniv (2017)](https://arxiv.org/abs/1705.08500) estudam a
troca entre cobertura e risco nas respostas aceitas. A mudança de plano é
medir ambos, conservando os limiares existentes de 0,80 e margem 0,20,
em vez de baixar a confiança para admitir perguntas novas. Não se aplicam
aqui as garantias estatísticas do artigo.

Hipótese de implementação: um roteador autoral separado, com classe fora,
pode reconhecer atos pessoais e entregar ao realizador os fatos ativos já
existentes. A seleção será estrutural e a escrita dos fatos continuará
ancorada e verificável. Não haverá novo coletor de memória nem promoção de
um modelo de geração livre. O conjunto de 12 sessões é desenvolvimento,
pois suas falhas foram inspecionadas; não será chamado de avaliação cega.
