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

## Próximo (registrado antes de rodar): v5b "conversa"

O professor só nas conversas comuns da fase 5 (`fase5:cena:*`); fatos, enciclopédia e OASST2 do
professor ficam de fora, e os fatos voltam a ser só como na v4. Mesma base, mesma receita, mesma
régua. Hipótese: mantém os fatos da v4 e leva o ganho de conversa. Vai para o chat só se ganhar da
v4 nas frases reais e não perder nos blinds nem nos fatos.
