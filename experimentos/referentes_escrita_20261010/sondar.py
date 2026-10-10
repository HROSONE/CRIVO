"""Executa sondas congeladas e preserva respostas e traces completos."""
import argparse
import copy
import hashlib
import json
import sys
import threading
import urllib.request
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT=H.parent.parent
sys.path.insert(0, str(ROOT))

def executar(modo, saida, candidato=None, historico_max=20, somente_sessoes=None, novas=False, aliases=False):
    arquivo=H/'casos.json'
    sha=H/'SHA256'
    assert hashlib.sha256(arquivo.read_bytes()).hexdigest()==sha.read_text().split()[0]
    if candidato:
        if modo == 'site':
            raise ValueError('O site usa apenas pesos aprovados; candidato é local.')
        try:
            from conversa_dialogo import CORPUS_V5_SHA256
        except ImportError as exc:
            raise RuntimeError('Carregador do experimento de acontecimentos indisponível.') from exc
    if historico_max < 1 or historico_max > 20:
        raise ValueError('O contrato HTTP público aceita no máximo vinte mensagens no piloto anteriores.')
    servidor = None
    url = 'https://crivo-mauve.vercel.app/api/chat'
    if modo == 'http':
        from web_local import criar_servidor
        servidor = criar_servidor(port=0)
        servidor.checkpoint_dialogo_candidato = candidato
        threading.Thread(target=servidor.serve_forever,daemon=True).start()
        url = 'http://127.0.0.1:%s/api/chat' % servidor.server_address[1]
    def health():
        with urllib.request.urlopen(url, timeout=90) as r:
            return json.load(r)
    out = {'modo': modo, 'historico_max':historico_max, 'sessoes': [], 'health_antes': health() if modo == 'site' else None, 'sessoes_selecionadas':somente_sessoes,'entradas_sha256':hashlib.sha256(arquivo.read_bytes()).hexdigest(),'novas':novas,'runtime_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ('orientacao_pratica.py','dialogo_situado.py','conversa_dialogo.py','compreensao_intencao.py','rede_dialogo_conversa.json.gz')}}
    try:
        for sessao in json.loads(arquivo.read_text())['sessoes']:
            if somente_sessoes and sessao['id'] not in somente_sessoes:
                continue
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
    finally:
        if servidor:
            servidor.shutdown()
            servidor.server_close()

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--modo', choices=['site','motor','http'], required=True);p.add_argument('--saida',required=True);p.add_argument('--candidato');p.add_argument('--historico-max',type=int,default=20);p.add_argument('--novas',action='store_true')
    p.add_argument('--aliases',action='store_true');a=p.parse_args();executar(a.modo,a.saida,a.candidato,a.historico_max,novas=a.novas,aliases=a.aliases)
