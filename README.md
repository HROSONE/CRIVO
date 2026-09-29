# Crivo v0.3 (em desenvolvimento)

Assistente de conversa em português, primeiro teste.
Assuntos: plantas, animais, clima, tempo, estações do ano, sistema solar e coisas de casa.

## Como usar

    python crivo.py                  # conversa no terminal
    python crivo.py "por que chove?" # uma pergunta só
    python crivo.py --teste          # bateria de testes (testes.json)

Só precisa de Python 3.8+, sem instalar nada.

## Como funciona (honestamente)

A resposta padrao do Crivo v0.3 utiliza um mecanismo de recuperacao, nao uma rede geradora de texto:
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

## Treinamento da rede neural propria (experimental)

A rede `RedeCrivo` e uma MLP original em Python puro, inicializada sem pesos pre-treinados. **Classifica intenções, não gera respostas abertas.** O recuperador do chatbot continua responsavel pelas respostas. O classificador neural, mesmo carregado, so e usado quando concorda com o recuperador e supera os limiares atuais; portanto, um benchmark neural melhor **nao garante** melhora no chatbot final.

### No GitHub (sem instalar nada no celular)

No GitHub, abra **Actions → Treinar cerebro original do Crivo → Run workflow**. O workflow tambem dispara quando o codigo neural ou a base de conhecimento mudar na `main`. Ele:

1. Executa a suite de regressao.
2. Treina do zero com todas as perguntas de `conhecimento.json`, 60 epocas, 48 neuronios ocultos e 512 dimensoes, representacao `portugues`.
3. Recarrega e valida os pesos no Crivo.
4. Disponibiliza o arquivo `rede_crivo.json` como artefato para download (retencao de 14 dias).

Para usar localmente, extraia `rede_crivo.json` para a **mesma pasta** do `conhecimento.json`, junto do `crivo.py`. O carregamento e automatico quando assinaturas e rotulos correspondem. Se as perguntas ou as regras linguisticas forem alteradas, um novo checkpoint criado por esse fluxo e rejeitado como desatualizado, sem impedir as respostas do recuperador; `Crivo.erro_rede` informa o motivo. Checkpoints antigos sem essas assinaturas continuam aceitos por compatibilidade.

### Treinamento manual parametrizado

```bash
python rede_neural.py --base conhecimento.json --saida rede_crivo.json --epocas 60 --ocultos 48 --dimensao 512 --modo portugues --semente 42
```

A medicao de **138/278 (49,64%)** para a rede com essas configuracoes foi obtida em uma validacao cruzada de desenvolvimento em que cada pergunta foi deixada de fora do treino da respectiva dobra. Esse numero **nao** mede o checkpoint treinado sobre todos os dados em perguntas inteiramente externas, nem demonstra compreensao geral ou efeito nas respostas reais. As regras de sinonimos foram desenvolvidas usando a mesma base e isso limita o grau de independencia da avaliacao.
