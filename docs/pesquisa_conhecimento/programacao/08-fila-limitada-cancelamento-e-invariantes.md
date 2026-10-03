# Fila limitada: de requisito a implementação verificável

## Contrato
O exemplo `AsyncQueue` em [engenharia.mjs](exemplos/engenharia.mjs) recebe capacidade positiva e limite positivo de waiters por direção. `push` resolve quando o item foi aceito na fila, não quando seu efeito foi processado pelo consumidor. `take` resolve com `{done:false,value}` ou, após drenar e fechar, `{done:true,value:undefined}`. Assim, um item cujo valor é undefined não equivale a EOF.

Produtor aguarda quando não há espaço. Consumidor aguarda quando não há item. Ambas esperas aceitam AbortSignal. Fechar é idempotente; rejeita writers ainda não aceitos, conserva itens já aceitos, drena esses itens e depois encerra readers. Não há reabertura. Esta é uma escolha semântica deliberada: outro produto pode precisar descartar itens ou persistir fila.

## Invariantes
1. `0 <= items.length <= capacity`.
2. Cada waiter pertence a exatamente uma lista enquanto pendente.
3. Cada waiter termina uma vez e remove seu listener de abort.
4. Cancelar waiter não consome item nem fabrica permit.
5. Ordem de entrega é FIFO entre itens aceitos; producers/readers aguardam em ordem da lista.
6. Depois de close, nenhum novo item é aceito e nenhum producer pendente permanece preso.

O pump alterna entrega de itens aos readers e admissão de writers enquanto há progresso. Promise resolve/reject agenda continuations; a operação interna não executa callback da aplicação diretamente. Ainda assim, APIs de host/valores arbitrários devem cumprir o contrato esperado: abstração didática não é defesa contra objetos Proxy hostis.

## Cancelamento na borda
Antes de registrar, checar signal já abortado evita waiter fantasma. Depois do registro, listener remove somente aquele waiter e dispara pump. Ao resolver, cleanup remove listener. A situação importante não é apenas Promise rejeitada: é provar que o waiter rejeitado não absorve o próximo item.

Um consumidor pode ser abortado depois que take resolveu. Nesse caso o item já foi entregue; sinal não desfaz entrega. Para processamento com efeito, a aplicação precisa decidir ack/retry/idempotência. Este exemplo não é broker durável.

## Capacidade não é orçamento total
O limite de itens não limita tamanho em bytes. maxWaiters reduz quantidade de esperas, mas cada waiter também retém seu payload. Um serviço precisa impor máximo por item e orçamento agregado antes de chamar push. Se dados são streams, preferir propagação de backpressure ao longo de toda cadeia.

Implementação usa arrays com shift/splice. Isto favorece legibilidade, mas operações individuais podem ser O(n) no número de itens/waiters. Para throughput alto, usar ring buffer/deque e estrutura de waiters removíveis, mantendo as mesmas propriedades. Medir antes de trocar.

## Evidência e extensão
Os testes exercitam FIFO, undefined, close, producer bloqueado, reader cancelado, writer cancelado, listener removido e fluxo concorrente de 60 valores. Eles não provam correção para todos interleavings/hosts. Extensões úteis: async iterator com retorno/cleanup, budget de bytes, graceful/abort close distintos, métricas de wait time e interface de ack.

**Relações:** js_async-queue, js_semaphore, backend_node-streams, js_resource-budget.

