"""Funções de treino dos pesos próprios; uso exclusivo no laboratório."""

import hashlib,json

from pathlib import Path

import numpy as np

import torch

from torch import nn



def sha256(caminho):
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()

def carregar(origem, dispositivo):
    from linguagem_profunda import Configuracao, LinguagemProfunda
    from pontuador_frases import BPE
    origem = Path(origem)
    meta = json.loads((origem / 'meta.json').read_text(encoding='utf-8'))
    with np.load(origem / 'pesos_numpy.npz', allow_pickle=False) as z:
        config = json.loads(str(z['meta'].item()))
        chaves = ('vocabulario', 'dimensao', 'camadas', 'cabecas', 'contexto', 'dropout')
        cfg = Configuracao(**{k: config[k] for k in chaves})
        if config['tokenizer_sha256'] != sha256(origem / 'tokenizer.json'):
            raise ValueError('Tokenizador não corresponde aos pesos existentes.')

        class Leitor(nn.Module):
            def __init__(self):
                super().__init__()
                self.base = LinguagemProfunda(cfg)
                self.cabeca = nn.Linear(cfg.dimensao, 1)

            def forward(self, ids, ultimos):
                b = self.base
                x = b.embedding(ids) + b.posicao(torch.arange(ids.shape[1], device=ids.device))
                for bloco in b.blocos:
                    x = bloco(x)
                x = b.norm(x)
                return self.cabeca(x[torch.arange(len(ids), device=ids.device), ultimos]).squeeze(-1)

        modelo = Leitor()
        estado = {}
        for nome, tensor in modelo.state_dict().items():
            chave = nome[5:] if nome.startswith('base.') else nome
            if chave not in z or tuple(z[chave].shape) != tuple(tensor.shape):
                raise ValueError('Peso ausente ou formato incompatível: ' + chave)
            estado[nome] = torch.from_numpy(np.array(z[chave], dtype=np.float32, copy=True))
        modelo.load_state_dict(estado, strict=True)
    return modelo.to(dispositivo), BPE(origem / 'tokenizer.json'), meta

def ajustar_cabeca(xs,cs,indices,w0,b0,l2):
    # CE agrupada com opção fixa nenhuma + BCE; não mistura grupos de fichas.
    w=torch.tensor(w0,requires_grad=True);b=torch.tensor(b0,requires_grad=True)
    opt=torch.optim.LBFGS([w,b],lr=.5,max_iter=80,line_search_fn='strong_wolfe')
    x=torch.cat([xs[i] for i in indices]);ys=[];ranges=[];start=0
    for i in indices:
        n=len(xs[i]);a=cs[i]['fato'];y=torch.zeros(n)
        if a is not None:y[a]=1
        ys.append(y);ranges.append((start,start+n,n if a is None else a));start+=n
    y=torch.cat(ys);group_weights=torch.cat([torch.full((len(xs[i]),),1/len(xs[i])) for i in indices])
    init=torch.tensor(w0)
    def closure():
        opt.zero_grad();z=x@w+b
        rank=torch.stack([torch.nn.functional.cross_entropy(torch.cat((z[a:e],z.new_zeros(1)))[None],torch.tensor([target])) for a,e,target in ranges]).mean()
        binary=(torch.nn.functional.binary_cross_entropy_with_logits(z,y,reduction='none')*group_weights).sum()/len(indices)
        loss=rank+.5*binary+l2*((w-init).square().sum()+(b-b0).square())
        loss.backward();return loss
    opt.step(closure)
    return w.detach(),b.detach()

def ajustar_calibrador(x,y,reg):
    x=torch.tensor(x,dtype=torch.float64);y=torch.tensor(y,dtype=torch.float64)
    w=torch.zeros(x.shape[1],dtype=torch.float64,requires_grad=True)
    opt=torch.optim.LBFGS([w],lr=.5,max_iter=80,line_search_fn='strong_wolfe')
    def closure():
        opt.zero_grad();loss=torch.nn.functional.binary_cross_entropy_with_logits(x@w,y)+reg*w[1:].square().sum();loss.backward();return loss
    opt.step(closure);return w.detach().numpy()

def sigmoid(z):return 1/(1+np.exp(-np.clip(z,-30,30)))
