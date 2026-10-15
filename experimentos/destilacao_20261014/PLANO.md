# Destilação 6b v5: plano (registrado antes de gerar, 14/10/2026)

Autorização: AGENTS.md (professor e juiz só fora do CRIVO que conversa). Aluno: o 46M v4
(24 camadas, d384, contexto 1024, tokenizador próprio). Nada aqui roda no chat.

## O que a pesquisa mudou no plano

| Antes eu acreditava | A pesquisa mostrou | Muda |
|---|---|---|
| Quanto maior o professor, melhor (7–14B). | Com distância grande de tamanho, o aluno aprende pior ("curse of capacity gap"); o melhor professor cresce de forma mais ou menos linear com o aluno [1][2][3]. | Dois professores da mesma família: um pequeno (≈1–2B) e um médio (≈7–8B). A mistura é medida contra só o médio. |
| Basta copiar as respostas do professor. | Modelos ≤3B aprendem mal com respostas longas e difíceis; misturar respostas curtas/simples com as do professor maior ajuda ("Mix Distillation") [4]. Modelos de poucos milhões falam com coerência quando os dados usam linguagem simples [5]. | O professor responde curto e simples (até ~120 palavras, vocabulário do dia a dia). Respostas longas só onde o assunto pede (explicação, poema, código), marcadas. |
| Destilação = aprender o texto do professor. | Treinar só no texto do professor cria descompasso: na hora de falar, o aluno vê os próprios erros, que nunca viu no treino. Usar as respostas do próprio aluno, corrigidas pelo professor, melhora (GKD) [6]. | Rodada 2 (depois da v5): o 46M responde, o professor corrige o texto, o 46M treina na correção. A forma exata do GKD (logits do professor nos tokens do aluno) não serve direto: os tokenizadores são diferentes. |
| Destilar logits exigiria o mesmo tokenizador. | Há perdas entre tokenizadores diferentes (ULD, por transporte ótimo) [7][8]. | Fica como experimento futuro; a v5 usa só texto (destilação por sequência). |
| O juiz dá uma nota confiável. | Juízes preferem a posição, respostas mais longas e o texto da própria família [9][10]. | Juiz de família diferente dos professores; comparação em pares, com a ordem trocada (só conta vitória nas duas ordens); nota relatada também por faixa de tamanho; o juiz é conferido contra as 15 frases reais do criador antes de valer como sinal. |

## Passos

1. **Perguntas** (`professor.py`, sem professor): conversa comum e fatos da fase 5 v4 (só as situações liberadas), OASST2 pt (treino da 6b), acervo, enciclopédia (30 mil). Ficam de fora: identidade, criador, gostos e fé (IDENTIDADE.md), crise e saúde urgente (crise.py), "não sei", nomes e lembranças, e toda frase da régua (dev, blinds, as 15 frases reais): a régua não pode ter sido vista pelo professor nem pelo aluno.
2. **Gerar** com os dois professores, `Qwen/Qwen3-1.7B` (pequeno) e `Qwen/Qwen3-8B` (médio), sem o modo de pensar, na A100 (`notebooks/destilacao_professor_a100_colab.ipynb`, conta hr87676620). Instrução: português do Brasil, curto, simples, sem dizer quem é. A revisão exata e a licença de cada um ficam no manifesto; o notebook para se a licença não for Apache 2.0 ou MIT.
3. **Filtro** (`professor.conferir`): idioma pt (sem chinês, inglês ou espanhol), tamanho, resposta cortada, sem repetição, sem markdown, sem "sou um modelo/assistente" nem nome de modelo. Com fatos: a regra de ouro da conferência do chat (número e nome próprio só do contexto ou da conversa) e pelo menos 40% das palavras de conteúdo dos fatos. Sem fatos, a regra de ouro é registrada; **o treino da v5 só usa exemplos que passam nela** (o que o chat aceitaria).
4. **Pasta separada** `dados_professor/` com origem (modelo, versão, data, licença) em cada linha.
5. **Treino** a partir do 46M v4, mesmas configurações da v4, duas misturas:
   - v5m: humanos (como na v4) + professor médio;
   - v5x: humanos + metade médio, metade pequeno.
   A proporção professor/humano é registrada.
6. **Régua própria** (decide): dev sentido, às cegas v1/v3/v4, Grok, paráfrases, 15 frases reais. Vai para o chat só se ganhar da v4 na régua.
7. **Juiz** (só relata): pares v5 × v4, ordem trocada, por tamanho.

## Limites conhecidos

- O tamanho ideal do professor para 46M não foi medido; os estudos [1][2] vão de dezenas de milhões a 7B, em inglês.
- [4] e [6] medem matemática, resumo e tradução, não conversa em português.
- A qualidade do português dos professores será olhada numa amostra antes do treino.

## Fontes

1. Mirzadeh et al., Improved Knowledge Distillation via Teacher Assistant (AAAI 2020).
2. Zhang et al., Lifting the Curse of Capacity Gap in Distilling Language Models (ACL 2023), arXiv 2305.12129.
3. Zhang et al., Towards the Law of Capacity Gap in Distilling Language Models, arXiv 2311.07052; Busbridge et al., Distillation Scaling Laws, arXiv 2502.08606.
4. Li et al., Small Models Struggle to Learn from Strong Reasoners (Findings ACL 2025), arXiv 2502.12143.
5. Eldan e Li, TinyStories, arXiv 2305.07759.
6. Agarwal et al., On-Policy Distillation of Language Models (ICLR 2024), arXiv 2306.13649.
7. Boizard et al., Towards Cross-Tokenizer Distillation: the Universal Logit Distillation Loss (TMLR 2025), arXiv 2402.12030.
8. Multi-Level Optimal Transport for Universal Cross-Tokenizer KD, arXiv 2412.14528.
9. Zheng et al., Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena (NeurIPS 2023).
10. Ye et al., Justice or Prejudice? Quantifying Biases in LLM-as-a-Judge (CALM).
