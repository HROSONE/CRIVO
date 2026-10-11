# Análise da aula contrastiva multivista

## Resultado principal

A intervenção foi reprovada para promoção.

Comparada à primeira turma da Escola Cognitiva (#148), a classificação auxiliar generalizou pior:

- professor **AÇÃO**: dev caiu de **25,0%** para **18,8%**;
- professor **FOCO**: dev caiu de **45,8%** para **35,4%**.

A geração preservou parte do ganho anterior:

- old334: **69/334**, CE **0,708**;
- fatorial96: **47,9%** das operações;
- holdout #148: **51,4%** das operações.

Mas continuou falhando na transferência mais difícil:

- known94: **0/94**, CE **7,156**;
- holdout #146: **38,9%**;
- prova prospectiva nova de 180 casos: **33,9%** das operações, primeiro token **21,7%**, CE **1,101**.

## O que aprendemos

Dividir o mesmo peso auxiliar entre a entrada real e uma segunda entrada sintética/anônima **não ensinou invariância**. A hipótese mais compatível com os resultados é que a cabeça passou a aprender duas superfícies diferentes, em vez de obrigar o mesmo estado semântico a permanecer estável entre elas.

Isso é especialmente importante porque o peso total, o corpus de geração, a seed, os hiperparâmetros, a arquitetura e os 81.433 parâmetros de produção permaneceram fixos. Portanto, a piora não veio de aumento de capacidade ou troca de modelo; veio do método de supervisão auxiliar.

## Próxima hipótese recomendada

Não classificar a vista sintética.

Manter a classificação `AÇÃO` e `FOCO` apenas sobre a entrada real e usar a segunda vista somente como **restrição de consistência da representação**:

1. codificar a entrada real;
2. codificar a mesma situação com identidades/superfície perturbadas;
3. puxar os dois estados internos para perto quando representam o mesmo conceito;
4. usar exemplos de conceitos diferentes como negativos para evitar colapso;
5. manter o mesmo lambda auxiliar total e os mesmos 81.433 parâmetros serializados;
6. descartar todo o aparato de ensino antes da inferência.

A diferença conceitual é importante: o professor deixa de dizer “acerte esta classe também nesta frase artificial” e passa a dizer “essas duas formas diferentes devem significar a mesma coisa internamente”.

Nenhum checkpoint desta aula deve ser ativado automaticamente.
