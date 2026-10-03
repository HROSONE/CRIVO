# Fichas avançadas: testes

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

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


