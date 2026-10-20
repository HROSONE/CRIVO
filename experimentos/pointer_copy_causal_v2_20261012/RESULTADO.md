# Pointer/Copy Causal v2 — resultado da execução de 12/10/2026

Notebook: `notebooks/pointer_copy_causal_v2_colab.ipynb` (commit `2a4bf92` clonado no Colab, T4).
Saída no Drive do dono: `CRIVO/checkpoints/experimento_pointer_copy/pointer_copy_20261012_042442/`
(`pointer_head.pt`, `resultado_pointer_copy.json`, `config_experimento.json`, `README_resultado.txt`).

## Identidade

- Base: `escola_curricular_longa/run_transferido_20261012/05_05_dialogo_estado`
  - `pesos.pt` SHA-256 `c0a56b1546495efafde5df99feebfa084fef414d512076d888b40c9828e4eb4e`
  - fingerprint dos parâmetros antes = depois `257a4eb41406…a1ea1566` (base intacta)
- Tokenizer `6e37a7508def…044dbe7e`.
- Cabeça pointer/gate: 24.961 parâmetros treináveis (rank 32); Transformer 100% congelado.
- 500 de 1000 passos (early stop). O estado selecionado é o do **passo 100**: o score
  composto do dev empatou no passo 300 e caiu depois; `dev_copy_exact` foi 0,0 em todas as avaliações.

## Blind congelado (600 casos, 100 entidades × 6 tarefas, 300 close / 300 distant)

| Métrica | Base | Pointer |
|---|---|---|
| cópia pura exata | 0,0% | **0,0%** |
| entidade exata em qualquer ponto da saída | 3,3% | 75,2% |
| close / distant | 1,3% / 5,3% | 73,0% / 77,3% |
| início / meio / fim | 6,0 / 2,5 / 1,5% | 72,0 / 76,5 / 77,0% |
| categoria | 0% | 87% |
| função | 2% | 67% |
| composição | 1% | 78% |
| invariância | 0% | **0%** |
| negação | 0% | **0%** |
| semântica geral | 0,6% | 46,4% |
| terminação com `<fim>` | 61,2% | 74,5% |

Preservação extra (12 prompts genéricos, primeiro token): top-1 100%, TV média 0,117.

Gates: 6/7. Falhou `copy_exact>=0.70` (0,0). **`gate_pass=false`, `ativo_no_chat=false`, `promovido=false`.**

## Leitura das amostras publicadas

- Cópia: o nome aparece, mas a saída não para nele (`zedi é um alimento`, `jkvx é um ve`,
  `entementeentemente é um instrumento`). Nome duplicado conta como "entidade exata".
- Respostas que deveriam começar por "Não." (invariância/negação) começam com um `T`
  vindo da base e corrompem o nome: `Tnteriores é um recipiente.`, `Tvx é um veículo…`.
- A base sozinha não preserva nomes inventados e troca por palavras próprias
  (`Trila é um objeto usado para`, `A categoria de ente foi substituída pela correção.`).

## Limites

- O prompt é montado colando IDs: o nome entra sem `Ġ` depois de um token de espaço solto
  (`'Ġchamado' 'Ġ' 'Z' 'or' …`), e a resposta usa os mesmos IDs. Em texto real o nome
  no meio da frase começa com `ĠZ` e no início da resposta com `Z` (IDs diferentes).
  Portanto a cópia medida aqui é a versão fácil (ID idêntico) e o texto está fora da
  distribuição da base. Os 75% não demonstram ganho em conversa.
- `entity_exact` aceita o nome em qualquer posição e repetido.
- Não houve avaliação conversacional (porta do comentário do #166) nem comparação com o motor atual.
- A cabeça não está integrada a `motor_dialogo_17m.py`.

## Decisão

Reprovado pelo próprio protocolo. Não entra no chat. Próximo passo único sugerido:
refazer o v2 com tokenização natural (texto completo → encode) e alvo de cópia que
inclua a parada em `<fim>`, mantendo este blind como regressão conhecida.
