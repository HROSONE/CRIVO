# Crivo v0.1

Assistente de conversa em português, primeiro teste.
Assuntos: plantas, animais, clima, tempo, estações do ano, sistema solar e coisas de casa.

## Como usar

    python crivo.py                  # conversa no terminal
    python crivo.py "por que chove?" # uma pergunta só
    python crivo.py --teste          # bateria de testes (testes.json)

Só precisa de Python 3.8+, sem instalar nada.

## Como funciona (honestamente)

O Crivo v0.1 **não é uma rede neural treinada**. Ele é um modelo de recuperação:
1. `conhecimento.json` guarda 77 respostas escritas à mão, com várias formas de perguntar cada uma.
2. Ao iniciar, ele indexa tudo com TF-IDF (o "treino" é esse índice).
3. A pergunta é normalizada (sem acento, plural, diminutivo, sinônimos) e comparada com a base.
4. Se a confiança é baixa, ele diz que não sabe em vez de inventar.
5. Hora, data, mês, ano e estação atual vêm do relógio do computador.

Comandos na conversa: `assuntos`, `exemplos`, `mais` (próxima resposta parecida), `sair`.

## Próximos passos

- Ampliar `conhecimento.json` (cada pergunta nova que falhar vira uma entrada).
- Usar esse mesmo arquivo como dataset para ajustar (fine-tune) um modelo generativo pequeno.
