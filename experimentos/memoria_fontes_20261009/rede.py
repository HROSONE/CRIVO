"""Corpo e cabeças anteriores próprios congelados; adapta evento e fontes."""
import math
import torch
from torch import nn
from apoio import INICIAL
from rede_eventos import RedeEventos
from linguagem_profunda import Configuracao,LinguagemProfunda

class MemoriaFontes(RedeEventos):
    def __init__(self,corpo,usuario_id,pad_id):
        super().__init__(corpo)
        for p in self.parameters():p.requires_grad_(False)
        d=corpo.config.dimensao;self.usuario_id=usuario_id;self.pad_id=pad_id
        self.fusao=nn.Sequential(nn.Linear(2*d,d),nn.GELU())
        self.delta_escopo=nn.Linear(d,2)
        self.evento_turno=nn.Linear(d,6)
        self.consultas_validade=nn.Linear(d,12*24)
        self.chaves_validade=nn.Linear(d,24)
        self.vies_validade=nn.Parameter(torch.zeros(3,4))
        nn.init.zeros_(self.delta_escopo.weight);nn.init.zeros_(self.delta_escopo.bias)
        nn.init.zeros_(self.consultas_validade.weight);nn.init.zeros_(self.consultas_validade.bias)

    def train(self,mode=True):
        super().train(mode);self.corpo.eval();return self

    @torch.no_grad()
    def representar(self,x,l):
        c=self.corpo;c.eval()
        def enc(y):
            h=c.embedding(y)+c.posicao(torch.arange(y.shape[1],device=y.device))
            for b in c.blocos:h=b(h)
            return c.norm(h)
        h=enc(x);atual=h[torch.arange(len(x),device=x.device),l-1]
        pos=torch.arange(x.shape[1],device=x.device)[None,:]
        starts=torch.where((x==self.usuario_id)&(pos<l[:,None]),pos,-1).max(-1).values
        assert bool((starts>=0).all())
        ul=l-starts;idx=starts[:,None]+torch.arange(int(ul.max()),device=x.device)[None,:]
        ultimo=x.gather(1,idx.clamp_max(x.shape[1]-1)).masked_fill(idx>=l[:,None],self.pad_id)
        local=enc(ultimo)[torch.arange(len(x),device=x.device),ul-1]
        q=self.consultas(atual).view(len(x),8,-1);k=self.chaves(h)
        points=torch.einsum('bhd,btd->bht',q,k)/math.sqrt(k.shape[-1])
        points+=self.vies_fonte(h).transpose(1,2)
        mask=pos>=l[:,None]
        original={'operacao':self.operacao(atual),'escopo':self.escopo(atual),'pontos':points.masked_fill(mask[:,None,:],-1e9)}
        return h,atual,local,mask,original

    def forward(self,x,l):
        h,atual,local,mask,orig=self.representar(x,l)
        z=self.fusao(torch.cat([atual,local],-1));scope=orig['escopo']+self.delta_escopo(z)
        q=self.consultas_validade(z).view(len(x),3,4,24);k=self.chaves_validade(h)
        val=torch.einsum('bsrd,btd->bsrt',q,k)/math.sqrt(24)+self.vies_validade[None,:,:,None]
        # Banco ativo apenas: escopo errado não altera a escolha das fontes.
        active=torch.nn.functional.logsigmoid(val[:,2])+math.log(2)
        bias=2*active
        points=(orig['pontos']+bias.repeat_interleave(2,dim=1)).masked_fill(mask[:,None,:],-1e9)
        return {'operacao':orig['operacao'],'escopo':scope,'evento':self.evento_turno(z),
                'pontos':points,'validade':val,'original':orig}

def carregar(tok,path=INICIAL):
    state=torch.load(path,map_location='cpu',weights_only=True)
    m=MemoriaFontes(LinguagemProfunda(Configuracao(**state['config'])),tok.token_to_id('<usuario>'),tok.token_to_id('<pad>'))
    faltas=m.load_state_dict(state['modelo'],strict=False)
    assert not faltas.unexpected_keys
    assert all(k.startswith(('fusao.','delta_escopo.','evento_turno.','consultas_validade.','chaves_validade.','vies_validade')) for k in faltas.missing_keys)
    return m,state
