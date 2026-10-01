"""Decodificação com cache K/V, sem alterar arquitetura, treino ou pesos.

Quando a janela enche, o prefixo é recalculado: as posições aprendidas voltam
a zero no modelo de referência, portanto não basta remover uma chave antiga.
"""
import torch
from torch.nn import functional as F


class CacheCausal:
    def __init__(self, modelo, ids):
        if not ids:
            raise ValueError('Prefixo vazio')
        self.modelo = modelo.eval()
        self.ids = list(ids[-modelo.config.contexto:])
        self.chaves = []
        self.valores = []
        self.logits = self._calcular(self.ids, prefixo=True)

    @torch.no_grad()
    def _calcular(self, ids, prefixo):
        modelo = self.modelo
        dispositivo = modelo.embedding.weight.device
        x = torch.tensor([ids],dtype=torch.long,device=dispositivo)
        inicio = 0 if prefixo else len(self.ids) - 1
        x = modelo.embedding(x) + modelo.posicao(torch.arange(inicio,inicio + len(ids),device=dispositivo))
        for i,bloco in enumerate(modelo.blocos):
            b,t,d = x.shape
            q,k,v = bloco.qkv(bloco.norm1(x)).chunk(3,dim=-1)
            q,k,v = [a.view(b,t,bloco.cabecas,d//bloco.cabecas).transpose(1,2) for a in (q,k,v)]
            if prefixo:
                self.chaves.append(k);self.valores.append(v)
            else:
                k = torch.cat((self.chaves[i],k),dim=2)
                v = torch.cat((self.valores[i],v),dim=2)
                self.chaves[i] = k;self.valores[i] = v
            # Na atualização de um token, todas as chaves são passadas/atuais.
            # is_causal=True com q=1 mascararia indevidamente as outras chaves.
            a = F.scaled_dot_product_attention(q,k,v,is_causal=prefixo,dropout_p=0.)
            x = x + bloco.projecao(a.transpose(1,2).contiguous().view(b,t,d))
            x = x + bloco.mlp(bloco.norm2(x))
        return F.linear(modelo.norm(x[:,-1,:]),modelo.embedding.weight)[0]

    def avancar(self, token):
        self.ids.append(token)
        if len(self.ids) > self.modelo.config.contexto:
            self.ids = self.ids[-self.modelo.config.contexto:]
            self.chaves = [];self.valores = []
            self.logits = self._calcular(self.ids,prefixo=True)
        else:
            self.logits = self._calcular([token],prefixo=False)
        return self.logits


@torch.no_grad()
def gerar(modelo,ids,fim,max_tokens=100,temperatura=.7,top_k=40,semente=42,proibidos=()):
    cache = CacheCausal(modelo,ids)
    rng = torch.Generator(device=modelo.embedding.weight.device).manual_seed(semente)
    saida = []
    for passo in range(max_tokens):
        logits = cache.logits.clone()
        for token in proibidos: logits[token] = -float('inf')
        if temperatura == 0:
            proximo = int(logits.argmax())
        else:
            logits = logits / temperatura
            if top_k:
                limiar = logits.topk(min(top_k,logits.numel())).values[-1]
                logits[logits < limiar] = -float('inf')
            proximo = int(torch.multinomial(logits.softmax(-1),1,generator=rng))
        if proximo == fim: return saida,True
        saida.append(proximo)
        if passo + 1 < max_tokens: cache.avancar(proximo)
    return saida,False
