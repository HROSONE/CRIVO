"""Casos autorais de desenvolvimento: intenção, contexto e conteúdo da resposta."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from web_core import responder_web


def avaliar():
    arquivo = RAIZ / 'avaliacoes/contato_contextual_v1/dev.json'
    casos = json.loads(arquivo.read_text(encoding='utf-8'))['casos']
    detalhes = []
    for c in casos:
        r = responder_web({'message': c['pergunta'], 'history': c['historico']})
        correto = ('id' not in c or r['id'] == c['id'])
        correto &= r['id'] not in c.get('id_proibido', [])
        correto &= all(t.casefold() in r['response'].casefold() for t in c.get('contem', []))
        correto &= all(t.casefold() not in r['response'].casefold() for t in c.get('nao_contem', []))
        detalhes.append({'nome': c['nome'], 'correto': bool(correto), 'id': r['id'], 'resposta': r['response']})
    return {'natureza': 'desenvolvimento autoral, sem certificação de compreensão geral',
            'casos': len(casos), 'corretos': sum(d['correto'] for d in detalhes),
            'dataset_sha256': hashlib.sha256(arquivo.read_bytes()).hexdigest(), 'detalhes': detalhes}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--saida', type=Path)
    args = parser.parse_args()
    resultado = avaliar()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if args.saida:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    sys.exit(resultado['corretos'] != resultado['casos'])
