# Conclusão da ablação léxico × replay — 10/10/2026

## Resposta que esta fase conseguiu dar

A ablação separou, **somente no desenvolvimento já conhecido**, as duas variáveis que tinham mudado juntas no PR #137: realocação de 151 entradas lexicais e replay legado. O holdout final de 10 sessões do PR #137 não foi lido nem usado nesta fase.

| Condição | CE dev total | Exatas antigas | Exatas novas | OOV não copiável no treino |
|---|---:|---:|---:|---:|
| original, sem replay | 1,791430 | 12/334 | 0/94 | 1.339 |
| original, com replay | 1,253973 | 42/334 | 1/94 | 1.339 |
| realocado, sem replay | 1,828367 | 20/334 | 0/94 | 0 |
| realocado, com replay | 1,387659 | 47/334 | 1/94 | 0 |

### 1. Replay ajuda de forma consistente neste desenvolvimento

Mantendo o léxico original, adicionar replay reduz a CE em **0,537457** e aumenta correspondências antigas de **12 para 42/334**. Mantendo o léxico realocado, reduz a CE em **0,440708** e aumenta correspondências antigas de **20 para 47/334**.

Isso é evidência contra a hipótese de que o replay legado tenha causado sozinho a regressão do PR #137. Neste recorte ele funciona como proteção parcial contra esquecimento.

### 2. A realocação lexical tem um custo, mas não é simplesmente “ruim”

A realocação elimina **1.339 ocorrências / 151 tipos de alvos de treino que o vocabulário original não consegue gerar nem copiar**. Portanto ela resolve uma limitação real de cobertura.

Ao mesmo tempo, sua contribuição pareada piora a CE total em **+0,036937** sem replay e **+0,133686** com replay. Porém as correspondências antigas sobem 12→20 e 42→47. As métricas divergem; não é válido concluir que retirar a realocação por si só melhora a conversa.

### 3. O problema maior agora é estabilidade da adaptação

O relatório de sessões do PR #137 registra **107/334** correspondências literais antigas antes da nova adaptação. Nesta ablação, depois de treinar nas sessões variadas, a melhor condição chega a **47/334**. Além disso, nenhuma condição passa de **1/94** nas quatro famílias novas de desenvolvimento.

Isso aponta para dois problemas simultâneos:

- **esquecimento do comportamento anterior durante o treino novo**;
- **generalização muito fraca para famílias de sessão mantidas fora do treino**.

A ablação não prova a causa da falha semântica das 10 sessões finais e não reabre esse teste agora conhecido. Ela mostra que simplesmente retirar replay ou simplesmente voltar ao vocabulário antigo não resolve o problema.

## Decisão

Nenhum checkpoint desta fase será promovido. Todos permanecem `aprovado: false` e `ativo_no_chat: false`. O runtime, o checkpoint público e a arquitetura do CRIVO não foram alterados.

## Próximo trabalho único

Antes de inventar nova arquitetura ou aumentar parâmetros, medir uma **curva controlada de replay** mantendo fixos:

- a mesma realocação lexical de 151 entradas;
- a mesma arquitetura de 81.433 parâmetros;
- o mesmo corpus autoral de sessões;
- a mesma validação antiga/nova;
- seed e hiperparâmetros da rodada, salvo apenas a proporção de replay.

Comparar pelo menos três doses de replay, incluindo a dose atual, e selecionar por um critério pré-congelado que exija simultaneamente **retenção do desenvolvimento antigo e melhora do desenvolvimento novo**. Não usar o holdout final conhecido para escolher a dose.

Se aumentar replay recuperar o comportamento antigo sem aprender as famílias novas, o gargalo passa a ser generalização do treino de sessões; se recuperar ambos, a mistura de dados era o principal defeito da adaptação. Só depois dessa medição decidir se vale testar congelamento/ancoragem de pesos.

## Limites

- Correspondência literal não mede naturalidade nem compreensão semântica.
- CE agrega tokens e pode discordar da correspondência literal.
- O desenvolvimento é conhecido e autoral; serve para diagnóstico, não para alegar capacidade geral.
- A avaliação final de 10 sessões do PR #137 continua regressão conhecida e não pode voltar a ser apresentada como teste inédito.
