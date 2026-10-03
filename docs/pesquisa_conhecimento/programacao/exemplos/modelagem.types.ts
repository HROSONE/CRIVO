import {money,addMoney,decodeMoney,applyOptionalPatch,reduceRequest,
type Money,type RequestState,type RequestEvent,type JsonValue,type ApiError} from './modelagem.js';
const m:Money=money('BRL',100n);
const n:Money=decodeMoney({currency:'BRL',minor:'25'});
addMoney(m,n);
// @ts-expect-error Valor cru não tem brand validada.
const forged:Money={currency:'BRL',minor:100n};
// @ts-expect-error Moeda fora do domínio aceito.
money('ZZZ',1n);
// @ts-expect-error Minor é bigint, não Number.
money('BRL',0.1);
const unchanged:string|undefined=applyOptionalPatch('Ana',{op:'keep'});
const removed:string|undefined=applyOptionalPatch('Ana',{op:'remove'});
// @ts-expect-error Replace exige value.
applyOptionalPatch('Ana',{op:'replace'});
// @ts-expect-error Success exige data.
const incomplete:RequestState<string>={status:'success'};
// @ts-expect-error Evento desconhecido.
const wrongEvent:RequestEvent<string>={type:'loaded',id:1};
const state:RequestState<string>=reduceRequest({status:'idle'},{type:'start',id:1});
// @ts-expect-error Objeto function não é JsonValue.
const unserializable:JsonValue=()=>1;
// @ts-expect-error Erro conflict exige resource.
const wrongError:ApiError={code:'conflict'};
void [forged,unchanged,removed,incomplete,wrongEvent,state,unserializable,wrongError];

