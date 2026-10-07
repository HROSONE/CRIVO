"""Executor NumPy experimental: modelo propõe, verificador veta; sem reparo."""
import argparse
import json
from pathlib import Path

from piloto import STATUS, contexto, executar, assinatura, ler_literal, ler_premissa


def prova_da_resposta(caso, resultado):
    status = resultado.get('status')
    if status not in ('sustentado', 'refutado'):
        return None
    alvo = ler_literal(caso['objetivo'])
    desejado = alvo if status == 'sustentado' else alvo.oposto()
    fatos = [p.consequente for p in map(ler_premissa, caso['premissas']) if not p.antecedentes]
    fatos += [ler_literal(p['conclusao']) for p in resultado['passos']]
    return assinatura(desejado) in {assinatura(f) for f in fatos}


class ExecutorPiloto:
    def __init__(self, pasta):
        from geracao_ancorada import GeracaoAncorada
        # Pesos experimentais explicitamente selecionados pela CLI, nunca o
        # singleton de produção nem sua aprovação. Não promove esse artefato.
        self.modelo = GeracaoAncorada(Path(pasta), exigir_aprovacao=False)
        if not self.modelo.disponivel:
            raise RuntimeError(self.modelo.motivo)
        if self.modelo.meta.get('papel') != 'piloto de passos':
            raise ValueError('Use somente pesos identificados como piloto de passos.')
        self.mascara = self.modelo.np.zeros(len(self.modelo.p['embedding.weight']), dtype=self.modelo.np.float32)
        for id_ in (self.modelo.doc, self.modelo.usu, self.modelo.ass, self.modelo.bpe.especiais['<pad>']):
            self.mascara[id_] = -self.modelo.np.inf

    def gerar(self, texto):
        g = self.modelo
        prompt = [g.doc] + g.bpe.codificar(texto) + [g.ass]
        if len(prompt) + 40 > g.meta['base']['config']['contexto']:
            raise ValueError('Contexto excedido; não truncar premissas.')
        # O executor existente limita a saída a 70 tokens e para em <fim>.
        # Sem máscara lexical da fonte, prefixo copiado ou costura de pares.
        return g._decodificar(prompt, self.mascara)

    def responder(self, premissas, objetivo):
        caso = dict(premissas=premissas, objetivo=objetivo)
        for p in premissas:
            ler_premissa(p)
        ler_literal(objetivo)
        r = executar(caso, self.gerar)
        r['prova_completa'] = prova_da_resposta(caso, r)
        if r['prova_completa'] is False:
            r['status_proposto'] = r['status']
            r['status'] = None
            r['motivo'] = 'conclusao_sem_prova'
        r['modelo_experimental'] = True
        return r


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pesos', type=Path, required=True)
    ap.add_argument('--premissa', action='append', required=True)
    ap.add_argument('--objetivo', required=True)
    args = ap.parse_args()
    r = ExecutorPiloto(args.pesos).responder(args.premissa, args.objetivo)
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
