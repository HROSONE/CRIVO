# JavaScript: raciocinar da linguagem ao runtime

## Camadas que não podem ser confundidas
ECMA-262 define valores, coerções, ambientes léxicos, objetos, funções, módulos e jobs. O navegador adiciona DOM, fetch, timers e event loops. Node adiciona módulos/pacotes, filesystem, streams, processos e worker threads. TypeScript verifica uma aproximação estática dessas operações. Uma decisão de V8 sobre alocação ou JIT não é contrato ECMAScript.

Antes de escrever módulo, declare: host, versão mínima, formato ESM/CJS, entrada externa, recursos, condições de erro, objetivo de escala e política de cancelamento. target de TS controla sintaxe emitida; lib controla declarações; nenhum instala API ausente.

## Prever execução em vez de memorizar snippets
```js
const logs = [];
logs.push('A');
Promise.resolve().then(() => logs.push('C'));
logs.push('B');
// Após o job de reação: A, B, C.
```
O handler da Promise não interrompe execução síncrona. Isto não estabelece ordem universal com todos callbacks de I/O/timers Node. Para perguntas de scheduling, desenhe task corrente, jobs enfileirados, pontos de suspensão e fases do host.

```js
const estado = { n: 1 };
const ler = () => estado.n;
estado.n = 2;
console.log(ler()); // 2
```
Closure captura acesso ao binding/ambiente, não fotografia automática de seus dados. Em UI, função criada por render acessa o snapshot daquele render. Mudança de objeto compartilhado e mudança de binding são problemas diferentes.

## Operações concorrentes com efeitos
```js
let saldo = 100;
async function debitar(valor) {
  const anterior = saldo;
  await Promise.resolve();
  saldo = anterior - valor;
}
```
Duas chamadas podem ler 100 antes de escrever. Uma thread de execução não elimina interleaving lógico em await. No banco, use operação atômica condicionada ou transação adequada. Mutex local não protege outras réplicas. Para dinheiro, precisão, autorização e idempotência também são invariantes.

## Política de erro e cleanup
Toda operação que abre recurso define dono, fechamento, deadline e propagação de erro. finally precisa fechar recurso, mas erro em cleanup pode substituir erro original se política for descuidada. AbortSignal expressa cancelamento cooperativo; retorno de timeout não desfaz efeito remoto. Error.cause conserva contexto técnico; resposta pública deve evitar stack e secrets.

## Performance sem folclore
Medir custo de CPU, allocations, I/O, fila e atraso do loop separadamente. Mover CPU para worker tem overhead de criação/transporte; fazer pool antes de saturar core sem limites apenas muda o gargalo. Streaming exige que consumidor exerça pressão e que cada etapa imponha limites. Caches devem ter bound, TTL/política e chave completa. WeakMap não oferece contador observável para budget.

## Critério de domínio do capítulo
Explicar 0.1+0.2 e limite seguro; distinguir own/herdado; prever closure em loop; encontrar Promise não retornada; cancelar tarefa sem leak; justificar ESM/resolução; diagnosticar retenção e pressão em stream. Os exemplos deste acervo são didáticos, não bibliotecas de produção.

Referências: ECMA-262, HTML Living Standard, Node.js API, Unicode Standard. Consulte os IDs das fichas correspondentes e suas limitações no catálogo.

