# Pertinência da reação a um relato (2026-10-03)

## O problema

Ao comparar pontuadores de frases, apareceu um erro que não tinha relação com o pontuador: o comentário
de senso comum (noção) e a pergunta de volta eram escolhidos só pela palavra-chave, sem olhar o que
aconteceu nem com quem.

| fala | antes |
|---|---|
| meu gato sumiu | "…gato costuma derrubar coisas da mesa… Ele é bagunceiro assim sempre?" |
| meu pai vai fazer uma cirurgia amanhã | "Certo. Conversa com pai costuma render histórias antigas." |
| meu avô plantou uma mangueira | "…O que você plantou?" |
| vi uma menina abrindo o guarda-chuva | "…guarda-chuva costuma ficar esquecido… Pegou chuva por causa disso?" |
| comi pizza ontem | "Que bom, comi pizza ontem!" |

As baterias existentes passavam com esses erros, porque medem estrutura (genérica, repetição, fatos), não a
pertinência.

## Medição primeiro

`avaliacoes/pertinencia_v1` (dev 25 casos, retido 16), escrita e registrada em commit **antes** da
correção. Cada caso é uma fala isolada, com marcas do erro (`nao_contem`) e reações esperadas
(`contem_algum`). Os controles são casos em que a noção combina e deve continuar aparecendo. O script
`scripts/avaliar_pertinencia.py` confere ainda, em todos os casos:

- **pessoa errada:** pergunta sobre "você" quando o fato é de outra pessoa;
- **primeira pessoa vazada:** verbo ou possessivo da fala repetido sem conversão.

| | dev | retido |
|---|---|---|
| antes | 7/25 | 6/16 |
| depois (com NumPy) | 25/25 | 14/16 |
| depois (sem NumPy) | 25/25 | 14/16 |

## O que mudou

- **`dados/nocoes_pt.json`:**
  - 28 noções de entidade (animais, pessoas, objetos, veículos) ganharam `eventos`: as raízes dos
    acontecimentos com que o "costuma" e a pergunta combinam ("gato" → derrubar, quebrar, arranhar…).
    Noções sem o campo continuam valendo para qualquer relato que as cite (chuva, pizza, trânsito);
  - `pergunta_livre` marca perguntas que servem mesmo assim ("Qual o nome dele?");
  - cirurgia e operação entram como eventos de saúde.
- **`nocoes.pertinencia`:**
  - decide se o comentário e a pergunta combinam com o relato;
  - numa cena vista de fora ("vi uma menina…"), nenhuma noção entra;
  - a noção de doença não é usada para um animal.
- **`conversa_cotidiana`:**
  - escolhe a primeira noção que combina;
  - sem noção que combine, a resposta repete o que a pessoa contou ("Certo, seu pai pintou a cerca.")
    e usa uma pergunta aberta;
  - pergunta sobre "você" não vai para fato de outra pessoa;
  - queda, machucado ou cirurgia de alguém passam a ter tom de saúde, com abertura de futuro ("Espero
    que dê tudo certo") quando o fato ainda vai acontecer;
  - sem o analisador (sem NumPy), quem viveu o fato é lido pelo começo da fala.
- **`presenca`:** "comi", "bebi", "fiz" no começo da fala são lidos como verbo, mesmo quando o
  etiquetador erra a classe ("Que bom, você comeu pizza ontem!").

## Sem regressão

Todas as outras baterias ficaram iguais às da `main` (presença, diálogo único, conversa cotidiana, memória
de relatos, suposição, crise, bateria de fatos, fluência), com uma melhora: presença (retido) 15/19 → 16/19.
`testes_pertinencia.py` trava os limiares (catraca) e cobre os casos principais com e sem NumPy.

## Limites

- A lista `eventos` é autoral e cobre 28 noções. Um acontecimento não previsto ("meu gato aprendeu a abrir a
  porta") fica sem noção e recebe pergunta aberta. Isso é conservador: perde um comentário possível, mas
  não diz algo fora de lugar.
- A resposta sem noção é mais simples ("Certo, sua irmã comprou um carro novo. E o que mais?"). Uma
  pergunta específica para cada tipo de acontecimento fica como próximo passo.
