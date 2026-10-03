// Padrões didáticos com invariantes explícitos. Node >=18; sem dependências.
export class QueueClosedError extends Error {
  constructor() { super('Fila encerrada'); this.name='QueueClosedError'; }
}
export class QueueOverloadedError extends Error {
  constructor() { super('Limite de waiters'); this.name='QueueOverloadedError'; }
}
export class AsyncQueue {
  #items=[]; #readers=[]; #writers=[]; #closed=false;
  constructor(capacity, {maxWaiters=capacity}={}) {
    if(!Number.isSafeInteger(capacity)||capacity<1) throw new RangeError('capacity');
    if(!Number.isSafeInteger(maxWaiters)||maxWaiters<1) throw new RangeError('maxWaiters');
    Object.defineProperties(this,{
      capacity:{value:capacity,enumerable:true},
      maxWaiters:{value:maxWaiters,enumerable:true}
    });
  }
  get size(){return this.#items.length;}
  get closed(){return this.#closed;}
  get pending(){return {readers:this.#readers.length,writers:this.#writers.length};}
  #wait(list,value,signal) {
    if(signal?.aborted) return Promise.reject(signal.reason);
    if(list.length>=this.maxWaiters) return Promise.reject(new QueueOverloadedError());
    return new Promise((resolve,reject)=>{
      const cleanup=()=>signal?.removeEventListener('abort',abort);
      const waiter={
        value,
        resolve(result){cleanup();resolve(result);},
        reject(error){cleanup();reject(error);}
      };
      const abort=()=>{
        const index=list.indexOf(waiter);
        if(index>=0) {list.splice(index,1);waiter.reject(signal.reason);this.#pump();}
      };
      list.push(waiter);
      signal?.addEventListener('abort',abort,{once:true});
      this.#pump();
    });
  }
  #pump() {
    let progress;
    do {
      progress=false;
      while(this.#readers.length && this.#items.length) {
        this.#readers.shift().resolve({done:false,value:this.#items.shift()});
        progress=true;
      }
      while(!this.#closed && this.#writers.length && this.#items.length<this.capacity) {
        const writer=this.#writers.shift();
        this.#items.push(writer.value);
        writer.resolve();progress=true;
      }
    } while(progress);
    if(this.#closed && this.#items.length===0)
      while(this.#readers.length) this.#readers.shift().resolve({done:true,value:undefined});
  }
  push(value,{signal}={}) {
    if(this.#closed)return Promise.reject(new QueueClosedError());
    return this.#wait(this.#writers,value,signal);
  }
  take({signal}={}) {return this.#wait(this.#readers,undefined,signal);}
  close() {
    if(this.#closed)return;
    this.#closed=true;
    while(this.#writers.length)this.#writers.shift().reject(new QueueClosedError());
    this.#pump();
  }
}
export class CircuitOpenError extends Error {
  constructor() {super('Circuito aberto');this.name='CircuitOpenError';}
}
export class CircuitBreaker {
  #state='closed';#failures=0;#retryAt=0;#epoch=0;#probe=false;
  constructor({threshold=3,cooldown=1000,now=()=>performance.now(),isFailure=()=>true}={}) {
    if(!Number.isSafeInteger(threshold)||threshold<1)throw new RangeError('threshold');
    if(!Number.isFinite(cooldown)||cooldown<0)throw new RangeError('cooldown');
    if(typeof now!=='function'||typeof isFailure!=='function')throw new TypeError('Callbacks');
    Object.defineProperties(this,{
      threshold:{value:threshold,enumerable:true},cooldown:{value:cooldown,enumerable:true},
      now:{value:now},isFailure:{value:isFailure}
    });
  }
  get state(){return this.#state;}
  async run(task) {
    if(this.#state==='open') {
      if(this.now()<this.#retryAt)throw new CircuitOpenError();
      this.#state='half-open';
    }
    const probe=this.#state==='half-open';
    if(probe&&this.#probe)throw new CircuitOpenError();
    if(probe)this.#probe=true;
    const epoch=this.#epoch;
    try {
      const value=await task();
      if(epoch===this.#epoch) {
        this.#failures=0;
        if(probe){this.#state='closed';this.#epoch++;}
      }
      return value;
    } catch(error) {
      if(epoch===this.#epoch) {
        if(this.isFailure(error)) {
          this.#failures++;
          if(probe||this.#failures>=this.threshold) {
            this.#state='open';this.#retryAt=this.now()+this.cooldown;this.#epoch++;
          }
        } else if(probe) {
          // Resposta de negócio comprova transporte funcional neste modelo.
          this.#state='closed';this.#failures=0;this.#epoch++;
        }
      }
      throw error;
    } finally {if(probe)this.#probe=false;}
  }
}
// Parser binário: uint32 big endian + payload. Bufferização limitada por maxFrame.
export class FrameDecoder {
  #header=new Uint8Array(4);#headerUsed=0;#payload=null;#payloadUsed=0;
  #ended=false;#failed=false;
  constructor(maxFrame=1024*1024) {
    if(!Number.isSafeInteger(maxFrame)||maxFrame<0||maxFrame>0xffffffff)
      throw new RangeError('maxFrame');
    Object.defineProperty(this,'maxFrame',{value:maxFrame,enumerable:true});
  }
  feed(chunk) {
    if(this.#ended||this.#failed)throw new Error('Decoder indisponível');
    if(!(chunk instanceof Uint8Array))throw new TypeError('Chunk deve ser Uint8Array');
    const frames=[];let offset=0;
    try {
      while(offset<chunk.length) {
        if(this.#payload===null) {
          const count=Math.min(4-this.#headerUsed,chunk.length-offset);
          this.#header.set(chunk.subarray(offset,offset+count),this.#headerUsed);
          this.#headerUsed+=count;offset+=count;
          if(this.#headerUsed<4)continue;
          const size=new DataView(this.#header.buffer).getUint32(0,false);
          if(size>this.maxFrame)throw new RangeError('Frame excede limite');
          this.#payload=new Uint8Array(size);this.#payloadUsed=0;
          if(size===0){frames.push(this.#payload);this.#payload=null;this.#headerUsed=0;}
        } else {
          const count=Math.min(this.#payload.length-this.#payloadUsed,chunk.length-offset);
          this.#payload.set(chunk.subarray(offset,offset+count),this.#payloadUsed);
          this.#payloadUsed+=count;offset+=count;
          if(this.#payloadUsed===this.#payload.length) {
            frames.push(this.#payload);this.#payload=null;this.#headerUsed=0;
          }
        }
      }
      return frames;
    } catch(error){this.#failed=true;this.#payload=null;throw error;}
  }
  end() {
    if(this.#ended||this.#failed)throw new Error('Decoder indisponível');
    this.#ended=true;
    if(this.#headerUsed!==0||this.#payload!==null)throw new Error('EOF parcial');
  }
}
export function encodeFrame(payload) {
  if(!(payload instanceof Uint8Array))throw new TypeError('Payload');
  const frame=new Uint8Array(4+payload.length);
  new DataView(frame.buffer).setUint32(0,payload.length,false);
  frame.set(payload,4);return frame;
}
export class ConflictError extends Error {
  constructor(){super('Versão em conflito');this.name='ConflictError';}
}
export class VersionedCell {
  #value;#version=0;
  constructor(value){this.#value=structuredClone(value);}
  read(){return {value:structuredClone(this.#value),version:this.#version};}
  compareAndSet(expected,value) {
    if(expected!==this.#version)throw new ConflictError();
    if(!Number.isSafeInteger(this.#version+1))throw new RangeError('Versão esgotada');
    const copy=structuredClone(value);
    this.#value=copy;this.#version++;return this.read();
  }
}
export async function runGroup(tasks,{signal}={}) {
  if(!Array.isArray(tasks))throw new TypeError('Esperado array de funções');
  // for...of observa buracos como undefined; some/map ignoram slots ausentes.
  for(const task of tasks)if(typeof task!=='function')
    throw new TypeError('Esperado array de funções');
  if(signal?.aborted)throw signal.reason;
  const controller=new AbortController();
  const abort=()=>controller.abort(signal.reason);
  signal?.addEventListener('abort',abort,{once:true});
  let failure;let failed=false;
  const promises=tasks.map(task=>Promise.resolve().then(()=>{
    if(controller.signal.aborted)throw controller.signal.reason;
    return task(controller.signal);
  }).catch(error=>{
    if(!failed){failed=true;failure=error;controller.abort(error);}
    throw error;
  }));
  try {
    const settled=await Promise.allSettled(promises);
    if(failed)throw failure;
    if(controller.signal.aborted)throw controller.signal.reason;
    return settled.map(result=>result.value);
  } finally {signal?.removeEventListener('abort',abort);}
}
export function transition(state,event) {
  if(event.type==='start') {
    if(!Number.isSafeInteger(event.id)||event.id<0)throw new TypeError('Request id');
    return Object.freeze({status:'loading',id:event.id});
  }
  if(event.type==='reset')return Object.freeze({status:'idle'});
  if(event.type!=='success'&&event.type!=='error')throw new TypeError('Evento desconhecido');
  // Eventos de operações anteriores são ignorados, não sobrescrevem geração ativa.
  if(state.status!=='loading'||state.id!==event.id)return state;
  return event.type==='success'
    ? Object.freeze({status:'success',data:event.data})
    : Object.freeze({status:'error',message:event.message});
}
