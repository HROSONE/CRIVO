# Auditoria de atalhos no corpus — 10/10/2026

Sem treino e sem leitura de pesos. Analisa apenas a composição do corpus de sessões.

## Informação que a identidade da família fornece sobre a saída

| Alvo | Condição | H(Y) | H(Y|X) | NMI |
|---|---|---:|---:|---:|
| abertura | familia | 4.731 | 3.114 | **0.342** |
| abertura | turno | 4.731 | 4.177 | **0.117** |
| abertura | familia_turno | 4.731 | 1.655 | **0.650** |
| prefixo2 | familia | 7.593 | 4.095 | **0.461** |
| prefixo2 | turno | 7.593 | 6.062 | **0.202** |
| prefixo2 | familia_turno | 7.593 | 1.954 | **0.743** |

## Pureza majoritária

- `abertura_por_familia`: **26.5%** (32 grupos).
- `abertura_por_familia_turno`: **45.2%** (192 grupos).
- `prefixo2_por_familia`: **13.3%** (32 grupos).
- `prefixo2_por_familia_turno`: **40.1%** (192 grupos).

## Cruzamento entre famílias

- Famílias de sessão no treino: **32**.
- **1472/2686 (54.8%)** exemplos usam prefixo de 2 tokens presente em no máximo duas famílias.
- No desenvolvimento novo, **59/94 (62.8%)** têm abertura alvo suportada por menos de 3 famílias de treino no mesmo turno.
- Aberturas totalmente sem suporte no treino: **27/94**; prefixos de 2 tokens totalmente sem suporte: **64/94**.

## Baseline superficial da mensagem atual

- Jaccard top1 com mesma abertura: **11/94**.
- Algum dos top5 Jaccard com mesma abertura: **13/94 (13.8%)**.

## Flags pré-congeladas

- atalho_familia_turno_forte: **sim**.
- prefixos_pouco_cruzados: **sim**.
- suporte_cross_family_novo_baixo: **sim**.
- texto_superficial_nao_resolve: **sim**.

A auditoria mede correlação estrutural do corpus; não prova que a rede use causalmente cada atalho.
