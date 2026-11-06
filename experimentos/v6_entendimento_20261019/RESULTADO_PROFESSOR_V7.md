# v7 — o professor (20/10/2026)

`notebooks/professor_v7_colab.ipynb`, A100, commit `a88c256`. **Professor: Qwen/Qwen3-32B-AWQ** (revisão `0499c3ac…`,
licença Apache 2.0, vLLM 0.31.0). Arquivo no Drive: `CRIVO/dados-professor-v7/falas_professor_v7.jsonl.gz`, sha256
`b980bae0dc45…`. **Falas da pessoa escritas por modelo de terceiros; não são humanas.** O arquivo não entra no repositório.

| etapa | falas |
|---|---|
| pedidos (108 situações × 8 estilos × 25) | 880 pedidos |
| lidas | 21.632 |
| fora na leitura | metatexto 416, repetida 206, saúde 123, longa 21 |
| aprovadas na conferência de rótulo (5 respostas) | **13.192 (61%)** |

Os 8 estilos ficaram equilibrados (1.497 a 1.728 falas cada).

## Depois dos filtros do gerar_v7.py (conferido aqui, com o arquivo do Drive)

| | minhas | do professor |
|---|---|---|
| treino | 667 falas (10.669 casos) | 4.860 falas (19.440 casos) |
| dev | 95 | 670 |
| blind v7 | 201 | 1.417 |

Saíram: detector de gatilhos 5.577, parecidas com teste 1.155, iguais a teste 344, ambíguas entre situações 180,
conflito com o treino antigo 8. **Falas novas de treino por situação: mediana 46,5 (mínimo 14), contra 7 no v6c.** 5.450
falas de treino não existiam no treino v3.

## O que a amostra mostra

Boa parte é variada e natural ("põe um lembrete pro meu celular tocar às 21h", "sem fiapo", "meu cérebro parece travado").
Há ruído de rótulo: em `oi` apareceram "bom dia, crivo" (sai pelo conflito com o treino antigo), "tá on" e "E ae, tudo em
paz?" (ficam). A conferência é do próprio professor, não humana.

O treino ainda não rodou.
