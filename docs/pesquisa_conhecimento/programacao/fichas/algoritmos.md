# Fichas avançadas: algoritmos

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## algoritmos_correcao — Prova por invariante

**Definição:** Invariante é propriedade preservada por transições; correção exige inicialização, preservação e conclusão.

**Mecanismo:** Loop invariant relaciona estado parcial ao objetivo; variante estritamente decrescente bem fundada ajuda provar término.

**Falhas comuns:** Passar exemplos não prova todo domínio; complexidade boa sem correção é inútil.

**Escolha:** Escrever pré/pós-condições e invariant antes de otimizar.

**Verificação proposta:** Provar busca binária e testar boundaries vazio/unitário/duplicados.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## algoritmos_complexidade — Complexidade e modelo de custo

**Definição:** O, Omega e Theta descrevem limites assintóticos sob variável e modelo definidos.

**Mecanismo:** Tempo pode depender de n, m, tamanho de número e distribuição. Amortizado analisa sequência, não média probabilística.

**Falhas comuns:** Ignorar tamanho do output/operandos ou chamar todo loop de O(n) distorce análise.

**Escolha:** Declarar unidade de custo e pior caso, esperado e amortizado separadamente.

**Verificação proposta:** Derivar custo de loops aninhados com bounds dependentes e output grande.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## algoritmos_amortizado — Análise amortizada

**Definição:** Limita custo por operação numa sequência mesmo com operações individuais caras.

**Mecanismo:** Método agregado, contábil e potencial distribuem custos; crescimento geométrico de vetor produz append amortizado constante.

**Falhas comuns:** Expandir capacidade por incremento constante pode dar custo total quadrático; amortizado não garante latência individual.

**Escolha:** Escolher estrutura pela necessidade de throughput e cauda de latência.

**Verificação proposta:** Calcular soma de cópias em doubling versus crescimento linear.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## algoritmos_binary-search — Busca binária e monotonicidade

**Definição:** Busca reduz intervalo mantendo que solução, se existir, está na região candidata.

**Mecanismo:** Boundaries half-open simplificam lower_bound; predicado precisa ser monotônico e índices precisam progredir.

**Falhas comuns:** Off-by-one, midpoint incorreto e condição que não reduz intervalo causam falha ou loop infinito.

**Escolha:** Usar para sorted search ou resposta viável monotônica, com invariant explícito.

**Verificação proposta:** Testar vazio, todos menores/maiores, repetidos e primeiro/último.

**Invariantes:** 0 <= left <= right <= n; prefixo < alvo; sufixo >= alvo

**Complexidade:** O(log n) comparações, O(1) memória extra; array sorted, comparações de custo constante.

**Modelo formal:** lower_bound = min({i | a[i] >= x} ∪ {n})

**Pré-requisitos:** algoritmos_correcao, algoritmos_complexidade

**Exemplo local:** exemplos/padroes.mjs#lowerBound

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## algoritmos_graphs — BFS, DFS e representação

**Definição:** Grafos modelam entidades e arestas; lista de adjacência versus matriz muda memória e operações.

**Mecanismo:** BFS encontra menor número de arestas em grafo não ponderado; DFS detecta estruturas com estados de visita.

**Falhas comuns:** Recursão profunda estoura stack JS; marcar visita tarde pode duplicar trabalho.

**Escolha:** Selecionar representação por densidade e traversal por objetivo.

**Verificação proposta:** Testar desconexo, ciclo, self-loop, multiaresta e 100 mil nós.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## algoritmos_dijkstra — Caminhos mínimos

**Definição:** Dijkstra requer pesos não negativos; Bellman-Ford pode lidar com negativos e detectar ciclos negativos alcançáveis.

**Mecanismo:** Priority queue com stale entries exige descarte; relaxação atualiza distância e predecessor.

**Falhas comuns:** Peso negativo invalida prova de Dijkstra; Infinity e overflow precisam cuidados.

**Escolha:** Escolher algoritmo pelo modelo de pesos e necessidade de detectar impossibilidade.

**Verificação proposta:** Testar zero, negativo, inacessível, empate e reconstrução do caminho.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## algoritmos_topological — Ordenação topológica e ciclos

**Definição:** DAG admite ordem que respeita dependências; grafo cíclico não admite ordem completa.

**Mecanismo:** Kahn remove vértices indegree zero; DFS usa estados/stack de caminho para detectar back edge.

**Falhas comuns:** Visitação booleana sozinha pode confundir nó finalizado com nó ativo; ordem não é necessariamente única.

**Escolha:** Usar para builds, migrações e scheduling com diagnóstico de ciclo.

**Verificação proposta:** Testar múltiplas ordens válidas, cycle e componente isolado.

**Invariantes:** Indegree corresponde às arestas restantes; todo nó emitido tem dependências já emitidas.

**Complexidade:** O(V+E) tempo e memória com lista de adjacência e fila indexada.

**Pré-requisitos:** algoritmos_graphs

**Exemplo local:** exemplos/padroes.mjs#topologicalOrder

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## algoritmos_scc — Componentes fortemente conexas

**Definição:** SCC agrupa nós mutuamente alcançáveis em grafo dirigido.

**Mecanismo:** Tarjan/Kosaraju produzem componentes; condensação vira DAG para análise de dependências.

**Falhas comuns:** Conectividade não dirigida não equivale a forte conexão; stack recursion pode ser limite.

**Escolha:** Usar para ciclos e modularização de dependências.

**Verificação proposta:** Validar mutual reachability em grafos pequenos e condensação acíclica.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## algoritmos_dp — Programação dinâmica

**Definição:** DP reutiliza soluções de subproblemas quando estado captura informação necessária para futuro.

**Mecanismo:** Recorrência, base e ordem devem eliminar dependências não resolvidas; memo e tabulation têm trade-offs de stack/memória.

**Falhas comuns:** Estado que omite informação relevante produz solução errada; memoizar problema sem overlap não ganha.

**Escolha:** Derivar estado e prova de optimal substructure antes de implementar.

**Verificação proposta:** Comparar com brute force em tamanhos pequenos e testar base/limites.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## algoritmos_greedy — Algoritmos greedy

**Definição:** Greedy escolhe decisão local e precisa prova de que ela pode integrar solução ótima.

**Mecanismo:** Exchange argument ou estrutura matemática pode justificar escolha; não basta parecer intuitiva.

**Falhas comuns:** Coin change greedy falha para conjuntos arbitrários de moedas.

**Escolha:** Usar só com prova ou como heurística explicitamente aproximada.

**Verificação proposta:** Encontrar contraexemplo mínimo e comparar com DP/brute force.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## algoritmos_sort — Ordenação e estabilidade

**Definição:** Ordenação requer relação coerente; estabilidade preserva ordem relativa de itens equivalentes.

**Mecanismo:** Comparison sorting tem limite inferior sob modelo; counting/radix usam restrições de representação/chaves.

**Falhas comuns:** Comparator não transitivo invalida resultado; locale comparison tem custo e semântica específicos.

**Escolha:** Escolher pelo domínio, estabilidade, memória e tamanho; não inferir implementação de sort do runtime.

**Verificação proposta:** Testar antisymmetry/transitivity, duplicatas e dados adversariais.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## algoritmos_complexity-hard — P, NP e reduções

**Definição:** P classifica decisão com algoritmo polinomial; NP admite certificado verificável em tempo polinomial.

**Mecanismo:** NP-complete combina pertença e NP-hardness sob redução; NP-hard não exige estar em NP.

**Falhas comuns:** NP não significa não polinomial provado; resultado teórico não impede casos práticos solúveis.

**Escolha:** Escolher exato, aproximação ou heurística por escala/garantia e estrutura do problema.

**Verificação proposta:** Construir redução na direção correta e definir problema de decisão.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)


