# Diálogo único e iniciativa (2026-10-02)

## Problema

Havia dois jeitos de conversar. As observações do dia ("hoje choveu")
tinham presença: reação, eco na voz de "você", noção, pergunta. Já os
relatos em primeira pessoa passavam pelo fluxo antigo de orientação, com
texto de formulário:

- "Você trouxe a ideia: “acho que trabalhei demais”. Que experiência…"
- "Você contou: “mas não tenho tempo”. Seu objetivo declarado é “aprender violão”."
- "não sei", "sei lá" e "ok" no meio da conversa voltavam ao menu
  ("faça uma pergunta sobre qualquer assunto", "Posso falar de astronomia…").
- "nada de mais" e "hmm" depois do "oi" caíam em "não entendi".

## O que muda

- **Mesma voz nos dois fluxos** (`dialogo_aberto.py`, `linguagem_conversa.py`):
  opinião vira eco em pergunta ("Você acha que trabalhou demais? Por que você
  acha isso?"); objetivo vira "Você contou que quer aprender violão. Que bom!
  Qual é a principal dificuldade para chegar lá?"; cada novo pedaço do relato
  recebe reação + eco ("Poxa, você não tem tempo.") e liga ao objetivo com as
  palavras da pessoa ("E pensando em “aprender violão”, o que você já
  tentou…?"). As perguntas de orientação (dificuldade → tentativa → mudança →
  próximo passo) continuam as mesmas.
- **Respostas curtas dentro da conversa** (`conversa_cotidiana.py`): "não sei",
  "ok", "nada", "hmm" depois de um relato recebem acolhimento + continuação
  do assunto (ou do objetivo), não o menu.
- **Iniciativa**: sem assunto nenhum ("oi" → "tudo bem" → "nada de mais"), o
  Crivo puxa conversa com uma pergunta leve que ainda não fez
  (`presenca.INICIATIVA`), sem repetir.
- **Conjugação mais segura** (`presenca.py`): pretérito em -ei pela grafia
  ("peguei" → "pegou", "fiquei" → "ficou"), futuro só quando o lema confirma
  ("comerei" → "comerá", mas "parei" → "parou"), presentes comuns que o
  etiquetador às vezes lê como substantivo ("eu gosto" → "você gosta") e
  "consigo", que o tokenizador separa em "com si".

## Medição

Bateria nova `avaliacoes/dialogo_unico_v1` (escrita antes das mudanças;
marcas de formulário valem ao pé da letra em todo turno):

| | antes | depois |
|---|---|---|
| dev | 8/21, 2 genéricas, 1 repetição | 21/21, 0, 0 |
| retido (agregado) | 7/18, 2, 1 | 16/18, 1, 0 |

Correção no dev, registrada em `limiares.json`: o turno do violão proibia
"Você contou", mas um cenário público anterior (`avaliar_conversacao.py`)
exige essa expressão. A proibição que vale é a do formulário ("Você contou: “").

Demais baterias sem perda: presença 35/35 (estrutura repetida 1 → 0),
15/19, 27/29; conversa cotidiana 36/36, 23/24, 12/15; memória 12/12, 8/8,
10/10.

## Limites conhecidos

- Depois de "gosto de cozinhar", "principalmente massa" ainda recebe a noção
  de macarrão com a pergunta "Fez com qual molho?", que supõe algo que a
  pessoa não disse.
- Sem o analisador (sem NumPy), não há eco na voz de "você": as palavras da
  pessoa vão citadas ("Entendi, você disse: “Só tenho 20 minutos por dia”."),
  para que o que ela contou nunca suma da resposta.
