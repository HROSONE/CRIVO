"""Registra falas e fontes; não transforma pertinência em aprovação neural."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

PASTA = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raiz', type=Path, required=True)
    ap.add_argument('--saida', type=Path, required=True)
    a = ap.parse_args()
    if a.saida.exists():
        raise SystemExit('Não sobrescrever resultados anteriores.')
    raiz = a.raiz.resolve()
    sys.path.insert(0, str(raiz))
    from crivo import Crivo
    casos = json.loads((PASTA / 'sondas.json').read_text())
    resultado = {'limite': casos['limite'],
                 'sondas_sha256': hashlib.sha256((PASTA / 'sondas.json').read_bytes()).hexdigest(),
                 'codigo_sha256': {n: hashlib.sha256((raiz / n).read_bytes()).hexdigest()
                                   for n in ('dialogo_situado.py', 'dialogo_aberto.py', 'linguagem_conversa.py')},
                 'sessoes': []}
    for c in casos['sessoes']:
        b = Crivo()
        sessao = {'nome': c['nome'], 'turnos': []}
        for texto in c['entradas']:
            ident, resposta = b.responder(texto)
            sessao['turnos'].append({'entrada': texto, 'ident': ident, 'resposta': resposta,
                                     'relatos': list(b.conversacao.relatos),
                                     'quadro': b.dialogo_situado.quadro(b.conversacao),
                                     'politica': b.dialogo_situado.ultimo})
        resultado['sessoes'].append(sessao)
        print(c['nome'], flush=True)
    a.saida.parent.mkdir(parents=True, exist_ok=True)
    a.saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
