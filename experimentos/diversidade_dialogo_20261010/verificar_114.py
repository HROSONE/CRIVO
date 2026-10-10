"""Gate preservado: 110/114, todos os 79 anteriores, 52 histórias, zero desvios."""
import argparse
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
CASOS = H.parent / 'escrita_acontecimentos_20261010/casos_congelados.json'
SHA = '9f5164f9aefbec71ec9e36aafebd7711cb95c2ab88c31b5b01975b67128645f8'


def verificar(d):
    assert hashlib.sha256(CASOS.read_bytes()).hexdigest() == SHA
    casos = json.loads(CASOS.read_text())['casos']
    rows = d['resultados']
    assert d['casos_sha256'] == SHA and not d['avaliacao_parcial_ids']
    assert [r['caso'] for r in rows] == [c['id'] for c in casos]
    m = dict(casos=sum(r['peca_correta_com_evidencia'] for r in rows), total=len(rows),
             antigos=sum(r['peca_correta_com_evidencia'] for r in rows[:79]),
             historias=sum(r.get('historia_entregue', False) for r in rows),
             trocas_dominio=sum(bool(r['trocas_dominio']) for r in rows),
             referentes_ausentes=sum(bool(r['referentes_ausentes']) for r in rows),
             desvios_proibidos=sum(bool(r['desvios']) for r in rows))
    assert m['total'] == 114 and m['casos'] >= 110 and m['antigos'] == 79 and m['historias'] == 52, m
    assert m['trocas_dominio'] == m['referentes_ausentes'] == m['desvios_proibidos'] == 0, m
    return m


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--arquivo', required=True); a = p.parse_args()
    print(verificar(json.loads(Path(a.arquivo).read_text())))
