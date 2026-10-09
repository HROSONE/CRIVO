"""SFT causal próprio com orçamento exato e persistência do último estado.

Não promove pesos. Não lê sessões/teste durante treino. Replay é conhecido.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import random
import shutil
import sys
import time

import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from curriculo import codificar, sha, salvar
from linguagem_profunda import carregar, fonte_dialogo, segmentos_dialogo, ESPECIAIS


def lote(rows, pad):
    n = max(len(e['x']) for e in rows)
    x = torch.full((len(rows), n), pad, dtype=torch.long)
    y = torch.full_like(x, -100)
    for i, e in enumerate(rows):
        x[i, :len(e['x'])] = torch.tensor(e['x'])
        y[i, :len(e['y'])] = torch.tensor(e['y'])
    return x, y


@torch.no_grad()
def ce(m, rows, pad):
    m.eval()
    total, tokens = 0., 0
    for i in range(0, len(rows), 8):
        x, y = lote(rows[i:i + 8], pad)
        n = int((y != -100).sum())
        total += float(m(x, y)[1]) * n
        tokens += n
    return total / tokens


def ler(p, tok):
    return [codificar(tok, e) for e in json.loads(Path(p).read_text())]


def treino(a):
    torch.set_num_threads(1)
    torch.manual_seed(20261009)
    m, tok, estado = carregar(a.base)
    novo = HERE / 'dados'
    antigo = a.antigo
    manifest = json.loads((novo / 'manifesto.json').read_text())
    for s in ('treino', 'validacao'):
        assert sha(novo / (s + '.json')) == manifest['sha256'][s]
    velhos = ler(antigo / 'treino.json', tok)
    humanos = [e for e in velhos if e['exemplo']['familia'] == 'replay_humano']
    velhos = [e for e in velhos if e['exemplo']['familia'] != 'replay_humano']
    exemplos = velhos if a.braco == 'controle' else ler(novo / 'treino.json', tok)
    dv = ler(novo / 'validacao.json', tok)
    dv_antigo = ler(antigo / 'validacao.json', tok)
    dh = []
    for e in json.loads((ROOT / 'dados/dialogos_humanos.json').read_text())['exemplos']:
        if e['split'] == 'validacao':
            try:
                dh.append(codificar(tok, e))
            except ValueError:
                pass
    assert humanos and exemplos and dv and dh
    out = HERE / a.braco
    out.mkdir(exist_ok=False)
    protocolo = {'base_sha256': sha(a.base / 'pesos.pt'), 'novo_manifesto_sha256': sha(novo / 'manifesto.json'),
        'antigo_treino_sha256': sha(antigo / 'treino.json'), 'antigo_validacao_sha256': sha(antigo / 'validacao.json'),
        'codigo_sha256': sha(__file__), 'seed': 20261009, 'lr': .0001,
        'lote': 8, 'autorais': 6, 'replay_humano': 2, 'tokens_alvo': a.tokens,
        'selecao': 'Menor CE na validação relacional, mesma seleção para ambos. Histórico de referência; não prova sessão gerada.',
        'ultima_atualizacao': 'Somente os alvos excedentes do último lote são mascarados para orçamento exato; entrada inteira preservada.',
        'max_segundos': a.max_segundos, 'braco': a.braco, 'aprovado_para_chat': False,
        'parametros_treinaveis': [n for n, w in m.named_parameters() if w.requires_grad]}
    salvar(out / 'protocolo.json', protocolo)
    pad = tok.token_to_id('<pad>')
    opt = torch.optim.AdamW(m.parameters(), lr=.0001, weight_decay=.01)
    rng = random.Random(70123)
    start = time.monotonic()
    hist = []
    initial = {'passo': 0, 'tokens_alvo': 0, 'ce_relacional': ce(m, dv, pad),
               'ce_antiga': ce(m, dv_antigo, pad), 'ce_humana': ce(m, dh, pad)}
    hist.append(initial)
    melhor = deepcopy(m.state_dict())
    nota = initial['ce_relacional']
    selecionado = 0
    nt, passo, proxima_avaliacao = 0, 0, 30000
    bench = None
    def persistir_atual():
        tmp = out / 'passo_atual.tmp'
        torch.save({'modelo': m.state_dict(), 'otimizador': opt.state_dict(),
                    'rng_python': rng.getstate(), 'rng_torch': torch.get_rng_state(),
                    'passo': passo, 'tokens_alvo': nt, 'protocolo': protocolo,
                    'melhor': melhor, 'nota': nota, 'selecionado': selecionado,
                    'historico': hist}, tmp)
        tmp.replace(out / 'passo_atual.pt')
    while nt < a.tokens and time.monotonic() - start < a.max_segundos:
        m.train()
        rows = [rng.choice(exemplos) for _ in range(6)] + [rng.choice(humanos) for _ in range(2)]
        rng.shuffle(rows)
        x, y = lote(rows, pad)
        restantes = a.tokens - nt
        validos = (y.reshape(-1) != -100).nonzero().flatten()
        if len(validos) > restantes:
            y.reshape(-1)[validos[restantes:]] = -100
        loss = m(x, y)[1]
        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(m.parameters(), 1.)
        opt.step()
        nt += int((y != -100).sum())
        passo += 1
        if passo == 100:
            bench = {'passos': passo, 'tokens_alvo': nt, 'segundos': round(time.monotonic() - start, 2)}
            bench['tokens_alvo_por_segundo'] = round(nt / bench['segundos'], 2)
            salvar(out / 'benchmark_100.json', bench)
            print(json.dumps({'benchmark': bench}), flush=True)
            persistir_atual()
        if nt >= proxima_avaliacao or nt == a.tokens:
            row = {'passo': passo, 'tokens_alvo': nt, 'ce_relacional': ce(m, dv, pad),
                   'ce_antiga': ce(m, dv_antigo, pad), 'ce_humana': ce(m, dh, pad),
                   'perda_ultimo_lote': float(loss.detach()), 'segundos': round(time.monotonic() - start, 2)}
            hist.append(row)
            print(json.dumps(row), flush=True)
            if row['ce_relacional'] < nota:
                nota = row['ce_relacional']
                melhor = deepcopy(m.state_dict())
                selecionado = passo
            proxima_avaliacao += 30000
            salvar(out / 'progresso.json', hist)
    # Teto antes do intervalo não pode apagar os pesos recém-ajustados.
    # Avaliar o último estado permite selecionar de fato o fim parcial.
    if hist[-1]['passo'] != passo:
        row = {'passo': passo, 'tokens_alvo': nt, 'ce_relacional': ce(m, dv, pad),
               'ce_antiga': ce(m, dv_antigo, pad), 'ce_humana': ce(m, dh, pad),
               'segundos': round(time.monotonic() - start, 2), 'parada_pelo_teto': True}
        hist.append(row)
        if row['ce_relacional'] < nota:
            nota, melhor, selecionado = row['ce_relacional'], deepcopy(m.state_dict()), passo
        salvar(out / 'progresso.json', hist)
    persistir_atual()
    m.load_state_dict(melhor)
    torch.save({**estado, 'modelo': m.state_dict(), 'passo': selecionado,
                'experimental': True, 'aprovado_para_chat': False, 'ajuste_relacional': protocolo}, out / 'pesos.pt')
    shutil.copyfile(a.base / 'tokenizer.json', out / 'tokenizer.json')
    salvar(out / 'relatorio.json', {'passos': passo, 'tokens_alvo': nt, 'passo_escolhido': selecionado,
        'historico': hist, 'segundos': round(time.monotonic() - start, 2), 'orcamento_completo': nt == a.tokens,
        'pesos_sha256': sha(out / 'pesos.pt'), 'benchmark': bench, 'aprovado_para_chat': False,
        'sessoes_lidas_no_treino': False, 'modelo_base_preservado': sha(a.base / 'pesos.pt') == protocolo['base_sha256'],
        'ultimo_estado_persistido': True, 'ultimo_estado_sha256': sha(out / 'passo_atual.pt')})


def avaliar(a):
    torch.set_num_threads(1)
    proto = json.loads((HERE / 'protocolo.json').read_text())
    assert sha(HERE / 'sessoes.json') == proto['sessoes_sha256']
    casos = json.loads((HERE / 'sessoes.json').read_text())['casos']
    out = HERE / 'avaliacao'
    out.mkdir(exist_ok=False)
    for nome, path in [('base', a.base), ('controle', HERE / 'controle'), ('relacional', HERE / 'relacional')]:
        m, tok, _ = carregar(path)
        results = []
        for c in casos:
            hist = []
            turnos = []
            for texto in c['turnos']:
                fonte = fonte_dialogo(tok, texto, hist, 256)
                seg, atual = segmentos_dialogo(tok, texto, hist)
                usados, mantidos = len(atual), 0
                for s in reversed(seg):
                    if usados + len(s) > 256:
                        break
                    usados += len(s)
                    mantidos += 1
                ids, fim = m.gerar(fonte, tok.token_to_id('<fim>'), max_tokens=60, temperatura=0,
                                  proibidos=[tok.token_to_id(t) for t in ESPECIAIS[:-1]])
                resposta = tok.decode(ids)
                turnos.append({'usuario': texto, 'resposta': resposta, 'fim': fim,
                    'tokens_entrada': len(fonte), 'entrada_real': tok.decode(fonte, skip_special_tokens=False),
                    'turnos_historico_omitidos_inicio': len(hist) - mantidos,
                    'tokens_prefixo_perdidos_ate_ultima_predicao': max(0, len(fonte) + max(0, len(ids)-1) - 256)})
                hist += [{'papel': 'usuario', 'texto': texto}, {'papel': 'assistente', 'texto': resposta}]
            results.append({'id': c['id'], 'familia': c['familia'], 'rubrica': c['rubrica'], 'turnos': turnos})
            salvar(out / (nome + '.json'), results)
            print(nome, c['id'], flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('acao', choices=['treino', 'avaliar'])
    p.add_argument('--braco', choices=['controle', 'relacional'])
    p.add_argument('--base', type=Path, default=ROOT / 'artefatos/linguagem_profunda')
    p.add_argument('--antigo', type=Path, default=Path('/workspace/experimentos/crivo-geracao-dialogo-20261008/dados'))
    p.add_argument('--tokens', type=int, default=180000)
    p.add_argument('--max-segundos', type=int, default=1800)
    a = p.parse_args()
    if a.acao == 'treino':
        if not a.braco:
            p.error('--braco é obrigatório no treino')
        treino(a)
    else:
        avaliar(a)
