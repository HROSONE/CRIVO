import test from 'node:test';
import assert from 'node:assert/strict';
import {
  lowerBound, parseUser, groupBy, take, topologicalOrder, LRU,
  mapBounded, abortableDelay, SingleFlight, decodeUtf8,
  parseSafeInteger, createCounter, compensatedSum
} from './padroes.mjs';

test('lower_bound encontra primeira posição e boundaries', () => {
  assert.equal(lowerBound([], 3), 0);
  assert.equal(lowerBound([1,2,2,5], 2), 1);
  assert.equal(lowerBound([1,2,2,5], 9), 4);
  assert.equal(lowerBound([1,2,2,5], 0), 0);
});
test('lower_bound satisfaz partição em entradas pequenas variadas', () => {
  for (let n = 0; n < 30; n++) {
    const a = Array.from({length:n}, (_,i) => Math.floor(i/3));
    for (let x = -1; x <= 12; x++) {
      const k = lowerBound(a,x);
      assert.ok(a.slice(0,k).every(v => v < x));
      assert.ok(a.slice(k).every(v => v >= x));
    }
  }
});
test('parser valida own properties, formato e campos desconhecidos', () => {
  assert.deepEqual(parseUser({id:'ana-1',name:' Ana '}), {id:'ana-1',name:'Ana'});
  for (const bad of [null, [], 3, {id:1,name:'Ana'}, {id:'a',name:''},
                     {id:'a',name:'A',admin:true}, Object.create({id:'a',name:'A'})])
    assert.throws(() => parseUser(bad));
});
test('parser não aceita chaves perigosas nem altera protótipo global', () => {
  const obj = JSON.parse('{"id":"a","name":"A","__proto__":{"polluted":true}}');
  assert.throws(() => parseUser(obj));
  assert.equal({}.polluted, undefined);
});
test('groupBy suporta chave __proto__ sem semântica de protótipo', () => {
  const g = groupBy(['__proto__','x','__proto__'], x => x);
  assert.equal(g.get('__proto__').length, 2);
});
test('take fecha generator e não consome para zero', () => {
  let closed = false, started = false;
  function* source() { started=true; try { yield 1; yield 2; } finally { closed=true; } }
  assert.deepEqual([...take(source(),0)], []);
  assert.equal(started,false);
  assert.deepEqual([...take(source(),1)], [1]);
  assert.equal(closed,true);
});
test('topological order respeita cada dependência', () => {
  const nodes = ['build','test','deploy','lint'];
  const edges = [['build','test'],['test','deploy'],['lint','deploy']];
  const result = topologicalOrder(nodes,edges);
  assert.equal(result.length,nodes.length);
  for (const [a,b] of edges) assert.ok(result.indexOf(a)<result.indexOf(b));
});
test('topological order rejeita ciclo e nó inexistente', () => {
  assert.throws(() => topologicalOrder(['a','b'],[['a','b'],['b','a']]), /Ciclo/);
  assert.throws(() => topologicalOrder(['a'],[['a','b']]), /desconhecido/);
});
test('LRU conserva acesso recente e limita tamanho', () => {
  const c = new LRU(2); c.set('a',1); c.set('b',2); c.get('a'); c.set('c',3);
  assert.equal(c.has('b'),false); assert.equal(c.get('a'),1);
  assert.equal(c.size,2);
});
test('LRU distingue ausência de undefined e update renova ordem', () => {
  const c = new LRU(2); c.set('a',undefined); c.set('b',2);
  assert.equal(c.has('a'),true); c.set('a',3); c.set('c',4);
  assert.equal(c.has('b'),false); assert.equal(c.get('a'),3);
});
test('mapBounded limita tarefas ativas e preserva ordem', async () => {
  let active=0, max=0;
  const result = await mapBounded([1,2,3,4,5],2,async x => {
    active++; max=Math.max(max,active);
    await new Promise(resolve => setImmediate(resolve));
    active--; return x*2;
  });
  assert.deepEqual(result,[2,4,6,8,10]); assert.ok(max<=2); assert.equal(active,0);
});
test('mapBounded lida com vazio e concorrência inválida', async () => {
  assert.deepEqual(await mapBounded([],3,x=>x), []);
  await assert.rejects(mapBounded([1],0,x=>x), RangeError);
});
test('mapBounded aguarda tarefas iniciadas antes de retornar falha', async () => {
  let finished=false;
  await assert.rejects(mapBounded([1,2],2,async x => {
    if (x===1) throw new Error('falha');
    await new Promise(resolve=>setImmediate(resolve)); finished=true;
  }), /falha/);
  assert.equal(finished,true);
});
test('delay abortado antes não agenda trabalho útil', async () => {
  const c = new AbortController(); c.abort(new Error('cancelado'));
  await assert.rejects(abortableDelay(1000,c.signal), /cancelado/);
});
test('delay abortado durante limpa timer e preserva causa', async () => {
  const c = new AbortController();
  const pending = abortableDelay(1000,c.signal); c.abort(new Error('prazo'));
  await assert.rejects(pending,/prazo/);
});
test('delay normal conclui e rejeita duração inválida', async () => {
  await abortableDelay(0);
  await assert.rejects(abortableDelay(-1),RangeError);
});
test('SingleFlight compartilha somente operação em andamento', async () => {
  const sf = new SingleFlight(); let calls=0;
  const task=async()=>{calls++; return 42;};
  const a=sf.run('k',task), b=sf.run('k',task);
  assert.equal(a,b); assert.equal(await a,42); assert.equal(calls,1);
  assert.equal(await sf.run('k',task),42); assert.equal(calls,2);
});
test('SingleFlight remove rejeição e permite recuperação', async () => {
  const sf=new SingleFlight();
  await assert.rejects(sf.run('k',()=>{throw new Error('falha');}),/falha/);
  assert.equal(await sf.run('k',()=>7),7);
});
test('UTF-8 incremental suporta todas fragmentações da mesma entrada', () => {
  const expected='ação 🌊'; const bytes=new TextEncoder().encode(expected);
  for (let i=0;i<=bytes.length;i++)
    assert.equal(decodeUtf8([bytes.slice(0,i),bytes.slice(i)]),expected);
});
test('UTF-8 inválido e EOF parcial são erros', () => {
  assert.throws(()=>decodeUtf8([new Uint8Array([0xc3])]),TypeError);
  assert.throws(()=>decodeUtf8([new Uint8Array([0xff])]),TypeError);
});
test('inteiro textual exige formato completo e faixa segura', () => {
  assert.equal(parseSafeInteger('0'),0); assert.equal(parseSafeInteger('-42'),-42);
  for (const bad of ['01','1x','1.0',' 1','9007199254740992'])
    assert.throws(()=>parseSafeInteger(bad));
});
test('closures de factories mantêm estado independente', () => {
  const a=createCounter(),b=createCounter(10);
  assert.equal(a.increment(),1);assert.equal(b.increment(),11);assert.equal(a.value(),1);
});
test('coerção, NaN, zeros e identidade têm semânticas distintas', () => {
  assert.equal([] == false,true); assert.equal(NaN === NaN,false);
  assert.equal(Object.is(-0,0),false);
  assert.equal(new Map([[NaN,1]]).get(NaN),1);
  assert.equal(new Set([{},{}]).size,2);
});
test('const e freeze superficial não congelam objeto aninhado', () => {
  const x=Object.freeze({nested:{n:1}});
  x.nested.n=2; assert.equal(x.nested.n,2);
  assert.throws(()=>{x.nested={n:3};},TypeError);
});
test('jobs Promise rodam após sequência síncrona', async () => {
  const logs=['A']; const done=Promise.resolve().then(()=>logs.push('C'));
  logs.push('B'); assert.deepEqual(logs,['A','B']); await done;
  assert.deepEqual(logs,['A','B','C']);
});
test('Promise.all não cancela operação sobrevivente', async () => {
  let finish; let finished=false;
  const surviving=new Promise(resolve=>{finish=()=>{finished=true;resolve(2);};});
  await assert.rejects(Promise.all([Promise.reject(new Error('erro')),surviving]));
  assert.equal(finished,false); finish(); await surviving; assert.equal(finished,true);
});
test('soma compensada reduz erro em exemplo específico, não prova estabilidade geral', () => {
  const a=Array(10000).fill(0.1);
  const plain=a.reduce((s,x)=>s+x,0);
  assert.ok(Math.abs(compensatedSum(a)-1000)<Math.abs(plain-1000));
});

