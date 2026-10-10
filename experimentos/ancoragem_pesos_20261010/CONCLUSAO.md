# Conclusão da ancoragem de pesos — 10/10/2026

## Veredito

A ancoragem L2-SP **não passou o critério pré-congelado**.

| Condição | CE antiga | Exatas antigas | CE nova | Exatas novas | CE total |
|---|---:|---:|---:|---:|---:|
| controle 1× | 0,943481 | 47/334 | 4,262217 | 1/94 | 1,387659 |
| 1× + âncora | 0,873541 | 43/334 | 4,636536 | 1/94 | 1,377179 |

A CE antiga melhora, mas a reprodução livre antiga cai de 47 para 43/334. Nas famílias novas, a CE piora fortemente e a reprodução permanece em 1/94. O ganho pequeno da CE total é dominado pelo bloco antigo maior e **não representa melhora conjunta**.

A força da âncora (`lambda = 0,004428901375`) foi calibrada sem olhar validação, a partir de 16 batches de treino no controle. Os 151 índices realocados permaneceram livres em `E`, `O` e `bo`, então o resultado não pode ser explicado simplesmente por prender os tokens novos à inicialização aleatória.

## O que esta sequência de experimentos mostrou

1. **Sem replay:** adaptação esquece fortemente comportamento antigo.
2. **Replay 1×:** reduz bastante o esquecimento, mas quase não generaliza às quatro famílias novas.
3. **Replay 2×:** preserva ainda mais o antigo, porém piora a CE nova.
4. **Replay 1× + L2-SP:** também desloca o modelo para retenção token a token e piora a CE nova.

Portanto o problema atual não é explicável apenas como falta de replay nem como deslocamento excessivo dos pesos preservados. Há evidência de um gargalo de **transferência/generalização**: o gerador aprende padrões presentes no treino, mas não transforma esse aprendizado em bom comportamento nas famílias inteiramente mantidas fora do treino.

## Decisão

- Não promover o checkpoint ancorado.
- Não aumentar força de ancoragem nesta frente.
- Não aumentar replay além de 2×.
- Não usar o holdout conhecido do PR #137 para escolher nova técnica.
- Preservar checkpoint público, runtime, memória, acervo, arquitetura e número de parâmetros.

## Próximo trabalho único

Antes de outro treino, fazer um **diagnóstico de transferência nas 94 respostas novas de desenvolvimento**.

O diagnóstico deve, sem alterar pesos:

1. medir por família e por posição do turno onde a CE explode;
2. separar tokens que exigem geração lexical de tokens copiáveis da fonte;
3. localizar o primeiro token em que a previsão diverge do alvo em geração livre;
4. comparar cada exemplo novo com os exemplos de treino mais próximos por estrutura textual, sem usar o alvo como entrada da rede;
5. repetir avaliação com histórico completo e sem histórico para distinguir falha de linguagem da falha de uso do contexto;
6. verificar se o problema está concentrado em léxico, forma de resposta, mudança de estado/referente ou dependência entre turnos.

Nenhum treino deve ser feito nessa fase diagnóstica. O resultado precisa apontar uma hipótese concreta antes da próxima mudança no gerador.

## Limites

- Desenvolvimento conhecido serve para diagnóstico, não para alegar capacidade nova.
- Correspondência literal não mede qualidade humana.
- Melhor CE total pode esconder regressão em um subconjunto menor; por isso antigo e novo permanecem separados.
- O holdout final de 10 sessões do PR #137 continua proibido para seleção e não volta a ser tratado como inédito.
