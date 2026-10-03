# Assunto errado e tom errado (2026-10-03)

## Como os erros apareceram

Numa conversa de 143 falas sobre os assuntos que o CRIVO já aprendeu, ele disse "não sei" em 49 e respondeu
errado em pelo menos outras 20. Os erros mais graves soavam confiantes:

| fala | antes |
|---|---|
| Por que o céu é azul? | "Azul: papel. Vermelho: plástico…" (cores da reciclagem) |
| Plantas respiram? / Respirar fundo ajuda? | "Peixes respiram pelas brânquias…" |
| Qual a diferença entre == e ===? | "Tempo é a condição da atmosfera…" |
| Se eu tenho 3 maçãs e como uma, quantas sobram? | "Comida pronta dura de 3 a 4 dias na geladeira…" |
| Perdi minha avó semana passada | "Que chato, você perdeu sua avó…" |
| Briguei com minha namorada | "Entendi, briguei com sua namorada." |
| Trabalhei muito e não almocei | "Almoço caprichado costuma dar aquele sono depois." |

## Medição primeiro

`avaliacoes/assunto_tom_v1` (dev 27 casos, retido 14) foi registrada em commit antes da correção. Os casos
são de três tipos:

- assunto (a resposta não pode ser sobre outro tema);
- tom;
- controles (perguntas que precisam continuar respondidas).

Um marcador do dev estava errado: "for...in", normalizado, coincidia com a resposta certa em Python. Ele foi
trocado por uma marca de resposta em JavaScript. A linha de base abaixo já usa o marcador corrigido.

| | dev | retido |
|---|---|---|
| main, com NumPy | 8/27 | 9/14 |
| main, sem NumPy | 10/27 | 10/14 |
| depois, com NumPy | 25/27 | 12/14 |
| depois, sem NumPy | 24/27 | 12/14 |

## Assunto: por que acontecia

O recuperador aceitava uma entrada da base quando a pergunta tinha uma palavra em comum com ela, mesmo que
fosse uma palavra lateral. "Azul" aparece num exemplo da reciclagem ("lixeira azul vermelha verde amarela").

Agora cada entrada tem um **núcleo**:
- as palavras presentes na maioria dos seus exemplos;
- as do identificador ("dengue", "natal_verao");
- as que formam sozinhas um exemplo ("o que é uma galáxia").

A entrada é descartada quando:
- a única palavra em comum não é do núcleo ("céu azul" × reciclagem);
- a pergunta cita outro assunto conhecido (núcleo de outra entrada ou ser/astro do grafo de relações), e a
  entrada não o menciona e só coincide numa palavra ou em palavras genéricas ("Plantas respiram?" × peixes);
- a pergunta cita outro ser, e metade ou mais do núcleo da entrada falta ("Golfinho respira debaixo
  d'água?" × peixes);
- o pedido é para escrever algo que o CRIVO não conhece ("Escreva fatorial em JavaScript" × introdução ao
  JavaScript).

Exceções que protegem respostas certas:
- quando a pergunta cita o assunto do identificador da entrada ("mofo no guarda-roupa" × mofo), só outro ser
  ou astro citado a desqualifica;
- as partes de seres ("penas", "folha") não contam como assunto à parte ("vale a pena").

Numa pergunta de classificação ("Morcego é ave?"), a entrada precisa falar do próprio sujeito.

Além disso, três tipos de pergunta não usam mais a base de fatos de outro tema:
- hipóteses ("Se todo A é B…");
- contas ("3 maçãs… quantas sobram");
- código (`==`, `=>`, `print(`), que só casa com programação.

**Conferência:** a suíte inteira foi rodada registrando toda resposta aceita pela base (488 perguntas
distintas). A regra rejeita só seis delas, e as seis eram respostas erradas ou vazias:
- "Qual a distância da Lua até a Terra?" recebia o tempo da luz do Sol;
- "Vênus é parecido com a Terra?" recebia "o planeta mais quente";
- "O que gato e computador têm em comum?" recebia cuidados com gatos;
- "Qual é o nome dessa coisa que você falou?" recebia as estações do ano;
- "Meu nome é Pessoa N" também recebia as estações do ano;
- "Um burro é um mamífero?" recebia a descrição de mamíferos (o CRIVO não tem "burro" cadastrado).

Validação cruzada (`avaliar_definicoes.py`, cada pergunta retirada do índice), acertos/erradas:

| | main | depois |
|---|---|---|
| coorte histórica sem grafo | 192/43 | 195/38 |
| coorte histórica com grafo | 192/43 | 196/37 |
| base atual sem grafo | 200/47 | 204/40 |
| base atual com grafo | 200/47 | 205/39 |

"o que é cadeia alimentar" aparece como perda do filtro de definição, mas já é "fora" na main com o filtro;
só entrou na lista porque, sem o filtro, a branch passou a acertá-la (a main respondia fotossíntese).

A base de perguntas não mudou. Alterá-la exige retreinar a rede classificadora.

## Tom

- **Perda (`nocoes.perda`):**
  - morte de uma pessoa ou de um bicho ("perdi minha avó", "meu gato morreu", "velório do meu tio") recebe o
    tom `luto`: pêsames ("Sinto muito pela sua perda.", "Meus sentimentos."), nenhum comentário de senso comum
    e nenhuma curiosidade sobre o assunto;
  - a despedida e a retomada não desejam "melhoras";
  - "Perdi o ônibus", "o celular morreu" e "morri de rir" não são perda.
- **Negação:** "não almocei" e "ele não quer comer" não puxam o comentário sobre almoço ou comida.
- **Primeira pessoa:** "Briguei/Discuti com…" vira "você brigou/discutiu". Os verbos em -i ganham o
  infinitivo pelo vocabulário dos vetores ("discuti" → discutir, "comi" → comer).
- **Término:** não é conquista nem recebe "Vocês estão juntos há quanto tempo?".
- **Feriado e fim de semana:** contam como coisa boa.
- **Perguntas novas:**
  - "Como você acha que ele tá?" é sobre o bicho ou a pessoa da conversa, não sobre o CRIVO;
  - "O que eu faço?" pede para pensar junto e retoma o que a pessoa contou.

## Sem regressão

As outras baterias ficaram iguais às da `main`:
- presença, conversa cotidiana, pertinência, memória de relatos;
- suposição, crise, fluência.

A bateria de fatos teve uma melhora: no retido, as respostas de assunto errado caíram de 2 para 1.
`testes_assunto_tom.py` trava os limiares (catraca) e cobre os casos principais, com e sem NumPy.

## Limites

- No dev, continuam sem solução "Como ordeno uma lista?" e "Como uso map em um array?". Eles caem em
  respostas vizinhas (criar lista, `for...of`) porque falta conteúdo sobre ordenar e sobre `map`.
- Recusar não é responder. Várias perguntas passaram de uma resposta errada para "não entendi". O passo
  seguinte é cobrir esses assuntos.
- A lista de palavras genéricas e o detector de perda são autorais e podem errar em frases não previstas.
