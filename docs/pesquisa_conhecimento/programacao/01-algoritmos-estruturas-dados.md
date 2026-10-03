# Algoritmos e estruturas de dados — fundamentos avançados

## 1. Modelo de custo
Analisar algoritmo exige definir input size n, operações dominantes e modelo computacional. Big-O dá upper asymptotic bound; Ω lower; Θ tight bound. O(2n) = O(n), mas constantes/cache/alocação importam na prática. Worst, average e amortized são perguntas diferentes.

## 2. Correção
Loop invariant é proposição verdadeira antes/depois de cada iteração. Prova típica: initialization, maintenance, termination. Partial correctness + termination => total correctness. Testes encontram contraexemplos; não constituem prova geral.

## 3. Recorrências
Divide-and-conquer frequentemente produz T(n)=aT(n/b)+f(n). Master theorem cobre famílias específicas, não toda recorrência. Merge sort: Θ(n log n); binary search: Θ(log n). Quicksort average expected Θ(n log n), worst Θ(n²); pivot strategy/distribution importam.

## 4. Amortized analysis
Average-case usa distribuição de inputs; amortized distribui custo de sequência de operações sem probabilidade. Dynamic array append é O(1) amortized apesar de resize ocasional O(n). Métodos aggregate, accounting e potential formalizam.

## 5. Arrays e linked structures
Array oferece random access O(1) sob modelo usual e locality boa; insertion middle O(n). Linked list permite relink O(1) quando node/position já conhecido, mas encontrar posição é O(n), overhead de ponteiros e locality ruim. Não dizer 'linked list insertion é O(1)' sem condição.

## 6. Stack/queue/deque
São ADTs definidos por operações/semântica, não representação. Stack LIFO; queue FIFO; deque nas duas extremidades. Podem ser implementados por arrays/ring buffers/linked structures com trade-offs.

## 7. Hash tables
Expected O(1) lookup depende de hash distribution/load factor/collision strategy. Worst-case pode ser O(n). Separate chaining e open addressing têm propriedades distintas. Resize/amortization e adversarial collision importam. Hash table não mantém ordem total por definição.

## 8. Trees
BST invariant: keys left/right obey ordering relation. Unbalanced BST pode degradar a chain O(n). AVL/red-black mantêm altura O(log n) via invariants/rebalancing. B/B+ trees aumentam branching factor para reduzir I/O/cache misses e são centrais em storage/indexing.

## 9. Heap
Heap garante ordem parcial parent-child; não é sorted array/tree. Binary heap supports find-min/max O(1), insertion e extract O(log n). Build-heap bottom-up é Θ(n), não Θ(n log n), por soma dos custos por altura.

## 10. Tries
Indexam por prefixos/símbolos; custo tende a depender do comprimento da chave, mas memória pode ser alta. Radix/compressed tries reduzem chains. Comparar com hash/B-tree conforme prefix query, ordering e storage.

## 11. Union-Find
Disjoint-set union com union by rank/size + path compression tem custo amortized O(α(n)), inverse Ackermann, praticamente constante em escalas usuais. Aplicações: connected components/Kruskal.

## 12. Graphs
Representação adjacency list ~O(V+E) space; matrix O(V²), com edge lookup direto. BFS encontra shortest paths em unweighted graph. DFS sustenta cycle/topological/SCC reasoning. Dijkstra requer nonnegative edge weights. Bellman-Ford tolera negative edges e detecta reachable negative cycles. Floyd-Warshall all-pairs Θ(V³).

## 13. Minimum spanning tree
Kruskal ordena edges e usa DSU; Prim expande frontier. MST minimiza peso total de spanning tree, não shortest path entre cada par. Confundir MST com shortest-path tree é erro conceitual.

## 14. Topological ordering
Existe somente para DAG. Kahn usa indegrees; DFS pode ordenar por finish time. Se todos vertices não forem processados, há cycle. Ordem pode não ser única.

## 15. Dynamic programming
Aplicável quando há overlapping subproblems e estrutura ótima apropriada. Definir state, transition, base, evaluation order e reconstruction. Memoization top-down e tabulation bottom-up podem ter mesma complexidade assintótica mas comportamento de memória/stack diferente.

## 16. Greedy
Escolha local só é correta quando propriedade pode ser provada (exchange argument, matroid etc.). 'Parece melhor agora' não basta. Dijkstra e Kruskal têm estruturas de correção específicas.

## 17. NP e NP-completeness
P: decidível em polynomial time por deterministic model. NP: solutions verificáveis em polynomial time (equivalent nondeterministic definition). NP-hard não implica estar em NP; NP-complete = em NP e NP-hard. Não se sabe se P=NP.

## 18. Approximation/randomization
Para NP-hard optimization, approximation ratio mede qualidade garantida sob definição. Randomized algorithms podem ter random runtime (Las Vegas) ou bounded error/output (Monte Carlo). Expected complexity precisa declarar fonte de randomness/assumptions.

## 19. Bloom filter
Probabilistic membership: false positives possíveis, false negatives não em implementação padrão sem deletion; bit array + k hashes. Trade-off entre m bits, n items, k hashes e false-positive probability aproximadamente (1-e^{-kn/m})^k sob assumptions.

## 20. Escolha por workload
Estrutura correta depende de operações dominantes, n, memory budget, locality, concurrency, persistence, ordering, adversarial input e implementation/runtime. Complexidade assintótica é uma dimensão, não decisão completa.

## Relações de recuperação
`lookup exact -> hash`; `ordered range -> balanced tree/B-tree`; `priority -> heap`; `prefix -> trie`; `connectivity unions -> DSU`; `unweighted shortest path -> BFS`; `nonnegative weighted shortest -> Dijkstra`; `negative edge -> Bellman-Ford`; `DAG dependencies -> topological`; `overlap subproblems -> DP candidate`. Estas são pistas, não regras cegas.

## Erros que o CRIVO deve rejeitar
- binary search em dados não ordenados sem estrutura equivalente;
- Dijkstra com peso negativo;
- declarar hash lookup worst-case O(1);
- confundir heap com coleção totalmente ordenada;
- dizer que linked list sempre insere O(1);
- aplicar greedy sem argumento de correção;
- dizer NP = 'não polinomial';
- confundir average com amortized.

**Treinamento:** nenhum. **Integração:** nenhuma.