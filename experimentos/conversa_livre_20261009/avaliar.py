"""Conversa aberta com valores atuais, sem enviar critérios ao motor."""
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


def avaliar(modo):
    bruto = (HERE / 'sessoes.json').read_bytes()
    protocolo = json.loads((HERE / 'protocolo.json').read_text())
    if hashlib.sha256(bruto).hexdigest() != protocolo['sha256_sessoes']:
        raise ValueError('O conjunto congelado mudou')
    resultados = []
    for caso in json.loads(bruto):
        bot = Crivo() if modo == 'motor' else None
        history, turnos = [], []
        for t in caso['turnos']:
            if bot:
                ident, resposta = bot.responder(t['texto'])
                geracao = bot.ultima_geracao
            else:
                from web_core import responder_web
                r = responder_web(dict(history=history, message=t['texto']))
                ident, resposta, geracao = r['id'], r['response'], r['generation']
            n = normalizar(resposta)
            erros = ['ausente: ' + ' / '.join(g) for g in t['grupos']
                     if not any(normalizar(v) in n for v in g)]
            erros += ['indevido: ' + v for v in t['proibir'] if normalizar(v) in n]
            if t['esclarecer'] and geracao.get('usada') and not any(
                    normalizar(v) in n for v in ('quem', 'qual', 'não sei', 'não informou')):
                erros.append('gerou sem esclarecer referente/informação ausente')
            turnos.append(dict(entrada=t['texto'], id=ident, resposta=resposta,
                               geracao=geracao, avaliado=bool(t['grupos'] or t['proibir']), erros=erros))
            history.append(t['texto'])
        resultados.append(dict(id=caso['id'], titulo=caso['titulo'],
                               adequada=not any(t['erros'] for t in turnos), turnos=turnos))
        print('Sessão', caso['id'], 'adequada:', resultados[-1]['adequada'], flush=True)
    avaliados = [t for s in resultados for t in s['turnos'] if t['avaliado']]
    return dict(commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                               universal_newlines=True).strip(),
                modo=modo, sha256_sessoes=protocolo['sha256_sessoes'],
                adequadas=sum(s['adequada'] for s in resultados), total=len(resultados),
                turnos_adequados=sum(not t['erros'] for t in avaliados), turnos_avaliados=len(avaliados),
                respostas_neurais=sum(t['geracao'].get('usada', False) for t in avaliados),
                fontes_sha256={n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest()
                               for n in ('crivo.py', 'memoria_sessao.py', 'realizacao_memoria.py',
                                         'geracao_conversa.py', 'web_core.py')},
                sessoes=resultados, limites=protocolo['limites'])


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--modo', choices=('motor', 'web'), default='motor')
    p.add_argument('--saida', required=True)
    p.add_argument('--exigir-meta', action='store_true')
    a = p.parse_args()
    r = avaliar(a.modo)
    Path(a.saida).write_text(json.dumps(r, ensure_ascii=False, indent=2) + '\n')
    print('{adequadas}/{total} sessões; {turnos_adequados}/{turnos_avaliados} solicitações'.format(**r))
    if a.exigir_meta and r['adequadas'] < 8:
        raise SystemExit(1)
