# Pointer/Copy Causal v4 — resultado da execução de 12/10/2026

Execução no Colab (T4) do commit `74eb786`. Saída no Drive:
`CRIVO/checkpoints/experimento_pointer_copy_v4/pointer_copy_v4_20261012_052906/`.
Resumo sem as linhas por caso: `resultado_resumo_v4.json`. Base `c0a56b15…` intacta
(fingerprint `257a4eb4…` antes = depois). Rodadas anteriores não tocadas.

## Decisão

**Reprovado.** `gate_pass=false`; candidato escolhido pelo dev = `A_troca_espaco` no passo 1
(praticamente sem treino), por isso o blind ficou igual à base (nome 25,8% × 25,7%;
semântica geral 19,0% × 19,0%). `ativo_no_chat=false`, `promovido=false`.

## O que a rodada mostrou

1. **As rotas novas aprendem as tarefas** (dev, 12 entidades × 6 tarefas):

   | Configuração | cópia+fim | categoria | função | invariância | composição | negação |
   |---|---|---|---|---|---|---|
   | passo 1 (todas) | 0% | 25% | 92% | 0% | 0% | 0% |
   | A, melhor passo | 0% | 83% | 42% | 0% | 58% | 0% |
   | AB, melhor passo | 75–83% | 75–83% | 0–50% | 0% | 17–58% | 0% |
   | ABC, melhor passo | 75% | 50–75% | 50–67% | 75–83% | 50–67% | 58–75% |

   A sozinha não para (confirma a teoria); a parada (B) leva cópia+fim de 0% para 75–83%;
   o adaptador (C) é o único que aprende "Não." em invariância/negação.

2. **Todas estragam as respostas comuns.** Acordo do primeiro token nas 12 perguntas genéricas:
   A 0,50–0,58; AB 0,50–0,83; ABC 0,00–0,08 (TV 0,95–0,99). A regra de preservação
   (top-1 ≥ 0,90 e TV ≤ 0,15) só aceitou o passo 1. ABC foi descartada em todos os passos.

3. **Teto da arquitetura (base real, teacher forcing):** cópia+fim 0% (v3) → 0% (A) → 56% (AB);
   nome alcançável no início da resposta 7–9% → 56–57%. O adaptador não tem teto estrutural.

## Limites

Dev pequeno (12 entidades por tarefa no monitor); holdout sintético de autoria do agente;
não houve porta conversacional.

## Próximo passo

A causa da reprovação agora é a falta de âncora fora das tarefas. O v5 testa exatamente isso:
KL na própria base em mensagens comuns do CRIVO, mantendo as arquiteturas AB e ABC.
