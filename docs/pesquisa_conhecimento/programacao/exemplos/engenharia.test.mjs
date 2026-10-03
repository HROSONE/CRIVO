import test from 'node:test';
import assert from 'node:assert/strict';
import {getEventListeners} from 'node:events';
import {AsyncQueue,QueueClosedError,QueueOverloadedError,CircuitBreaker,CircuitOpenError,
FrameDecoder,encodeFrame,VersionedCell,ConflictError,runGroup,transition} from './engenharia.mjs';
import {abortableDelay} from './padroes.mjs';
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function deferred(){let resolve,reject;const promise=new Promise((a,b)=>{resolve=a;reject=b;});return {promise,resolve,reject};}

test('fila valida capacidade/waiters',()=>{
  assert.throws(()=>new AsyncQueue(0),RangeError);
  assert.throws(()=>new AsyncQueue(2,{maxWaiters:0}),RangeError);
  const q=new AsyncQueue(1);assert.throws(()=>{q.capacity=0;},TypeError);
});
test('fila preserva FIFO e distingue undefined de encerramento',async()=>{
  const q=new AsyncQueue(2);await q.push(undefined);await q.push(2);
  assert.deepEqual(await q.take(),{done:false,value:undefined});
  assert.deepEqual(await q.take(),{done:false,value:2});
  q.close();assert.deepEqual(await q.take(),{done:true,value:undefined});
});
test('fila aplica backpressure antes de exceder capacidade',async()=>{
  const q=new AsyncQueue(1);await q.push(1);
  let accepted=false;const pending=q.push(2).then(()=>{accepted=true;});
  await tick();assert.equal(accepted,false);assert.equal(q.size,1);
  assert.equal((await q.take()).value,1);await pending;
  assert.equal(q.size,1);assert.equal((await q.take()).value,2);
});
test('fila entrega a reader pendente e remove listener após sucesso',async()=>{
  const q=new AsyncQueue(1);const c=new AbortController();
  const read=q.take({signal:c.signal});
  assert.equal(getEventListeners(c.signal,'abort').length,1);
  await q.push(7);assert.equal((await read).value,7);
  assert.equal(getEventListeners(c.signal,'abort').length,0);
});
test('reader cancelado não consome próximo item',async()=>{
  const q=new AsyncQueue(1);const c=new AbortController();
  const rejected=assert.rejects(q.take({signal:c.signal}),/cancelado/);
  c.abort(new Error('cancelado'));await rejected;
  await q.push(9);assert.equal((await q.take()).value,9);
  assert.deepEqual(q.pending,{readers:0,writers:0});
});
test('writer cancelado não aparece na fila e libera waiter',async()=>{
  const q=new AsyncQueue(1);await q.push(1);const c=new AbortController();
  const rejected=assert.rejects(q.push(2,{signal:c.signal}),/cancelado/);
  c.abort(new Error('cancelado'));await rejected;
  assert.equal((await q.take()).value,1);
  assert.equal(q.size,0);assert.deepEqual(q.pending,{readers:0,writers:0});
});
test('fila abortada antes não altera estado',async()=>{
  const q=new AsyncQueue(1);const c=new AbortController();c.abort(new Error('antes'));
  await assert.rejects(q.push(1,{signal:c.signal}),/antes/);
  await assert.rejects(q.take({signal:c.signal}),/antes/);
  assert.equal(q.size,0);
});
test('close drena itens aceitos e rejeita writers bloqueados',async()=>{
  const q=new AsyncQueue(1);await q.push(1);
  const rejected=assert.rejects(q.push(2),QueueClosedError);q.close();await rejected;
  assert.equal((await q.take()).value,1);assert.equal((await q.take()).done,true);
  await assert.rejects(q.push(3),QueueClosedError);q.close();
});
test('close resolve readers em espera sem reter callbacks',async()=>{
  const q=new AsyncQueue(2);const c=new AbortController();
  const a=q.take({signal:c.signal}),b=q.take();q.close();
  assert.equal((await a).done,true);assert.equal((await b).done,true);
  assert.equal(getEventListeners(c.signal,'abort').length,0);
});
test('limite de waiters protege fila de esperas ilimitadas',async()=>{
  const q=new AsyncQueue(1);const first=q.take();
  await assert.rejects(q.take(),QueueOverloadedError);
  q.close();await first;
});
test('modelo FIFO conserva todos valores com producer/consumer concorrentes',async()=>{
  const q=new AsyncQueue(3,{maxWaiters:3});
  const received=[];
  const consumer=(async()=>{for(;;){const r=await q.take();if(r.done)break;received.push(r.value);await tick();}})();
  for(let i=0;i<60;i++){await q.push(i);assert.ok(q.size<=3);}
  q.close();await consumer;
  assert.deepEqual(received,Array.from({length:60},(_,i)=>i));
});
test('breaker abre por falhas e não executa call recusada',async()=>{
  let clock=0,calls=0;const b=new CircuitBreaker({threshold:2,cooldown:10,now:()=>clock});
  assert.throws(()=>{b.threshold=0;},TypeError);
  const fail=()=>{calls++;throw new Error('rede');};
  await assert.rejects(b.run(fail),/rede/);assert.equal(b.state,'closed');
  await assert.rejects(b.run(fail),/rede/);assert.equal(b.state,'open');
  await assert.rejects(b.run(fail),CircuitOpenError);assert.equal(calls,2);
});
test('breaker permite só um probe e fecha ao recuperar',async()=>{
  let clock=0;const b=new CircuitBreaker({threshold:1,cooldown:10,now:()=>clock});
  await assert.rejects(b.run(()=>{throw new Error('rede');}));
  clock=10;const d=deferred();const probe=b.run(()=>d.promise);
  assert.equal(b.state,'half-open');
  await assert.rejects(b.run(()=>42),CircuitOpenError);
  d.resolve(7);assert.equal(await probe,7);assert.equal(b.state,'closed');
});
test('probe falho reabre com novo cooldown',async()=>{
  let clock=0;const b=new CircuitBreaker({threshold:1,cooldown:10,now:()=>clock});
  const fail=()=>{throw new Error('rede');};
  await assert.rejects(b.run(fail));clock=10;await assert.rejects(b.run(fail));
  assert.equal(b.state,'open');clock=19;await assert.rejects(b.run(()=>1),CircuitOpenError);
  clock=20;assert.equal(await b.run(()=>1),1);
});
test('erro de negócio não soma falha técnica',async()=>{
  const b=new CircuitBreaker({threshold:1,isFailure:e=>e.message==='rede'});
  await assert.rejects(b.run(()=>{throw new Error('negocio');}));
  assert.equal(b.state,'closed');assert.equal(await b.run(()=>2),2);
});
test('sucesso antigo não fecha circuito aberto por outra call',async()=>{
  const b=new CircuitBreaker({threshold:1});const d=deferred();
  const old=b.run(()=>d.promise);
  await assert.rejects(b.run(()=>{throw new Error('rede');}));
  d.resolve(4);assert.equal(await old,4);assert.equal(b.state,'open');
});
test('decoder produz mesmos frames em toda fragmentação',()=>{
  const expected=[new Uint8Array([1,2,3]),new Uint8Array([]),new TextEncoder().encode('ação')];
  const parts=expected.map(encodeFrame);
  const all=new Uint8Array(parts.reduce((n,p)=>n+p.length,0));let offset=0;
  for(const p of parts){all.set(p,offset);offset+=p.length;}
  for(let i=0;i<=all.length;i++){
    const d=new FrameDecoder(100);
    const actual=[...d.feed(all.slice(0,i)),...d.feed(all.slice(i))];d.end();
    assert.deepEqual(actual,expected);
  }
});
test('decoder aceita fragmentação byte a byte',()=>{
  const bytes=encodeFrame(new Uint8Array([9,8,7,6]));
  const d=new FrameDecoder(4);let actual=[];
  for(const byte of bytes)actual.push(...d.feed(new Uint8Array([byte])));
  d.end();assert.deepEqual(actual,[new Uint8Array([9,8,7,6])]);
});
test('decoder rejeita tamanho antes de ler payload e fica terminal',()=>{
  const d=new FrameDecoder(2);
  assert.throws(()=>{d.maxFrame=Infinity;},TypeError);
  assert.throws(()=>d.feed(new Uint8Array([0,0,0,3])),RangeError);
  assert.throws(()=>d.feed(new Uint8Array([1,2,3])),/indisponível/);
});
test('decoder rejeita EOF parcial no header e no payload',()=>{
  const a=new FrameDecoder();a.feed(new Uint8Array([0,0]));
  assert.throws(()=>a.end(),/EOF/);
  const b=new FrameDecoder();b.feed(new Uint8Array([0,0,0,2,1]));
  assert.throws(()=>b.end(),/EOF/);
});
test('decoder não compartilha payload com chunk que pode ser mutado',()=>{
  const input=encodeFrame(new Uint8Array([1,2]));const d=new FrameDecoder();
  const [frame]=d.feed(input);input.fill(0);assert.deepEqual(frame,new Uint8Array([1,2]));
  d.end();assert.throws(()=>d.feed(new Uint8Array()),/indisponível/);
});
test('cell detecta conflito sem sobrescrever vencedor',()=>{
  const cell=new VersionedCell({n:1});const a=cell.read(),b=cell.read();
  assert.equal(cell.compareAndSet(a.version,{n:2}).version,1);
  assert.throws(()=>cell.compareAndSet(b.version,{n:3}),ConflictError);
  assert.deepEqual(cell.read(),{value:{n:2},version:1});
});
test('cell clona nas fronteiras de entrada/saída',()=>{
  const original={n:1};const cell=new VersionedCell(original);original.n=5;
  const read=cell.read();read.value.n=9;assert.equal(cell.read().value.n,1);
  const next={n:3};cell.compareAndSet(0,next);next.n=8;
  assert.equal(cell.read().value.n,3);
});
test('falha de clone em CAS não consome versão',()=>{
  const cell=new VersionedCell({n:1});
  assert.throws(()=>cell.compareAndSet(0,()=>1));
  assert.equal(cell.read().version,0);assert.equal(cell.read().value.n,1);
});
test('grupo retorna resultados em ordem, mesmo concluindo fora de ordem',async()=>{
  const a=deferred(),b=deferred();const work=runGroup([()=>a.promise,()=>b.promise]);
  b.resolve(2);a.resolve(1);assert.deepEqual(await work,[1,2]);
});
test('grupo falho cancela siblings e aguarda cleanup',async()=>{
  const first=deferred();let cleaned=false;
  const work=runGroup([
    ()=>first.promise,
    async signal=>{try{await abortableDelay(1000,signal);}finally{await tick();cleaned=true;}}
  ]);
  const rejection=assert.rejects(work,/primaria/);
  await tick();first.reject(new Error('primaria'));await rejection;assert.equal(cleaned,true);
});
test('abort de parent encerra grupo e remove listener',async()=>{
  const parent=new AbortController();
  const work=runGroup([signal=>abortableDelay(1000,signal)],{signal:parent.signal});
  const rejection=assert.rejects(work,/parent/);
  await tick();parent.abort(new Error('parent'));await rejection;
  assert.equal(getEventListeners(parent.signal,'abort').length,0);
});
test('grupo com parent já abortado não inicia tarefas',async()=>{
  let called=false;const parent=new AbortController();parent.abort(new Error('antes'));
  await assert.rejects(runGroup([()=>{called=true;}],{signal:parent.signal}),/antes/);
  assert.equal(called,false);
});
test('grupo vazio e tarefas inválidas têm contratos explícitos',async()=>{
  assert.deepEqual(await runGroup([]),[]);
  await assert.rejects(runGroup([3]),TypeError);
  await assert.rejects(runGroup(new Array(1)),TypeError);
});
test('máquina ignora resposta de geração anterior',()=>{
  let state=transition({status:'idle'},{type:'start',id:1});
  state=transition(state,{type:'start',id:2});
  const previous=state;
  assert.equal(transition(state,{type:'success',id:1,data:'antigo'}),previous);
  state=transition(state,{type:'success',id:2,data:'novo'});
  assert.deepEqual(state,{status:'success',data:'novo'});
  assert.equal(transition(state,{type:'error',id:2,message:'tardio'}),state);
});
test('máquina reset, erro atual e eventos inválidos',()=>{
  let state=transition({status:'idle'},{type:'start',id:1});
  state=transition(state,{type:'error',id:1,message:'erro'});
  assert.deepEqual(state,{status:'error',message:'erro'});
  assert.deepEqual(transition(state,{type:'reset'}),{status:'idle'});
  assert.throws(()=>transition(state,{type:'start',id:-1}),TypeError);
  assert.throws(()=>transition(state,{type:'weird'}),TypeError);
});
