# Síntese de funções Python a partir de exemplos (caminho 3, etapa 1)

**Resultado (13/10/2026):**
- No **blind**, com até 3 perguntas, o motor acertou **24 de 32** funções, errou **2** e não respondeu **6**.
- No **desenvolvimento**, acertou 28 de 32 e não errou nenhuma.
- Nada disso está ligado ao chat.

## Por que este caminho

O criador decidiu manter a regra do projeto (nenhum modelo de terceiros) e ensinar o próprio
CRIVO a programar.

As tentativas anteriores com rede neural escrevendo código livre não acertaram nada:
- modelos de 2,6M a 6M parâmetros;
- o código compilava, mas acertou 0 de 16 tarefas e 0 de 28 no conjunto reservado (`docs/AJUSTES_LOGICA_PROGRAMACAO.md`).

O que já funcionava no repositório era o motor de JavaScript do chat (`programacao_chat.py`). Ele
procura uma função numa gramática pequena e confere cada candidata nos exemplos.

Esta etapa faz o mesmo para Python (`sintese_python.py`):
- **busca de baixo para cima por tamanho**: das expressões menores para as maiores;
- **equivalência observacional**: duas expressões que dão os mesmos valores contam como uma só;
- **gramática** com números, textos, listas, map/filter e somas/contagens com condição;
- **pergunta quando há dúvida**: se duas funções batem com os exemplos e discordam numa entrada
  nova, o motor pergunta a saída dessa entrada, em vez de escolher no chute. Escolhe a entrada que
  mais divide as funções ainda possíveis.
- **orçamento**: se a busca para pelo limite antes de olhar todas as alternativas, a resposta
  conta como incerta.
- **tradução conferida**: o texto Python é só a tradução da expressão encontrada. Os testes
  (`testes_sintese_python.py`) conferem, em todas as expressões até o tamanho 4, que a tradução
  dá o mesmo resultado que a avaliação interna.

Sem rede neural, sem modelo de terceiros e sem executar código enviado pela pessoa.

## Protocolo

1. `tarefas.py` foi escrito antes do motor e congelado no commit `9252be8` (SHA `eeaadffd…`). São
   32 tarefas de desenvolvimento e 32 blind, cada uma com:
   - uma referência escrita à mão;
   - de 1 a 4 exemplos;
   - de 3 a 8 entradas ocultas.

   Duas tarefas de cada parte estão fora da gramática de propósito: ali o certo é não responder.
2. O motor foi ajustado olhando **só os erros do desenvolvimento**.
3. O motor foi congelado no commit `8cf65f9` (SHA `fdb16ccd…`), e o blind rodou **uma vez**, depois.

Cada tarefa termina num destes resultados:
- **certa**: acerta todas as entradas ocultas;
- **errada**: bate com os exemplos e erra alguma oculta;
- **sem resposta**.

Cada tarefa roda em três modos:
- **direto**: responde a menor função;
- **cauteloso**: não responde se houver dúvida;
- **pergunta**: até 3 perguntas, respondidas pela referência como a pessoa responderia.

## Resultados

| | modo | certas | erradas | sem resposta | perguntas (média) |
|---|---|---|---|---|---|
| desenvolvimento | direto | 26 | 5 | 1 | — |
| | cauteloso | 9 | 0 | 23 | — |
| | **pergunta** | **28** | **0** | **4** | 1,06 |
| **blind** | direto | 22 | 9 | 1 | — |
| | cauteloso | 4 | 2 | 26 | — |
| | **pergunta** | **24** | **2** | **6** | 1,38 |

Arquivos: `resultado_desenvolvimento.json` e `resultado_blind.json`, com cada função gerada.

### O que o blind mostra

- **Perguntar é o que segura o erro.** Respondendo direto, 9 das 31 respostas do blind estavam
  erradas. Com perguntas, ficaram 2 de 26.
- **As 2 erradas são o mesmo defeito.** "Conta quantas vezes a letra a aparece" e "tamanho da
  maior palavra" saíram como "conta as vogais". Nos exemplos dados (banana → 3, casa → 2…), contar
  vogais dava o mesmo resultado. A função certa era maior que essa, e o motor só procura
  alternativas até um tamanho acima da menor. Ele não viu dúvida e não perguntou. É um caso clássico
  de exemplos que, por coincidência, servem para uma função mais simples.
- **Sem resposta (6):**
  - 2 de propósito: mediana e máximo divisor comum com 12;
  - 4 que não se resolveram em 3 perguntas: negativo, começa com "a", palíndromo de frase e maior
    que cem.

  Nesses casos o motor disse que não tinha certeza, em vez de errar.

## Limites, ditos com franqueza

- **O mesmo autor escreveu as tarefas e o motor, na mesma sessão.** O blind protege contra
  ajustar o motor depois de ver os erros, mas não contra uma gramática pensada já conhecendo a
  lista. Por exemplo, a operação "ímpar" entrou junto com "par" por simetria, e há tarefas de ímpar
  no blind. Um teste independente de verdade precisa de pedidos escritos por outra pessoa, como o
  criador.
- 32 tarefas por parte é pouco: um erro a mais ou a menos muda 3 pontos.
- A gramática é pequena: uma expressão Python por função, sem `if` e sem laço escrito à mão. Fora
  dela, o motor não responde.
- Ainda precisa de exemplos. Entender só a descrição em português ("faz uma função que…") é a
  etapa 2.

## Próximo passo proposto (nada decidido)

- **Confirmar antes de entregar**: mesmo sem dúvida, mostrar o que a função dá numa entrada nova
  ("para 'aeiou' ela dá 5; é isso?"). Isso teria pegado os 2 erros do blind. Como essa ideia
  surgiu depois de ver o blind, ela precisa de um blind novo para ser medida, de preferência com
  pedidos do criador.
- Ligar no chat só com o aviso "passou nos seus exemplos; confira", e só se o criador quiser.
