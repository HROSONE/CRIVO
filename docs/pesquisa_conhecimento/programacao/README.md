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