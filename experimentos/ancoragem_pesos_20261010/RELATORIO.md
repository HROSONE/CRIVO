# Ancoragem dos pesos — 10/10/2026

Controle 1× e candidato ancorado usam o mesmo corpus, vocabulário realocado, arquitetura e hiperparâmetros. A única mudança do candidato é a regularização L2-SP dos pesos preservados. Os 151 índices lexicais realocados ficam livres em `E`, `O` e `bo`.

A força foi calibrada **sem validação**: 16 batches do treino no checkpoint controle, alvo de 25% da norma do gradiente de tarefa antes do Adam. `lambda = 0.004428901375`.

| Condição | CE antiga | Exatas antigas | CE nova | Exatas novas | CE total |
|---|---:|---:|---:|---:|---:|
| controle 1× | 0.943481 | 47/334 | 4.262217 | 1/94 | 1.387659 |
| 1× + âncora | 0.873541 | 43/334 | 4.636536 | 1/94 | 1.377179 |

## Critério pré-congelado

- Reter antigo: **não**.
- Melhorar CE nova: **não**.
- Não regredir exatas novas: **sim**.
- Sucesso conjunto: **não**.

## Integridade

- Holdout final conhecido do PR #137 lido: **não**.
- Promoção permitida nesta fase: **não**.
- Runtime/checkpoint público alterado: **não**.
- Arquitetura/parâmetros/modelos externos: **inalterados**.

## Limites

A avaliação usa desenvolvimento conhecido e autoral. Correspondência literal não mede naturalidade/compreensão. A calibração da âncora usa normas antes do Adam; o otimizador é adaptativo, portanto 25% é uma escala de gradiente, não uma razão garantida de deslocamento.
