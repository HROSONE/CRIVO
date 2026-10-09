"""Segundo painel prospectivo autoral, sem ler código/predições do ledger.

Frases inteiramente novas; schema/executor/tokenizer/preparo próprios são as
únicas dependências. Três entidades têm fatos separados. Gold jamais entra
na entrada codificada: usamos primeiro somente turnos e placeholders nulos.
"""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import sys

REPO = Path('/workspace/CRIVO-interpretador-contextual')
CONTEXTUAL = REPO / 'experimentos/interpretador_contextual_20261008'
PREPARO = REPO / 'experimentos/memoria_fontes_20261009'
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(CONTEXTUAL))
sys.path.insert(0, str(PREPARO))
from corpus import Sessao
from modelo import esperado, recuperar
from preparo import codificar
from tokenizers import Tokenizer

SAIDA = Path(__file__).resolve().parent
TOKENIZER = REPO / 'artefatos/linguagem_profunda/tokenizer.json'
SEMENTE = 2026100993
PLANOS = ['Zéfiro', 'Ilhéu', 'Ardósia', 'Fagulha', 'Pórfiro', 'Açucena']
PESSOAS = ['Irma', 'Berenice', 'Osvaldo', 'Raul', 'Úrsula', 'Henrique']
OBJETOS = ['atestado', 'recibo', 'visado', 'cédula', 'protocolo', 'comprovante']
TRAJETORIAS = [
    ['correcao', 'hipotese', 'retorno'],
    ['hipotese', 'consulta', 'retorno'],
    ['hipotese', 'confirmacao', 'retorno'],
    ['correcao', 'hipotese', 'confirmacao', 'retorno'],
    ['hipotese', 'correcao', 'consulta', 'retorno'],
    ['correcao', 'hipotese', 'hipotese', 'retorno', 'consulta'],
    ['hipotese', 'retorno', 'correcao', 'hipotese', 'confirmacao'],
    ['hipotese', 'confirmacao', 'correcao', 'hipotese', 'retorno'],
    ['correcao', 'consulta', 'hipotese', 'confirmacao', 'retorno'],
]
RETORNOS = [
    'Agora encerre a imaginação; os fatos confirmados continuam. ',
    'O que não foi confirmado deve ser descartado. Use a realidade. ',
    'Sem simulações pendentes, use os fatos consolidados. ',
    'Não aplique a suposição; recupere só a situação factual. ',
]
CONFIRMACOES = [
    'Eu conferi: a hipótese corrente ocorreu e virou fato. ',
    'Agora é realidade: todos os dados da última hipótese. ',
    'O cenário hipotético mais recente aconteceu, e ficou confirmado. ',
    'Não há mais suposição: confirmo o último cenário como factual. ',
]
CONSULTAS = [
    'Quanto ao mesmo cenário, mantenha tudo e responda novamente. ',
    'Eu só repito a pergunta; não altero a situação atual. ',
    'Sem atualizar dados, faça outra análise da situação. ',
    'O caso em uso continua igual; mostre a resposta de novo. ',
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def escrever(path, valor):
    path.write_text(json.dumps(valor, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def montar(indice, tentativa=0):
    rng = random.Random(SEMENTE + indice * 104729 + tentativa * 10000019)
    preco = indice % 2 == 0
    rep = (indice // 2) % 4
    seq = TRAJETORIAS[indice // 8]
    s = Sessao(f'ledger-prospectivo-autoria-{indice:03d}-{tentativa:02d}',
               'precos' if preco else 'requisitos', 'teste_ledger_prospectivo_autoria')
    nomes = rng.sample(PLANOS if preco else PESSOAS, 3)
    valores = rng.sample(range(1001, 1700), 12)
    real = {}
    virtual = None
    ativo = False
    ref = {}
    out = []
    consulta = None
    alvo_ultimo = None
    perguntas_p = [
        'Qual é o mais em conta: {a} ou {b}?',
        'Quanto diferencia o custo de {a} e {b}?',
        'Entre {a} e {b}, quem cobra menos?',
        'Compare o dinheiro exigido por {a} e {b}.',
    ]
    perguntas_r = [
        'Qual é a situação da entrada de {n}?',
        '{n} satisfaz as condições já dadas?',
        'Pode liberar {n} pela exigência citada?',
        'A documentação de {n} prova a entrada?',
    ]

    def pergunta(etapa):
        nonlocal consulta
        if preco:
            pares = [(0, 1), (1, 2), (2, 0)]
            consulta = list(pares[(rep + etapa) % 3])
            if (rep + etapa) % 2:
                consulta.reverse()
            return perguntas_p[(rep + etapa) % 4].format(
                a=nomes[consulta[0]], b=nomes[consulta[1]])
        consulta = (rep + 2 * etapa) % 3
        return perguntas_r[(rep + etapa) % 4].format(n=nomes[consulta])

    if preco:
        partes = []
        for i in rng.sample([0, 1, 2], 3):
            partes += [('n' + str(i), nomes[i]), ' custa ',
                       ('v' + str(i), str(valores[i])), ' reais. ']
        sp = s.fala(partes + [pergunta(0)])
        for i in range(3):
            real[i] = sp['v' + str(i)]
    else:
        x, y = rng.sample(OBJETOS, 2)
        posses = [f'tem {x} e {y}', f'tem {x} e não tem {y}',
                  f'tem {x}', f'tem {x} e não tem {x}']
        partes = ['No controle de entrada são exigidos ', ('r', x + ' e ' + y), '. ']
        for i in rng.sample([0, 1, 2], 3):
            partes += [('n' + str(i), nomes[i]), ' ',
                       ('v' + str(i), posses[(rep + i) % 4]), '. ']
        sp = s.fala(partes + [pergunta(0)])
        regra = sp['r']
        for i in range(3):
            real[i] = sp['v' + str(i)]
            ref[i] = sp['n' + str(i)]

    def emitir(evento):
        banco = virtual if ativo else real
        args = [banco[i] for i in consulta] if preco else [regra, banco[consulta]]
        e = s.exemplo('comparar_custos' if preco else 'verificar_requisitos',
                      args, None if preco else ref[consulta], ativo)
        e['evento'] = evento
        e['trajetoria'] = '>'.join(seq)
        e['painel'] = 'ledger_prospectivo_autoria_reservado'
        e['consulta_entidades'] = [nomes[i] for i in consulta] if preco else [nomes[consulta]]
        e['atualizacao_outra_entidade'] = (alvo_ultimo not in consulta if preco else alvo_ultimo != consulta) if alvo_ultimo is not None else False
        e['resultado_gold'] = esperado(e)
        out.append(e)

    emitir('declaracao')
    for etapa, evento in enumerate(seq, 1):
        variante = (rep + etapa) % 4
        alvo_ultimo = None
        if evento in ('correcao', 'hipotese'):
            alvo_ultimo = (rep + etapa) % 3
            n = nomes[alvo_ultimo]
            if preco:
                if evento == 'correcao':
                    frases = [
                        ['Eu anotei errado; ', n, ' custa '],
                        ['O valor anterior é erro: ', n, ' custa '],
                        ['Não vale o dado anterior: ', n, ' custa '],
                        ['Agora corrija o fato: ', n, ' custa '],
                    ]
                    finais = [' reais na realidade. ', ' reais, confirmado. ',
                              ' reais de verdade. ', ' reais, como fato. ']
                else:
                    frases = [
                        ['Se imaginarmos outro caso, ', n, ' custa '],
                        ['O caso só imaginado tem ', n, ' a '],
                        ['Para uma nova hipótese, suponha ', n, ' custa '],
                        ['Sem assumir ocorrência, teste ', n, ' a '],
                    ]
                    finais = [' reais; nada mudou de verdade. ', ' reais; não ocorreu. ',
                              ' reais; o real permanece. ', ' reais no cenário imaginário. ']
                sp = s.fala(frases[variante] + [('v', str(valores[etapa + 3])),
                                                 finais[variante], pergunta(etapa)])
            else:
                # Toda atualização contém inventário completo da pessoa citada.
                proibidos = {real[alvo_ultimo]['texto']}
                if virtual is not None:
                    proibidos.add(virtual[alvo_ultimo]['texto'])
                disponiveis = [v for v in posses if v not in proibidos]
                posse = disponiveis[(rep + etapa) % len(disponiveis)]
                if evento == 'correcao':
                    frases = [
                        ['Eu anotei errado; ', n, ' '],
                        ['O inventário anterior é erro: ', n, ' '],
                        ['Não vale o registro anterior: ', n, ' '],
                        ['Agora corrija o fato: ', n, ' '],
                    ]
                    finais = [' na realidade. ', ', confirmado. ',
                              ' de verdade. ', ', como fato. ']
                else:
                    frases = [
                        ['Se imaginarmos outro caso, ', n, ' '],
                        ['O caso só imaginado diz que ', n, ' '],
                        ['Para uma nova hipótese, suponha que ', n, ' '],
                        ['Sem assumir ocorrência, imagine ', n, ' '],
                    ]
                    finais = ['; nada mudou de verdade. ', '; não ocorreu. ',
                              '; o real permanece. ', ' no cenário imaginário. ']
                sp = s.fala(frases[variante] + [('v', posse), finais[variante], pergunta(etapa)])
            novo = dict(real)
            novo[alvo_ultimo] = sp['v']
            if evento == 'correcao':
                real = novo
                virtual = None
                ativo = False
            else:
                virtual = novo
                ativo = True
        elif evento == 'confirmacao':
            assert ativo and virtual is not None
            s.fala([CONFIRMACOES[variante], pergunta(etapa)])
            real = dict(virtual)
            virtual = None
            ativo = False
        elif evento == 'retorno':
            s.fala([RETORNOS[variante], pergunta(etapa)])
            virtual = None
            ativo = False
        else:
            assert evento == 'consulta'
            s.fala([CONSULTAS[variante], pergunta(etapa)])
        emitir(evento)
    return out


def verificar(es, tok):
    counts = []
    for e in es:
        exigir = lambda cond: cond or (_ for _ in ()).throw(AssertionError('Contrato estrutural do gold inválido.'))
        exigir(4 <= len(es) <= 6)
        exigir(e['resultado_gold']['executavel'])
        item = codificar(tok, e)
        input_only = codificar(tok, {'turnos': e['turnos'], 'argumentos': [None] * 3, 'referente': None})
        exigir(item['ids'] == input_only['ids'] and item['offsets'] == input_only['offsets'])
        for span, (a, b) in zip(e['argumentos'] + [e['referente']], zip(item['pontos'][::2], item['pontos'][1::2])):
            previsto = recuperar(item, a, b)
            if span is None:
                exigir(previsto is None)
            else:
                exigir(e['turnos'][span['turno']][span['inicio']:span['fim']] == span['texto'])
                exigir(previsto is not None and previsto['texto'] == span['texto'] and previsto['turno'] == span['turno'])
        counts.append(len(item['ids']))
    return counts


def main():
    if (SAIDA / 'casos.json').exists() or (SAIDA / 'protocolo.json').exists():
        raise FileExistsError('Painel fechado existe; nunca sobrescrever após sua geração.')
    tok = Tokenizer.from_file(str(TOKENIZER))
    tok.encode_special_tokens = True
    rows, lengths, descartes, vistos = [], [], [], set()
    for i in range(72):
        for tentativa in range(200):
            es = montar(i, tentativa)
            try:
                tokens = verificar(es, tok)
            except ValueError as exc:
                descartes.append({'indice': i, 'tentativa': tentativa,
                                  'motivo': str(exc), 'sessao_inteira_descartada': True})
                continue
            textos = [json.dumps(e['turnos'], ensure_ascii=False) for e in es]
            if any(t in vistos for t in textos):
                descartes.append({'indice': i, 'tentativa': tentativa,
                                  'motivo': 'Contexto duplicado', 'sessao_inteira_descartada': True})
                continue
            rows.extend(es)
            lengths.extend(tokens)
            vistos.update(textos)
            break
        else:
            raise RuntimeError(f'Sessão {i} não coube: não omitir seus gold nem truncar.')
    escrever(SAIDA / 'casos.json', rows)
    completas = [e for e in rows if e['etapa'] == len(TRAJETORIAS[int(e['sessao'].split('-')[-2]) // 8])]
    contagens = {
        'sessoes': 72, 'exemplos': len(rows), 'max_tokens': max(lengths),
        'tokens_entrada': sum(lengths), 'familias': dict(Counter(e['familia'] for e in rows)),
        'eventos': dict(Counter(e['evento'] for e in rows)),
        'hipotese_ativa': dict(Counter(str(e['hipotese']) for e in rows)),
        'sessoes_por_trajetoria': dict(Counter(e['trajetoria'] for e in rows if e['etapa'] == 0)),
        'comprimentos_sessao': dict(Counter(len(e['turnos']) for e in completas)),
        'atualizacoes_outra_entidade_que_a_consulta': sum(e['atualizacao_outra_entidade'] for e in rows),
        'verificados_gold_fontes_offsets_sem_rotulos_no_input': len(rows),
        'descartes_sessoes_inteiras': len(descartes),
    }
    protocolo = {
        'identificador': 'crivo_ledger_20261009_autoria_prospectiva_v1',
        'criado_utc': datetime.now(timezone.utc).isoformat(), 'semente': SEMENTE,
        'uso': 'Avaliação única fechada. Raiz e implementador não leem casos.json ou gerar.py até '
               'congelar o novo ledger e completar testes de contrato próprios.',
        'autoria': 'Outro subagente da equipe; não leu ledger.py, código da nova implementação, '
                   'suas previsões ou exemplos de trabalho. Autoria conhece apenas métricas agregadas '
                   'de falha da rodada anterior, interfaces/executor e contrato de estado declarado.',
        'proveniencia': 'Frases inteiramente novas em relação ao painel prospectivo anterior; '
                       'novos nomes/objetos/valores e consultas de três entidades. Sem modelo/API/corpus externo.',
        'semantica': {
            'fatos': 'Dicionário de fontes mais recentes por entidade, com regra de ingresso compartilhada.',
            'hipotese': 'Toda nova hipótese começa copiando fatos e muda somente a entidade citada.',
            'correcao': 'Atualização factual explícita muda a entidade citada e encerra qualquer hipótese.',
            'confirmacao': 'Promove todo o último cenário hipotético aos fatos sem repetir seus valores.',
            'retorno': 'Descarta só hipótese ainda não confirmada, preservando fatos inclusive confirmações.',
            'consulta': 'Não altera fatos ou hipótese. O escopo é o cenário ativo da conversa inteira.',
            'ordem': 'Nos custos, argumentos seguem os dois nomes da pergunta. Inventário segue o nome '
                     'explícito consultado. Dados de outras entidades são distratores.',
            'inventario': 'Declarações completas com tem/não tem, duas condições; ausência não prova '
                          'negação e conflito positivo/negativo é contraditório.',
        },
        'schema': {
            'entrada_inferencia': ['turnos'],
            'gold_exclusivo_medicao': ['operacao', 'argumentos', 'referente', 'hipotese',
                                      'evento', 'resultado_gold', 'consulta_entidades',
                                      'atualizacao_outra_entidade'],
            'span': 'turno, inicio inclusivo, fim exclusivo, texto literal',
            'metadados': ['sessao', 'familia', 'etapa', 'split', 'classe', 'trajetoria', 'painel'],
        },
        'contagens': contagens,
        'sha256': {
            'casos.json': sha(SAIDA / 'casos.json'), 'gerar.py': sha(__file__),
            'tokenizer_proprio': sha(TOKENIZER), 'schema_corpus': sha(CONTEXTUAL / 'corpus.py'),
            'executor_gold': sha(CONTEXTUAL / 'modelo.py'), 'preparo': sha(PREPARO / 'preparo.py'),
        },
        'descartes': descartes,
        'limites': [
            'Outra autoria de agente dentro da mesma equipe, mesma gramática/executor fechado; '
            'não avaliação humana ou externa independente.',
            '72 sessões parametrizam nove trajetórias e quatro variantes; prefixos são correlacionados.',
            'Perguntas explícitas, nomes de uma palavra, requisitos binários e preços inteiros. '
            'Não mede pronomes ambíguos, conversa livre, contexto longo ou raciocínio geral.',
            'Sem inferência ou seleção por teste. Gold failures não foram omitidos; somente contextos '
            'inteiros acima de 256 tokens ou duplicados podem ser regenerados e são registrados.',
        ],
    }
    escrever(SAIDA / 'protocolo.json', protocolo)
    print(json.dumps({'contagens': contagens, 'casos_sha256': sha(SAIDA / 'casos.json'),
                      'protocolo_sha256': sha(SAIDA / 'protocolo.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
