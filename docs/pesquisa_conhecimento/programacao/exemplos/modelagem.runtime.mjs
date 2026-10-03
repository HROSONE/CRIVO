import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {money,addMoney,encodeMoney,decodeMoney,applyOptionalPatch,reduceRequest,errorMessage}
  =require(process.argv[2]); // Caminho absoluto do JS compilado fornecido no comando.

test('moeda usa unidades menores BigInt e serialização explícita',()=>{
  const total=addMoney(money('BRL',10n),money('BRL',20n));
  assert.deepEqual(encodeMoney(total),{currency:'BRL',minor:'30'});
  assert.deepEqual(decodeMoney(encodeMoney(total)),total);
});
test('moeda rejeita mistura, faixa e dado externo inválido',()=>{
  assert.throws(()=>addMoney(money('BRL',1n),money('USD',1n)),TypeError);
  assert.throws(()=>money('ZZZ',1n),TypeError);
  assert.throws(()=>money('BRL',1),RangeError);
  assert.throws(()=>addMoney(money('BRL',10n**18n),money('BRL',1n)),RangeError);
  for(const bad of [null,[],{currency:'BRL',minor:'1x'},{currency:'BRL',minor:'01'},
      {currency:'USD',minor:'9'.repeat(1000)},{currency:'BRL',minor:'1',admin:true}])
    assert.throws(()=>decodeMoney(bad));
});
test('decode não aceita campos herdados',()=>{
  assert.throws(()=>decodeMoney(Object.create({currency:'BRL',minor:'1'})),TypeError);
});
test('factory congela valor e não usa Number no wire',()=>{
  const value=money('BRL',9007199254740993n);
  assert.equal(encodeMoney(value).minor,'9007199254740993');
  assert.throws(()=>{value.minor=4n;},TypeError);
});
test('patch distingue manter, substituir e remover',()=>{
  assert.equal(applyOptionalPatch('A',{op:'keep'}),'A');
  assert.equal(applyOptionalPatch('A',{op:'replace',value:'B'}),'B');
  assert.equal(applyOptionalPatch('A',{op:'remove'}),undefined);
  assert.throws(()=>applyOptionalPatch('A',{op:'unknown'}));
});
test('reducer tipado conserva estado diante de resposta antiga',()=>{
  let s=reduceRequest({status:'idle'},{type:'start',id:1});
  s=reduceRequest(s,{type:'start',id:2});
  assert.equal(reduceRequest(s,{type:'success',id:1,data:'velho'}),s);
  assert.deepEqual(reduceRequest(s,{type:'success',id:2,data:'novo'}),{status:'success',data:'novo'});
});
test('reducer typed cobre erro e reset',()=>{
  const s=reduceRequest({status:'idle'},{type:'start',id:1});
  assert.deepEqual(reduceRequest(s,{type:'error',id:1,message:'erro'}),{status:'error',message:'erro'});
  assert.deepEqual(reduceRequest(s,{type:'reset'}),{status:'idle'});
  assert.throws(()=>reduceRequest(s,{type:'start',id:NaN}),TypeError);
});
test('erros públicos têm mapping definido e fallback inválido',()=>{
  assert.equal(errorMessage({code:'validation',fields:{name:'required'}}),'Entrada inválida');
  assert.equal(errorMessage({code:'conflict',resource:'pedido'}),'Conflito em pedido');
  assert.equal(errorMessage({code:'unavailable',retryable:true}),'Tente mais tarde');
  assert.throws(()=>errorMessage({code:'unknown'}));
});

