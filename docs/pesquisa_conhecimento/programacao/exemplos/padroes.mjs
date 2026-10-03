// Exemplos autorais didáticos. Node >=18; sem rede, dependências ou side effects externos.
// Estas abstrações não são bibliotecas de produção. Limitações estão no README.
export function lowerBound(sorted, value) {
  let left = 0, right = sorted.length;
  while (left < right) {
    const mid = left + Math.floor((right - left) / 2);
    if (sorted[mid] < value) left = mid + 1;
    else right = mid;
  }
  return left;
}
export function assertNever(value) {
  throw new Error('Variante inesperada: ' + String(value));
}
export function parseUser(input) {
  if (input === null || typeof input !== 'object' || Array.isArray(input))
    throw new TypeError('Esperado objeto');
  if (!Object.hasOwn(input, 'id') || typeof input.id !== 'string' ||
      !/^[a-z0-9-]{1,64}$/.test(input.id)) throw new TypeError('id inválido');
  if (!Object.hasOwn(input, 'name') || typeof input.name !== 'string' ||
      input.name.trim().length === 0 || input.name.length > 200)
    throw new TypeError('name inválido');
  const allowed = new Set(['id', 'name']);
  if (Reflect.ownKeys(input).some(key => !allowed.has(key)))
    throw new TypeError('Campo desconhecido');
  return Object.freeze({ id: input.id, name: input.name.trim() });
}
export function groupBy(items, keyOf) {
  const groups = new Map();
  for (const item of items) {
    const key = keyOf(item);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  }
  return groups;
}
export function* take(iterable, limit) {
  if (!Number.isSafeInteger(limit) || limit < 0) throw new RangeError('limit');
  if (limit === 0) return;
  let count = 0;
  for (const value of iterable) {
    yield value;
    if (++count === limit) return;
  }
}
export function topologicalOrder(nodes, edges) {
  const known = new Set(nodes);
  if (known.size !== nodes.length) throw new Error('Nó duplicado');
  const next = new Map(nodes.map(n => [n, []]));
  const degree = new Map(nodes.map(n => [n, 0]));
  for (const [from, to] of edges) {
    if (!known.has(from) || !known.has(to)) throw new Error('Nó desconhecido');
    next.get(from).push(to);
    degree.set(to, degree.get(to) + 1);
  }
  const queue = nodes.filter(n => degree.get(n) === 0);
  const result = [];
  // Índice de leitura evita shift repetido em array grande.
  for (let head = 0; head < queue.length; head++) {
    const node = queue[head];
    result.push(node);
    for (const child of next.get(node)) {
      degree.set(child, degree.get(child) - 1);
      if (degree.get(child) === 0) queue.push(child);
    }
  }
  if (result.length !== nodes.length) throw new Error('Ciclo');
  return result;
}
export class LRU {
  #entries = new Map();
  constructor(capacity) {
    if (!Number.isSafeInteger(capacity) || capacity < 1) throw new RangeError('capacity');
    this.capacity = capacity;
  }
  get size() { return this.#entries.size; }
  has(key) { return this.#entries.has(key); }
  get(key) {
    if (!this.#entries.has(key)) return undefined;
    const value = this.#entries.get(key);
    this.#entries.delete(key);
    this.#entries.set(key, value);
    return value;
  }
  set(key, value) {
    this.#entries.delete(key);
    this.#entries.set(key, value);
    if (this.size > this.capacity)
      this.#entries.delete(this.#entries.keys().next().value);
  }
}
// mapBounded não cancela automaticamente tarefas já iniciadas quando uma falha.
// O chamador passa signal/cleanup à tarefa se seu contrato exige cancelamento.
export async function mapBounded(items, concurrency, task) {
  if (!Number.isSafeInteger(concurrency) || concurrency < 1)
    throw new RangeError('concurrency');
  const results = new Array(items.length);
  let cursor = 0;
  let failed = false;
  async function worker() {
    while (!failed && cursor < items.length) {
      const index = cursor++;
      try { results[index] = await task(items[index], index); }
      catch (error) { failed = true; throw error; }
    }
  }
  const outcomes = await Promise.allSettled(
    Array.from({ length: Math.min(concurrency, items.length) }, worker));
  const failure = outcomes.find(result => result.status === 'rejected');
  if (failure) throw failure.reason;
  return results;
}
export function abortableDelay(ms, signal) {
  if (!Number.isFinite(ms) || ms < 0 || ms > 2147483647)
    return Promise.reject(new RangeError('ms'));
  return new Promise((resolve, reject) => {
    if (signal?.aborted) { reject(signal.reason); return; }
    const cleanup = () => signal?.removeEventListener('abort', onAbort);
    const timer = setTimeout(() => { cleanup(); resolve(); }, ms);
    function onAbort() { clearTimeout(timer); cleanup(); reject(signal.reason); }
    signal?.addEventListener('abort', onAbort, { once: true });
  });
}
export class SingleFlight {
  #pending = new Map();
  run(key, task) {
    if (this.#pending.has(key)) return this.#pending.get(key);
    // Agendar task após inserir promise evita reentrância síncrona antes do registro.
    const promise = Promise.resolve().then(task);
    this.#pending.set(key, promise);
    const cleanup = () => {
      if (this.#pending.get(key) === promise) this.#pending.delete(key);
    };
    promise.then(cleanup, cleanup);
    return promise;
  }
}
export function decodeUtf8(chunks) {
  const decoder = new TextDecoder('utf-8', { fatal: true });
  let text = '';
  for (const bytes of chunks) text += decoder.decode(bytes, { stream: true });
  return text + decoder.decode();
}
export function parseSafeInteger(text) {
  if (typeof text !== 'string' || !/^-?(0|[1-9][0-9]*)$/.test(text))
    throw new TypeError('Inteiro textual canônico esperado');
  const n = Number(text);
  if (!Number.isSafeInteger(n)) throw new RangeError('Fora da faixa segura');
  return n;
}
export function createCounter(start = 0) {
  let n = start;
  return { increment() { return ++n; }, value() { return n; } };
}
export function compensatedSum(values) {
  let sum = 0, correction = 0;
  for (const value of values) {
    const adjusted = value - correction;
    const next = sum + adjusted;
    correction = (next - sum) - adjusted;
    sum = next;
  }
  return sum;
}

