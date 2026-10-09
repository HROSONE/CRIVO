"""Diagnóstico direto do gerador maior próprio no formato em que foi treinado.

Não altera nem contorna a guarda do chat: geração crua é armazenada apenas
no laboratório. Estado assistido não avalia extração aprendida.
"""
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
from geracao_ancorada import GeracaoAncorada
from linguagem_profunda import LinguagemProfunda, Configuracao, ESPECIAIS


if __name__ == '__main__':
    torch.set_num_threads(1)
    p = Path(__file__).parent
    output = p / 'ancorado_estado_assistido.json'
    if output.exists():
        raise ValueError('Preservar a coleta existente.')
    casos = json.loads((p / 'casos.json').read_text())['casos']
    g = GeracaoAncorada()
    assert g.disponivel
    modelo = LinguagemProfunda(Configuracao(**g.meta['base']['config']))
    modelo.load_state_dict({k: torch.from_numpy(v.copy()) for k, v in g.p.items()})
    modelo.eval()
    protocolo = {'formato': '<documento> fato ... <usuario> pergunta <assistente>',
                 'condicao': 'estado_assistido', 'temperatura': 0, 'max_tokens': 80,
                 'guarda_chat_alterada': False, 'saida_crua_somente_laboratorio': True,
                 'politica': 'Mesma geração gulosa do causal 2.6M; sem restrição de vocabulário ou penalidades próprias do executor ancorado.',
                 'parametros': sum(w.numel() for w in modelo.parameters()),
                 'config': g.meta['base']['config'],
                 'pesos_numpy_sha256': hashlib.sha256((ROOT / 'artefatos/geracao_pt/pesos_numpy.npz').read_bytes()).hexdigest(),
                 'casos_sha256': hashlib.sha256((p / 'casos.json').read_bytes()).hexdigest(),
                 'limite': 'Outro checkpoint, tokenizer, treino e formato. Não isola efeito de parâmetros. Só avalia resposta com estado manual. Nenhuma promoção.'}
    result = {'protocolo': protocolo, 'entradas': [], 'aprovado_para_chat': False}
    for c in casos:
        fonte = []
        for f in c['estado']:
            fonte += [g.doc] + g.bpe.codificar(f)
        fonte += [g.usu] + g.bpe.codificar(c['pedido']) + [g.ass]
        assert len(fonte) <= modelo.config.contexto
        start = time.monotonic()
        ids, fim = modelo.gerar(fonte, g.fim, max_tokens=80, temperatura=0,
                               proibidos=[g.doc, g.usu, g.ass, g.bpe.especiais['<pad>']])
        # IDs explícitos: jamais depender da ordem do dicionário de especiais.
        assert all(t not in (g.doc, g.usu, g.ass, g.bpe.especiais['<pad>']) for t in ids)
        texto = g.decodificar(ids)
        result['entradas'].append({'caso': c['id'], 'fatos': c['estado'], 'pedido': c['pedido'],
                                  'tokens_entrada': len(fonte), 'entrada_token_ids': fonte,
                                  'resposta': texto, 'fim': fim, 'tokens_saida': len(ids),
                                  'prefixo_perdido_ate_ultima_predicao': max(0, len(fonte) + max(0, len(ids)-1) - 256),
                                  'segundos': round(time.monotonic()-start, 3)})
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
        print(c['id'], flush=True)
