"""Geração causal dos pesos próprios sem PyTorch no servidor.

Mesmo BPE e atenção do pontuador, agora em decodificação token a token com
cache K/V. Não contém frases de resposta nem consulta tabelas de diálogo.
Disponibilizar este runtime não é aprovar a qualidade de um checkpoint.
"""
from functools import lru_cache
import hashlib
import math
from pathlib import Path

from pontuador_frases import Pontuador, _erf


class GeradorNumpy:
    def __init__(self,pasta):
        self.modelo=Pontuador(pasta)
        p=self.modelo
        if not p.disponivel:raise ValueError(p.motivo)
        if hashlib.sha256((Path(pasta)/'tokenizer.json').read_bytes()).hexdigest()!=p.meta['tokenizer_sha256']:
            raise ValueError('Tokenizador difere do checkpoint próprio')
        self.inverso={v:k for k,v in p.bpe.vocab.items()}
        self.bytes_inversos={v:k for k,v in p.bpe.bytes.items()}

    def fonte(self,mensagem,historico):
        p=self.modelo;b=p.bpe;tokens=b.especiais
        atual=[tokens['<usuario>']]+b.codificar(mensagem)+[tokens['<fim>'],tokens['<assistente>']]
        if len(atual)>p.contexto:raise ValueError('Mensagem atual excede contexto; não será cortada silenciosamente')
        fonte=list(atual)
        segmentos=[]
        for h in historico:
            if h['papel'] in ('usuario','assistente'):
                segmentos.append([tokens['<'+h['papel']+'>']]+b.codificar(h['texto'])+[tokens['<fim>']])
        for s in reversed(segmentos):
            if len(s)+len(fonte)>p.contexto:break
            fonte=s+fonte
        return fonte

    def decodificar(self,ids):
        texto=''.join(self.inverso[i] for i in ids)
        return bytes(self.bytes_inversos[c] for c in texto).decode('utf-8',errors='replace')

    def responder(self,mensagem,historico=(),max_tokens=160,temperatura=0.,semente=42):
        np=self.modelo.np
        cache=CacheNumpy(self.modelo,self.fonte(mensagem,historico))
        rng=np.random.default_rng(semente);saida=[];fim=False
        especiais=self.modelo.bpe.especiais
        proibidos=[especiais[t] for t in ('<pad>','<documento>','<usuario>','<assistente>')]
        for _ in range(max_tokens):
            logits=cache.logits.copy();logits[proibidos]=-np.inf
            if temperatura==0:token=int(logits.argmax())
            else:
                logits/=temperatura
                limiar=np.partition(logits,-40)[-40];logits[logits<limiar]=-np.inf
                prob=np.exp(logits-logits.max()).astype(np.float64);prob/=prob.sum()
                token=int(rng.choice(len(prob),p=prob))
            if token==especiais['<fim>']:fim=True;break
            saida.append(token);cache.avancar(token)
        return dict(texto=self.decodificar(saida),completa=fim,tokens=len(saida),
            passo=self.modelo.meta['passo'],modelo='transformer_causal_do_zero',runtime='numpy',
            temperatura=temperatura)


class CacheNumpy:
    def __init__(self,modelo,ids):
        self.modelo=modelo;self.ids=list(ids);self.chaves=[];self.valores=[]
        self.logits=self._calcular(self.ids,True)

    def _calcular(self,ids,prefixo):
        m=self.modelo;np=m.np;p=m.p
        inicio=0 if prefixo else len(self.ids)-1
        x=p['embedding.weight'][ids]+p['posicao.weight'][inicio:inicio+len(ids)]
        h=m.cabecas;d=x.shape[-1]//h;t=len(ids)
        for c in range(m.camadas):
            b='blocos.%d.'%c
            q,k,v=np.split(m._norm(x,b+'norm1')@p[b+'qkv.weight'].T,3,axis=-1)
            q,k,v=[a.reshape(t,h,d).transpose(1,0,2) for a in (q,k,v)]
            if prefixo:self.chaves.append(k);self.valores.append(v)
            else:
                k=np.concatenate((self.chaves[c],k),axis=1)
                v=np.concatenate((self.valores[c],v),axis=1)
                self.chaves[c]=k;self.valores[c]=v
            s=q@k.transpose(0,2,1)/math.sqrt(d)
            if prefixo:s+=np.triu(np.full((t,t),-np.inf,dtype=np.float32),1)
            a=np.exp(s-s.max(-1,keepdims=True));a/=a.sum(-1,keepdims=True)
            x=x+(a@v).transpose(1,0,2).reshape(t,h*d)@p[b+'projecao.weight'].T
            f=m._norm(x,b+'norm2')@p[b+'mlp.0.weight'].T+p[b+'mlp.0.bias']
            f=.5*f*(1+_erf(f/math.sqrt(2.),np))
            x=x+f@p[b+'mlp.2.weight'].T+p[b+'mlp.2.bias']
        return m._norm(x[-1:], 'norm')[0]@p['embedding.weight'].T

    def avancar(self,token):
        self.ids.append(token)
        if len(self.ids)>self.modelo.contexto:
            self.ids=self.ids[-self.modelo.contexto:];self.chaves=[];self.valores=[]
            self.logits=self._calcular(self.ids,True)
        else:self.logits=self._calcular([token],False)
        return self.logits


@lru_cache(maxsize=2)
def _carregar(pasta,assinatura_pesos,assinatura_tokenizer):
    return GeradorNumpy(pasta)


def carregar(pasta):
    pasta=Path(pasta).resolve()
    arquivos=[pasta/'pesos_numpy.npz',pasta/'tokenizer.json']
    assinaturas=[(p.stat().st_mtime_ns,p.stat().st_size) for p in arquivos]
    return _carregar(str(pasta),*assinaturas)
