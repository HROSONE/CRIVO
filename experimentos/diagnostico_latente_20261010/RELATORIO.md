# Diagnóstico latente do primeiro token — 10/10/2026

Sem treino. Sonda o checkpoint 1× no estado após o primeiro passo do decoder (`h` + contexto de atenção, 72 dimensões).

| Recorte | N | Top1 alvo | Acurácia | Rank mediano | Alvo top5 | P(alvo) média |
|---|---:|---:|---:|---:|---:|---:|
| treino | 3699 | 1998/3699 | 54.0% | 1.0 | 3192 | 0.3468 |
| dev antiga | 334 | 133/334 | 39.8% | 2.0 | 250 | 0.3061 |
| dev nova | 94 | 10/94 | 10.6% | 7.0 | 41 | 0.1047 |

## Vizinhança latente

- Dev nova: top5 contém ao menos um exemplo de treino com a mesma abertura alvo em **17/94** (18.1%).
- Dev antiga: mesma medida = **196/334** (58.7%).
- Quando a dev nova tem vizinho top5 com abertura correta, a cabeça ainda erra o primeiro token em **11/17** (64.7%).
- Margem cosseno média do melhor vizinho com mesma abertura menos melhor abertura diferente: **-0.0699**.

## Separação no desenvolvimento novo

- Cosseno intra-família: **0.7833**; inter-família: **0.6981**; Δ = **0.0852**.
- Cosseno mesma abertura alvo: **0.7287**; abertura diferente: **0.7180**; Δ = **0.0107**.

## Gate gerar × copiar no dev novo

- `fonte_disponivel`: n=32, gate gerar médio **0.7801**, mediana **0.8148**.
- `geracao_lexical`: n=62, gate gerar médio **0.8855**, mediana **0.9766**.

## Flags pré-congeladas

- gap_primeiro_token_novo: **sim**.
- gap_acuracia_antiga_menos_nova: **0.2918**.
- vizinhanca_nao_transfere_abertura: **sim**.
- cabeca_falha_mesmo_com_vizinho_correto: **sim**.
- gate_pouco_condicionado: **não**.
- delta_gate_lexical_menos_fonte: **0.1055**.
- familia_latente_separavel: **sim**.

## Limites

- Cosseno de um estado de 72 dimensoes nao prova semantica geral.
- Familias do desenvolvimento sao conhecidas e servem apenas para diagnostico.
- Primeiro token e uma sonda local; nao mede sozinho qualidade da resposta inteira.
