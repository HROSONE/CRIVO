# Classificador de compreensão (v0)

Primeira etapa do ensino de compreensão: decidir o **tipo** da pergunta (quem, o que, qual,
quanto, quando, onde, como, por que, para que, se, pedido, afirmação) e o **alvo** (sobre o
Crivo, sobre a pessoa, sobre o mundo, prática, outro).

## Arquivos

- `rotulos.json`: o que cada rótulo quer dizer.
- `seed.jsonl`: 64 exemplos escritos à mão, com divisão `treino` (37), `dev` (15) e `regua` (12).
- `classificador_regras.py`: classificador de base, só com regras. É o ponto de comparação.
- `avaliar.py`: mede o classificador em cada divisão.

## Resultado atual (19/10/2026)

| divisão | tipo | alvo | observação |
|---|---|---|---|
| treino (37) | 1,00 | 0,81 | as regras foram escritas olhando esses exemplos: número inflado |
| dev (15) | 1,00 | 0,80 | também viu as regras: número inflado |
| regua (12) | 0,92 | 0,92 | o número honesto, mas a amostra é pequena |

Erros na régua: "você faria isso se pudesse?" (o "se" no meio da frase não é pego) e
"o que você acha disso?" (alvo deveria ser "outro").

## Regras de uso

- A `regua` não serve para ajustar regras nem para treinar. Se um erro nela levar a mudar uma
  regra, a régua deixa de ser régua e passa a ser dado de treino: nesse caso, criar outra.
- Exemplos novos vêm de geração com modelo externo, com origem marcada (modelo, versão, data,
  licença). Os rótulos são conferidos por um programa e por revisão humana de amostra.
- Os fatos nunca vêm do modelo externo.

## Limites conhecidos

- 64 exemplos é uma semente. Não serve para treinar um classificador neural; serve para testar
  o pipeline e a régua.
- O classificador de regras acerta frases fora do padrão só por sorte. Esse é o motivo de
  passar para um classificador treinado.

## Próximo passo

1. Gerar com modelo externo algumas centenas de exemplos por rótulo, com origem marcada.
2. Revisar uma amostra humana e conferir os rótulos.
3. Treinar um classificador pequeno, próprio, em NumPy, e comparar com as regras na mesma régua.
