"""Avaliação única após treino; critérios fixados antes de ler saídas do teste.

Todos os textos e erros são preservados. Não seleciona nem altera pesos.
Avalia contrato estrutural, não qualidade de conversa generativa geral.
"""
import argparse
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import torch
from corpus import CLASSES, escrever
from modelo import Interprete, codificar, esperado, metricas, norm
from treinar import avaliar


def normalizar_resultado(v):
    if isinstance(v, dict): return {k:normalizar_resultado(x) for k,x in v.items()}
    if isinstance(v, list): return [normalizar_resultado(x) for x in v]
    if isinstance(v, str):
        try: return str(Decimal(v).normalize())
        except InvalidOperation: return norm(v)
    if isinstance(v, (int,float)) and not isinstance(v,bool): return str(Decimal(str(v)).normalize())
    return v


def conferir_motor(e, ident, texto, r, a):
    gold=esperado(e)['resultado'];op=e['operacao']
    if op in ('comparar_custos','tempo_restante'):
        return bool(r and r.get('operacao')==op and bool(r.get('hipotese'))==e['hipotese']
                    and normalizar_resultado(r.get('resultado'))==normalizar_resultado(gold))
    if op=='verificar_requisitos':
        aliases={'sustentado':'provado','refutado':'refutado','indeterminado':'indeterminado','inconsistente':'contraditorio'}
        status=aliases.get(r.get('resultado',{}).get('status')) if r else None
        return bool(r and r.get('operacao')==op and bool(r.get('hipotese'))==e['hipotese'] and status==gold['status'])
    if op=='resumir_objetivos':
        # Contrato de meta atual + limite. O painel não pontua livre redação.
        if not a:return False
        gs={norm(g) for g in a.get('objetivos',[])}
        ls={norm(re.sub(r'^(?:eu\s+)?tenho\s+', '', g, flags=re.I)) for g in a.get('impedimentos',[])}
        if e['hipotese']:
            return norm(gold['objetivo']) in norm(a.get('alternativa') or '') and norm(gold['restricao']) in ls
        return gs=={norm(gold['objetivo'])} and norm(gold['restricao']) in ls
    if op=='consultar_valor':
        # Motor atual não oferece esse contrato tipado de consulta por pessoa.
        # Conservar a resposta para leitura manual, sem adivinhar significado.
        return False
    if op=='esclarecer':
        return bool((r and r.get('status')=='ambiguo') or ident=='contexto:sem_referencia')
    return False


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--raiz',type=Path,required=True)
    parser.add_argument('--experimento',type=Path,required=True);args=parser.parse_args()
    p=args.experimento;saida=p/'avaliacao';saida.mkdir(exist_ok=False)
    torch.set_num_threads(1);sys.path.insert(0,str(args.raiz))
    from linguagem_profunda import carregar
    from crivo import Crivo
    manifest=json.loads((p/'dados/manifesto.json').read_text())
    raw=(p/'dados/teste.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==manifest['sha256']['teste']
    # Ambos os braços precisam completar o orçamento antes de abrir o teste.
    rels={b:json.loads((p/b/'relatorio.json').read_text()) for b in ['controle','contextual']}
    assert all(r['passos']==600 and not r['teste_lido_no_treino'] for r in rels.values())
    exemplos=json.loads(raw);inicio=time.monotonic();rs={}
    for b in ['controle','contextual']:
        corpo,tok,_=carregar(args.raiz/'artefatos/linguagem_profunda')
        itens=[codificar(tok,e) for e in exemplos]
        estado=torch.load(p/b/'pesos.pt',map_location='cpu',weights_only=True)
        m=Interprete(corpo,b);m.load_state_dict(estado['modelo'])
        rs[b]=avaliar(m,itens,tok.token_to_id('<pad>'))
        escrever(saida/(b+'.json'),rs[b]);print(b,metricas(rs[b]),flush=True)
    atual=[];controle=[];bot=None;sessao=None
    for i,e in enumerate(exemplos):
        if e['sessao']!=sessao:sessao=e['sessao'];bot=Crivo()
        texto=e['turnos'][-1];t=time.monotonic()
        try:
            ident,resposta=bot.responder(texto)
            h=bot.historico[-1] if bot.historico and bot.historico[-1].get('pergunta')==texto else {}
            r=h.get('raciocinio_conversa') if ident=='conversa:raciocinio' else None
            a=h.get('argumentos_conversa') if ident=='conversa:argumentos' else None
            correto=conferir_motor(e,ident,resposta,r,a)
            row={'sessao':sessao,'familia':e['familia'],'etapa':e['etapa'],'id':ident,
                 'resposta':resposta,'raciocinio':r,'argumentos':a,'contrato':correto}
        except Exception as exc:
            row={'sessao':sessao,'familia':e['familia'],'etapa':e['etapa'],'erro':type(exc).__name__,
                 'mensagem':str(exc),'contrato':False}
        row['segundos']=round(time.monotonic()-t,3);atual.append(row)
        # Controle usa o extrator/motor atuais; classificador pode vetar domínio
        # errado. É um braço diagnóstico distinto do Crivo atual sem esse veto.
        gate=rs['controle'][i]['classe_correta']
        controle.append({**row,'classe_predita':rs['controle'][i]['classe_predita'],
                         'classe_correta':gate,'contrato':bool(row['contrato'] and gate)})
        escrever(saida/'crivo_atual.json',atual)
        if (i+1)%40==0:print('motor',i+1,metricas(atual),flush=True)
    escrever(saida/'controle_execucao.json',controle)
    # Resultado com todos os argumentos/fontes/escopo, e operação executável.
    candidato=[]
    for row in rs['contextual']:
        candidato.append({**row,'contrato':bool(row['contrato'] and row['execucao']['executavel'] and row['resultado_correto'])})
    resultado={'teste_sha256':manifest['sha256']['teste'], 'crivo_atual':metricas(atual),
        'controle_execucao':metricas(controle),'candidato_execucao':metricas(candidato),
        'controle_classes':metricas(rs['controle']),'candidato_argumentos':metricas(rs['contextual']),
        'corretos_so_resultado_candidato':sum(r['resultado_correto'] for r in rs['contextual']),
        'propostas_nao_executaveis':sum(not r['execucao']['executavel'] for r in rs['contextual']),
        'candidato_executaveis_incorretas':sum(r['execucao']['executavel'] and not r['resultado_correto'] for r in rs['contextual']),
        'aprovado_para_chat':False,'avaliacao_independente':False,'segundos':round(time.monotonic()-inicio,2),
        'limite':'Painel sintético autoral. Candidato tem ponteiros/execução sobre histórico bruto; baseline tem memória persistente e rotas próprias. Critérios de metadados subestimam respostas equivalentes sem contrato exportado, especialmente consultas e esclarecimentos. Não mede conversa livre nem isola causalmente arquitetura, objetivo e extrator.'}
    familias=resultado['candidato_execucao']['por_familia']
    diff=resultado['candidato_execucao']['sessoes_completas']/100-resultado['crivo_atual']['sessoes_completas']/100
    resultado['ganho_sessoes_sobre_atual']=diff
    resultado['atingiu_utilidade_piloto']=diff>=.20 and min(r['acuracia'] for r in familias.values())>=.80
    escrever(saida/'resultado.json',resultado);print(json.dumps(resultado,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
