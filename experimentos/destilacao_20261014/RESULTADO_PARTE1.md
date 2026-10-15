# Destilação 6b v5, parte 1: o caderno do professor (14/10/2026)

Notebook `notebooks/destilacao_professor_a100_colab.ipynb`, conta hr87676620, A100, vLLM 0.31.0,
`professor.py` v1. 64.768 perguntas (fase 5 v4, enciclopédia, acervo, OASST2 pt), as mesmas para os
dois professores. Caderno: `CRIVO/dados-professor/dados_professor.json.gz`, 89.858 exemplos,
sha256 dos dados `79c1a5d6ef40e31b260b31d45a3dd9969d03897e58ef65f6fce3a7d713cbb695`. São dados de
modelos de terceiros, não falas humanas (AGENTS.md).

| | pequeno (Qwen3-1.7B) | médio (Qwen3-8B) |
|---|---|---|
| aceitas | 45.935 / 64.768 (71%) | 43.923 / 64.768 (68%) |
| com a regra de ouro | 45.514 | 43.421 |
| fora: não usou os fatos | 12.050 | 15.666 |
| fora: inventou número/nome | 5.728 | 7.787 |
| fora: repetição | 3.653 | 524 |
| fora: idioma | 403 | 150 |
| fora: falou de si | 145 | 60 |
| fase 5 aceitas | 29.073 / 33.584 | 29.012 / 33.584 |
| enciclopédia aceitas | 15.898 / 29.663 | 13.951 / 29.663 |
| OASST2 aceitas | 368 / 590 | 475 / 590 |
| acervo aceitas | 596 / 931 | 485 / 931 |

## O que a amostra mostrou (10 aceitas de cada, impressas no notebook)

- **O médio fala bem:** curto, natural, do jeito pedido ("Claro! Me conta o que precisa.", "Aí sim,
  cara. Tô aqui pra te ajudar. O que tá rolando?").
- **O pequeno passa no filtro e não faz sentido:** "me da uma luz ai" → "Vem, tá escuro aqui! Vamos
  brincar de luz?"; "crivo, preciso de uma força aqui" → "Ah, o cachorro tá crivo?"; puxa assunto
  da conversa anterior fora de hora ("calcular a concentração de íons H⁺"). O filtro confere forma
  e verdade, não sentido: ele não pega isso.
- **Leitura:** a pesquisa sobre a distância de tamanho (PLANO.md) supunha um professor menor *e
  bom*; o 1.7B não é bom em português. A diferença aqui é de qualidade, não só de tamanho. Isso é
  observação de uma amostra de 10, não medida.
- **Falsos positivos do filtro de idioma:** respostas curtas sem as palavras da lista ("tchau! boa
  noite e sonhos bons 😊") caem como "idioma". Pouco (150 no médio); corrigir na v2 do filtro.
- **"Não usou os fatos" é severo** na enciclopédia (metade fora): o verbete tem muitas palavras de
  conteúdo e o professor resume. É o lado seguro (o que entra está perto da fonte).

## Decisão para a parte 2 (registrada antes de treinar)

- **v5 médio primeiro** (`notebooks/fase6b_v5_professor_colab.ipynb`, `MISTURA = "medio"`). A mista
  (metade do pequeno) continua no plano, mas só roda depois e só se a médio não piorar a régua:
  pela amostra, o pequeno tende a ensinar respostas sem sentido.
- **Mudança do plano:** a v5 parte da **mesma base da 6a** com a **receita inteira da v4** (mesmos
  dados, passos, escolha pelo sentido e régua) e o professor ×2. Assim a comparação com a v4 tem uma
  diferença só. (O plano dizia "a partir do 46M v4"; treinar de novo a v4 nos mesmos dados misturaria
  dois efeitos.) Com os mesmos passos, o professor entra no lugar de parte das legendas.
- **Limite da régua:** o sentido (`sentido.py`) julga por listas feitas no jeito da fase 5. Uma
  resposta boa do professor, com outras palavras, pode contar como errada. Por isso o juiz entra
  depois, ao lado (AGENTS.md), e as 15 frases reais do criador continuam valendo.
