"""Repete os critérios congelados e mede quem efetivamente escreveu a resposta.

Os critérios de fidelidade continuam no avaliador original. Observamos apenas
o trace do turno final, sem enviar critérios ou respostas esperadas ao motor.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT))


def avaliar(modo):
    caminho = ROOT / 'experimentos/memoria_prospectiva_20261009/avaliar.py'
    spec = importlib.util.spec_from_file_location('avaliador_congelado', caminho)
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    traces = []
    base = original.Crivo

    class Observado(base):
        def responder(self, texto):
            resultado = super().responder(texto)
            traces.append(copy.deepcopy(dict(geracao=self.ultima_geracao,
                                              memoria=self.memoria_sessao.ultimo)))
            return resultado

    import web_core
    responder_web = web_core.responder_web

    def observado_web(payload):
        resultado = responder_web(payload)
        traces.append(copy.deepcopy(dict(geracao=resultado.get('generation'),
                                          memoria=resultado.get('session_memory'))))
        return resultado

    alvo = patch.object(original, 'Crivo', Observado) if modo == 'motor' else patch.object(
        web_core, 'responder_web', observado_web)
    with alvo:
        resultado = original.avaliar(modo)
    turnos = [t for s in resultado['sessoes'] for t in s['turnos']]
    if len(turnos) != len(traces):
        raise AssertionError('Número de traces difere do número de mensagens avaliadas')
    for turno, trace in zip(turnos, traces):
        turno.update(trace)
    elegiveis = [t for t in turnos if (t.get('memoria') or {}).get('acao') == 'consulta'
                 and (t.get('memoria') or {}).get('afirmacoes')]
    usados = [t for t in elegiveis if (t.get('geracao') or {}).get('usada')]
    lidos = [t for t in elegiveis if (t.get('geracao') or {}).get('leu_memoria')]
    motivos = {}
    for t in elegiveis:
        if t not in usados:
            motivo = (t.get('geracao') or {}).get('motivo', 'sem_trace')
            motivos[motivo] = motivos.get(motivo, 0) + 1
    resultado['realizacao'] = dict(consultas_com_fatos=len(elegiveis),
                                   consultas_lidas_pelo_transformer=len(lidos),
                                   respostas_do_transformer=len(usados),
                                   respostas_preservadas_pelo_recuo=len(elegiveis) - len(usados),
                                   motivos_recuo=motivos)
    for nome in ('realizacao_memoria.py', str(HERE.relative_to(ROOT) / 'avaliar.py')):
        resultado['fontes_sha256'][nome] = hashlib.sha256((ROOT / nome).read_bytes()).hexdigest()
    resultado['pesos_sha256'] = hashlib.sha256(
        (ROOT / 'artefatos/geracao_pt/pesos_numpy.npz').read_bytes()).hexdigest()
    resultado['limites'] = ['Reutiliza desenvolvimento congelado; não é avaliação cega nova.',
                            'Fidelidade com recuo não equivale a sucesso neural em todos os turnos.',
                            'A seleção continua estruturada; prefixo da fonte e guarda literal limitam a realização.']
    return resultado


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--modo', choices=('motor', 'web'), default='motor')
    parser.add_argument('--saida', required=True)
    parser.add_argument('--exigir-meta', action='store_true')
    parser.add_argument('--exigir-realizacao', action='store_true')
    args = parser.parse_args()
    resultado = avaliar(args.modo)
    Path(args.saida).write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + '\n')
    print('{adequadas}/{total} sessões adequadas; {realizacao}'.format(**resultado), flush=True)
    if args.exigir_meta and resultado['adequadas'] < 12:
        raise SystemExit(1)
    if args.exigir_realizacao and not resultado['realizacao']['respostas_do_transformer']:
        raise SystemExit('Nenhuma consulta foi realizada pelo Transformer próprio')
