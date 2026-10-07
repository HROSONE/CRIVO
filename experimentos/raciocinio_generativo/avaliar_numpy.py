"""Avalia pesos exportados sem PyTorch; não seleciona nem altera checkpoints."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from responder_piloto import ExecutorPiloto
from piloto import interpretar, ler_premissa
from diagnosticar import verificar_passos


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pesos', type=Path, required=True)
    ap.add_argument('--casos', type=Path, required=True)
    ap.add_argument('--saida', type=Path, required=True)
    args = ap.parse_args()
    executor = ExecutorPiloto(args.pesos)
    casos = json.loads(args.casos.read_text(encoding='utf-8'))
    linhas = []
    selecao = Counter()
    for c in casos:
        r = executor.responder(c['premissas'], c['objetivo'])
        # Diagnóstico contrafactual: ignorar apenas a redação resolveria?
        # Esta proposta modificada não entra na execução nem em seus acertos.
        try:
            p = interpretar(r['saidas'][0])
            if isinstance(p, str):
                selecao['termino_sem_passo'] += 1
            else:
                regra = ler_premissa(c['premissas'][int(p['regra'][1:])])
                proposta = dict(p, conclusao=regra.consequente.texto())
                ok, motivo = verificar_passos(c['premissas'], [proposta])
                selecao['selecao_valida_ignorando_redacao' if ok else motivo] += 1
        except (ValueError, KeyError, TypeError, IndexError):
            selecao['formato_invalido'] += 1
        correto = r['status'] == c['status']
        precisa = c['status'] in ('sustentado', 'refutado')
        r.update(id=c['id'], esperado=c['status'], correto=correto,
                 contrato=correto and (not precisa or r['prova_completa'] is True),
                 ood_estrutura=c['ood_estrutura'], modo=c['modo'])
        linhas.append(r)
    def resumo(ls):
        return dict(n=len(ls), classificacoes_corretas=sum(r['correto'] for r in ls),
                    contratos_completos=sum(r['contrato'] for r in ls),
                    provas_necessarias=sum(r['esperado'] in ('sustentado','refutado') for r in ls),
                    provas_completas=sum(r['correto'] and r['prova_completa'] is True for r in ls),
                    passos_aceitos=sum(len(r['passos']) for r in ls))
    out = dict(total=resumo(linhas), ood=resumo([r for r in linhas if r['ood_estrutura']]),
               diagnostico_primeira_selecao=dict(selecao),
               casos=linhas, pesos_sha256=hashlib.sha256((args.pesos/'pesos_numpy.npz').read_bytes()).hexdigest())
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(out['total']))


if __name__ == '__main__':
    main()
