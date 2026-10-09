"""Coleta sessões com histórico autogerado; nunca aprova por coincidência."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
import torch
from linguagem_profunda import carregar, fonte_dialogo, segmentos_dialogo, ESPECIAIS
from curriculo import sha, salvar


def coletar(modelo, casos, saida):
    if saida.exists():
        raise ValueError('Preservar a coleta existente.')
    saida.parent.mkdir(parents=True, exist_ok=True)
    m, tok, _ = carregar(modelo)
    inputs = json.loads(casos.read_text())['casos']
    result = {'modelo_sha256': sha(modelo / 'pesos.pt'), 'casos_sha256': sha(casos),
              'codigo_sha256': sha(__file__), 'temperatura': 0, 'max_tokens': 60,
              'aprovado_para_chat': False, 'sessoes': []}
    for c in inputs:
        hist, turnos = [], []
        for texto in c['turnos']:
            fonte = fonte_dialogo(tok, texto, hist, m.config.contexto)
            seg, atual = segmentos_dialogo(tok, texto, hist)
            usados, mantidos = len(atual), 0
            for s in reversed(seg):
                if usados + len(s) > m.config.contexto:
                    break
                usados += len(s)
                mantidos += 1
            ids, fim = m.gerar(fonte, tok.token_to_id('<fim>'), max_tokens=60, temperatura=0,
                              proibidos=[tok.token_to_id(t) for t in ESPECIAIS[:-1]])
            resposta = tok.decode(ids)
            turnos.append({'usuario': texto, 'resposta': resposta, 'fim': fim,
                'tokens_entrada': len(fonte), 'entrada_real': tok.decode(fonte, skip_special_tokens=False),
                'turnos_historico_omitidos_inicio': len(hist) - mantidos,
                'tokens_prefixo_perdidos_ate_ultima_predicao': max(0, len(fonte) + max(0, len(ids)-1) - m.config.contexto)})
            hist += [{'papel': 'usuario', 'texto': texto}, {'papel': 'assistente', 'texto': resposta}]
        result['sessoes'].append({'id': c['id'], 'familia': c['familia'], 'rubrica': c['rubrica'], 'turnos': turnos})
        salvar(saida, result)
        print(c['id'], flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--modelo', type=Path, required=True)
    p.add_argument('--casos', type=Path, default=HERE / 'sessoes.json')
    p.add_argument('--saida', type=Path, required=True)
    a = p.parse_args()
    torch.set_num_threads(1)
    coletar(a.modelo, a.casos, a.saida)
