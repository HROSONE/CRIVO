# Fichas avançadas: testes

Exportação determinística de `catalogo-avancado.json`. Síntese autoral; referências remotas precisam de conferência editorial. Acervo não integrado ao runtime.

## testes_unit-integration — Unidade, integração e E2E

**Definição:** Escopos de teste verificam lógica isolada, componentes conectados e fluxo real respectivamente.

**Mecanismo:** Unit é rápido e localizado; integração encontra contrato/infra; E2E cobre comportamento visível com maior custo.

**Falhas comuns:** Mocks em toda fronteira podem reproduzir erro da implementação; E2E isolado não localiza falha bem.

**Escolha:** Distribuir testes por risco e manter poucos fluxos completos críticos.

**Verificação proposta:** Inserir bug de integração e verificar teste que realmente o detecta.

**Referências recomendadas:** [Node.js test runner](https://nodejs.org/api/test.html)

## testes_property — Property based testing

**Definição:** Gera entradas e verifica propriedades gerais, com shrinking para contraexemplo menor.

**Mecanismo:** Leis como roundtrip, idempotência e preservação de invariant são melhores que cópia da lógica interna.

**Falhas comuns:** Gerador que exclui casos difíceis gera confiança falsa; propriedade tautológica não protege.

**Escolha:** Definir domínio amplo, edges e oráculo independente.

**Verificação proposta:** Testar sort preserva multiset e ordem; serialização com perdas documentadas.

**Referências recomendadas:** [fast-check documentation](https://fast-check.dev/docs/)

## testes_fuzz — Fuzzing e entrada adversarial

**Definição:** Fuzzing explora entradas para encontrar crashes, hangs e violações.

**Mecanismo:** Coverage-guided melhora exploração; harness precisa isolamento, deadlines e limite de recursos.

**Falhas comuns:** Não encontrar crash não prova segurança; oráculo limitado ignora saída incorreta.

**Escolha:** Usar parsers, protocolos e boundaries complexas com corpus seed e regressões mínimas.

**Verificação proposta:** Mutar comprimento, encoding, nesting e frames parciais.

**Referências recomendadas:** [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

## testes_mutation — Mutation testing

**Definição:** Altera implementação para medir se testes detectam mudanças relevantes.

**Mecanismo:** Mutantes sobreviventes podem indicar falta de assertions ou casos; alguns são equivalentes.

**Falhas comuns:** Cobertura de linha alta não prova que resultado é verificado; score não é objetivo isolado.

**Escolha:** Aplicar em regras críticas e revisar sobreviventes por significado.

**Verificação proposta:** Trocar operador de limite e verificar caso de fronteira mata mutante.

**Referências recomendadas:** [Node.js test runner](https://nodejs.org/api/test.html)

## testes_browser-tests — Automação de navegador

**Definição:** Teste real observa DOM, rede, navegação e interação em engine.

**Mecanismo:** Locators por role/nome e auto-wait reduzem fragilidade; controlar dados/tempo evita dependência externa.

**Falhas comuns:** sleep fixo fica flaky/lento; teste que só vê screenshot pode perder semântica e acessibilidade.

**Escolha:** Verificar usuário consegue completar tarefa, incluindo falha/estado vazio.

**Verificação proposta:** Testar reload, keyboard, erro de API e request/response esperados.

**Referências recomendadas:** [Playwright documentation](https://playwright.dev/docs/intro)

## testes_determinism — Tempo e aleatoriedade controláveis

**Definição:** Clock, RNG e scheduling são dependências que influenciam reprodutibilidade.

**Mecanismo:** Injetar interfaces permite testar deadline, expiração e jitter sem sleeps; seeds reproduzem casos quando algoritmo é estável.

**Falhas comuns:** Fake timers não simulam rede/loop integralmente; seed não controla nondeterminismo concorrente.

**Escolha:** Testar lógica com controle e reservar integração com relógio real para contratos relevantes.

**Verificação proposta:** Verificar expiração na borda, retry budget e cancelamento.

**Referências recomendadas:** [Node.js test runner](https://nodejs.org/api/test.html)

## testes_sort-property — Leis de ordenação como oráculo

**Definição:** Teste de sort pode verificar ordem e preservação do multiset sem copiar algoritmo.

**Mecanismo:** Geradores com duplicatas/boundaries e comparator coerente cobrem famílias de entrada.

**Falhas comuns:** Comparar só primeiro/último elemento permite perda/duplicação do meio passar.

**Escolha:** Verificar cardinalidade, multiset, monotonicidade e estabilidade se prometida.

**Verificação proposta:** Gerar todos arrays pequenos sobre alfabeto limitado e mutar implementação.

**Relações:** testes_property

**Referências recomendadas:** [fast-check documentation](https://fast-check.dev/docs/)

## testes_linearizability-test — Histórias concorrentes

**Definição:** História registra invocações/respostas para verificar existência de ordem sequencial legal.

**Mecanismo:** Checking precisa respeitar real-time order e modelo do objeto; espaço cresce e requer limites.

**Falhas comuns:** Ordenar por timestamp final não prova linearizability; teste de stress sem oráculo só observa crash.

**Escolha:** Definir modelo pequeno e explorar interleavings controlados.

**Verificação proposta:** Contador/fila com operações sobrepostas deve corresponder a ordem legal.

**Relações:** distribuidos_consistency

**Referências recomendadas:** [Jepsen consistency models](https://jepsen.io/consistency)

## testes_model-based — Model based testing

**Definição:** Modelo simples de estado serve de referência para sequências de comandos.

**Mecanismo:** Gerador escolhe operações válidas/inválidas e compara observações; shrinking reduz sequência de falha.

**Falhas comuns:** Modelo que copia implementação herda bug; assert só no fim pode perder transição ilegal transitória.

**Escolha:** Especificar modelo independente e invariant depois de cada comando.

**Verificação proposta:** Fila/LRU: comparar estado e outputs por sequência; reproduzir seed/caso mínimo.

**Relações:** testes_property

**Referências recomendadas:** [fast-check documentation](https://fast-check.dev/docs/)

## testes_time-travel — Relógio virtual e deadlines

**Definição:** Clock injetado permite testar política temporal sem atraso real.

**Mecanismo:** Deadline inclui espera e execução; clock monotônico não sofre ajuste civil; scheduler fake deve modelar callbacks necessários.

**Falhas comuns:** Sleep de 10ms deixa teste dependente de carga; fake clock não simula I/O real.

**Escolha:** Isolar lógica de tempo e manter testes reais só para integração do host.

**Verificação proposta:** Avançar relógio até antes/na/depois da borda e verificar transições.

**Relações:** testes_determinism

**Referências recomendadas:** [Node.js test runner](https://nodejs.org/api/test.html)

## testes_fault-injection — Injeção de falhas por etapa

**Definição:** Falha controlada revela comportamento em janelas raras de efeito/commit/cleanup.

**Mecanismo:** Criar hooks de teste/adapters permite parar antes/depois de write, publish, ack e response.

**Falhas comuns:** Testar só exceção antes do efeito não cobre efeito cometido com confirmação perdida.

**Escolha:** Enumerar pontos de falha e resultado legal antes de testar.

**Verificação proposta:** Crash após commit, antes de resposta; reexecutar com chave e verificar efeito único.

**Relações:** distribuidos_idempotencia

**Referências recomendadas:** [Google Site Reliability Engineering](https://sre.google/books/)

## testes_parser-equivalence — Equivalência entre fragmentações

**Definição:** Parser incremental correto deve observar mesma mensagem independentemente de chunk boundaries.

**Mecanismo:** Oracle pode ser parser de referência ou resultado esperado fixo; tamanho total/EOF devem ser parte do contrato.

**Falhas comuns:** Testar um chunk por mensagem não exercita incrementalidade real.

**Escolha:** Fragmentar cada posição e combinações pequenas; testar estado parcial/erro terminal.

**Verificação proposta:** Header/payload dividido byte a byte e múltiplos frames no chunk.

**Relações:** fronteira_streaming-parsers

**Referências recomendadas:** [Node.js test runner](https://nodejs.org/api/test.html)

