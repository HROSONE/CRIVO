"""Diagnóstico reproduzível do contrato de raciocínio, via API e histórico.

Os 15 casos autorais foram congelados antes da implementação. O teste formal
com teorias aleatórias e oráculo independente está em testes_raciocinio_ativo.
Este conjunto não mede compreensão irrestrita de linguagem nem inteligência.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from web_core import responder_web


def avaliar():
    arquivo = RAIZ / 'avaliacoes/raciocinio_ativo_v1/dev.json'
    casos = json.loads(arquivo.read_text(encoding='utf-8'))['casos']
    detalhes = []
    for c in casos:
        resposta = responder_web({'message': c['message'], 'history': c['history']})
        d = resposta.get('reasoning', {})
        correto = (resposta['mechanism'] == 'raciocinio_ativo' and not resposta['has_proof'] and
                   d.get('origem') == 'premissas_da_sessao' and d.get('comprovado_no_mundo') is False)
        correto &= 'status' not in c or d.get('status') == c['status']
        correto &= 'operation' not in c or d.get('operacao') == c['operation']
        correto &= 'assumption' not in c or any(l['texto'] == c['assumption'] for p in d.get('propostas', []) for l in p['suposicoes'])
        detalhes.append({'id': c['id'], 'correto': bool(correto), 'response_id': resposta['id'],
                         'response': resposta['response'], 'reasoning': d})
    fontes = ['raciocinio_ativo.py', 'exploracao_conhecimento.py', 'crivo.py', 'linguagem_conversa.py', 'web_core.py']
    return {'natureza': 'desenvolvimento autoral, contrato explícito e limitado, sem certificação de inteligência geral',
            'casos': len(casos), 'corretos': sum(c['correto'] for c in detalhes),
            'dataset_sha256': hashlib.sha256(arquivo.read_bytes()).hexdigest(),
            'codigo_sha256': {f: hashlib.sha256((RAIZ / f).read_bytes()).hexdigest() for f in fontes},
            'detalhes': detalhes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path)
    args = parser.parse_args()
    resultado = avaliar()
    print(json.dumps({k: v for k, v in resultado.items() if k != 'detalhes'}, ensure_ascii=False))
    if args.saida:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if resultado['corretos'] != resultado['casos']:
        sys.exit(1)
