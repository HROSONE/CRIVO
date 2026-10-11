# Análise pós-treino fatorial — 11/10/2026

O experimento confirma uma hipótese importante: a composição do corpus estava permitindo um atalho `família + turno -> forma de resposta`. Ao quebrar esse atalho, a mesma rede de 81.433 parâmetros, com o mesmo vocabulário de 720 entradas e a mesma quantidade total de treino, melhorou materialmente sem aumento de capacidade.

## Ganho causal observado

- NMI da abertura condicionada a família+turno caiu de **0,650** para **0,106**.
- NMI dos dois primeiros tokens caiu de **0,743** para **0,136**.
- Prefixos de dois tokens restritos a no máximo duas famílias caíram de **54,8%** para **0,0%**.
- Na validação antiga, CE caiu de **0,9435** para **0,7228** e reproduções exatas subiram de **47/334** para **64/334**.
- Na avaliação fatorial congelada de 96 exemplos, CE caiu de **3,3671** para **0,6580**, reproduções exatas foram de **0/96** para **22/96**, primeiro token de **5,2%** para **28,1%** e o placar semântico das seis operações de **5,2%** para **38,5%**.

Isso apoia a interpretação de que a falha dominante não era simplesmente falta de parâmetros: dados com fatores cruzados permitem à mesma arquitetura aprender melhor o ato de resposta.

## Onde ainda falha

O ganho não é uniforme entre as seis operações na avaliação fatorial final:

| Operação | Controle | Candidato fatorial |
|---|---:|---:|
| corrigir pessoa | 0/16 | **16/16** |
| guardar hipótese | 0/16 | **16/16** |
| pedir detalhe | 0/16 | **4/16** |
| recordar objeto | 2/16 | **1/16** |
| recordar pessoa | 3/16 | **0/16** |
| mensagem sem horário | 0/16 | **0/16** |

A saída `Não. Isso ainda é uma possibilidade.` continua dominando indevidamente diversos casos de recordar pessoa/objeto e pedir detalhe. Em mensagens sem horário, há confusão frequente com o ato de pedir esclarecimento.

Portanto o candidato **não está pronto para o chat** apesar de passar o portão experimental agregado.

## Regressão importante fora do novo recorte

Nos 94 exemplos conhecidos de sessões novas do experimento anterior, usados aqui apenas como diagnóstico:

- controle: CE **4,2622**, **1/94** exata;
- candidato fatorial: CE **7,1249**, **0/94** exata.

A acurácia do primeiro token sobe ligeiramente, mas a distribuição completa piora. Isso mostra que substituir integralmente o antigo bloco `sessao_completa` por seis operações fatoriais removeu parte da cobertura das famílias anteriores.

Esses 94 exemplos já são conhecidos e não podem virar um novo teste final. Servem apenas para mostrar a regressão e impedir uma promoção precipitada.

## Decisão

- `checkpoint_fatorial.json.gz`: **experimental**;
- `aprovado`: somente no recorte fatorial congelado;
- `ativo_no_chat`: **false**;
- nenhuma alteração no runtime;
- nenhuma promoção de pesos nesta fase.

## Próximo passo recomendado

O melhor próximo experimento continua sendo de **dados, não de arquitetura**:

1. manter o cruzamento fatorial que quebrou o atalho;
2. reintroduzir uma amostra balanceada do antigo bloco de sessões para evitar esquecimento das famílias anteriores, sem aumentar os 3.699 exemplos totais;
3. adicionar pares mínimos/contrastivos em que palavras parecidas apareçam com atos diferentes — por exemplo, `pessoa` em recordar e corrigir, `pedido` em esclarecer e escrever, possibilidade mencionada em contextos que não exijam resposta de hipótese — para impedir um novo atalho lexical;
4. congelar uma **nova avaliação prospectiva**, com famílias, formulações e combinações não vistas nesta rodada, antes do próximo treino;
5. exigir simultaneamente preservação da validação antiga, não regressão do conjunto conhecido de 94 e melhora no novo holdout prospectivo.

Só se um corpus misto/contrastivo bem controlado continuar falhando deve-se testar uma alteração de representação ou objetivo auxiliar. A evidência atual ainda indica que há ganho substancial disponível na composição dos dados.
