// Modelos autorais TS: construção validada, patch e transições.
// Não representam autorização, transação ou persistência.
export type Currency='BRL'|'USD';
declare const moneyBrand:unique symbol;
export type Money=Readonly<{currency:Currency;minor:bigint;[moneyBrand]:true}>;
const MAX_MINOR=10n**18n;
function within(n:bigint):boolean{return n>=-MAX_MINOR&&n<=MAX_MINOR;}
export function money(currency:Currency,minor:bigint):Money {
  if(currency!=='BRL'&&currency!=='USD')throw new TypeError('Currency');
  if(typeof minor!=='bigint'||!within(minor))throw new RangeError('Minor');
  return Object.freeze({currency,minor}) as Money;
}
export function addMoney(a:Money,b:Money):Money {
  if(a.currency!==b.currency)throw new TypeError('Moedas distintas');
  return money(a.currency,a.minor+b.minor);
}
export function encodeMoney(value:Money):{currency:Currency;minor:string} {
  return {currency:value.currency,minor:value.minor.toString()};
}
export function decodeMoney(value:unknown):Money {
  if(value===null||typeof value!=='object'||Array.isArray(value))throw new TypeError('Objeto');
  if(!Object.hasOwn(value,'currency')||!Object.hasOwn(value,'minor'))throw new TypeError('Campos');
  const input=value as Record<string,unknown>;
  const currency=input['currency'],minor=input['minor'];
  if(currency!=='BRL'&&currency!=='USD')throw new TypeError('Currency');
  // Limite antes de converter inteiro arbitrário.
  if(typeof minor!=='string'||minor.length>21||!/^(-?(0|[1-9][0-9]*))$/.test(minor))
    throw new TypeError('Minor textual');
  if(Reflect.ownKeys(value).some(k=>k!=='currency'&&k!=='minor'))throw new TypeError('Campo extra');
  return money(currency,BigInt(minor));
}
export type Patch<T>=
  | Readonly<{op:'keep'}>
  | Readonly<{op:'replace';value:T}>
  | Readonly<{op:'remove'}>;
export function applyOptionalPatch<T>(current:T|undefined,patch:Patch<T>):T|undefined {
  switch(patch.op){
    case 'keep':return current;
    case 'replace':return patch.value;
    case 'remove':return undefined;
    default:return impossible(patch);
  }
}
export type RequestState<T>=
  | Readonly<{status:'idle'}>
  | Readonly<{status:'loading';id:number}>
  | Readonly<{status:'success';data:T}>
  | Readonly<{status:'error';message:string}>;
export type RequestEvent<T>=
  | Readonly<{type:'start';id:number}>
  | Readonly<{type:'reset'}>
  | Readonly<{type:'success';id:number;data:T}>
  | Readonly<{type:'error';id:number;message:string}>;
function impossible(value:never):never{throw new Error('Variante inesperada');}
export function reduceRequest<T>(state:RequestState<T>,event:RequestEvent<T>):RequestState<T>{
  switch(event.type){
    case 'start':
      if(!Number.isSafeInteger(event.id)||event.id<0)throw new TypeError('Request id');
      return Object.freeze({status:'loading',id:event.id});
    case 'reset':return Object.freeze({status:'idle'});
    case 'success':
      return state.status==='loading'&&state.id===event.id
        ?Object.freeze({status:'success',data:event.data}):state;
    case 'error':
      return state.status==='loading'&&state.id===event.id
        ?Object.freeze({status:'error',message:event.message}):state;
    default:return impossible(event);
  }
}
export type JsonValue=null|boolean|number|string|readonly JsonValue[]|{readonly [key:string]:JsonValue};
export type ApiError=
  | {code:'validation';fields:Readonly<Record<string,string>>}
  | {code:'conflict';resource:string}
  | {code:'unavailable';retryable:boolean};
export function errorMessage(error:ApiError):string {
  switch(error.code){
    case 'validation':return 'Entrada inválida';
    case 'conflict':return 'Conflito em '+error.resource;
    case 'unavailable':return error.retryable?'Tente mais tarde':'Indisponível';
    default:return impossible(error);
  }
}
// Limites: number pode conter NaN/Infinity; JsonValue não valida runtime.
// Brands são assertions internas após factory, não proteção contra cast hostil.

