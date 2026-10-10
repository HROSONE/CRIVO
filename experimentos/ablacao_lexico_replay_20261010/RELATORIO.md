# Ablação: realocação lexical × replay — 10/10/2026

Esta fase isola duas variáveis que mudaram juntas no PR #137. **O holdout final de 10 sessões não foi lido nem usado para selecionar nada.**

A entropia cruzada do desenvolvimento completo só deve ser comparada **dentro do mesmo léxico**. No léxico original, alvos não geráveis são colapsados em `<desconhecido>` pelo treinador, o que torna uma comparação direta de CE entre vocabulários enviesada. Para comparar os dois léxicos, o relatório usa também o subconjunto em que o alvo inteiro é gerável por ambos.

Suporte comum: **334** exemplos antigos + **47** novos = **381** exemplos.

| Condição | Replay | Léxico | CE dev completo* | CE suporte comum | Exatas antiga | Exatas nova | OOV não copiável treino |
|---|---:|---|---:|---:|---:|---:|---:|
| `original_sem_replay` | não | original | 1.791430 | 1.441263 | 12/334 | 0/94 | 1339 |
| `original_com_replay` | sim | original | 1.253973 | 1.011271 | 42/334 | 1/94 | 1339 |
| `realocado_sem_replay` | não | realocado | 1.828367 | 1.496598 | 20/334 | 0/94 | 0 |
| `realocado_com_replay` | sim | realocado | 1.387659 | 1.124344 | 47/334 | 1/94 | 0 |

\* CE completa é comparável apenas entre as duas linhas do mesmo léxico.

## Efeitos pareados válidos

Valores negativos em ΔCE são melhora; positivos são piora.

- **Realocação sem replay, no suporte comum:** ΔCE = +0.055335.
- **Realocação com replay, no suporte comum:** ΔCE = +0.113073.
- **Replay com léxico original, desenvolvimento completo:** ΔCE = -0.537457.
- **Replay com léxico realocado, desenvolvimento completo:** ΔCE = -0.440708.

## Leitura

- O replay pode ser avaliado diretamente porque cada comparação mantém o mesmo vocabulário.
- A realocação deve ser julgada pelo suporte comum, cobertura e geração livre; não pela CE total cruzada entre léxicos.
- A realocação remove alvos não copiáveis do treino, mas reinicializa 151 entradas e suas colunas de saída; os dois efeitos competem.

## Limites

- A comparação usa apenas desenvolvimento conhecido; não reabre o holdout final.
- Correspondência literal mede reprodução do alvo, não pertinência semântica.
- Nenhum checkpoint desta ablação é promovido ao chat; todos permanecem `aprovado: false` e `ativo_no_chat: false`.
