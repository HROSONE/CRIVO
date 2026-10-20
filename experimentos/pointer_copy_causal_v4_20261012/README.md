# Pointer/Copy Causal v4 — atacar as três causas medidas no v3

Notebook: `notebooks/pointer_copy_causal_v4_colab.ipynb`. Saída no Drive:
`CRIVO/checkpoints/experimento_pointer_copy_v4/pointer_copy_v4_<data>/`.
Nada do v2/v3 é carregado ou sobrescrito.

## Causas (medidas no v3) e intervenções

| Causa medida no v3 | Variante |
|---|---|
| Primeiro token do nome sem `Ġ` no início da resposta não está no prompt (copiável em 8–11%) | **A**: a cópia pode emitir a variante com/sem `Ġ` do token do prompt (mapa tirado do próprio vocabulário; 1.548 IDs têm variante) |
| `<fim>` nunca está no prompt; base nunca o põe em primeiro após um nome solto (teto 0%) | **AB**: A + rota explícita de parada na mistura |
| Base abre respostas com `Trila…` e não diz "Não." em invariância/negação | **ABC**: AB + adaptador low-rank dos logits (rank 32), iniciado em zero |

Transformer e `lm_head` continuam congelados (fingerprint conferido antes, durante e depois).
As três variantes começam neutras, usam os mesmos lotes e os hiperparâmetros do v2/v3.

## Protocolo

- Dados: os mesmos arquivos congelados do v3 (SHA-256 conferidos).
- Dev passa a ter as 6 tarefas (12 entidades × 6 no monitor), porque é ele que escolhe.
- Cada variante guarda o melhor passo do dev entre os que mantêm a preservação de respostas
  genéricas (top-1 ≥ 0,90 e TV ≤ 0,15).
- **O candidato é a variante com maior score de dev, escolhida e impressa antes de abrir o blind.**
  As outras também são avaliadas no blind, só para atribuição.
- Gates iguais aos do v3, no candidato, no blind novo. Blind v2 (formato real e legado) como regressão.
- Teto de cada arquitetura sob teacher forcing, medido com a base real antes do treino.
- Mesmo com `gate_pass=true`: porta conversacional pendente, `ativo_no_chat=false`, `promovido=false`.

## Verificação feita antes de publicar

- Execução completa em CPU com pesos aleatórios da mesma arquitetura: conferência de SHA,
  re-tokenização, treino das três variantes, escolha, avaliação e salvamento. Sem erros nem avisos.
- Teste de sobreajuste (8 casos de cópia de treino, base aleatória, 250 passos):
  A copia o nome mas não para (`zhxv` → `zhxvhvxh`, 0/8 com `<fim>`);
  AB copia e para (8/8). Mostra que as rotas funcionam; não mede generalização.
- Limite conhecido de A: quando a palavra é segmentada de outro jeito sem o espaço
  (`Ġx|yz` × `xy|z`), a troca por token não alcança o nome; no blind novo a parte copiável
  do primeiro token sobe de 9% para ~60%. O adaptador (ABC) é a variante que cobre o resto.
