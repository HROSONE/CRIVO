# Conversas reais de vários turnos

Conversas do criador com o chat, refeitas turno a turno no `web_core.responder_web`, com o histórico das
mensagens anteriores, como o site manda. Cada turno tem regras mínimas (escritas no projeto) do que uma
resposta boa precisa ter; o teste mede quantos turnos passam e quantas conversas passam inteiras.

- `conversas.json`: as conversas. Papel `dev` = usada para construir o ambiente (`ambiente.py`), não vale
  como prova. Papel `teste` = só medida, nunca usada para ajustar regra ou código.
- `rodar.py [saida.json] [--papel dev|teste]`: roda com a voz do modelo ligada (o 46M v7c).
  Com `CRIVO_MOTOR_NATIVO=<libcrivo.so>`, usa o motor em C (as mesmas respostas, mais rápido).

## Resultados (dev: a conversa do "Palarerepípedo", 12 turnos)

| versão | turnos que passam |
|---|---|
| chat de 20/10 (v7c, antes do ambiente) — `resultado_base.json` | 4/12 |
| com o ambiente (casa, alimento, juiz) — `resultado_ambiente.json` | 11/12 |

Limites: é a conversa usada para construir o ambiente, então o 11/12 mostra que o ambiente resolve os
casos que motivaram cada peça, não que generaliza. A prova são as conversas de papel `teste`, que o
criador está preparando. O turno 8 ("Você consegue me entender?") ainda falha: a frase escolhida começa
com "Claro!", mas fala de desabafo. Nos turnos 3, 6 e 7 o modelo não disse o resultado (a palavra
corrigida, a pergunta que ele fez) em nenhuma das tentativas, e ficou o texto conferido do ambiente,
como já acontece com os verbetes da Wikipédia.
