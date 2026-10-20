# Pointer/Copy Causal v3 — desenho corrigido, mesma cabeça

Notebook: `notebooks/pointer_copy_causal_v3_colab.ipynb`.
Evidência do v2 preservada sem alteração: `experimentos/pointer_copy_causal_v2_20261012/RESULTADO.md`,
`notebooks/pointer_copy_causal_v2_colab.ipynb` e, no Drive,
`CRIVO/checkpoints/experimento_pointer_copy/pointer_copy_20261012_042442/` (o v3 grava em
`experimento_pointer_copy_v3/` e nunca carrega o `pointer_head.pt` do v2).

## O que muda em relação ao v2

| | v2 | v3 |
|---|---|---|
| Montagem | IDs do nome colados após um `Ġ` solto | texto completo → `lp.fonte_dialogo` / `lp.codificar_texto` + `<fim>` |
| Nome no prompt | `'Ġ' 'Z' 'or'…` (fora da distribuição) | `'ĠZ' 'or'…` (como no chat) |
| Nome no início da resposta | mesmos IDs do prompt | sem `Ġ`, como o runtime gera |
| `<fim>` da cópia pura | só dentro da perda de mistura | termo explícito `0.50 * fim_copia_ce` |
| Acerto da cópia | IDs iguais, sem exigir parada | texto = nome **e** `<fim>` |
| Nome duplicado (`zedizedi`) | contava como entidade exata | não conta |
| Artigos | "um ferramenta" | "uma ferramenta" |
| Cabeça | rank 32, p_gen 0,9 | **idêntica** (código copiado), **reinicializada** |
| Base | `c0a56b15…` | a mesma, conferida por SHA e fingerprint `257a4eb4…` |
| Hiperparâmetros | 1000 passos, batch 16, lr 2e-3, paciência 4 | iguais |

## Dados congelados antes do treino (`preparar_v3.py`)

- `blind_regressao_v2.json`: as 100 entidades do blind v2, reproduzidas executando as
  próprias células do notebook v2 (conferidas contra os nomes das amostras publicadas:
  `entemente`, `jkvx`, `zedi`, `anteriores`). Traz os 600 casos no formato antigo
  (comparação direta com o v2) e os mesmos 600 no formato real.
- `blind_novo_v3.json`: 100 entidades inéditas (disjuntas das 660 usadas no v2),
  50 close / 50 distant, 600 casos com a tokenização do runtime.
- `treino_dev_v3.json`: 480 treino / 80 dev, disjuntos dos dois blinds.
- `manifesto.json`: SHA-256 de cada arquivo e do `dados_v3.py`; o notebook confere
  os quatro e re-tokeniza os 1.200 casos em formato real, exigindo igualdade de IDs.

## Limite estrutural medido antes de treinar

A saída é `p_gen·p_vocab + (1−p_gen)·p_copy`, e `p_copy` só tem massa em IDs do prompt.
Para um alvo fora do prompt, qualquer token com `p_vocab` maior também recebe pelo menos
`p_gen·p_vocab`, então esse alvo só vence o argmax se já for o top-1 da base congelada.

Isso pega dois pontos centrais desta prova:

- o `<fim>` nunca está no prompt;
- quando o nome abre a resposta (cópia, categoria, função, composição), o primeiro token
  vem sem `Ġ` e só é copiável por ID em 8–11% dos casos do blind novo; em invariância e
  negação ("Não. nome…") o nome inteiro é copiável em 100%.

A célula 8 mede o teto por tarefa com a base real sob teacher forcing e o grava no
resultado. Se o teto de exact-name+fim ficar abaixo de 70%, o gate de cópia é
inalcançável por esta arquitetura, e isso é a resposta causal da rodada, não um
motivo para mexer na cabeça no meio do experimento.

## Gates (blind novo)

`exact_name_fim_copia>=0.70`, `exact_name_distant>=0.65`, `|close−distant|<=0.10`,
`max(posição)−min(posição)<=0.10`, regressão de função `<=5pp`, regressão de semântica
geral `<=2pp`, hash do Transformer igual. Preservação top-1/TV como checagem extra.
Mesmo com `gate_pass=true`: porta conversacional pendente, `ativo_no_chat=false`,
`promovido=false`.

## Verificação feita antes de publicar

Execução completa em CPU com pesos aleatórios da mesma arquitetura (só valida execução,
conferência de SHA, re-tokenização e salvamento; nenhuma métrica de capacidade). As
métricas aceitam os 600 alvos do blind novo e rejeitam as falhas observadas no v2
(nome sem parar, nome duplicado colado, primeiro caractere trocado).
