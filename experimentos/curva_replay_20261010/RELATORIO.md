# Curva de replay — 10/10/2026

Mesma rede, mesmo léxico realocado, mesmo corpus novo, mesma validação e mesmos hiperparâmetros. 0× e 1× são checkpoints já congelados; **somente 2× foi treinado nesta fase**. O holdout final conhecido do PR #137 não foi lido.

| Dose | Treino | CE antiga | Exatas antigas | CE nova | Exatas novas | CE total |
|---:|---:|---:|---:|---:|---:|---:|
| 0× | 2700 | 1.265409 | 20/334 | 5.471622 | 0/94 | 1.828367 |
| 1× | 3699 | 0.943481 | 47/334 | 4.262217 | 1/94 | 1.387659 |
| 2× | 4698 | 0.799406 | 73/334 | 4.392715 | 1/94 | 1.280333 |

## Critério pré-congelado: 2× contra 1×

- Reter antigo: **sim**.
- Não regredir novo: **sim**.
- Melhorar CE nova: **não**.
- Sucesso conjunto: **não**.

## Limites

- Oversampling também aumenta o número de atualizações por época; esta fase mede a dose efetiva no procedimento atual.
- Correspondência literal é diagnóstico, não medida completa de naturalidade/compreensão.
- O desenvolvimento é conhecido; nenhum destes checkpoints pode ser promovido por esta fase.
- O holdout final de 10 sessões do PR #137 continua excluído e conhecido.
