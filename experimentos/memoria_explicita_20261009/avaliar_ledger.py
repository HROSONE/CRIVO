"""Composição input-only com o checkpoint anterior; não treina nem promove pesos."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import hashlib
ROOT=Path(__file__).resolve().parents[2]
FONTES=ROOT/'experimentos/memoria_fontes_20261009'
sys.path.insert(0,str(FONTES))
from apoio import INICIAL,ASSOC,CONTEXT,sha,escrever
from preparo import codificar
from rede_eventos import coletar,carregar
from modelo import conferir,executar,esperado
from avaliar_memoria import enriquecer,medir,diagnostico
from ledger import aplicar
from tokenizers import Tokenizer
import torch

def ler(p):return json.loads(Path(p).read_text())
def exigir(x,m):
    if not x:raise RuntimeError(m)

def compor(rows,es):
    out=[]
    for r,e in zip(rows,es):
        exigir((r['sessao'],r['etapa'])==(e['sessao'],e['etapa']),'Cache fora de ordem.')
        p,d=aplicar(list(e['turnos']),deepcopy(r['proposta']))
        if not d['aplicado']:exigir(p==r['proposta'],'Abstenção deve preservar proposta neural.')
        execucao=executar(p);gold=esperado(e)
        out.append({'sessao':e['sessao'],'familia':e['familia'],'etapa':e['etapa'],
                    'evento':e.get('evento'),'trajetoria':e.get('trajetoria'),
                    'evento_previsto':None,**conferir(e,p),'proposta':p,
                    'proposta_neural':r['proposta'],'memoria':d,'execucao':execucao,
                    'resultado_correto':execucao.get('resultado')==gold.get('resultado') and p['hipotese']==e['hipotese']})
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--laboratorio',type=Path,required=True)
    ap.add_argument('--protocolo-sha256',required=True);a=ap.parse_args();lab=a.laboratorio
    exigir(not (lab/'avaliacao').exists(),'Avaliação existente; preservar e não reescolher no teste.')
    exigir(sha(lab/'protocolo.json')==a.protocolo_sha256,'Protocolo difere do hash congelado.')
    p=ler(lab/'protocolo.json')
    for nome,h in p['codigo_sha256'].items():exigir(sha(Path(__file__).parent/nome)==h,'Código alterado: '+nome)
    exigir(sha(INICIAL)==p['pesos_iniciais_sha256'],'Checkpoint anterior alterado.')
    ativo=ROOT/'artefatos/linguagem_profunda/pesos.pt'
    exigir(sha(ativo)==p['pesos_ativos_sha256'],'Pesos ativos alterados.')
    autoria=lab/'avaliacao_autoria'
    for nome,h in p['autoria_sha256'].items():exigir(sha(autoria/nome)==h,'Autoria alterada: '+nome)
    for nome,h in p['dependencias_sha256'].items():exigir(sha(ROOT/nome)==h,'Dependência alterada: '+nome)
    cache_protocolo=ler(FONTES/'protocolo.json')
    exigir(cache_protocolo['inicial_sha256']==p['pesos_iniciais_sha256'],'Cache de outro checkpoint.')
    exigir(cache_protocolo['codigo']['preparo.py']==sha(FONTES/'preparo.py'),'Cache de outro preparo.')
    cache_resumo=ler(FONTES/'avaliacao/resumo.json')
    exigir(cache_resumo['protocolo_sha256']==sha(FONTES/'protocolo.json'),'Cache de outro protocolo.')
    exigir(cache_resumo['avaliador_sha256']==sha(FONTES/'avaliar_memoria.py'),'Cache de outro avaliador.')
    # Somente depois dos guardas o novo painel pode ser desserializado.
    dados={'novo_reservado':ler(autoria/'casos.json'),
           'prospectivo_anterior_conhecido':ler(FONTES/'avaliacao_autoria/casos.json'),
           'retencao_conhecida':ler(ROOT/'experimentos/retencao_contrastes_20261008/dados/teste.json'),
           'associacao_conhecida':ler(ASSOC/'dados/teste.json'),
           'contextual_conhecido':ler(CONTEXT/'dados/teste.json')}
    exigir(len(dados['novo_reservado'])==368,'Novo painel deve conter todos os368 prefixos.')
    exigir(len({e['sessao'] for e in dados['novo_reservado']})==72,'Novo painel deve conter todas as72 sessões.')
    torch.set_num_threads(1);torch.manual_seed(20261016)
    tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));tok.encode_special_tokens=True
    m,_=carregar(path=INICIAL)
    destino=lab/'avaliacao';destino.mkdir();res={};diag={}
    for nome,es in dados.items():
        if nome=='novo_reservado':
            items=[]
            for e in es:
                it=codificar(tok,{'turnos':e['turnos'],'argumentos':[None]*3,'referente':None})
                it['exemplo']=e;items.append(it)
            bruto,base=coletar(m,items,tok.token_to_id('<pad>'))
            for row in bruto+base:row['evento_previsto']=None;row['evento_turno_sem_treino']=True
            enriquecer(bruto,es);escrever(destino/(nome+'_baseline_bruto.json'),bruto)
        else:
            old='prospectivo_autoria' if nome=='prospectivo_anterior_conhecido' else nome
            base=ler(FONTES/'avaliacao'/f'anterior_preparo_novo_{old}_limitado.json')
        final=compor(base,es);enriquecer(base,es);enriquecer(final,es)
        b,f=medir(base),medir(final)
        b.pop('evento_correto',None);f.pop('evento_correto',None)
        f['memoria_aplicada']=sum(v['memoria']['aplicado'] for v in final)
        f['abstencoes']=len(es)-f['memoria_aplicada']
        aplicadas=[v for v in final if v['memoria']['aplicado']]
        f['acuracia_na_cobertura']=sum(v['contrato'] for v in aplicadas)/len(aplicadas) if aplicadas else None
        f['falhas_sem_fonte_literal']=sum(v['memoria'].get('fonte_literal_invalida',False) for v in final)
        res[nome]={'baseline':b,'memoria_explicita':f};diag[nome]={'baseline':diagnostico(base),'memoria_explicita':diagnostico(final)}
        escrever(destino/(nome+'_baseline_limitado.json'),base);escrever(destino/(nome+'_memoria_explicita.json'),final)
        print(json.dumps({'painel':nome,'n':len(es),'baseline':b['contratos_corretos'],'memoria':f['contratos_corretos'],
                          'sessoes_base':b['sessoes_completas'],'sessoes_memoria':f['sessoes_completas'],'cobertura':f['memoria_aplicada']},ensure_ascii=False),flush=True)
    exigir(sha(ativo)==p['pesos_ativos_sha256'],'Pesos ativos alterados na avaliação.')
    novo=res['novo_reservado'];mnovo=novo['memoria_explicita'];bnovo=novo['baseline']
    crit=p['criterios'];eventos={ev:mnovo['por_evento'][ev]['acuracia_contrato'] for ev in ['correcao','hipotese','retorno','confirmacao']}
    familias={f:v['acuracia'] for f,v in mnovo['por_familia'].items()}
    drops={nome:100*(v['baseline']['acuracia_contrato']-v['memoria_explicita']['acuracia_contrato']) for nome,v in res.items() if nome!='novo_reservado'}
    melhora=100*(mnovo['acuracia_contrato']-bnovo['acuracia_contrato'])
    passou=all(v>=crit['evento_min'] for v in eventos.values()) and all(v>=crit['familia_min'] for v in familias.values()) and mnovo['fracao_sessoes_completas']>=crit['sessoes_min'] and melhora>=crit['ganho_geral_pp_min'] and max(drops.values())<=crit['queda_regressoes_pp_max']
    escrever(destino/'resumo.json',{'resultados':res,'diagnosticos':diag,'criterios':{'eventos':eventos,'familias':familias,'ganho_geral_pp':melhora,'quedas_regressoes_pp':drops,'passou_criterio_sintetico':passou},
        'protocolo_sha256':a.protocolo_sha256,'aprovado_para_chat':False,'pesos_alterados':False,
        'limites':['Sistema híbrido: transformer próprio anterior, cópia limitada, ledger/gramática e executor determinísticos. Não atribuir os ganhos da memória a treinamento neural.',
                  'Novo painel reservado, outra autoria na mesma equipe; gramática finita, não avaliação externa independente nem conversa livre.',
                  'Os outros quatro painéis já eram conhecidos e usados somente à regressão/diagnóstico.',
                  'Não há causal LM, geração livre, uso de modelos externos ou ativação dos candidatos reprovados.']})
if __name__=='__main__':main()
