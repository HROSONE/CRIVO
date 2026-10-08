"""Piloto posterior ao teste primário, com outro painel prospectivo.

Nenhum novo treinamento: composição de dois transformers próprios já treinados.
Congela a regra de composição antes de prever o painel. Não é avaliação externa.
"""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'escopo_eventos_20261008'))
import torch
from torch import nn
from tokenizers import Tokenizer
from base import ROOT,INICIAL,sha,escrever
from rede_eventos import carregar,coletar,medidas
from normalizacao import codificar
import dados

class EscopoPreservado(nn.Module):
    def __init__(self,novo,anterior):
        super().__init__();self.novo=novo;self.anterior=anterior
    def forward(self,x,l):
        out=self.novo(x,l);out['escopo']=self.anterior(x,l)['escopo']
        return out

def preparar(saida):
    saida.mkdir(exist_ok=False)
    dados.PLANOS['teste']=['Pinho','Praia','Vale','Ferro']
    dados.PESSOAS['teste']=['Nina','Hugo','Mila','Enzo']
    dados.OBJETOS['teste']=['bilhete','cupom','carimbo','etiqueta']
    dados.FORMAS['teste']={
        'inicio':['O valor atual de {n} é {v} reais. '],
        'correcao':['Não estou simulando. Corrijo o dado real: {n} custa {v} reais. '],
        'hipotese':['Não é o caso real. Imagine uma alternativa em que {n} custa {v} reais. '],
        'retorno':['Não use a alternativa. Calcule com os fatos já corrigidos. '],
        'consulta':['Mantenha tudo como está e repita a comparação. '],
        'confirmacao':['Agora a alternativa deixou de ser imaginária: é o que aconteceu de verdade. '],
        'pergunta':['Compare os gastos de {a} e {b}.'],
        'regra':['Para entrar, os objetos exigidos são {v}. '],
        'posse':['Sobre {n}, a informação confirmada é que {v}. '],
        'corr_posse':['Não é simulação. Corrijo os dados reais: {n} {v}. '],
        'hip_posse':['Imagine apenas uma alternativa: {n} {v}, sem modificar os fatos reais. '],
        'ret_posse':['Não use o inventário imaginário. Volte aos objetos reais corrigidos. '],
        'perg_posse':['Confira se os fatos permitem que {n} entre.'],
    }
    tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));tok.encode_special_tokens=True
    rows=[];i=100000;aceitos=0;rejeitados=0
    while aceitos<48:
        es=dados.construir('teste',i);i+=1
        try:
            for e in es:codificar(tok,e)
        except ValueError:rejeitados+=1;continue
        rows+=es;aceitos+=1
    escrever(saida/'casos.json',rows)
    escrever(saida/'protocolo.json',{'codigo_sha256':sha(__file__),'casos_sha256':sha(saida/'casos.json'),
        'anterior_sha256':sha(INICIAL),'candidato':'eventos selecionado pela validação primária, passo 600',
        'regra_antes_das_previsoes':'Operação, ponteiros e evento da rede nova; escopo da rede anterior; mesma preparação nova. Nenhum alvo guia a composição.',
        'sessoes':aceitos,'prefixos':len(rows),'rejeitados_sem_truncar':rejeitados,
        'criterio_piloto':'Melhorar contrato geral e cada evento crítico versus anterior; não pode promover chat.',
        'limites':'Frases e entidades novas; mesmas regras e autoria do corpus anterior, perguntas Compare favorecem normalizador. Piloto posterior ao teste primário que diagnosticou regressão de escopo. Uma semente. Não é evidência independente; não há novo treino nesta composição.'})
    print('Painel e composição registrados antes da previsão:',len(rows),'prefixos',flush=True)

def avaliar(saida,candidato):
    p=json.loads((saida/'protocolo.json').read_text());assert sha(__file__)==p['codigo_sha256']
    assert sha(saida/'casos.json')==p['casos_sha256'];assert sha(INICIAL)==p['anterior_sha256']
    torch.set_num_threads(1);torch.manual_seed(20261013)
    tok=Tokenizer.from_file(str(ROOT/'artefatos/linguagem_profunda/tokenizer.json'));tok.encode_special_tokens=True
    items=[codificar(tok,e) for e in json.loads((saida/'casos.json').read_text())];pad=tok.token_to_id('<pad>')
    antigo,_=carregar();novo,_=carregar(candidato);comb=EscopoPreservado(novo,antigo)
    p['candidato_sha256']=sha(candidato)
    escrever(saida/'protocolo_modelos.json',p)
    res={}
    for nome,m in [('anterior',antigo),('eventos',novo),('escopo_preservado',comb)]:
        raw,lim=coletar(m,items,pad)
        escrever(saida/(nome+'_bruto.json'),raw);escrever(saida/(nome+'_limitado.json'),lim)
        res[nome]={'bruto':medidas(raw),'limitado':medidas(lim)}
        print(nome, sum(r['contrato'] for r in lim),'/',len(lim),flush=True)
    a=res['anterior']['limitado'];c=res['escopo_preservado']['limitado']
    criticos=['correcao','hipotese','retorno','confirmacao']
    passou=c['acuracia_contrato']>a['acuracia_contrato'] and all(c['por_evento'][e]['acuracia_contrato']>=a['por_evento'][e]['acuracia_contrato'] for e in criticos)
    escrever(saida/'resumo.json',{'resultados':res,'criterio_piloto_passou':passou,'aprovado_para_chat':False,
        'novo_treino':False,'limites':p['limites'],'protocolo_sha256':sha(saida/'protocolo.json'),
        'parametros_instanciados':sum(x.numel() for x in comb.parameters()),'pesos_externos':False})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--saida',type=Path,required=True)
    p.add_argument('--preparar',action='store_true');p.add_argument('--candidato',type=Path);a=p.parse_args()
    if a.preparar:preparar(a.saida)
    else:
        assert a.candidato;avaliar(a.saida,a.candidato)
