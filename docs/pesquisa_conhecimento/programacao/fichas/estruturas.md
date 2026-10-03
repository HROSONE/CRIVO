# Fichas avançadas: estruturas

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## estruturas_hash — Hash tables e colisões

**Definição:** Hash mapeia chaves a buckets; colisões exigem resolução e política de redimensionamento.

**Mecanismo:** Custo esperado pode ser constante com condições sobre hash/carga, mas pior caso depende da implementação.

**Falhas comuns:** Hash fraco em entrada hostil gera degradação; ordem e igualdade de chave precisam contrato.

**Escolha:** Usar quando lookup predomina, mas considerar adversário e bounds de memória.

**Verificação proposta:** Testar colisões, resize, delete e workload com chaves repetidas.

**Complexidade:** O(1) esperado sob hipóteses adequadas de hash/load factor; pior caso depende da estrutura.

**Pré-requisitos:** algoritmos_complexidade, algoritmos_amortizado

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## estruturas_heap — Heap e priority queue

**Definição:** Heap mantém propriedade de prioridade entre pai/filhos sem ordenação total do array.

**Mecanismo:** Inserção/extract tipicamente O(log n); heapify bottom-up O(n). Comparator determina direção e empates.

**Falhas comuns:** Iterar heap não produz sequência ordenada; decrease-key pode exigir índice ou lazy duplicates.

**Escolha:** Usar para top-k, scheduler e seleção repetida de extremos.

**Verificação proposta:** Verificar invariant após operação e comparar extrações com sort de referência.

**Invariantes:** Prioridade do pai não é menor que a do filho no max-heap.

**Complexidade:** Insert/extract O(log n), peek O(1), heapify O(n) sob modelo padrão.

**Pré-requisitos:** algoritmos_complexidade

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## estruturas_trees — Árvores balanceadas

**Definição:** BST ordena chaves; balanceamento evita altura linear em entradas desfavoráveis.

**Mecanismo:** AVL e red-black usam rotações/invariantes diferentes; B-trees otimizam acesso em páginas.

**Falhas comuns:** BST simples com inserção sorted vira lista; duplicatas exigem política.

**Escolha:** Escolher pela necessidade de range/order e perfil memória/disco.

**Verificação proposta:** Testar sequência sorted, delete raiz, duplicatas e invariant de balanceamento.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## estruturas_trie — Tries e busca por prefixo

**Definição:** Trie organiza caminhos por unidades de chave e compartilha prefixos.

**Mecanismo:** Custo depende de comprimento e representação de filhos; compactação reduz nós e overhead.

**Falhas comuns:** Unicode code units versus grafemas altera semântica; trie denso pode desperdiçar memória.

**Escolha:** Usar para prefixos/autocomplete com normalização definida e métricas reais.

**Verificação proposta:** Testar prefixo vazio, chave prefixo de outra e Unicode normalizado.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## estruturas_union-find — Disjoint set union

**Definição:** Union-find mantém partição em componentes com find e union.

**Mecanismo:** Path compression e union by rank/size dão custo amortizado muito baixo sob análise conhecida.

**Falhas comuns:** Não suporta remoção/arbitrária divisão de componente sem outra abordagem; rank não é altura atual após compression.

**Escolha:** Usar para conectividade incremental e Kruskal.

**Verificação proposta:** Comparar com componentes por BFS e verificar união repetida.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)

## estruturas_probabilistic — Bloom filters e aproximação

**Definição:** Bloom filter responde possível presença com falso positivo, sem falso negativo sob inserções/estrutura intacta.

**Mecanismo:** Número de bits e hashes controla erro; não permite delete ingênuo sem variante específica.

**Falhas comuns:** Tratar possível presente como prova perde dados; taxa aumenta com carga.

**Escolha:** Usar para evitar lookup caro sem tomar decisão autoritativa.

**Verificação proposta:** Medir falso positivo com dados não inseridos e checar inseridos.

**Referências recomendadas:** [MIT 6.006 Introduction to Algorithms](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/)


