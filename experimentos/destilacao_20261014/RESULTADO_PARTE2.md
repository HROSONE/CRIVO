# Destilação 6b v5, parte 2: a v4 com o professor médio (14/10/2026)

`notebooks/fase6b_v5_professor_colab.ipynb`, `MISTURA = "medio"`, conta hr87676620, A100. A mesma
base da 6a e a receita inteira da v4; a única diferença é o professor médio (Qwen3-8B), 43.421
exemplos ×2, **10,0% dos tokens de conversa** (fase 5 28.677, enciclopédia 13.951, acervo 485,
OASST2 308). Resumo: `resumo_fase6b_v5_medio.json`. Pesos: `CRIVO/transformer-crivo-46m-conversa-v5-medio/`
(só do CRIVO; `ativo_no_chat: false`).

## Régua própria (decide)

| | v5 médio | v4 46M (no chat) | v4 F |
|---|---|---|---|
| blind v3 | 64,3% | 65,7% | 63,5% |
| blind v1 | **69,6%** | 65,3% | 69,8% |
| paráfrases | 72,2% | 73,7% | 76,2% |
| Grok | 73,9% | 73,2% | 70,9% |
| blind v4 | 92,5% | 92,3% | 92,2% |
| frases reais do criador | **10/15** | 12/15 | 14/15 |
| sem freio: v3 / frases reais | 65,0% / 10 | 66,0% / 12 | |
| fatos do acervo: usa o fato | **0,7** | 0,9 | |
| conferência: perguntas livres / OASST2 separado | 0,875 / 0,4 | 1,0 / 0,6 | |

**Não vai para o chat.** Ganha no blind v1 (+4,3) e quase empata no resto, mas perde nas frases
reais (10 contra 12) e piora nos fatos do acervo.

## O que as respostas mostram

- **Fatos:** a v4 repete o fato do acervo; a v5 aprendeu a reescrever como o professor, e o 46M
  erra ao reescrever: "densidade" → "a razão entre o volume que você ocupa e o volume do corpo";
  "RNA … ajuda a produzir proteínas e vertebrados"; "voleibol … ajuda a evitar lesões". O
  professor escrevia o fato com outras palavras (o filtro exigia só 40% das palavras); o aluno
  pegou o jeito de parafrasear sem pegar a precisão.
- **Frases reais:** perdeu "e cade as respostas boas?" (respondeu como cumprimento) e "tenho dois
  cachorros" (resposta genérica). Ganhou "serio mesmo?"/"tá vendo…" em parte. São 15 frases: 2 de
  diferença é pouco para concluir sozinho, mas vai no mesmo sentido dos fatos.
- **Conversa comum:** parecida com a v4, às vezes mais natural ("Imagino. Dia puxado cansa o corpo
  e a cabeça. Conseguiu descansar um pouco?").
- **OASST2 e conhecimento geral** continuam fracos nas duas (código, listas e explicações sem
  sentido); 10% de professor não mudou isso.

## Limites

- Um treino só por receita (sem repetir com outra semente); diferenças de 1–2 pontos podem ser ruído.
- O juiz ainda não rodou; o sentido julga por listas no jeito da fase 5.

## Próximo: a v5b "conversa" foi suspensa antes de rodar (revisão de 15/10/2026)

A primeira ideia (o professor só nas conversas comuns da fase 5) repete um erro já registrado
(`experimentos/fase6b_conversa_humana/RESULTADO.md`, v3, "respostas em conflito"):

- **As perguntas do professor na fase 5 são as mesmas falas do treino da fase 5**, com outra
  resposta. Cada uma das ~20 mil falas de conversa teria duas respostas-alvo diferentes. Na v3, duas
  respostas para "você é humano?" (fase 5 e IDENTIDADE.md) deixaram essas situações em 0%. A v5b
  faria isso em todas as conversas comuns.
- **Sinal na v5 médio, nas situações em que o professor entrou:** risada nas paráfrases 11,4% →
  0,8%; amor_bom no blind v3 → 0%. Não dá para separar conflito de régua: o sentido julga por
  listas no jeito da fase 5, e uma resposta boa do professor com outras palavras conta como errada.
  Por isso o juiz tem que vir antes de outro treino.

**Ordem nova (antes de qualquer treino):**
1. **Juiz, sem treinar nada:** v4 × v5 médio, comparação em pares com a ordem trocada, num juiz de
   outra família, em falas novas que nenhum dos dois viu. Responde se o professor melhorou a conversa
   e a régua não viu, ou se piorou mesmo.
2. **Só depois, se o juiz mostrar ganho:** o professor só em falas que a fase 5 não tem (pedidos e
   conversas do dia a dia fora das listas, conversas de vários turnos), sem nenhuma fala repetida
   do treino; fatos do professor fora.
