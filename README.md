# Crivo v0.2 (em desenvolvimento)

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

## Evolução experimental (PR #1)

- `Crivo.ensinar(id, topico, perguntas, resposta)` permite acrescentar entradas revisadas pelo desenvolvedor e persistir no JSON; não é aprendizagem autônoma.
- `historico` guarda as últimas 20 perguntas respondidas; `ultimo_assunto` oferece retomada limitada de referências.
- Perguntas negativas sobre ações recebem resposta de incerteza em vez de afirmação potencialmente perigosa.
- `python -m unittest discover -p 'testes*.py' -v` executa os testes adicionais; `python crivo.py --teste` executa os 65 testes existentes.
- Workflow GitHub Actions testa três versões de Python; conferir resultados antes de integrar.

**Limites:** não possui rede neural, aprendizagem a partir de texto livre, raciocínio lógico geral nem geração aberta de linguagem. Recuperar respostas e lembrar referências não equivale a compreender português. Para evoluir em direção a um modelo próprio, é necessário criar um conjunto de dados de treino, uma arquitetura treinável, um procedimento de otimização e avaliações independentes. Não marcar funcionalidades como aprovadas sem testes executados.
