// Fixtures autorais para typecheck strict. Sem dependência externa.
export type Result<T,E> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };
export function unwrapOr<T,E>(result: Result<T,E>, fallback:T):T {
  return result.ok ? result.value : fallback;
}
declare const userIdBrand: unique symbol;
declare const orderIdBrand: unique symbol;
export type UserId = string & {readonly [userIdBrand]: true};
export type OrderId = string & {readonly [orderIdBrand]: true};
export function userId(input:unknown): UserId {
  if(typeof input!=='string' || !/^[a-z0-9-]{1,64}$/.test(input))
    throw new TypeError('UserId inválido');
  return input as UserId; // assertion localizada após prova runtime
}
export function get<T,K extends keyof T>(object:T,key:K):T[K] {
  return object[key];
}
export type LoadState<T> =
  | {status:'idle'}
  | {status:'loading'; requestId:number}
  | {status:'success'; data:T}
  | {status:'error'; message:string};
function impossible(value:never):never { throw new Error('Estado inesperado'); }
export function label<T>(state:LoadState<T>):string {
  switch(state.status) {
    case 'idle':return 'Pronto';
    case 'loading':return 'Carregando';
    case 'success':return 'Concluído';
    case 'error':return state.message;
    default:return impossible(state);
  }
}
export type ElementOf<T> = T extends readonly (infer E)[] ? E : never;
export type IsString<T> = T extends string ? true : false;
export type IsEntirelyString<T> = [T] extends [string] ? true : false;
export type EventName = `pedido:${'criado'|'cancelado'}`;
const handlers = {
  'pedido:criado': (id:string)=>id,
  'pedido:cancelado': (id:string)=>id
} satisfies Record<EventName,(id:string)=>string>;
const name:string=get({name:'Ana',age:3},'name');
const u:UserId=userId('ana');
// @ts-expect-error OrderId e UserId são semanticamente distintos.
const wrong:OrderId=u;
// @ts-expect-error Não existe esta chave.
get({name:'Ana'},'missing');
// @ts-expect-error Estado success exige data.
const incomplete:LoadState<number>={status:'success'};
// @ts-expect-error unknown requer narrowing.
const unsafe:string=({} as unknown).name;
const a:IsString<string|number>=true;
const b:IsString<string|number>=false;
const c:IsEntirelyString<string|number>=false;
const indexed:ReadonlyArray<number>=[1,2];
// @ts-expect-error Acesso indexado pode ser undefined em noUncheckedIndexedAccess.
const certain:number=indexed[9];
type Config={port?:number};
// @ts-expect-error Ausência difere de undefined sob exactOptionalPropertyTypes.
const invalidConfig:Config={port:undefined};
void [handlers,name,u,wrong,incomplete,unsafe,a,b,c,certain,invalidConfig];

