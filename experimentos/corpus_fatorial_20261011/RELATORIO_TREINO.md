# Treino fatorial — resultado

Um único candidato. Mesma inicialização, arquitetura, vocabulário, quantidade de treino e hiperparâmetros do controle; muda somente a composição do bloco de sessões.

| Medida | Controle 1× | Corpus fatorial |
|---|---:|---:|
| CE antiga (334) | 0.9435 | 0.7228 |
| Exatas antigas | 47/334 | 64/334 |
| CE final fatorial (96) | 3.3671 | 0.6580 |
| Exatas final fatorial | 0/96 | 22/96 |
| Primeiro token final | 5.2% | 28.1% |
| Operações final | 5.2% | 38.5% |

## Portão pré-congelado

- Reter exatas antigas: **sim**.
- CE antiga dentro do limite: **sim**.
- Melhorar CE final em ≥15%: **sim** (80.5%).
- Ganhar ≥15 p.p. no primeiro token: **sim** (22.9 p.p.).
- Ganhar ≥15 p.p. nas operações: **sim** (33.3 p.p.).
- Sucesso conjunto: **SIM**.

O checkpoint permanece experimental e `ativo_no_chat=false`, independentemente do resultado.
