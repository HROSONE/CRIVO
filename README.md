# Crivo v0.4 (em desenvolvimento)

Assistente de conversa em português, primeiro teste.
Assuntos: plantas, animais, clima, tempo, estações do ano, sistema solar, coisas de casa e programação.

## Como usar

    python crivo.py                  # conversa no terminal
    python crivo.py "por que chove?" # uma pergunta só
    python crivo.py --teste          # bateria de testes (testes.json)

Só precisa de Python 3.8+, sem instalar nada.

## Como funciona (honestamente)

A resposta padrao do Crivo v0.4 utiliza um mecanismo de recuperacao, nao uma rede geradora de texto:
1. `conhecimento.json` guarda 122 assuntos escritos à mão, com 459 formas de perguntar; 45 assuntos novos são de programação.
2. Ao iniciar, ele indexa tudo com TF-IDF (o "treino" é esse índice).
3. A pergunta é normalizada (sem acento, plural, diminutivo, sinônimos) e comparada com a base.
4. Se a confiança é baixa, ele diz que não sabe em vez de inventar.
5. Hora, data, mês, ano e estação atual vêm do relógio do computador.
6. Programação usa um índice por domínio e respeita a linguagem pedida. Exemplos cadastrados são exibidos junto das explicações, sem executar código do usuário.

Comandos na conversa: `assuntos`, `exemplos`, `mais` (próxima resposta parecida), `sair`.

## Próximos passos

- Ampliar `conhecimento.json` (cada pergunta nova que falhar vira uma entrada).
- Ampliar e avaliar a rede própria, inicializada do zero; sem modelos pré-treinados.

## Programação ensinada no código

O currículo contém **45 assuntos, 181 perguntas de treino e 31 exemplos** adicionados diretamente a `conhecimento.json`:

| Área | Conteúdo |
|---|---|
| Fundamentos | Programação, algoritmos, variáveis, tipos e investigação de bugs |
| Python | Entrada/saída, condições, laços, funções, listas, dicionários, comparação, exceções, arquivos, JSON, classes, módulos, ambiente virtual e testes |
| Web | HTML, CSS, API e HTTP |
| JavaScript | Variáveis, funções, arrays, DOM, promessas e async/await |
| SQL | Tabelas, SELECT/WHERE, JOIN e parâmetros com sqlite3 |
| Git | Controle de versão, commit, branch e revisão de diferenças |

Experimente:

```bash
python crivo.py "Definir uma função que soma em Python"
python crivo.py "Faça um exemplo de função de soma em JavaScript"
python crivo.py "Como resolver ValueError no Python?"
python crivo.py "Me mostra uma página básica em HTML"
```

O campo `resposta` guarda a explicação; `exemplo` guarda linguagem e código fixo. `area`/`linguagens` orientam a seleção, `identificadores` reconhece nomes de erro e `fontes` registra documentação consultada. O programa funciona offline: esses links não são consultados durante a conversa. Exemplos e explicações são autorais, conferidos nas documentações de [Python](https://docs.python.org/3/), [MDN](https://developer.mozilla.org/en-US/docs/Web/), [PostgreSQL](https://www.postgresql.org/docs/current/tutorial-sql.html) e [Git](https://git-scm.com/docs).

O índice calcula relevância separadamente para assuntos gerais e programação. A correspondência exata preserva operadores como `=`, `==` e `!=`, além de nomes como `C++` e `C#`; preservar nomes não significa ter conteúdo sobre essas linguagens. O classificador neural continua usando sua representação experimental anterior.

**Validação de desenvolvimento:** 45 perguntas novas de programação e um controle sobre plantas passaram; as frases não são cópias literais do treino, mas foram usadas durante o ajuste, portanto não são teste cego. As 181 perguntas cadastradas retornam os assuntos esperados. Exemplos Python são executados em pastas temporárias; exemplos JavaScript têm a sintaxe verificada e, quando independentes do navegador, a saída testada; SQL usa um banco SQLite em memória. HTML/CSS e comandos de Git/venv são exemplos didáticos, sem teste de navegador ou execução de comandos Git nesses testes.

Na avaliação que retira a pergunta de sua rodada de busca: **119/181 acertos em programação**, com 26 respostas erradas e 36 abstenções. Os **278 casos antigos mantiveram exatamente 192 acertos, 44 erros e 42 abstenções**, incluindo os mesmos erros. Os 65 testes originais e os 24 diálogos anteriores continuam passando. Resultados completos e limites estão em `avaliacao_programacao.json`.

**Limite:** isto ensina conceitos e exemplos recuperáveis. O Crivo não gera programas arbitrários, não executa trechos recebidos nem corrige automaticamente projetos. Treinar a rede com todos os assuntos amplia seus rótulos; não demonstra que ela aprendeu a escrever código livremente.

```bash
python -m unittest testes_programacao -v
```

O Crivo requer apenas Python; verificar os exemplos JavaScript também requer Node.js. O CI instala Node.js e testa Python 3.8, 3.11 e 3.13. As regressões executam em cada PR/push. Comparações neurais extensas ficam em **Actions → Testes Crivo → Run workflow → benchmark** (`portugues` ou `historico`), para não repetir toda a pesquisa a cada alteração. O treino dos pesos continua automático quando a base muda na `main`.

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

## Diálogo com esclarecimento

O Crivo agora guarda as opções que acabou de oferecer e entende a sua escolha:

```text
você > planta
Crivo > Encontrei duas possibilidades próximas. Qual delas você quer?
1. o que é fotossíntese
2. quantas vezes devo regar as plantas
você > a segunda
Crivo > [resposta cadastrada sobre regar]
```

- Aceita `1`, `2`, `a primeira`, `a segunda`, `opção 2` e nomes que identifiquem uma única opção, como `a de regar`.
- `Sim` confirma quando há apenas uma sugestão. Com duas opções, pede uma escolha explícita.
- `Não` ou `nenhuma das duas` cancela a escolha; uma pergunta nova descarta a pendência anterior.
- Registra no histórico a escolha e a pergunta que gerou as opções. `Mais` também atualiza o assunto para a resposta que foi efetivamente mostrada.
- A pendência pertence à instância de `Crivo`, não é salva no conhecimento e é descartada quando `ensinar()` muda a base.

Em 24 sequências de desenvolvimento fixadas antes da implementação, o resultado passou de **3/24 para 24/24**. A avaliação de perguntas isoladas permaneceu idêntica: **192 acertos, 44 erros e 42 abstenções em 278 perguntas**; os 65 testes originais continuam passando. O ganho medido é na continuidade da conversa. Não mede generalização para qualquer diálogo, aumento de conhecimento ou melhora da rede neural.

Os casos e o avaliador estão em `testes_dialogo.py`; o comparativo está em `avaliacao_dialogo.json`. Para verificar:

```bash
python -m unittest testes_dialogo -v
python avaliar_recuperador.py
```

## Experimentos de recuperação de programação (PR #8)

A sonda `experimento_programacao_adversarial.py` mede o **recuperador de
respostas fixas**, não geração de código nem inteligência geral. Identificou
quatro limitações reais da v0.4: negação descritiva em `const`, paráfrases
para entrada de dados em Python, JavaScript atuando sobre HTML e distinção de
`git diff` versus `git commit`. A quinta falha original era um erro
no próprio teste: `sistema_solar` é uma categoria, não um ID de resposta;
o esclarecimento foi aceito como resultado correto para a pergunta ampla.

As alterações do experimento são pontuais:
- Algumas equivalências de consulta são usadas **somente em contexto
  técnico explícito**, sem alterar a base de exemplos.
- HTML/CSS podem ser contexto de uma consulta JavaScript, sem exigir que
  cada entrada tenha todas essas linguagens como áreas próprias.
- Em uma consulta Git que pede comparar alterações de arquivos, `diff`
  entra como pista adicional; pedidos explícitos sobre `commit` e `push`
  não recebem essa pista.
- A negação descritiva sobre uma variável JavaScript que "não muda" é
  diferenciada de negações gerais que continuam pedindo esclarecimento.

**Medições reproduzíveis, sem rede neural:**
- Na sonda de desenvolvimento de 27 casos, o resultado final é **27/27**.
  Essa sonda orientou os ajustes; **não é teste cego** e inclui a correção
  de um resultado esperado inválido.
- Em 12 controles adicionais escritos depois dos ajustes, **11/12**. A
  pergunta "Como obter informações de quem usa o programa Python?"
  ainda foi associada a `prog_variavel` em vez de `py_input`. O
  recuperador continua limitado diante de algumas paráfrases.
- Nos 278 casos gerais anteriores, sem programação, o resultado permanece
  **192 acertos, 44 erros e 42 abstenções**; o experimento encerra com erro
  se os acertos gerais caírem abaixo de 192 ou as respostas erradas subirem
  acima de 44.

Rode `python experimento_programacao_adversarial.py` para gerar o relatório
JSON completo; `python -m unittest discover -p 'testes*.py'` inclui os
testes de regressão semântica. **Os resultados não atestam que o CRIVO
escreva programas sob demanda**: ele continua recuperando explicações e
exemplos previamente cadastrados, sem modelos externos.

## Interpretação de entrada do usuário (PR #9)

O recuperador usa um conjunto **restrito de pistas linguísticas** para reconhecer
quando uma consulta Python descreve pedir/receber informação da pessoa que
digita no terminal, ainda que não mencione literalmente `input`. Termos
como "pessoa", "usuário", "digitação" e verbos de solicitação precisam
formar uma combinação reconhecível. Isso não treina uma nova rede, nem
gera funções inéditas: o Crivo continua selecionando o exemplo `py_input`
previamente escrito.

A regra não é aplicada a pedidos sobre formulários web, câmera, APIs,
WhatsApp e outras interfaces não ensinadas; nesses casos deve admitir que
não sabe, em vez de exibir o exemplo de entrada pelo terminal. Outra
correção impede que "informe seu nome" dentro de uma pergunta de
programação acione a apresentação social do assistente. Perguntas que
descrevem interações JavaScript com campos HTML recebem pistas de DOM.
"Funciona" foi tratado como verbo genérico apenas na consulta,
evitando bloquear um assunto claramente reconhecido por uma palavra
não cadastrada.

**Métricas de desenvolvimento, não teste cego:**
- Bateria pré-registrada de 29 perguntas: **19/29 antes**, **29/29 após**.
- Controles adicionais elaborados depois das primeiras alterações:
  **23/23** após o ajuste. Esses controles detectaram inicialmente dois
  falsos positivos (`input` para câmera e formulário web), posteriormente
  corrigidos.
- Benchmark histórico de perguntas gerais com pergunta removida do índice:
  **192/278 corretas, 44 erradas, 42 abstenções**, sem alteração.
- O relatório detalhado e os testes estão em
  `experimento_entrada_usuario.py` e `testes_entrada_usuario.py`.

Os resultados foram utilizados para guiar o desenvolvimento e **não
significam compreensão geral, precisão de 100% fora dessas baterias nem
capacidade de programar arbitrariamente**. Melhorias posteriores exigem
casos novos e aferição independente.

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
