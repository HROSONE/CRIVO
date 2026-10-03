# Sistemas, memória e concorrência — modelo mental profundo

## 1. Processo, thread e endereço
Process é unidade de isolamento/recursos definida pelo OS; thread é fluxo de execução dentro de processo e normalmente compartilha address space. Distinções exatas são OS/runtime-dependent. User thread, kernel thread e task não são sinônimos universais.

## 2. Virtual memory
Virtual address é traduzido para physical mapping por page tables/TLB. Page fault pode significar demand paging, copy-on-write ou acesso inválido dependendo do caso. Virtual memory fornece abstração/isolation; não significa simplesmente 'usar disco como RAM'.

## 3. Stack e heap
Stack/heap são modelos/regiões de runtime, não propriedades universais da linguagem. Stack frames costumam conter control/local state; heap suporta lifetime não estritamente LIFO. Escape analysis pode mover/eliminar allocations. 'Objeto sempre fica no heap' é frequentemente falso como garantia de linguagem.

## 4. Allocation e lifetime
Manual allocation exige ownership discipline; GC rastreia reachability segundo algoritmo/runtime, não 'objetos sem uso' semanticamente. Reference counting não coleta cycles sozinho. Tracing GC inclui mark-sweep/copying/generational/concurrent variants com trade-offs de pause, throughput e memory.

## 5. RAII e ownership
RAII liga resource lifetime a object lifetime/destruction. Rust ownership/borrowing busca garantir memory safety e data-race freedom para safe code por regras de ownership, references e lifetimes; `unsafe` cria obrigações explícitas que o compilador não verifica integralmente.

## 6. Undefined behavior
Em C/C++, UB permite ao implementation/compiler assumir que certos estados não ocorrem; não significa resultado aleatório específico. Signed overflow em C/C++ pode ser UB em contextos definidos pelo standard; comportamento depende de linguagem/operação. Nunca raciocinar sobre UB como se hardware behavior fosse garantia.

## 7. Data race vs race condition
Race condition é dependência incorreta de timing/interleaving em sentido amplo. Data race tem definição mais formal ligada a conflicting accesses sem synchronization/happens-before em memory model específico. Pode haver race condition sem data race.

## 8. Atomicity, visibility, ordering
Atomic operation evita observação de estado parcial segundo garantias da operação, mas não resolve automaticamente invariant composto. Visibility e ordering dependem do memory model. `volatile` não é mutex e em Java/C/C++ possui semânticas diferentes.

## 9. Happens-before
Happens-before é relação formal usada para raciocinar sobre visibility/order, não simplesmente wall-clock order. Synchronization operations podem criar edges; ausência deles pode permitir reorderings/compiler/CPU effects dentro do modelo.

## 10. Mutex
Mutex fornece mutual exclusion; correctness exige proteger o invariant certo em todas as paths. Lock não torna algoritmo automaticamente deadlock-free/fair. Granularity afeta contention e complexity.

## 11. Deadlock
Condições clássicas de Coffman: mutual exclusion, hold-and-wait, no preemption, circular wait. Quebrar uma condição pode prevenir classe de deadlocks. Lock ordering é técnica comum. Timeout detecta/mitiga alguns casos, não prova ausência.

## 12. Livelock e starvation
Deadlock: ninguém progride. Livelock: atores continuam reagindo mas não completam trabalho. Starvation: um participante é indefinidamente privado de progresso. Fairness depende de scheduler/primitives.

## 13. Semaphores/condition variables
Semaphore representa permits/counting synchronization. Condition variable permite aguardar mudança de predicate associada a lock; esperar em loop rechecando predicate lida com spurious wakeups/competition. Notification não é armazenamento de estado.

## 14. Lock-free/wait-free
Lock-free garante system-wide progress; wait-free garante per-operation bounded progress para cada thread sob definição. Non-blocking não significa faster. ABA, reclamation e memory ordering tornam estruturas lock-free difíceis.

## 15. Async vs parallel
Async estrutura waiting/concurrency sem exigir múltiplos cores. Parallelism executa trabalho simultaneamente. Event loop pode lidar com muitas I/O tasks numa thread, mas CPU-bound work ainda bloqueia loop se não delegado.

## 16. Futures/promises/coroutines
Representam/compoem computation assíncrona de formas runtime/language-specific. `await` geralmente suspende coroutine/task, não necessariamente OS thread. Blocking call dentro de async path pode destruir scalability.

## 17. Channels/actors
Message passing reduz shared mutable state, mas não elimina races lógicas, deadlock/protocol bugs ou backpressure. Actor isolation depende do runtime e do que pode ser compartilhado.

## 18. Backpressure
Producer faster than consumer gera queue growth, latency e memory pressure. Estratégias: bounded queues, blocking, dropping, batching, rate limiting, demand signaling. Escolha depende de semantics de perda.

## 19. Cache/locality
CPU caches exploram temporal/spatial locality. Estrutura assintoticamente equivalente pode diferir drasticamente por locality. False sharing ocorre quando independent data de threads ocupa mesma cache line e coherence gera tráfego.

## 20. Debugging concorrente
Heisenbugs mudam com instrumentation/timing. Usar thread sanitizers/race detectors quando disponíveis, deterministic tests/model checking para protocolos pequenos, tracing com IDs, lock-order diagnostics e stress. 'Adicionar sleep' não corrige sincronização.

## 21. Invariants
Exemplo producer-consumer bounded buffer: `0 <= size <= capacity`; enqueue/dequeue devem preservar invariant; waits dependem de predicates `not_full/not_empty`. Raciocinar por invariant é mais robusto que decorar API.

## 22. Segurança
Memory corruption pode virar vulnerability. Bounds/use-after-free/double-free/uninitialized access têm classes distintas. Memory-safe language reduz classes, não elimina injection, auth bugs, logic errors, resource exhaustion ou unsafe FFI.

## Mapa de recuperação
`travamento circular -> deadlock`; `CPU 100%, sem progresso -> livelock/spin candidate`; `resultado muda por timing -> race candidate`; `async lento -> blocking/event-loop/backpressure`; `segfault após free -> lifetime/UAF`; `alto cache miss -> locality/layout`; `contador atomic mas invariant quebra -> compound atomicity`.

**Treinamento:** nenhum. **Integração:** nenhuma.