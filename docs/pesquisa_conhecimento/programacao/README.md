# Base de conhecimento de programação — arquitetura

**Branch:** `pesquisa/base-programacao-avancada`
**Objetivo:** construir conhecimento recuperável de ciência da computação e engenharia de software, separado de treino/integração.

## Estado inicial auditado
O CRIVO já possui cobertura introdutória de fundamentos, Python, JavaScript, HTML, CSS, SQL, Git, HTTP e debugging. A avaliação existente registra 122 assuntos, 459 perguntas e 31 exemplos no conjunto avaliado; a própria avaliação ressalva que retrieval correto não prova geração de código. Java, C++, Rust/compiladores, drivers e sistemas maiores aparecem explicitamente fora do escopo atual.

## Modelo de conhecimento
Cada unidade avançada deve registrar quando aplicável: `id | domínio | conceito | definição | pré-requisitos | mecanismo | invariantes | modelo formal | complexidade | implementação | exemplos | contraexemplos | falhas comuns | debugging | trade-offs | segurança | relações | fontes`.

Recuperação deve privilegiar conceitos e relações, não decorar formulações de perguntas. Ex.: `race condition -> shared mutable state -> interleaving -> critical section -> synchronization -> mutex/atomic/channel -> memory model`.

## Currículo
1. Matemática discreta, lógica, conjuntos, relações, grafos, combinatória e probabilidade.
2. Algoritmos: correção, invariantes, complexidade, recursão, divide-and-conquer, greedy, dynamic programming, graph algorithms, randomized/approximation.
3. Estruturas: arrays, linked structures, stacks/queues, hash tables, trees, heaps, tries, union-find, graphs, probabilistic structures.
4. Paradigmas e linguagens: imperative, OO, functional, declarative; Python, JS/TS, Java/Kotlin, C/C++, C#, Rust, Go e SQL.
5. Type systems e semântica: static/dynamic, nominal/structural, generics, variance, algebraic types, inference, effects.
6. Memória: stack/heap, allocation, GC, RAII, ownership/borrowing, aliasing, lifetime, locality/cache.
7. Concorrência/paralelismo: threads, async, races, locks, atomics, memory ordering, actors/channels, deadlock/livelock/starvation.
8. Sistemas operacionais: processes, syscalls, scheduling, virtual memory, filesystems, IPC, permissions.
9. Arquitetura: ISA, pipelines, caches, branch prediction, SIMD, multicore, coherence.
10. Redes: Ethernet/IP/TCP/UDP/TLS/DNS/HTTP, congestion, routing, sockets, failure.
11. Bancos: relational algebra, indexes/B-trees, query plans, transactions, isolation, MVCC, WAL, replication.
12. Compiladores: lexing, parsing, AST, semantic analysis, IR, optimization, codegen, linking, JIT.
13. Distribuídos: partial failure, clocks, consensus, replication, partitioning, consistency, idempotency, queues.
14. Engenharia: requirements, modularity, APIs, architecture, testing, debugging, observability, CI/CD, versioning.
15. Segurança defensiva: threat modeling, memory safety, authn/authz, injection, XSS/CSRF, crypto concepts, secrets, supply chain.
16. Web/mobile/backend/cloud: browser/runtime, frontend state, REST/RPC, Android, containers, orchestration, deployment.
17. Performance: profiling, asymptotics vs constants, locality, allocation, I/O, contention, benchmarking.
18. Software correctness: contracts, property testing, fuzzing, static analysis, model checking/formal verification.

## Critério de profundidade
Saber nome/definição = básico. Explicar mecanismo e trade-offs = intermediário. Derivar comportamento, diagnosticar falha e escolher estrutura = avançado. Relacionar modelos formais, implementação real, limites, performance, segurança e evidência/standards = especialista.

## Regra epistemológica
Documentação oficial/specification/standard é fonte primária para comportamento de linguagem/protocolo. Livro/paper pode explicar teoria. Exemplo de código não substitui especificação. Implementation detail não deve ser apresentado como garantia da linguagem. Versões importam.

## Regra de avaliação
Separar: (a) retrieval conceitual; (b) explicação; (c) leitura de código; (d) previsão de execução; (e) debugging; (f) geração; (g) design; (h) revisão; (i) generalização para problema novo. Acerto em (a) não prova (f)-(i).

**Treinamento:** nenhum. **Integração:** nenhuma.
## Ampliação de 03/10/2026: acervo avançado

200 fichas autorais em 22 domínios; 60 dedicadas diretamente a JavaScript/TypeScript.
Cada ficha traz definição, mecanismo, falhas, critério de escolha, verificação proposta e referência.
Invariantes, complexidade, pré-requisitos, relações e exemplos locais foram adicionados onde
há modelo específico. A lista de fontes é referência recomendada; sua conferência remota/editorial
está pendente nesta execução. O conteúdo não é transcrição de documentação externa.

### Ler e consultar
- [Catálogo estruturado](catalogo-avancado.json): fonte de verdade das 200 fichas.
- [Semântica JavaScript](03-javascript-semantica-e-runtime.md).
- [Modelagem TypeScript](04-typescript-modelagem-e-contratos.md).
- [Backend, transações e falhas](05-backend-transacoes-e-falhas.md).
- [Segurança web](06-seguranca-web-e-fronteiras.md).
- [Roteiro para gerar projetos do zero](07-gerar-projetos-do-zero.md).
- [Fichas por domínio](fichas/): exportação Markdown do catálogo.
- [Exemplos e limites](exemplos/README.md): 14 implementações, 27 testes Node e fixtures TS.
- [40 desafios de projeto](desafios-projetos.json): material didático público, não holdout.
- [Manifesto](manifesto.json): contagens, bytes e SHA-256 para reproduzir auditoria.
- [Resultado da validação](VALIDACAO.md): checks efetivamente executados e pendências.

```sh
python scripts/acervo_programacao.py --validar
python scripts/acervo_programacao.py --buscar "typescript narrowing unknown" --limite 5
node --test docs/pesquisa_conhecimento/programacao/exemplos/padroes.test.mjs
tsc -p docs/pesquisa_conhecimento/programacao/exemplos/tsconfig.json
```

A busca é lexical determinística, com normalização de acentos e peso de título; não
é busca semântica nem integração ao chatbot. Retornar ficha não garante que ela responda
completamente à consulta. Catálogo/Markdown são duas representações do mesmo conteúdo,
e não devem ser contados como conhecimentos diferentes.

### Cobertura e plano de integração futuro
JavaScript/TypeScript, web, React, redes, backend, dados, segurança, algoritmos,
estruturas, sistemas, compiladores, arquitetura, testes, engenharia, operação,
corretude, geração e fronteira; panorama comparativo de Python/Rust/Go/C++/Java/C#.
Conteúdo de GPU, CRDTs, efeitos e concorrência estruturada tem limites de aplicação
e suporte registrados. Este acervo é amplo, mas não cobre literalmente toda programação.

Antes de integrar: conferir fontes por edição/runtime; revisar fichas; transformar
unidades em formato do recuperador escolhido; medir precisão e recall com paráfrases
novas; conservar IDs/proveniência; isolar treino e avaliação por famílias; só promover
geração após testes executáveis independentes. Não acrescentar os desafios públicos
ao treino e depois chamá-los de avaliação externa.

**Estado:** pesquisa expandida, sem treinamento, sem mudança no runtime e sem
capacidade de geração/senioridade demonstrada. Quantidade de fichas não certifica competência.

