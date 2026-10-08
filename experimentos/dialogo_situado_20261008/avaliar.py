"""Conversas autorais separadas; avalia apenas respostas reais do chat."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
sys.path.insert(0, str(RAIZ))
from crivo import Crivo
from avaliar_dialogo_real import falhas_turno


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('split', choices=('desenvolvimento','validacao','validacao_temporal_nova','validacao_final_nova'))
    p.add_argument('--saida', type=Path, required=True)
    p.add_argument('--exigir-todos', action='store_true', help='Falhar quando algum contrato não passar.')
    args = p.parse_args()
    if args.saida.exists():
        raise SystemExit('Use saída nova.')
    f = PASTA/(args.split+'.json')
    h = hashlib.sha256(f.read_bytes()).hexdigest()
    assert h == json.loads((PASTA/'manifesto_casos.json').read_text())['arquivos'][f.name]
    inicio = time.monotonic()
    resultados = []
    for c in json.loads(f.read_text()):
        b = Crivo()
        anteriores = []
        turnos = []
        for t in c['turnos']:
            ident, resposta = b.responder(t['pergunta'])
            falhas = falhas_turno(t, ident, resposta, anteriores, b)
            if any(ident.startswith(prefixo) for prefixo in t.get('ids_excluir_prefixo',())):
                falhas.append('rota factual substituída pelo diálogo')
            turnos.append(dict(pergunta=t['pergunta'], id=ident, resposta=resposta,
                               passou=not falhas, falhas=falhas))
            anteriores.append(resposta)
        resultados.append(dict(nome=c['nome'], passou=all(t['passou'] for t in turnos), turnos=turnos))
    ts = [t for c in resultados for t in c['turnos']]
    r = dict(split=args.split, mensagens=len(ts), acertos=sum(t['passou'] for t in ts),
             dialogos=len(resultados), dialogos_completos=sum(c['passou'] for c in resultados),
             casos=resultados, casos_sha256=h, tempo_segundos=round(time.monotonic()-inicio,3),
             limite='Validação autoral de pertinência e contratos. Exige leitura das respostas; não demonstra compreensão geral.')
    r['fontes_codigo_sha256'] = {nome:hashlib.sha256((RAIZ/nome).read_bytes()).hexdigest()
        for nome in ('crivo.py','dialogo_situado.py','linguagem_conversa.py','compreensao_intencao.py')}
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in r.items() if k!='casos'},ensure_ascii=False),flush=True)
    if args.exigir_todos and r['acertos'] != r['mensagens']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
