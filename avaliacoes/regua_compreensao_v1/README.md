# Régua de compreensão v1

55 casos para medir se o Crivo entende a pergunta e responde certo.

- `casos.json`: as perguntas, o que a resposta deve (ou não deve) conter, e a origem de cada caso.
  - `do_usuario`: perguntas que o Henrique fez no teste de 19/10/2026.
  - `autoral`: perguntas escritas para controle.
- `rodar.py`: roda os casos no chat e confere cada resposta.
- `resultado_base.json`: a primeira medida, feita antes de qualquer treino novo.

## Regras de uso

- Esta régua é só para avaliar. As perguntas e respostas dela **não entram em nenhum dado de treino** e não são mostradas ao professor ou ao juiz.
- Não ajustar o código para passar um caso específico. Se um caso falha, a correção tem que ser geral.
- Medir de novo sempre que houver mudança no chat, no motor de respostas ou em um modelo candidato.
- Ler as falhas, não só o número: alguns casos são lacunas conhecidas, marcadas em `nota`.
