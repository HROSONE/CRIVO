"""Sondas autorais: separa restrições, inferência simbólica e saída neural.

Não importa conjuntos congelados, não treina e não altera o caminho do chat.
Uso: OPENBLAS_NUM_THREADS=1 python experimentos/raciocinio_generativo/diagnosticar.py
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

from geracao_ancorada import motivo_da_guarda, preserva_evidencia
from raciocinio_ativo import SistemaPremissas, ler_literal, ler_premissa


SONDAS = [
    dict(id='copia', fatos=['A luz acende quando o sensor responde.'],
         pergunta='O que acontece quando o sensor responde?',
         candidato='A luz acende quando o sensor responde.', candidato_valido=True),
    dict(id='reordenacao', fatos=['A luz acende quando o sensor responde.'],
         pergunta='O que acontece quando o sensor responde?',
         candidato='Quando o sensor responde, a luz acende.', candidato_valido=True),
    dict(id='conclusao_dois_passos', fatos=['O sensor responde.',
         'Se o sensor responde, então o painel liga.', 'Se o painel liga, então a luz acende.'],
         pergunta='O que podemos concluir?', candidato='A luz acende.', candidato_valido=True),
    dict(id='resumo_seletivo', fatos=['O sensor responde. O painel liga. A luz acende.'],
         pergunta='Resuma o estado da luz.', candidato='A luz acende.', candidato_valido=True),
    dict(id='inversao_invalida', fatos=['Se o sensor responde, então o painel liga.'],
         pergunta='Qual é a condição?', candidato='Se o painel liga, então o sensor responde.',
         candidato_valido=False),
    dict(id='negacao_invalida', fatos=['O painel não liga.'],
         pergunta='Qual é o estado do painel?', candidato='O painel liga.', candidato_valido=False),
]


def assinatura(literal):
    return literal.nome, literal.negativo


def verificar_passos(premissas, passos):
    """Verificador experimental de modus ponens para regras com conjunção.

    Cada passo cita uma regra e fatos/passo anteriores. Sem busca nem modelo;
    não confunde uma conclusão válida globalmente com a validade deste passo.
    IDs p0... são premissas; s0... são passos já aceitos. Não suporta 'ou'.
    """
    sistema = SistemaPremissas(tuple(ler_premissa(p) for p in premissas))
    if not sistema.mundos:
        return False, 'premissas_em_conflito'
    regras, fatos = {}, {}
    for i, p in enumerate(sistema.premissas):
        (regras if p.antecedentes else fatos)['p%d' % i] = p if p.antecedentes else p.consequente
    for i, passo in enumerate(passos):
        regra = regras.get(passo.get('regra'))
        if regra is None or regra.operador != 'e':
            return False, 'regra_ausente_ou_nao_suportada'
        refs = passo.get('apoios', [])
        if any(r not in fatos for r in refs):
            return False, 'apoio_ausente_ou_futuro'
        if {assinatura(fatos[r]) for r in refs} != {assinatura(a) for a in regra.antecedentes}:
            return False, 'antecedentes_nao_satisfeitos'
        conclusao = ler_literal(passo['conclusao'])
        if assinatura(conclusao) != assinatura(regra.consequente):
            return False, 'consequente_incorreto'
        fatos['s%d' % i] = conclusao
    return True, 'passos_verificados'


def sondar_verificador():
    premissas = ['O sensor responde', 'Se o sensor responde, então o painel liga',
                 'Se o painel liga, então a luz acende']
    passos = [dict(regra='p1', apoios=['p0'], conclusao='O painel liga'),
              dict(regra='p2', apoios=['s0'], conclusao='A luz acende')]
    controle = SistemaPremissas(tuple(ler_premissa(p) for p in premissas))
    if controle.analisar(ler_literal('A luz acende'))['status'] != 'sustentado':
        raise AssertionError('O controle lógico não confirmou a conclusão da sonda.')
    casos = [
        ('cadeia_valida', premissas, passos, True),
        ('apoio_futuro', premissas, list(reversed(passos)), False),
        ('salto_sem_painel', premissas,
         [dict(regra='p2', apoios=['p0'], conclusao='A luz acende')], False),
        ('conclusao_errada', premissas,
         [dict(regra='p1', apoios=['p0'], conclusao='A luz acende')], False),
        ('conflito', premissas + ['O sensor não responde'], passos, False),
        ('condicao_ausente', ['Se o sensor responde, então o painel liga'],
         [dict(regra='p0', apoios=['p1'], conclusao='O painel liga')], False),
    ]
    saida = []
    for nome, ps, etapas, esperado in casos:
        aceito, motivo = verificar_passos(ps, etapas)
        if aceito != esperado:
            raise AssertionError('Verificador divergiu do contrato: ' + nome)
        saida.append(dict(id=nome, aceito=aceito, motivo=motivo, esperado=esperado))
    return saida


def diagnosticar(neural=False, ablacao=False):
    resultados = []
    modelo = None
    if neural or ablacao:
        from geracao_ancorada import geracao
        modelo = geracao()
        if not modelo.disponivel:
            raise RuntimeError(modelo.motivo)
    for s in SONDAS:
        motivo = motivo_da_guarda(s['candidato'], s['fatos'], s['pergunta'])
        preserva = preserva_evidencia(s['candidato'], s['fatos'])
        linha = dict(s, motivo_guarda=motivo, preserva_evidencia=preserva,
                     candidato_aceito=motivo is None and preserva)
        if modelo:
            trace = {}
            linha['saida_modelo'] = modelo.gerar(s['pergunta'], s['fatos'],
                                                tentativas=1, diagnostico=trace)
            linha['diagnostico_modelo'] = trace
            linha['tokens_prompt'] = len(modelo.prompt(s['pergunta'], s['fatos']))
            if ablacao:
                # Experimento local: remove máscara, prefixo e restrição de
                # pares juntos. Não altera gerar(), cache ou aprovação.
                mascara = modelo.np.zeros(modelo.p['embedding.weight'].shape[0], dtype=modelo.np.float32)
                livre = modelo._decodificar(modelo.prompt(s['pergunta'], s['fatos']), mascara)
                motivo_livre = motivo_da_guarda(livre, s['fatos'], s['pergunta'])
                preserva_livre = preserva_evidencia(livre, s['fatos'])
                linha['ablacao_conjunta'] = dict(saida=livre, motivo_guarda=motivo_livre,
                                               preserva_evidencia=preserva_livre,
                                               aceito_guarda_atual=motivo_livre is None and preserva_livre)
        resultados.append(linha)
    meta = json.loads((RAIZ / 'artefatos/geracao_pt/meta.json').read_text(encoding='utf-8'))
    arquivos = ['artefatos/geracao_pt/meta.json', 'artefatos/geracao_pt/pesos_numpy.npz',
                'artefatos/geracao_pt/tokenizer.json', 'geracao_ancorada.py', 'raciocinio_ativo.py',
                'experimentos/raciocinio_generativo/diagnosticar.py']
    hashes = {a: hashlib.sha256((RAIZ / a).read_bytes()).hexdigest() for a in arquivos}
    return dict(versao=1, base=meta['base'], treino=meta['treino'],
                proveniencia=dict(python=sys.version.split()[0], sha256=hashes),
                parametros=int(sum(a.size for a in modelo.p.values())) if modelo else None,
                sondas=resultados, verificador=sondar_verificador(),
                limites=['Sondas exploratórias de seis casos, não benchmark de capacidade geral.',
                         'Validade dos candidatos linguísticos foi anotada manualmente.',
                         'Aceitação da guarda não é acerto semântico.',
                         'Inferência direta do gerador, não avaliação completa do chat.',
                         'Ablação remove três restrições juntas; não isola seus efeitos individuais.',
                         'Verificador simbólico experimental não é raciocínio aprendido.'])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--neural', action='store_true', help='Executa também os pesos atuais (NumPy).')
    ap.add_argument('--ablacao', action='store_true', help='Testa também decodificação livre, fora do chat.')
    ap.add_argument('--saida', type=Path, required=True)
    args = ap.parse_args()
    relatorio = diagnosticar(neural=args.neural, ablacao=args.ablacao)
    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Sondas:', len(relatorio['sondas']), '| contratos de passos:', len(relatorio['verificador']))
    print('Relatório:', args.saida)


if __name__ == '__main__':
    main()
