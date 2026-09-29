# Crivo v0.3 (em desenvolvimento)

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
- Ampliar e avaliar a rede própria, inicializada do zero; sem modelos pré-treinados.

## Evolução experimental (PR #1)

- `Crivo.ensinar(id, topico, perguntas, resposta)` permite acrescentar entradas revisadas pelo desenvolvedor e persistir no JSON; não é aprendizagem autônoma.
- `historico` guarda as últimas 20 perguntas respondidas; `ultimo_assunto` oferece retomada limitada de referências.
- Perguntas negativas sobre ações recebem resposta de incerteza em vez de afirmação potencialmente perigosa.
- `python -m unittest discover -p 'testes*.py' -v` executa os testes adicionais; `python crivo.py --teste` executa os 65 testes existentes.
- Workflow GitHub Actions testa três versões de Python; conferir resultados antes de integrar.

**Limites:** a rede neural experimental classifica intenções; não aprende autonomamente a partir de texto livre, não possui raciocínio lógico geral nem geração aberta de linguagem. Recuperar respostas e lembrar referências não equivale a compreender português. Para evoluir em direção a um modelo próprio, é necessário criar um conjunto de dados de treino, uma arquitetura treinável, um procedimento de otimização e avaliações independentes. Não marcar funcionalidades como aprovadas sem testes executados.


## Assertividade v0.3

- Recuperação usa similaridade ponderada por raridade das palavras e média/melhor exemplo; duplicar perguntas idênticas não aumenta a pontuação.
- Vocabulário revisado no código reconhece mais flexões e sinônimos. Correção de grafia só atua em termos desconhecidos de pelo menos cinco letras com um único candidato próximo no índice.
- Perguntas exatamente cadastradas têm prioridade; empates entre intenções diferentes pedem esclarecimento antes de qualquer reforço neural.
- Saudações junto de perguntas não encerram a análise. Hora e data locais não interceptam perguntas sobre outros lugares ou acontecimentos históricos.
- Negações não cadastradas pedem reformulação, com tratamento limitado de perguntas de prevenção. Isso não equivale a compreender qualquer negação.
- Histórico também registra respostas exatas; `mais` não reaproveita resultados após uma pergunta sem resposta.

### Medição reproduzível

    python crivo.py --teste
    python -m unittest discover -p 'testes*.py' -v
    python avaliar_recuperador.py

Comparação com `ec8fd2a1698e82663eb146adf2d0ad55608d2295`, mesma base de conhecimento:

| Medida em 278 perguntas | Antes | v0.3 |
|---|---:|---:|
| Respostas corretas | 181 | 192 |
| Respostas erradas | 51 | 44 |
| Abstenções/pedidos de esclarecimento | 46 | 42 |
| Acerto sobre todas as perguntas | 65,1% | 69,1% |
| Precisão entre respostas dadas | 78,0% | 81,4% |

Os 65 testes originais continuam passando. Os 19 casos novos de conversa são regressões de desenvolvimento, não evidência de generalização independente. Resultados e erros restantes estão em `avaliacao_assertividade.json`.

**Protocolo e limite:** a avaliação retira cada pergunta do índice na sua rodada, mas mantém as respostas e outras perguntas da mesma intenção. Foi usada durante o desenvolvimento e não é um teste cego. Seus números não são diretamente comparáveis aos da rede neural treinada apenas com perguntas. A pontuação de similaridade não é probabilidade de verdade. A melhora é no mecanismo de escolha de respostas, não uma alegação de inteligência geral.
