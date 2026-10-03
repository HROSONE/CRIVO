"""Rede própria V3: igualdade sobre diferença prevista e cobertura por posição."""
import hashlib
import json
from pathlib import Path
from rede_estruturas import RedeEstruturas,dados as dados_v2,grupo
from interpretacao_estruturas import efeito_exato


def particao_indice(xs):
    chave=json.dumps(xs,separators=(',',':'))
    n=int(hashlib.sha256(('indice-completo-v1:'+chave).encode()).hexdigest()[:8],16)%10
    return 'validacao' if n==0 else 'teste' if n==1 else 'treino'


def dados():
    import random
    rs=[r for r in dados_v2() if r['op']!='indice']
    rng=random.Random(20261011);arrays=[]
    # Todos os índices válidos de cada array ficam na mesma partição.
    # Arrays de 16 posições recebem cobertura suficiente para identificar os 16 coeficientes.
    for _ in range(1200):arrays.append([rng.randrange(-16,17) for _ in range(16)])
    for _ in range(1200):arrays.append([rng.randrange(-16,17) for _ in range(rng.randrange(1,17))])
    vistos=set()
    for xs in arrays:
        chave=tuple(xs)
        if chave in vistos:continue
        vistos.add(chave);split=particao_indice(xs)
        for idx in range(len(xs)):
            rs.append(dict(op='indice',a=xs,b=idx,resultado=efeito_exato('indice',xs,idx),split=split))
    return rs


class RedePrecisa(RedeEstruturas):
    def __init__(self,semente=7):
        super().__init__(semente)
        rng=self.np.random.default_rng(semente+900)
        # Distância e constante: logits aprendidos; não calcula a==b como atributo.
        self.parametros['igualdade']=rng.normal(0,.1,(2,2))
    def features_igualdade(self,a,b):
        # O delta vem da cabeça aritmética própria. Sem acesso ao executor exato.
        delta=super().prever('-',a,b)
        return [abs(delta),1.]
    def loss_igualdade(self,x,y):
        np=self.np;z=x@self.parametros['igualdade'];z-=z.max(axis=1,keepdims=True)
        p=np.exp(z);p/=p.sum(axis=1,keepdims=True)
        loss=float(-np.log(np.maximum(p[np.arange(len(y)),y],1e-15)).mean())
        dz=p.copy();dz[np.arange(len(y)),y]-=1;dz/=len(y)
        return loss,x.T@dz
    def treinar(self,registros,passos=5000,semente=11,lote=128):
        if not registros or any(r['split']!='treino' for r in registros):raise ValueError('Somente partição treino')
        if not 2<=lote<=256:raise ValueError('Igualdade exige lote entre 2 e 256')
        iguais=[r for r in registros if r['op']=='===']
        if not iguais:raise ValueError('Faltam exemplos de igualdade')
        # O parent conserva arquitetura, Adam e operadores restantes; agora vê todos os índices.
        hist=super().treinar([r for r in registros if r['op'] not in ('===','!==')],passos,semente,lote)
        np=self.np;x=np.asarray([self.features_igualdade(r['a'],r['b']) for r in iguais]);y=np.asarray([int(r['resultado']) for r in iguais])
        grupos=[np.flatnonzero(y==i) for i in (0,1)]
        if any(not len(g) for g in grupos):raise ValueError('Igualdade exige as duas classes no treino')
        rng=np.random.default_rng(semente+800);p=self.parametros['igualdade'];m=np.zeros_like(p);v=np.zeros_like(p)
        for passo in range(1,2001):
            # Metade iguais, metade diferentes; a seleção usa somente exemplos de treino.
            n0=lote//2;ids=np.concatenate((rng.choice(grupos[0],n0),rng.choice(grupos[1],lote-n0)))
            loss,g=self.loss_igualdade(x[ids],y[ids]);m=.9*m+.1*g;v=.999*v+.001*g*g
            p-=.01*(m/(1-.9**passo))/(np.sqrt(v/(1-.999**passo))+1e-8)
            if passo==1 or passo%500==0:hist.append(dict(etapa='igualdade',passo=passo,perda=loss))
        return hist
    def prever(self,op,a,b=0):
        if op not in ('===','!=='):return super().prever(op,a,b)
        if type(a) is not int or type(b) is not int or abs(a)>16 or abs(b)>16:raise ValueError('Igualdade neural exige inteiros [-16,16]')
        np=self.np;x=np.asarray(self.features_igualdade(a,b));z=x@self.parametros['igualdade']
        igual=bool(z.argmax())
        return igual if op=='===' else not igual
    def salvar(self,pasta):
        super().salvar(pasta);p=Path(pasta)/'config.json';cfg=json.loads(p.read_text())
        cfg.update(versao=2,arquitetura='efeitos_estruturados_precisos',igualdade='cabeca_linear_sobre_diferenca_prevista',etapas=['operadores','igualdade'])
        p.write_text(json.dumps(cfg,indent=2)+'\n')
    @classmethod
    def carregar(cls,pasta):
        import numpy as np
        cfg=json.loads((Path(pasta)/'config.json').read_text())
        if cfg.get('versao')!=2 or cfg.get('arquitetura')!='efeitos_estruturados_precisos':raise ValueError('Modelo preciso incompatível')
        r=cls()
        with np.load(Path(pasta)/'rede.npz',allow_pickle=False) as d:
            if set(d.files)!=set(r.parametros):raise ValueError('Parâmetros divergentes')
            for k,p in r.parametros.items():
                if d[k].shape!=p.shape or not np.isfinite(d[k]).all():raise ValueError('Pesos inválidos')
                r.parametros[k]=d[k].copy()
        return r
