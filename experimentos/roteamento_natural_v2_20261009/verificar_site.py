"""Reproduz os mesmos 35 casos no site, verificando o commit publicado."""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
from pathlib import Path
import urllib.request

from avaliar import H, v1

URL = 'https://crivo-mauve.vercel.app/api/chat'


def health():
    with urllib.request.urlopen(URL, timeout=35) as resposta:
        return json.load(resposta)


def consultar(caso):
    payload = {'message': caso['entrada']['texto'], 'history': caso['entrada']['anteriores']}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
    momento = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with urllib.request.urlopen(req, timeout=35) as resposta:
        row = v1.pontuar(caso, json.load(resposta))
        row.update(quando_utc=momento, http_status=resposta.status, pedido=payload)
        return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--commit', required=True)
    parser.add_argument('--saida', required=True)
    args = parser.parse_args()
    arquivo = H / 'casos_congelados.json'
    sha = hashlib.sha256(arquivo.read_bytes()).hexdigest()
    assert sha == (H / 'SHA256').read_text().split()[0]
    dataset = json.loads(arquivo.read_text())
    original = H.parent / 'roteamento_natural_20261009' / 'casos_congelados.json'
    assert hashlib.sha256(original.read_bytes()).hexdigest() == dataset['originais_sha256']
    assert dataset['casos'][:25] == json.loads(original.read_text())['casos']
    antes = health()
    assert antes['build_commit'] == args.commit, 'O site ainda está em outro commit'
    out = {'url': URL, 'codigo_publicado': args.commit, 'casos_sha256': sha,
           'metodo': 'HTTP público; apenas message/history, até dois turnos, sem memory injetada',
           'health_antes': antes, 'resultados': []}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for row in pool.map(consultar, dataset['casos']):
            out['resultados'].append(row)
            Path(args.saida).write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
            print(row['caso'], 'PASS' if row['peca_correta_com_evidencia'] else 'FAIL', flush=True)
    out['health_depois'] = health()
    out['resumo'] = v1.resumo(out['resultados'])
    out['novos'] = v1.resumo([r for r in out['resultados'] if r['caso'].startswith('pos-')])
    Path(args.saida).write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    assert out['health_depois']['build_commit'] == args.commit
    assert out['resumo']['pecas_corretas_com_evidencia'] >= dataset['criterios']['peca_correta_minimo']
    assert out['novos']['pecas_corretas_com_evidencia'] == 10
    assert out['resumo']['desvios'] == out['resumo']['trocas_dominio'] == 0
    assert out['resumo']['casos_com_referentes_ausentes'] == 0
    print(json.dumps(out['resumo'], ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
