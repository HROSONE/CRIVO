"""Baseline pública somente leitura; pesos experimentais não são publicados."""
import json
import sys
import urllib.request
from pathlib import Path

DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(DIR))
from executar import protocolo


def requisicao(dados=None):
    req = urllib.request.Request('https://crivo-mauve.vercel.app/api/chat',
        data=None if dados is None else json.dumps(dados, ensure_ascii=False).encode(),
        headers={'Content-Type': 'application/json', 'User-Agent': 'CRIVO-avaliacao-propria/1.0'})
    with urllib.request.urlopen(req, timeout=90) as resposta:
        return json.load(resposta)


def executar():
    protocolo()
    avaliacao = json.loads((DIR/'avaliacao_congelada.json').read_text())
    resultado = {'saude_antes': requisicao(), 'sessoes': [],
        'limite': 'contrato público recebe somente mensagens anteriores do usuário; não equivale à entrada textual com dois papéis'}
    for sessao in avaliacao['sessoes']:
        historico, turnos = [], []
        for turno in sessao['turnos']:
            resposta = requisicao({'message': turno['mensagem'], 'history': historico})
            turnos.append({'mensagem': turno['mensagem'], 'historico': historico.copy(), 'resposta_http': resposta})
            historico.append(turno['mensagem'])
        resultado['sessoes'].append({'id': sessao['id'], 'turnos': turnos})
        print('Site:', sessao['id'], flush=True)
    pedido = avaliacao['pedido_do_dono']['mensagem']
    resultado['pedido_do_dono'] = {'mensagem': pedido, 'resposta_http': requisicao({'message': pedido, 'history': []})}
    resultado['saude_depois'] = requisicao()
    (DIR/'antes_site.json').write_text(json.dumps(resultado, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    executar()
