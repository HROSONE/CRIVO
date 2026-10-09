"""Avalia respostas reais; os critérios nunca são enviados ao CRIVO."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))
from composicao_textual import normalizar
from crivo import Crivo


def avaliar():
    casos_bytes = (HERE / 'sessoes.json').read_bytes()
    protocolo = json.loads((HERE / 'protocolo.json').read_text())
    if hashlib.sha256(casos_bytes).hexdigest() != protocolo['sha256_sessoes']:
        raise ValueError('O conjunto congelado mudou')
    resultados = []
    for caso in json.loads(casos_bytes):
        bot = Crivo(**protocolo['configuracao'])
        turnos = []
        for turno in caso['turnos']:
            ident, resposta = bot.responder(turno['texto'])
            n = normalizar(resposta)
            erros = ['ausente: ' + v for v in turno['presentes'] if normalizar(v) not in n]
            erros += ['indevido: ' + v for v in turno['ausentes'] if normalizar(v) in n]
            if turno['algum'] and not any(normalizar(v) in n for v in turno['algum']):
                erros.append('não esclareceu desconhecimento/ambiguidade')
            turnos.append(dict(entrada=turno['texto'], id=ident, resposta=resposta, erros=erros))
        memoria = getattr(bot, 'memoria_sessao', None)
        resultados.append(dict(id=caso['id'], titulo=caso['titulo'],
                               adequada=not any(t['erros'] for t in turnos), turnos=turnos,
                               estado=memoria.exportar() if memoria else None))
    return dict(commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                               universal_newlines=True).strip(),
                sha256_sessoes=protocolo['sha256_sessoes'],
                configuracao=protocolo['configuracao'],
                adequadas=sum(r['adequada'] for r in resultados), total=len(resultados),
                sessoes=resultados)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--saida', required=True)
    parser.add_argument('--exigir-meta', action='store_true')
    args = parser.parse_args()
    resultado = avaliar()
    Path(args.saida).write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + '\n')
    print('{adequadas}/{total} sessões adequadas'.format(**resultado), flush=True)
    if args.exigir_meta and resultado['adequadas'] < 12:
        raise SystemExit(1)
