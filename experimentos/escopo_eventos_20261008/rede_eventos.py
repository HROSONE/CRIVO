"""Cabeça auxiliar própria. O evento alvo nunca entra na inferência."""
import math
import torch
from torch import nn
from base import INICIAL
from modelo import Interprete, lote, proposta, conferir, executar, esperado, metricas
from decodificar import proposta_limitada
from dados import EVENTOS
from linguagem_profunda import Configuracao, LinguagemProfunda

class RedeEventos(Interprete):
    def __init__(self, corpo):
        super().__init__(corpo,'contextual')
        self.evento=nn.Linear(corpo.config.dimensao,len(EVENTOS))

    def forward(self,x,comprimentos):
        c=self.corpo
        h=c.embedding(x)+c.posicao(torch.arange(x.shape[1],device=x.device))
        for b in c.blocos:h=b(h)
        h=c.norm(h);atual=h[torch.arange(len(x),device=x.device),comprimentos-1]
        q=self.consultas(atual).view(len(x),8,-1);k=self.chaves(h)
        pontos=torch.einsum('bhd,btd->bht',q,k)/math.sqrt(k.shape[-1])
        pontos+=self.vies_fonte(h).transpose(1,2)
        mask=torch.arange(x.shape[1],device=x.device)[None,:]>=comprimentos[:,None]
        return {'operacao':self.operacao(atual),'escopo':self.escopo(atual),
                'evento':self.evento(atual),'pontos':pontos.masked_fill(mask[:,None,:],-1e9)}

def carregar(path=INICIAL,device='cpu'):
    s=torch.load(path,map_location='cpu',weights_only=True)
    m=RedeEventos(LinguagemProfunda(Configuracao(**s['config'])))
    faltas=m.load_state_dict(s['modelo'],strict=False)
    assert not faltas.unexpected_keys
    assert set(faltas.missing_keys) in [set(),{'evento.weight','evento.bias'}]
    return m.to(device),s

@torch.no_grad()
def coletar(m,itens,pad):
    m.eval();raw=[];limited=[];device=next(m.parameters()).device
    for i in range(0,len(itens),16):
        bs=itens[i:i+16];x,l=lote(bs,pad);ls=m(x.to(device),l.to(device))
        for j,item in enumerate(bs):
            e=item['exemplo']
            for dst,dec in [(raw,proposta),(limited,proposta_limitada)]:
                p=dec(item,ls,j);out=executar(p);gold=esperado(e)
                dst.append({'sessao':e['sessao'],'familia':e['familia'],'etapa':e['etapa'],
                    'evento':e.get('evento'),'trajetoria':e.get('trajetoria'),
                    'evento_previsto':EVENTOS[int(ls['evento'][j].argmax())],
                    **conferir(e,p),'proposta':p,'execucao':out,
                    'resultado_correto':out.get('resultado')==gold.get('resultado') and p['hipotese']==e['hipotese']})
    return raw,limited

def medidas(rows):
    out=metricas(rows)
    for campo in ['evento','trajetoria']:
        vals=sorted({r[campo] for r in rows if r.get(campo)})
        out['por_'+campo]={k:metricas([r for r in rows if r.get(campo)==k]) for k in vals}
    out['escopo_correto']=sum(r['escopo'] for r in rows)/len(rows)
    if any(r.get('evento') for r in rows):
        out['evento_correto']=sum(r['evento']==r['evento_previsto'] for r in rows)/len(rows)
    return out

def macro_eventos(rows):
    grupos=medidas(rows)['por_evento']
    return sum(v['acuracia_contrato'] for v in grupos.values())/len(grupos)

def macro_familias(rows):
    fs=metricas(rows)['por_familia']
    return sum(v['acuracia'] for v in fs.values())/len(fs)
