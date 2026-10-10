# Ablação: realocação lexical × replay — 10/10/2026

Esta fase isola duas variáveis que mudaram juntas no PR #137. **O holdout final de 10 sessões não foi lido nem usado para selecionar nada.**

| Condição | Replay | Léxico | CE dev total | Exatas dev antiga | Exatas dev nova | OOV não copiável treino |
|---|---:|---|---:|---:|---:|---:|
| `original_sem_replay` | não | original | 1.791430 | 12/334 | 0/94 | 1339 |
| `original_com_replay` | sim | original | 1.253973 | 42/334 | 1/94 | 1339 |
| `realocado_sem_replay` | não | realocado | 1.828367 | 20/334 | 0/94 | 0 |
| `realocado_com_replay` | sim | realocado | 1.387659 | 47/334 | 1/94 | 0 |

## Efeitos pareados no desenvolvimento

Valores negativos em ΔCE são melhora; valores positivos são piora.

- **Realocação sem replay:** ΔCE = +0.036937.
- **Realocação com replay:** ΔCE = +0.133686.
- **Replay com léxico original:** ΔCE = -0.537457.
- **Replay com léxico realocado:** ΔCE = -0.440708.

## Limites

- A comparação usa apenas desenvolvimento conhecido; não reabre o holdout final.
- Correspondência literal mede reprodução do alvo, não pertinência semântica.
- O vocabulário original pode ter alvos não copiáveis; isso é parte da variável lexical, não erro ocultado.
- Nenhum checkpoint desta ablação é promovido ao chat; todos permanecem `aprovado: false` e `ativo_no_chat: false`.
