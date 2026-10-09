"""Avalia somente falas brutas; conserva respostas, valores, fontes e erros."""
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
    ap.add_argument('--modo', choices=['componente', 'motor', 'web'], default='componente')
    ap.add_argument('--exigir-todos', action='store_true')
    a = ap.parse_args()
    if a.saida.exists():
        raise SystemExit('Não sobrescrever resultados anteriores.')
    digest = hashlib.sha256((PASTA/'controle.json').read_bytes()).hexdigest()
    assert digest == json.loads((PASTA/'protocolo.json').read_text())['controle_sha256']
    sys.path.insert(0, str(a.raiz.resolve()))
    from raciocinio_conversa import RaciocinioConversa
    if a.modo != 'componente':
        from crivo import Crivo
        from web_core import responder_web
    casos = json.loads((PASTA/'controle.json').read_text())['sessoes']
    out = dict(controle_sha256=digest, modo=a.modo, sessoes=[],
               motor_sha256=hashlib.sha256((a.raiz/'raciocinio_conversa.py').read_bytes()).hexdigest(),
               limite='Controle de desenvolvimento autoral; não mede geração livre ou raciocínio neural geral.')
    for c in casos:
        bot = RaciocinioConversa() if a.modo == 'componente' else Crivo(usar_linguagem_neural=False, usar_geracao=False)
        hist = []
        sessao = dict(id=c['id'], turnos=[])
        for t in c['turnos']:
            row = dict(esperado=t)
            try:
                if a.modo == 'web':
                    raw = responder_web(dict(message=t['texto'], history=hist), usar_geracao=False)
                    analise = raw.get('conversational_reasoning')
                    resposta = raw['response']
                else:
                    raw = bot.responder(t['texto'])
                    resposta = raw[1] if raw else None
                    if a.modo == 'componente':
                        analise = bot.ultimo
                    else:
                        analise = bot.historico[-1].get('raciocinio_conversa') if raw[0] == 'conversa:raciocinio' else None
                row.update(resposta=resposta, analise=analise, correto=bool(
                    analise and analise['operacao'] == c['operacao']
                    and analise.get('resultado') == t['resultado']
                    and analise['hipotese'] == t['hipotese']))
            except Exception as e:
                row.update(correto=False, erro=type(e).__name__, mensagem=str(e))
            sessao['turnos'].append(row)
            hist.append(t['texto'])
        out['sessoes'].append(sessao)
    rows = [r for s in out['sessoes'] for r in s['turnos']]
    out['resumo'] = dict(n=len(rows), corretos=sum(r['correto'] for r in rows),
                         sessoes_completas=sum(all(r['correto'] for r in s['turnos']) for s in out['sessoes']),
                         erros=sum('erro' in r for r in rows))
    a.saida.parent.mkdir(parents=True, exist_ok=True)
    a.saida.write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(out['resumo']))
    if a.exigir_todos and out['resumo']['corretos'] != len(rows):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
