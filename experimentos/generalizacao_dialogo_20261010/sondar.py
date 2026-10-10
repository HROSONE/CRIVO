"""Executa sondas congeladas e preserva respostas e traces completos."""
import argparse
import copy
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parent.parent))

def executar(modo, saida, candidato=None, historico_max=10):
    assert hashlib.sha256((H / 'sondas.json').read_bytes()).hexdigest() == (H / 'SHA256').read_text().split()[0]
    if candidato:
        if modo == 'site':
            raise ValueError('O site usa apenas pesos aprovados; candidato é local.')
        try:
            from conversa_dialogo import CORPUS_V4_SHA256
        except ImportError as exc:
            raise RuntimeError('Aplique piloto_integracao.patch num checkout isolado antes de avaliar o candidato.') from exc
    if historico_max < 1 or historico_max > 10:
        raise ValueError('O contrato HTTP público aceita no máximo dez mensagens anteriores.')
    url = 'https://crivo-mauve.vercel.app/api/chat'
    def health():
        with urllib.request.urlopen(url, timeout=90) as r:
            return json.load(r)
    out = {'modo': modo, 'historico_max':historico_max, 'sessoes': [], 'health_antes': health() if modo == 'site' else None}
    for sessao in json.loads((H / 'sondas.json').read_text())['sessoes']:
        anteriores, rows = [], []
        out['sessoes'].append({'id':sessao['id'],'resultados':rows})
        if modo == 'motor':
            from crivo import Crivo
            from ecossistema import mecanismo_do_turno
            bot = Crivo(checkpoint_dialogo_candidato=candidato)
        for texto in sessao['turnos']:
            if modo == 'motor':
                ident, resposta = bot.responder(texto)
                r = dict(id=ident, response=resposta, mechanism=mecanismo_do_turno(bot,texto,ident), natural_routing=copy.deepcopy(bot.ultima_rota_natural), dialogue_generation=copy.deepcopy(bot.dialogo_conversa.trace))
            else:
                req = urllib.request.Request(url, data=json.dumps({'message':texto,'history':anteriores[-historico_max:]}).encode(), headers={'Content-Type':'application/json'}, method='POST')
                with urllib.request.urlopen(req, timeout=90) as resp:
                    r = json.load(resp)
            rows.append({'usuario':texto, 'resposta':r})
            Path(saida).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
            anteriores.append(texto)
            print(sessao['id'], texto, '\n ', r['response'], flush=True)
        Path(saida).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    if modo == 'site':
        out['health_depois'] = health()
    Path(saida).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--modo', choices=['site','motor'], required=True);p.add_argument('--saida',required=True);p.add_argument('--candidato');p.add_argument('--historico-max',type=int,default=10)
    a=p.parse_args();executar(a.modo,a.saida,a.candidato,a.historico_max)
