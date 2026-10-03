"""Pesos próprios de efeitos numéricos, booleanos e estruturais; sem fallback."""
import hashlib
import json
from pathlib import Path
from interpretacao_estruturas import efeito_exato, unidades

NUMERICAS=('+','-','<','<=','>','>=','===','!==')
LOGICAS=('&&','||','!')


def grupo(r):
    if r['op'] in NUMERICAS:
        a,b=r['a'],r['b'];chave=[r['op'],min(a,b),max(a,b)]
    else:chave=[r['op'],r['a'],r['b']]
    return json.dumps(chave,sort_keys=True,ensure_ascii=True,separators=(',',':'))


def particao(r):
    n=int(hashlib.sha256(('efeitos-estruturas-v1:'+grupo(r)).encode()).hexdigest()[:8],16)%10
    return 'validacao' if n==0 else 'teste' if n==1 else 'treino'


def dados():
    import random
    registros=[]
    def adicionar(op,a,b=0):
        r=dict(op=op,a=a,b=b,resultado=efeito_exato(op,a,b));r['split']=particao(r);registros.append(r)
    for op in NUMERICAS:
        for a in range(-16,17):
            for b in range(-16,17):adicionar(op,a,b)
    # Todas as tabelas booleanas ficam no treino: mede-se sua composição em programas inéditos.
    for op in LOGICAS:
        for a in (False,True):
            for b in ((False,True) if op!='!' else (False,)):
                registros.append(dict(op=op,a=a,b=b,resultado=efeito_exato(op,a,b),split='treino'))
    rng=random.Random(20261003)
    for _ in range(2400):
        tamanho=rng.randrange(17);xs=[rng.randrange(-16,17) for _ in range(tamanho)]
        adicionar('comprimento',xs)
        if xs:adicionar('indice',xs,rng.randrange(tamanho))
        texto=''.join(rng.choice('aéZ 💻') for _ in range(rng.randrange(9)))
        adicionar('comprimento',texto)
    unicos={}
    for r in registros:
        chave=json.dumps([r['op'],r['a'],r['b']],sort_keys=True,ensure_ascii=True)
        unicos.setdefault(chave,r)
    return list(unicos.values())


def features_num(op,a,b):
    if op not in NUMERICAS or type(a) is not int or type(b) is not int or abs(a)>512 or abs(b)>512:
        raise ValueError('Efeito numérico fora do domínio')
    return [float(op==p) for p in NUMERICAS]+[a/16,b/16]


def features_log(op,a,b):
    if op not in LOGICAS or type(a) is not bool or op!='!' and type(b) is not bool:raise ValueError('Lógica exige booleanos')
    return [float(op==p) for p in LOGICAS]+[float(a),float(b)]


def estrutura(a):
    xs=unidades(a) if type(a) is str else a
    if type(xs) is not list or len(xs)>16:raise ValueError('Rede estrutural exige até 16 posições UTF-16/array')
    return [1. if i<len(xs) else 0. for i in range(16)]


def vetor_indice(a,b):
    if type(a) is not list or not 0<len(a)<=16 or type(b) is not int or not 0<=b<len(a) or any(type(x) is not int or abs(x)>16 for x in a):
        raise ValueError('Índice neural exige array de inteiros em [-16,16]')
    return [x/16 for x in a]+[0.]*(16-len(a)),[float(i==b) for i in range(16)]


class RedeEstruturas:
    def __init__(self,semente=7):
        import numpy as np
        self.np=np;rng=np.random.default_rng(semente)
        self.parametros={}
        for prefixo,n,h in (('n',10,96),('l',5,16)):
            self.parametros[prefixo+'w1']=rng.normal(0,(2/n)**.5,(n,h))
            self.parametros[prefixo+'b1']=np.zeros(h)
            self.parametros[prefixo+'w2']=rng.normal(0,(2/h)**.5,(h,2))
            self.parametros[prefixo+'b2']=np.zeros(2)
        self.parametros['arit']=rng.normal(0,.1,6)
        self.parametros['comprimento']=rng.normal(0,.1,17)
        self.parametros['indice']=rng.normal(0,.1,(16,16))
        self.parametros['indice_bias']=np.zeros(16)
    def forward(self,x,prefixo):
        np=self.np;p=self.parametros;h=np.tanh(x@p[prefixo+'w1']+p[prefixo+'b1'])
        z=h@p[prefixo+'w2']+p[prefixo+'b2'];z-=z.max(axis=1,keepdims=True)
        ps=np.exp(z);ps/=ps.sum(axis=1,keepdims=True);return h,ps
    def loss_mlp(self,x,y,prefixo,pesos=None):
        np=self.np;h,p=self.forward(x,prefixo)
        if pesos is None:pesos=np.full(len(y),1/len(y))
        loss=float(-(np.log(np.maximum(p[np.arange(len(y)),y],1e-15))*pesos).sum())
        dz=p.copy();dz[np.arange(len(y)),y]-=1;dz*=pesos[:,None]
        dh=(dz@self.parametros[prefixo+'w2'].T)*(1-h*h)
        return loss,{prefixo+'w1':x.T@dh,prefixo+'b1':dh.sum(0),prefixo+'w2':h.T@dz,prefixo+'b2':dz.sum(0)}
    def arit_features(self,x):
        np=self.np;return np.column_stack((x[:,0],x[:,1],x[:,0]*x[:,-2],x[:,0]*x[:,-1],x[:,1]*x[:,-2],x[:,1]*x[:,-1]))
    def loss_linear(self,x,y,chave):
        d=x@self.parametros[chave]-y/16
        return float((d*d).mean()),{chave:x.T@(2*d/len(y))}
    def loss_indice(self,x,q,y):
        d=(q@self.parametros['indice']*x).sum(1)+q@self.parametros['indice_bias']-y/16
        loss=float((d*d).mean())
        return loss,{'indice':q.T@(x*(2*d/len(y))[:,None]),'indice_bias':q.T@(2*d/len(y))}
    def treinar(self,registros,passos=5000,semente=11,lote=128):
        np=self.np
        if not registros or any(r['split']!='treino' for r in registros):raise ValueError('Somente treino permitido')
        if not 1<=passos<=12000 or not 1<=lote<=256:raise ValueError('Orçamento inválido')
        subsets={k:[r for r in registros if r['op'] in ops] for k,ops in (
            ('arit',('+','-')),('n',NUMERICAS[2:]),('l',LOGICAS),('comprimento',('comprimento',)),('indice',('indice',)))}
        if not all(subsets.values()):raise ValueError('Faltam operações no treino')
        arrays={}
        for k,rs in subsets.items():
            y=np.asarray([int(r['resultado']) for r in rs])
            if k in ('n','arit'):x=np.asarray([features_num(r['op'],r['a'],r['b']) for r in rs])
            elif k=='l':x=np.asarray([features_log(r['op'],r['a'],r['b']) for r in rs])
            elif k=='comprimento':x=np.asarray([estrutura(r['a'])+[1.] for r in rs])
            else:
                pares=[vetor_indice(r['a'],r['b']) for r in rs];x=np.asarray([a for a,b in pares]);q=np.asarray([b for a,b in pares]);arrays['q']=q
            arrays[k]=(x,y)
        rng=np.random.default_rng(semente);m={k:np.zeros_like(p) for k,p in self.parametros.items()};v={k:np.zeros_like(p) for k,p in self.parametros.items()};historico=[]
        for passo in range(1,passos+1):
            gs={};losses={}
            for k,(x,y) in [(k,z) for k,z in arrays.items() if k!='q']:
                ids=rng.integers(len(y),size=lote);xx=x[ids];yy=y[ids]
                if k in ('n','l'):
                    pesos=None
                    if k=='n':
                        pesos=np.zeros(lote)
                        # Cada operador/classe tem peso equilibrado usando apenas este lote de treino.
                        for op in range(2,len(NUMERICAS)):
                            for label in (0,1):
                                mask=(xx[:,op]==1)&(yy==label);pesos[mask]=1/max(1,mask.sum())
                        pesos/=max(pesos.sum(),1e-12)
                    loss,g=self.loss_mlp(xx,yy,k,pesos);gs.update(g)
                elif k=='arit':
                    loss,g=self.loss_linear(self.arit_features(xx),yy,k);gs.update(g)
                elif k=='comprimento':
                    loss,g=self.loss_linear(xx,yy,k);gs.update(g)
                else:
                    loss,g=self.loss_indice(xx,arrays['q'][ids],yy);gs.update(g)
                losses[k]=loss
            for k,g in gs.items():
                m[k]=.9*m[k]+.1*g;v[k]=.999*v[k]+.001*g*g
                self.parametros[k]-=.003*(m[k]/(1-.9**passo))/(np.sqrt(v[k]/(1-.999**passo))+1e-8)
            if passo==1 or passo%1000==0 or passo==passos:historico.append(dict(passo=passo,perdas=losses))
        return historico
    def prever(self,op,a,b=0):
        np=self.np;p=self.parametros
        if op=='*':
            # Multiplicação é composição manual de adições previstas, não uma cabeça que recebe a*b.
            if type(a) is not int or type(b) is not int or abs(a)>16 or abs(b)>16:raise ValueError('Multiplicação neural exige operandos em [-16,16]')
            resultado=0
            for _ in range(abs(b)):resultado=self.prever('+',resultado,a)
            return self.prever('-',0,resultado) if b<0 else resultado
        if op in NUMERICAS:
            x=np.asarray([features_num(op,a,b)])
            if op in ('+','-'):
                resultado=int(np.rint((self.arit_features(x)@p['arit'])[0]*16))
                if abs(resultado)>512:raise ValueError('Saída numérica excede domínio')
                return resultado
            if abs(a)>16 or abs(b)>16:raise ValueError('Comparação neural exige [-16,16]')
            return bool(self.forward(x,'n')[1].argmax(1)[0])
        if op in LOGICAS:return bool(self.forward(np.asarray([features_log(op,a,b)]),'l')[1].argmax(1)[0])
        if op=='comprimento':return int(np.rint(np.asarray(estrutura(a)+[1.])@p['comprimento']*16))
        if op=='indice':
            x,q=vetor_indice(a,b);return int(np.rint((np.asarray(q)@p['indice']@np.asarray(x)+np.asarray(q)@p['indice_bias'])*16))
        raise ValueError('Operação não aprendida: '+op)
    def salvar(self,pasta):
        p=Path(pasta);p.mkdir(parents=True,exist_ok=True);self.np.savez(p/'rede.npz',**self.parametros)
        cfg=dict(versao=1,arquitetura='efeitos_estruturados',parametros=sum(x.size for x in self.parametros.values()),pesos_externos=False,operandos_treino=[-16,16],posicoes=16)
        (p/'config.json').write_text(json.dumps(cfg,indent=2)+'\n')
    @classmethod
    def carregar(cls,pasta):
        import numpy as np
        cfg=json.loads((Path(pasta)/'config.json').read_text())
        if cfg.get('versao')!=1 or cfg.get('arquitetura')!='efeitos_estruturados':raise ValueError('Modelo incompatível')
        r=cls()
        with np.load(Path(pasta)/'rede.npz',allow_pickle=False) as d:
            if set(d.files)!=set(r.parametros):raise ValueError('Parâmetros divergentes')
            for k,p in r.parametros.items():
                if d[k].shape!=p.shape or not np.isfinite(d[k]).all():raise ValueError('Pesos inválidos')
                r.parametros[k]=d[k].copy()
        return r
