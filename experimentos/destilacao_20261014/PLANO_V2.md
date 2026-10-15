# Destilação v2: plano (registrado antes do piloto, 15/10/2026)

Lições da v1 (RESULTADO_PARTE1.md, RESULTADO_PARTE2.md): as falas do professor eram as do treino da
fase 5 com outra resposta (conflito, o mesmo erro da v3); o filtro só conferia a forma; o professor
pequeno falava besteira; reescrever fatos fez o 46M errar fatos.

## Dados (`professor_v2.py`, `notebooks/destilacao_v2_colab.ipynb`)

- **Meta: 87.000 conversas aprovadas** para o treino (pedido do criador). Rodadas até a meta; se a grade
  acabar antes, o caderno fica menor e o número é relatado (a exigência não baixa). Passando da meta,
  ficam as de nota maior.
- **Falas novas** escritas pelo professor (133 temas × 20 intenções × 7 jeitos de escrever = 18.620 pedidos). Ficam
  fora as falas que já existem na fase 5 (todas as partes, incluindo o histórico), as falas sobre
  o CRIVO e as de crise ou saúde urgente.
- **Dois turnos:** o professor escreve a reação da pessoa e responde de novo.
- **Professor maior:** Qwen3-32B-AWQ (ou 14B, o que existir e couber; Apache 2.0).
- **Juiz de outra família** (Mistral Small 24B w4a16 ou Phi-4): nota de 1 a 5; só entra 4 ou 5.
  Mais o filtro de forma e a regra de ouro obrigatória (nada de número ou nome inventado).
- **O juiz é testado:** em cada rodada, 60 respostas trocadas de conversa de propósito. Se ele aprovar
  mais de 10% delas, o notebook para.
- **Sem repetição:** a mesma resposta no máximo 3 vezes; nenhum começo de resposta (4 palavras) acima
  de 1% do caderno.
- **Sem fatos do professor.** Os fatos ficam como na v4.
- **Prova:** 15% das falas novas (por hash) nunca treinam.
- **Piloto antes:** 40 pedidos; o criador lê 30 aprovadas e 10 reprovadas. Só com o ok dele roda o
  caderno inteiro.

## Treino (v6, depois do caderno)

A receita inteira da v4 (mesma base da 6a, mesmos dados, mesmos passos, mesma escolha pelo sentido)
mais o caderno v2 ×2. A fase 5 não muda.

## Para ir ao chat (as duas coisas)

1. **Régua própria, sem piorar:** cada blind ≥ v4 − 1,5 ponto; frases reais ≥ 12/15; fatos do
   acervo (usa o fato) ≥ 0,85.
2. **Juiz, ganhando:** nas falas da prova, v6 × v4 em pares, cada par julgado nas duas ordens; só
   conta quando o juiz escolhe o mesmo nas duas. v6 precisa vencer ≥ 55% desses pares.

O juiz não substitui a régua (AGENTS.md): sem o item 1, não vai.
