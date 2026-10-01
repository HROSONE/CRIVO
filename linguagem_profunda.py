"""Transformer causal autoral: arquitetura, vocabulário e pesos aprendidos do zero.

Dependências opcionais em requirements-treino.txt. Não importa nada no motor
normal: este é um laboratório até a avaliação de conversa justificar promoção.
"""
import json
import hashlib
from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F

VERSAO = 1
ESPECIAIS = ['<pad>', '<documento>', '<usuario>', '<assistente>', '<fim>']


@dataclass
class Configuracao:
    vocabulario: int = 4096
    dimensao: int = 192
    camadas: int = 4
    cabecas: int = 6
    contexto: int = 256
    dropout: float = .1

    def __post_init__(self):
        if self.dimensao % self.cabecas or min(self.vocabulario, self.dimensao,
                self.camadas, self.cabecas, self.contexto) <= 0:
            raise ValueError('Configuração de atenção inválida')


class Bloco(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.norm1 = nn.LayerNorm(config.dimensao)
        self.norm2 = nn.LayerNorm(config.dimensao)
        self.qkv = nn.Linear(config.dimensao, 3 * config.dimensao, bias=False)
        self.projecao = nn.Linear(config.dimensao, config.dimensao, bias=False)
        self.mlp = nn.Sequential(nn.Linear(config.dimensao, 4 * config.dimensao),
                                 nn.GELU(), nn.Linear(4 * config.dimensao, config.dimensao),
                                 nn.Dropout(config.dropout))
        self.cabecas = config.cabecas
        self.dropout = config.dropout

    def forward(self, x):
        b, t, d = x.shape
        q, k, v = self.qkv(self.norm1(x)).chunk(3, dim=-1)
        q, k, v = [a.view(b, t, self.cabecas, d // self.cabecas).transpose(1, 2)
                   for a in (q, k, v)]
        a = F.scaled_dot_product_attention(q, k, v, is_causal=True,
                 dropout_p=self.dropout if self.training else 0.)
        x = x + self.projecao(a.transpose(1, 2).contiguous().view(b, t, d))
        return x + self.mlp(self.norm2(x))


class LinguagemProfunda(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.embedding = nn.Embedding(config.vocabulario, config.dimensao)
        self.posicao = nn.Embedding(config.contexto, config.dimensao)
        self.blocos = nn.ModuleList([Bloco(config) for _ in range(config.camadas)])
        self.norm = nn.LayerNorm(config.dimensao)
        self.apply(self._iniciar)

    @staticmethod
    def _iniciar(modulo):
        if isinstance(modulo, (nn.Linear, nn.Embedding)):
            nn.init.normal_(modulo.weight, std=.02)
            if isinstance(modulo, nn.Linear) and modulo.bias is not None:
                nn.init.zeros_(modulo.bias)

    def forward(self, ids, alvos=None):
        if ids.shape[1] > self.config.contexto:
            raise ValueError('Sequência excede contexto')
        x = self.embedding(ids) + self.posicao(torch.arange(ids.shape[1], device=ids.device))
        for bloco in self.blocos:
            x = bloco(x)
        logits = F.linear(self.norm(x), self.embedding.weight)
        perda = None if alvos is None else F.cross_entropy(
            logits.reshape(-1, self.config.vocabulario), alvos.reshape(-1), ignore_index=-100)
        return logits, perda

    @torch.no_grad()
    def gerar(self, ids, fim, max_tokens=100, temperatura=.7, top_k=40, semente=42,
              proibidos=()):
        self.eval()
        rng = torch.Generator(device=self.embedding.weight.device).manual_seed(semente)
        ids = list(ids)
        saida = []
        terminou = False
        for _ in range(max_tokens):
            x = torch.tensor([ids[-self.config.contexto:]], dtype=torch.long,
                             device=self.embedding.weight.device)
            logits = self(x)[0][0, -1].clone()
            for token in proibidos:
                logits[token] = -float('inf')
            if temperatura == 0:
                proximo = int(logits.argmax())
            else:
                logits = logits / temperatura
                if top_k:
                    limiar = logits.topk(min(top_k, logits.numel())).values[-1]
                    logits[logits < limiar] = -float('inf')
                proximo = int(torch.multinomial(logits.softmax(-1), 1, generator=rng))
            if proximo == fim:
                terminou = True
                break
            saida.append(proximo)
            ids.append(proximo)
        return saida, terminou


def codificar_texto(tokenizer, texto):
    """Texto não pode injetar marcadores de papel através de tokens especiais."""
    return tokenizer.encode(texto, add_special_tokens=False).ids


def segmentos_dialogo(tokenizer, mensagem, historico=()):
    segmentos = []
    for turno in historico:
        papel = turno['papel']
        if papel not in ('usuario', 'assistente'):
            continue
        segmentos.append([tokenizer.token_to_id('<' + papel + '>')] +
                         codificar_texto(tokenizer, turno['texto']) +
                         [tokenizer.token_to_id('<fim>')])
    atual = [tokenizer.token_to_id('<usuario>')] + codificar_texto(tokenizer, mensagem)
    atual += [tokenizer.token_to_id('<fim>'), tokenizer.token_to_id('<assistente>')]
    return segmentos, atual


def fonte_dialogo(tokenizer, mensagem, historico, contexto):
    segmentos, atual = segmentos_dialogo(tokenizer, mensagem, historico)
    if len(atual) > contexto:
        raise ValueError('Mensagem atual excede contexto; não será cortada silenciosamente')
    fonte = list(atual)
    for segmento in reversed(segmentos):
        if len(segmento) + len(fonte) > contexto:
            break
        fonte = segmento + fonte
    return fonte


def carregar(diretorio, dispositivo='cpu'):
    from tokenizers import Tokenizer
    diretorio = Path(diretorio)
    # pesos.pt só contém tensores e metadados básicos; nunca usar weights_only=False.
    estado = torch.load(diretorio / 'pesos.pt', map_location=dispositivo, weights_only=True)
    if estado['versao'] != VERSAO:
        raise ValueError('Versão de checkpoint desconhecida')
    digest = hashlib.sha256((diretorio / 'tokenizer.json').read_bytes()).hexdigest()
    if digest != estado['execucao']['tokenizer_sha256']:
        raise ValueError('Tokenizador difere do usado no treino')
    modelo = LinguagemProfunda(Configuracao(**estado['config'])).to(dispositivo)
    modelo.load_state_dict(estado['modelo'])
    tokenizer = Tokenizer.from_file(str(diretorio / 'tokenizer.json'))
    tokenizer.encode_special_tokens = True
    if tokenizer.get_vocab_size() != modelo.config.vocabulario:
        raise ValueError('Vocabulário incompatível')
    modelo.eval()
    return modelo, tokenizer, estado


def conversar(diretorio, mensagem, historico=(), max_tokens=100, temperatura=.7,
              semente=42, dispositivo='cpu'):
    modelo, tokenizer, estado = carregar(diretorio, dispositivo)
    fonte = fonte_dialogo(tokenizer, mensagem, historico, modelo.config.contexto)
    ids, terminou = modelo.gerar(fonte, tokenizer.token_to_id('<fim>'), max_tokens,
                               temperatura=temperatura, semente=semente,
                               proibidos=[tokenizer.token_to_id(t) for t in ESPECIAIS[:-1]])
    return {'texto': tokenizer.decode(ids), 'completa': terminou,
            'tokens': len(ids), 'passo': estado['passo'], 'experimental': True}


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--modelo', required=True)
    p.add_argument('--mensagem')
    p.add_argument('--temperatura', type=float, default=.7)
    p.add_argument('--max-tokens', type=int, default=100)
    args = p.parse_args()
    torch.set_num_threads(3)
    if args.mensagem:
        print(json.dumps(conversar(args.modelo, args.mensagem, max_tokens=args.max_tokens,
                                   temperatura=args.temperatura), ensure_ascii=False))
    else:
        modelo, tokenizer, estado = carregar(args.modelo)
        historico = []
        while True:
            try:
                mensagem = input('Você: ')
            except (EOFError, KeyboardInterrupt):
                break
            if mensagem.strip() == '/sair':
                break
            fonte = fonte_dialogo(tokenizer, mensagem, historico, modelo.config.contexto)
            ids, fim = modelo.gerar(fonte, tokenizer.token_to_id('<fim>'), args.max_tokens,
                                   temperatura=args.temperatura,
                                   proibidos=[tokenizer.token_to_id(t) for t in ESPECIAIS[:-1]])
            texto = tokenizer.decode(ids)
            print('CRIVO experimental:', texto)
            historico.extend([{'papel':'usuario', 'texto':mensagem},
                              {'papel':'assistente', 'texto':texto}])
