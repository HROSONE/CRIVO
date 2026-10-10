# Aprofundamento: onde o sinal de abertura se perde — 10/10/2026

Sem treino. Compara quatro representações do mesmo checkpoint 1×.

| Componente | Top5 abertura correta nova | Top5 antiga | Margem nova | Δ família nova | Δ abertura nova |
|---|---:|---:|---:|---:|---:|
| encoder_h | 15/94 (16.0%) | 70/334 (21.0%) | -0.0576 | 0.0131 | 0.0077 |
| decoder_h | 14/94 (14.9%) | 63/334 (18.9%) | -0.0428 | 0.0102 | 0.0042 |
| contexto_atencao | 15/94 (16.0%) | 196/334 (58.7%) | -0.1090 | 0.1717 | 0.0068 |
| combinado | 17/94 (18.1%) | 196/334 (58.7%) | -0.0699 | 0.0852 | 0.0107 |

## Atenção no primeiro passo

A razão `massa por token` compara a massa de atenção no pedido atual com a fração de tokens que ele ocupa; 1,0 seria proporcional ao tamanho.

| Recorte | Casos com histórico | Massa atual | Fração tokens atual | Razão massa/token | Entropia normalizada |
|---|---:|---:|---:|---:|---:|
| treino | 3153 | 0.2046 | 0.2133 | 0.8788 | 0.4538 |
| dev_antiga | 240 | 0.3164 | 0.4353 | 0.7233 | 0.3811 |
| dev_nova | 80 | 0.1785 | 0.1701 | 1.2833 | 0.5316 |

Estas métricas não provam semântica geral; servem para localizar o gargalo antes de outra intervenção.
