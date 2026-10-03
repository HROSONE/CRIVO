"""Rede própria de efeitos com regressão aritmética e MLP booleano: pesos aleatórios, NumPy opcional, sem pesos externos."""
import hashlib
from pathlib import Path
import json
from interpretacao_estados import OPERACOES, efeito_exato


def particao(op,a,b):
    # Reversões de um mesmo par de operandos permanecem juntas em cada operação.
    grupo=op+':'+str(min(a,b))+':'+str(max(a,b))
    n=int(hashlib.sha256(('efeitos-v1:'+grupo).encode()).hexdigest()[:8],16)%10
    return 'validacao' if n==0 else 'teste' if n==1 else 'treino'


def dados():
    return [dict(op=op,a=a,b=b,resultado=efeito_exato(op,a,b),split=particao(op,a,b))
            for op in OPERACOES for a in range(-8,9) for b in range(-8,9)]


def features(op,a,b):
    if op not in OPERACOES or type(a) is not int or type(b) is not int or abs(a)>8 or abs(b)>8:
        raise ValueError('Rede só prevê quatro operações com operandos inteiros em [-8,8]')
    return [float(op==p) for p in OPERACOES]+[a/8,b/8]


class RedeEfeitos:
    def __init__(self,semente=7,ocultas=64):
        import numpy as np
        if not 4<=ocultas<=128:raise ValueError('Tamanho inválido')
        self.np=np;rng=np.random.default_rng(semente)
        self.w1=rng.normal(0,(2/6)**.5,(6,ocultas));self.b1=np.zeros(ocultas)
        self.w2=rng.normal(0,(2/ocultas)**.5,(ocultas,2));self.b2=np.zeros(2)
        self.wn=rng.normal(0,.1,6)
    def forward(self,x):
        np=self.np;h=np.tanh(x@self.w1+self.b1);z=h@self.w2+self.b2
        z-=z.max(axis=1,keepdims=True);p=np.exp(z);p/=p.sum(axis=1,keepdims=True)
        return h,p
    def numericas(self,x):
        # Canais por operação e operando. Não calcula soma/subtração nos atributos.
        np=self.np
        return np.column_stack((x[:,0],x[:,1],x[:,0]*x[:,4],x[:,0]*x[:,5],x[:,1]*x[:,4],x[:,1]*x[:,5]))
    def perda_gradientes(self,x,y):
        np=self.np;h,p=self.forward(x);n=self.numericas(x)
        arit=x[:,:2].sum(axis=1)>0;logica=~arit
        residuo=(n@self.wn-y/8)*arit
        # Pesos balanceiam os resultados booleanos; são calculados só no lote de treino.
        pesos=np.zeros(len(y))
        for rotulo in (0,1):
            ids=logica & (y==rotulo);pesos[ids]=1/max(1,ids.sum())
        pesos/=max(pesos.sum(),1e-12)
        yi=np.where(logica,y,0).astype(int)
        perda=float((residuo**2).sum()/max(1,arit.sum())-
            (np.log(np.maximum(p[np.arange(len(y)),yi],1e-15))*pesos).sum())
        dz=p.copy();dz[np.arange(len(y)),yi]-=1;dz*=pesos[:,None]
        dw2=h.T@dz;db2=dz.sum(axis=0);dh=(dz@self.w2.T)*(1-h*h)
        dwn=n.T@(2*residuo/max(1,arit.sum()))
        return perda,(x.T@dh,dh.sum(axis=0),dw2,db2,dwn)
    def treinar(self,registros,passos=4000,lote=128,taxa=.003,semente=11):
        np=self.np
        if not registros or any(r['split']!='treino' for r in registros):raise ValueError('Treino exige somente partição treino')
        if not 1<=passos<=20000 or not 1<=lote<=512 or not 0<taxa<=.1:raise ValueError('Hiperparâmetros inválidos')
        x=np.asarray([features(r['op'],r['a'],r['b']) for r in registros]);y=np.asarray([int(r['resultado']) for r in registros])
        parametros=(self.w1,self.b1,self.w2,self.b2,self.wn)
        m=[np.zeros_like(p) for p in parametros];v=[np.zeros_like(p) for p in parametros]
        rng=np.random.default_rng(semente);historico=[]
        for passo in range(1,passos+1):
            ids=rng.integers(len(y),size=lote);perda,gs=self.perda_gradientes(x[ids],y[ids])
            for i,(p,g) in enumerate(zip(parametros,gs)):
                m[i]=.9*m[i]+.1*g;v[i]=.999*v[i]+.001*g*g
                p-=taxa*(m[i]/(1-.9**passo))/(np.sqrt(v[i]/(1-.999**passo))+1e-8)
            if passo==1 or passo%500==0 or passo==passos:historico.append(dict(passo=passo,perda=perda))
        return historico
    def prever(self,op,a,b):
        np=self.np;x=np.asarray([features(op,a,b)])
        if op in ('+','-'):return int(np.rint((self.numericas(x)@self.wn)[0]*8))
        _,p=self.forward(x);return bool(p.argmax(axis=1)[0])
    def avaliar(self,registros):
        rs={}
        for op in OPERACOES:
            xs=[r for r in registros if r['op']==op];acertos=0
            for r in xs:
                try:
                    v=self.prever(op,r['a'],r['b']);acertos+=type(v) is type(r['resultado']) and v==r['resultado']
                except ValueError:pass
            rs[op]=dict(total=len(xs),corretos=acertos,taxa=acertos/len(xs) if xs else None)
        return rs
    def salvar(self,pasta):
        p=Path(pasta);p.mkdir(parents=True,exist_ok=True)
        self.np.savez(p/'rede.npz',w1=self.w1,b1=self.b1,w2=self.w2,b2=self.b2,wn=self.wn)
        (p/'config.json').write_text(json.dumps(dict(versao=2,arquitetura='regressao_condicionada_por_operador_e_mlp_booleano',operacoes=OPERACOES,dominio=[-8,8],ocultas=len(self.b1),parametros=sum(x.size for x in (self.w1,self.b1,self.w2,self.b2,self.wn)),pesos_pre_treinados=False),indent=2)+'\n')
    @classmethod
    def carregar(cls,pasta):
        import numpy as np
        cfg=json.loads((Path(pasta)/'config.json').read_text())
        if cfg['versao']!=2 or cfg['operacoes']!=list(OPERACOES) or cfg['dominio']!=[-8,8]:raise ValueError('Modelo incompatível')
        r=cls(ocultas=cfg['ocultas'])
        with np.load(Path(pasta)/'rede.npz',allow_pickle=False) as d:
            for n in ('w1','b1','w2','b2','wn'):
                v=d[n]
                if v.shape!=getattr(r,n).shape or not np.isfinite(v).all():raise ValueError('Pesos inválidos')
                setattr(r,n,v.copy())
        return r
