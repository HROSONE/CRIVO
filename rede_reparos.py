"""Rede autoral pequena para ordenar edições; aprende de contratos de treino."""
import json
from pathlib import Path

import numpy as np
from interpretacao_estruturas import ParserEstruturas

TIPOS = ('inserir_incremento', 'remover_statement', 'operador', 'constante',
         'metodo', 'atribuicao', 'expressao')
CONTEXTOS = ('while', 'declarar', 'atribuir_alvo', 'expressao', 'if', 'bin',
             'num', 'metodo', 'var', 'indice', 'propriedade')
TOKENS = ('+', '-', '*', '<', '<=', '>', '>=', '===', '!==', '&&', '||',
          'trim', 'toLowerCase', 'toUpperCase', 'push', 'slice', 'includes')
NOMES = ([f'tipo:{t}' for t in TIPOS] + [f'contexto:{t}' for t in CONTEXTOS] +
         [f'{lado}:{t}' for lado in ('antes', 'depois') for t in TOKENS] +
         ['delta_tamanho', 'profundidade', 'proporcao_falhas', 'erro_orcamento',
          'erro_indice', 'erro_tipo'])


def features(edicao, inicial):
    valores = [float(edicao['tipo'] == t) for t in TIPOS]
    valores += [float(edicao['contexto'] == t) for t in CONTEXTOS]
    for lado in ('antes', 'depois'):
        tokens = ParserEstruturas(edicao[lado]).tokens
        valores += [float(t in tokens) for t in TOKENS]
    erros = ' '.join(r.get('erro', '') for r in inicial)
    valores += [float(np.clip(edicao['tamanho_delta'] / 80, -1, 1)),
                min(len(edicao['caminho_ast']) / 12, 1),
                sum(not r['correto'] for r in inicial) / len(inicial),
                float('Orçamento' in erros), float('Índice' in erros),
                float('exige' in erros or 'booleana' in erros)]
    return np.asarray(valores, dtype=np.float64)


def loss_grad(x, alvo, w, b, v):
    h = np.tanh(x @ w + b)
    z = h @ v
    z -= z.max()
    p = np.exp(z)
    p /= p.sum()
    loss = -float(np.sum(alvo * np.log(np.maximum(p, 1e-300))))
    dz = p - alvo
    dv = h.T @ dz
    dh = (dz[:, None] * v) * (1 - h*h)
    return loss, (x.T @ dh, dh.sum(axis=0), dv)


class RedeReparos:
    def __init__(self, seed=7):
        rng = np.random.default_rng(seed)
        self.w = rng.normal(0, .12, (len(NOMES), 16))
        self.b = np.zeros(16)
        self.v = rng.normal(0, .12, 16)

    @property
    def parametros(self):
        return self.w.size + self.b.size + self.v.size

    def nota(self, edicao, inicial):
        return float(np.tanh(features(edicao, inicial) @ self.w + self.b) @ self.v)

    def treinar(self, grupos, passos=1200, seed=107):
        if not grupos or any(g['split'] != 'treino' for g in grupos):
            raise ValueError('Rede só aceita grupos de treino')
        if type(passos) is not int or not 1 <= passos <= 5000:
            raise ValueError('Orçamento de treino inválido')
        dados = []
        for g in grupos:
            x = np.asarray(g['features'], dtype=np.float64)
            y = np.asarray(g['corretas'], dtype=np.float64)
            if (x.ndim != 2 or x.shape[1] != len(NOMES) or len(x) > 1024 or
                    y.shape != (len(x),) or not np.isfinite(x).all() or
                    not np.isin(y, (0, 1)).all() or not y.sum()):
                raise ValueError('Grupo inválido ou sem correção disponível')
            dados.append((x, y/y.sum()))
        rng = np.random.default_rng(seed)
        parametros = [self.w, self.b, self.v]
        ms = [np.zeros_like(p) for p in parametros]
        vs = [np.zeros_like(p) for p in parametros]
        inicial = float(np.mean([loss_grad(x, y, *parametros)[0] for x, y in dados]))
        for t in range(1, passos+1):
            x, y = dados[int(rng.integers(len(dados)))]
            _, grads = loss_grad(x, y, *parametros)
            for p, m, v, grad in zip(parametros, ms, vs, grads):
                m *= .9
                m += .1 * grad
                v *= .999
                v += .001 * grad*grad
                p -= .01 * (m/(1-.9**t)) / (np.sqrt(v/(1-.999**t)) + 1e-8)
        final = float(np.mean([loss_grad(x, y, *parametros)[0] for x, y in dados]))
        return dict(loss_inicial=inicial, loss_final=final, passos=passos,
                    grupos_treino=len(dados), parametros=self.parametros)

    def salvar(self, pasta):
        p = Path(pasta)
        p.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(p/'rede.npz', w=self.w, b=self.b, v=self.v)
        (p/'config.json').write_text(json.dumps(dict(versao=1, arquitetura='ranking_edicoes_ast',
                                                   features=NOMES, parametros=self.parametros), indent=2)+'\n')

    @classmethod
    def carregar(cls, pasta):
        p = Path(pasta)
        c = json.loads((p/'config.json').read_text())
        if c != dict(versao=1, arquitetura='ranking_edicoes_ast', features=NOMES,
                     parametros=len(NOMES)*16+32):
            raise ValueError('Formato de rede incompatível')
        r = cls()
        with np.load(p/'rede.npz', allow_pickle=False) as d:
            if set(d.files) != {'w', 'b', 'v'}:
                raise ValueError('Chaves de pesos inválidas')
            for nome in ('w', 'b', 'v'):
                a = d[nome]
                if a.shape != getattr(r, nome).shape or a.dtype.kind != 'f' or not np.isfinite(a).all():
                    raise ValueError('Pesos inválidos')
                setattr(r, nome, a.copy())
        return r
