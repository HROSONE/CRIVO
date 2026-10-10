"""Avaliação diagnóstica do checkpoint isolado; não é integração nem aprovação."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parent.parent
sys.path.insert(0, str(ROOT))
from dialogo_seq2seq import DialogoSeq2Seq
from preparar import condicionar

spec = importlib.util.spec_from_file_location('juiz_roteamento', H.parent / 'roteamento_natural_20261009/avaliar.py')
juiz = importlib.util.module_from_spec(spec)
spec.loader.exec_module(juiz)


def ler_modelo(path):
    path = Path(path)
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def baseline_site():
    dataset = json.loads((H / 'casos_congelados.json').read_text())
    raw = json.loads((H / 'evidencias/site_125.json').read_text())
    respostas = {r['caso']: r['resposta'] for r in raw['resultados']}
    respostas['pos125-so-isso'] = json.loads((H / 'evidencias/so_isso_site.json').read_text())['resposta']
    respostas['pos125-definicao'] = json.loads((H / 'evidencias/definicao_comparacao_site.json').read_text())['resultados'][0]['resposta']
    rows = [juiz.pontuar(c, respostas[c['id']]) for c in dataset['casos']]
    return {'base': dataset['base'], 'casos_sha256': hashlib.sha256((H / 'casos_congelados.json').read_bytes()).hexdigest(),
            'metodo': 'Respostas HTTP já observadas no commit do #125; nenhuma resposta alvo injetada.',
            'resumo': juiz.resumo(rows), 'resultados': rows}


def entrada_observada(caso, resposta):
    route = resposta.get('natural_routing') or {}
    ato = route.get('ato', '')
    if not ato and resposta.get('id', '').startswith('social:'):
        ato = 'capacidades'
    fatos = '; '.join(route.get('referentes', []))
    if route.get('personagem'):
        fatos = 'personagem: ' + route['personagem']
    historico = [{'papel': 'usuario', 'texto': t} for t in caso['entrada']['anteriores']]
    return condicionar(caso['entrada']['texto'], historico, fatos, ato)


def pontuar_texto(caso, gerada, entrada):
    texto = gerada['texto']
    esperado = caso['esperado']
    faltam = [t for t in esperado['conteudo_minimo'] if not juiz.contem(texto, t)]
    refs = [t for t in esperado['referentes'] if not juiz.contem(texto, t)]
    proibidos = [t for t in esperado['desvios_proibidos'] if juiz.contem(texto, t)]
    frases = [x for x in re.split(r'[.!?]+', texto) if x.strip()]
    recuo = bool(re.search(r'não consegui|pode esclarecer|qual texto|não posso escrever', texto, re.I))
    narrativa = True
    if caso['id'] in ('real-19', 'real-20'):
        narrativa = len(frases) >= (5 if caso['id'] == 'real-19' else 3) and not recuo
    fonte = ' '.join([entrada['mensagem']] + [h['texto'] for h in entrada['historico']])
    numeros_novos = sorted(set(re.findall(r'\b\d+\b', texto)) - set(re.findall(r'\b\d+\b', fonte)))
    # Os nomes autorais do corpus jamais podem substituir o referente real.
    from preparar import nome
    nomes_novos = [nome(i) for i in range(960) if juiz.contem(texto, nome(i)) and not juiz.contem(fonte, nome(i))]
    valida = gerada['completa'] and not (faltam or refs or proibidos or numeros_novos or nomes_novos) and narrativa
    return {'caso': caso['id'], 'conteudo_minimo_atendido': bool(valida), 'completa': gerada['completa'],
            'faltam': faltam, 'referentes_ausentes': refs, 'desvios': proibidos,
            'numeros_inventados': numeros_novos, 'nomes_inventados': nomes_novos,
            'historia_entregue': narrativa if caso['id'] in ('real-19', 'real-20') else None,
            'frases': len(frases), 'entrada_modelo': entrada, 'gerada': gerada}


def avaliar(modelo_path, saida):
    baseline = baseline_site()
    respostas = {r['caso']: r['resposta'] for r in baseline['resultados']}
    dataset = json.loads((H / 'casos_congelados.json').read_text())
    modelo = DialogoSeq2Seq(ler_modelo(modelo_path))
    out = {'checkpoint': str(modelo_path), 'checkpoint_sha256': hashlib.sha256(Path(modelo_path).read_bytes()).hexdigest(),
           'casos_sha256': baseline['casos_sha256'], 'aprovado': False,
           'metodo': 'Geração isolada em 10 casos dialógicos reais; ato/referentes vêm do trace atual, nunca dos rótulos esperados.',
           'limite': 'Diagnóstico de conteúdo, término e preservação. Não mede roteamento integrado nem 10 conversas manuais; revisão de naturalidade ainda necessária.',
           'resultados': []}
    for caso in dataset['casos']:
        if 'dialogo_historia_capacidades' not in caso['grupos']:
            continue
        entrada = entrada_observada(caso, respostas[caso['id']])
        gerada = modelo.gerar(**entrada, max_tokens=96)
        row = pontuar_texto(caso, gerada, entrada)
        out['resultados'].append(row)
        Path(saida).write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
        print(caso['id'], 'PASS' if row['conteudo_minimo_atendido'] else 'FAIL', gerada['texto'], flush=True)
    rows = out['resultados']
    out['resumo'] = {'total': len(rows), 'conteudo_minimo_atendido': sum(r['conteudo_minimo_atendido'] for r in rows),
                     'completas': sum(r['completa'] for r in rows),
                     'casos_com_referentes_ausentes': sum(bool(r['referentes_ausentes']) for r in rows),
                     'casos_com_inventados': sum(bool(r['nomes_inventados'] or r['numeros_inventados']) for r in rows),
                     'historias_entregues': sum(r['historia_entregue'] is True for r in rows)}
    Path(saida).write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(out['resumo'], ensure_ascii=False), flush=True)
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--modelo', default=str(ROOT / 'rede_dialogo_seq2seq.json.gz'))
    parser.add_argument('--saida', required=True)
    args = parser.parse_args()
    avaliar(args.modelo, args.saida)
