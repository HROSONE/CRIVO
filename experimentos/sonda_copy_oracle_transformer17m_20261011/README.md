# Sonda copy-oracle do Transformer 17,43M

Diagnóstico **sem treino** sobre V4 e V5 congeladas. Usa o mesmo holdout prospectivo de 120 casos da auditoria pareada (`55fab7f65ded87c721fe44bf84d6b69a1153c32caa3675feb95ce1a7887707f0`).

## Pergunta

A recuperação já encontra parte das entidades, mas a geração erra muitos tokens dentro dessas entidades. Quanto do erro desapareceria se existisse uma rota explícita de cópia da fonte para a saída?

## Dois limites

1. **pointer atual** — um token de entidade só pode ser corrigido quando o pointer V4/V5 aponta exatamente o início do span correto e o ID BPE esperado existe naquele span.
2. **span correto (oracle)** — limite superior: conhece qual span é o correto, mas ainda só pode copiar IDs de tokens que realmente existem nesse span da fonte.

Fora dos tokens de entidade o Transformer permanece inalterado. Na geração livre, o oracle só interfere enquanto a saída ainda está alinhada ao prefixo-alvo; depois da primeira divergência não relacionada à cópia, volta integralmente ao modelo original.

A sonda mede teacher forcing e geração greedy, operação, slot, resposta exata, extensão de prefixo e recuperação da primeira divergência. Resultado positivo não autoriza promoção nem cria checkpoint novo; serve apenas para decidir se uma cabeça de cópia própria do CRIVO merece ser o próximo experimento controlado.
