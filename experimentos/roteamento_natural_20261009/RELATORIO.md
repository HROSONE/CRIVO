# Roteamento natural e fidelidade da tarefa — 2026-10-09

O candidato aciona a peça correta com evidência de resposta pertinente em **23/25** casos reais congelados, contra **0/25** na linha de base selecionada entre falhas anteriores. Há **zero desvios proibidos**, **zero trocas de domínio** e **zero casos com referentes ausentes**. Isso atende à meta desta etapa (18/25), sem demonstrar conversa livre geral.

| Medida no mesmo conjunto | Baseline | Candidato |
|---|---:|---:|
| Peça correta com evidência na resposta | 0/25 | 23/25 |
| Casos com desvios proibidos | 17 | 0 |
| Casos com troca de domínio identificada | 5 | 0 |
| Casos com referentes ausentes | 18 | 0 |

## Protocolo preservado

- Os 25 exemplos são extraídos exclusivamente dos registros da [auditoria pública anterior](../auditoria_usuario_20261009/RELATORIO.md). Nenhum caso inventado entra nessa pontuação.
- O commit `d4b44c0` congela o conjunto e `ac30c6c` registra o baseline **antes de qualquer edição no motor**.
- SHA-256 do conjunto: `c75845b1488ea1539fc4c69c5f5ccd9e74280a3a67ef4af9360f062f28836c2d`.
- Cada entrada usa o turno atual e até dois turnos anteriores de usuário, pelo adaptador HTTP padrão, sem memória preenchida pelo avaliador. Não se infere informação eliminada pelo recorte de contexto.
- O baseline original permanece em `baseline.json`. `baseline_reavaliada.json` aplica às mesmas respostas a correção do radical `própr` (próprio/próprios) e as métricas adicionais. Os casos e seu SHA não mudaram. O score principal continua 0/25.
- `candidato.json` identifica o código medido: `8734914f13117dcfe61a65a225117f26e7e7f277`. `candidato_corrigido_ci.json` mede o ajuste de prioridade e de descrição das capacidades, no commit `ca69a49ece5f67b4e99949b0a7d168eb1b2bbcfd`, com os mesmos 23/25 e zero desvios. Os dois snapshots foram preservados.
- Rótulos de rota não bastam: o avaliador exige executor efetivo, estado executado, guarda aceita, conteúdo mínimo e ausência de desvios proibidos. Esclarecimentos da guarda não recebem ponto como escrita.

## O que mudou

O seletor na compreensão de intenção usa operadores explícitos e o estado já existente: pessoas da sessão, orçamento e hipótese, fichas mostradas e última escrita. Ele antecede o recuperador por associação de palavras e despacha para memória, cálculo, composição factual, programação, escrita ou esclarecimento. Entradas sem uma operação reconhecida conservam as rotas anteriores.

A memória existente passa a ler declarações compostas, parentesco antes do nome e correções pronominais não ambíguas. Cada fato conserva a mensagem **integral do usuário** como fonte. Citações, ficção, hipóteses e perguntas continuam protegidas; não foi criado outro coletor.

O cálculo existente passa a reconhecer reservas de minutos e limites de orçamento. A projeção de descanso permanece hipotética; uma correção real atualiza valores e fontes sem confirmar a alternativa. A falta de orçamento ou de duração provoca um esclarecimento pertinente. Uma conta avulsa é interpretada condicionalmente, sem inventar quais atividades foram subtraídas.

Antes da entrega, a guarda confere tipo da resposta, unidades e valores calculados, atividades, preferências, unidades factuais selecionadas, referentes e quantidade explícita de frases. Uma saída rejeitada não vira uma história entregue nem permanece como resposta anterior oculta.

## Limites observados

- **real-19:** o gerador autoral mantém a capivara astronauta, mas produz três frases quando o pedido exige cinco. A guarda rejeita o rascunho e oferece esclarecer o formato. Não se conta como história realizada.
- **real-20:** como a história anterior não foi entregue, não se inventa um texto anterior para alterar. A resposta conserva capivara astronauta e amigo e pede esclarecimento. Não se conta como revisão realizada.
- **real-22:** o pedido chega ao motor próprio de programação, que informa seu limite para o laço enviado. As variáveis do trecho são identificadas textualmente; **o código não foi executado nem corrigido**. O ponto mede roteamento pertinente, não suporte geral a JavaScript.
- **real-13 e real-17:** faltam dados no contexto congelado. O cálculo pede as informações necessárias; não cria durações ou um orçamento por adivinhação.
- O exemplo cotidiano e a explicação infantil usam composição de fatos existentes. A adaptação de linguagem continua limitada; não se demonstrou ensino livre nem raciocínio causal aprendido.

O conjunto é uma regressão conhecida usada no desenvolvimento, **não uma avaliação cega de generalização**. A camada estrutural é limitada; ainda será preciso avaliar paráfrases e tarefas não vistas em uma etapa separada, sem modificar esse conjunto.

## Pesos e integração

Não houve treino, alteração de pesos, aumento de parâmetros, ampliação de acervo nem integração de modelo externo. Os hashes dos checkpoints ativos `artefatos/geracao_pt/pesos_numpy.npz`, `rede_geracao.json` e `rede_intencao_gerativa.json` coincidem com os da auditoria. O Transformer que já realizava fatos da sessão continua disponível, com suas guardas anteriores.

O job `roteamento-natural` verifica os contratos e reproduz os 25 casos, exigindo a meta. Usa somente logs e saída temporária, sem upload de artefatos. A bateria completa permanece no PR; o push pós-merge conserva a verificação rápida da main.

Comandos reproduzíveis:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest testes_roteamento_natural -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/roteamento_natural_20261009/avaliar.py --saida /tmp/roteamento-natural.json --exigir-meta
```

O próximo trabalho, após integração validada, é a realização supervisionada de tarefa e referentes, especialmente esses dois pedidos de escrita. Esta etapa não inicia esse treinamento.

## Regressões encontradas pelo primeiro CI

O job de conteúdo revelou que “organizar minhas ideias” era interceptado pelo cálculo só por haver tempo disponível. A rota temporal agora exige pedido explícito de tempo ou retomada de resultado/atividades calculadas. O job de programação e a regressão B revelaram a omissão de “rastrear estados” na descrição das capacidades ativas; a descrição foi corrigida, sem ampliar o motor.

As duas causas foram reproduzidas e corrigidas antes de atualizar o PR. Passaram 13 testes de prioridades/hipóteses/guarda, um contrato de capacidades e 67 testes de conteúdo e proveniência. O mesmo conjunto congelado foi reproduzido novamente: 23/25, zero desvios e zero referentes ausentes. Isso não substitui a validação completa do novo commit no CI.
