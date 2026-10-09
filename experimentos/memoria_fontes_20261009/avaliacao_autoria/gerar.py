"""Painel prospectivo de outra autoria de agente, sem acessar previsões.

Só importa o schema, codificação própria e executor fechado para verificar o
gold. Nenhum modelo é instanciado e nenhum checkpoint é aberto. Este arquivo
não fornece exemplos de treino; casos.json permanece reservado à avaliação.
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
EVENTOS = REPO / 'experimentos/escopo_eventos_20261008'
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(CONTEXTUAL))
sys.path.insert(0, str(EVENTOS))
from corpus import Sessao
from modelo import esperado, recuperar
from normalizacao import codificar, normalizar
from tokenizers import Tokenizer

SAIDA = Path(__file__).resolve().parent
TOKENIZER = REPO / 'artefatos/linguagem_profunda/tokenizer.json'
SEMENTE = 2026100947
NOMES_PLANOS = ['Safira', 'Jaspe', 'Ônix', 'Quartzo', 'Opala', 'Topázio']
NOMES_PESSOAS = ['Ester', 'Valdo', 'Celina', 'Gaspar', 'Íris', 'Érico']
OBJETOS = ['permissão', 'voucher', 'plaqueta', 'autorização', 'identificação', 'cupom']
TRAJETORIAS = [
    ['correcao', 'hipotese', 'retorno'],
    ['hipotese', 'consulta', 'retorno', 'correcao'],
    ['hipotese', 'correcao', 'retorno'],
    ['hipotese', 'confirmacao', 'retorno'],
    ['correcao', 'hipotese', 'confirmacao', 'retorno'],
    ['hipotese', 'confirmacao', 'hipotese', 'retorno', 'correcao'],
    ['correcao', 'hipotese', 'consulta', 'retorno'],
    ['hipotese', 'retorno', 'hipotese', 'confirmacao', 'retorno'],
    ['correcao', 'correcao', 'hipotese', 'retorno', 'consulta'],
    ['hipotese', 'hipotese', 'confirmacao', 'consulta', 'retorno'],
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def escrever(path, valor):
    path.write_text(json.dumps(valor, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def montar(indice, tentativa=0):
    """Transição explícita de estado produz fontes; gold nunca altera texto."""
    rng = random.Random(SEMENTE + indice * 104729 + tentativa * 10000019)
    preco = indice % 2 == 0
    seq = TRAJETORIAS[(indice // 8) % len(TRAJETORIAS)]
    repeticao = (indice // 2) % 4
    s = Sessao(f'prospectivo-autoria-{indice:03d}-{tentativa:02d}',
               'precos' if preco else 'requisitos', 'teste_prospectivo_autoria')
    out = []
    ativo = False
    virtual = None
    referencias = None
    nomes = rng.sample(NOMES_PLANOS if preco else NOMES_PESSOAS, 3)
    numeros = rng.sample(range(601, 940), 12)
    perguntas_preco = [
        'Qual sai por menos, {a} ou {b}, e por quanto?',
        'Entre {a} e {b}, qual custo vence e qual a diferença?',
        'Quanto é a diferença de custo de {a} para {b}?',
        'Compare {a} com {b} usando a situação atual.',
    ]
    perguntas_requisito = [
        'Com esses dados, {n} está apto a entrar?',
        'A entrada de {n} é garantida pela regra?',
        'O que se sabe permite liberar {n}?',
        'Pela regra, a entrada de {n} está provada?',
    ]
    ordem = [0, 1]

    def pergunta(etapa):
        nonlocal ordem
        if preco:
            ordem = [1, 0] if (repeticao + etapa) % 2 else [0, 1]
            return perguntas_preco[(repeticao + etapa) % 4].format(
                a=nomes[ordem[0]], b=nomes[ordem[1]])
        return perguntas_requisito[(repeticao + etapa) % 4].format(n=nomes[0])

    if preco:
        # A terceira oferta é um custo válido, mas não responde à consulta.
        partes = []
        for i in rng.sample([0, 1, 2], 3):
            partes += [('n' + str(i), nomes[i]), ' custa ',
                       ('v' + str(i), str(numeros[i])), ' reais. ']
        partes += [pergunta(0)]
        sp = s.fala(partes)
        real = [sp['v0'], sp['v1']]
    else:
        x, y, z = rng.sample(OBJETOS, 3)
        # Quatro valores de verdade; nada ausente equivale a negativo.
        posses = [f'tem {x} e {y}', f'tem {x} e não tem {y}',
                  f'tem {x}', f'tem {x} e não tem {x}']
        inicio = repeticao % 4
        partes = ['Para entrar são exigidos ', ('r', x + ' e ' + y), '. ',
                  ('n', nomes[0]), ' ', ('v', posses[inicio]), '. ',
                  nomes[1], ' tem ' + z + ' e não tem ' + y + '. ', pergunta(0)]
        sp = s.fala(partes)
        referencias = sp['n']
        real = [sp['r'], sp['v']]

    def emitir(evento, etapa):
        valores = virtual if ativo else real
        args = [valores[i] for i in ordem] if preco else list(valores)
        e = s.exemplo('comparar_custos' if preco else 'verificar_requisitos',
                      args, referencias, ativo)
        e['evento'] = evento
        e['trajetoria'] = '>'.join(seq)
        e['painel'] = 'prospectivo_autoria_reservado'
        e['caracteristicas'] = {
            'distrator_com_fatos': True,
            'mudanca_ordem_consulta': preco,
            'confirmacao_sem_repetir_alvos': 'confirmacao' in seq,
            'apos_confirmacao_retorna': any(a == 'confirmacao' and 'retorno' in seq[j+1:]
                                           for j, a in enumerate(seq)),
            'variante_autoria': repeticao,
        }
        # Mantém o resultado esperado fora da entrada da inferência.
        e['resultado_gold'] = esperado(e)
        out.append(e)

    emitir('declaracao', 0)
    for etapa, evento in enumerate(seq, 1):
        if evento in ('correcao', 'hipotese'):
            if preco:
                quem = (repeticao + etapa) % 2
                valor = numeros[etapa + 3]
                if evento == 'correcao':
                    aberturas = [
                        ['Não é hipótese: o preço correto de ', nomes[quem], ' é '],
                        ['Eu corrigi o registro real de ', nomes[quem], ': custa '],
                        ['Só ajusto o fato: ', nomes[quem], ' custa '],
                        ['Fora da imaginação, o custo real de ', nomes[quem], ' é '],
                    ]
                else:
                    aberturas = [
                        ['Não aconteceu; nesta nova hipótese, ', nomes[quem], ' custa '],
                        ['Só para imaginar outra alternativa, ', nomes[quem], ' custaria '],
                        ['Sem trocar os fatos, suponha ', nomes[quem], ' a '],
                        ['Imagine um caso novo: ', nomes[quem], ' custa '],
                    ]
                partes = aberturas[(repeticao + etapa) % 4] + [('v', str(valor)), ' reais. ']
                # Uma consulta ativa com número de entrega testa relevância.
                if etapa == 1 and len(seq) < 4:
                    partes += ['A entrega segue em ', ('d', str(numeros[10])), ' dias. ']
                partes += [pergunta(etapa)]
                novos = s.fala(partes)
                atual = list(real)
                atual[quem] = novos['v']
            else:
                posse = posses[(inicio + etapa) % 4]
                if evento == 'correcao':
                    aberturas = [
                        ['Não estou imaginando: no registro real, ', nomes[0], ' '],
                        ['Eu errei nos fatos: na realidade, ', nomes[0], ' '],
                        ['Só corrijo o inventário factual: ', nomes[0], ' '],
                        ['Fora de qualquer hipótese, ', nomes[0], ' '],
                    ]
                else:
                    aberturas = [
                        ['Não ocorreu; nesta alternativa imaginada, ', nomes[0], ' '],
                        ['Só para testar outra possibilidade, ', nomes[0], ' '],
                        ['Sem mudar o inventário real, imagine que ', nomes[0], ' '],
                        ['Imagine um caso novo no qual ', nomes[0], ' '],
                    ]
                novos = s.fala(aberturas[(repeticao + etapa) % 4] +
                                [('v', posse), '. ', pergunta(etapa)])
                atual = [real[0], novos['v']]
            if evento == 'correcao':
                real = atual
                virtual = None
                ativo = False
            else:
                virtual = atual
                ativo = True
        elif evento == 'confirmacao':
            assert ativo and virtual is not None
            frases = [
                'Agora confirmo: a última alternativa virou realidade. ',
                'O que era imaginado foi comprovado; registre como fato. ',
                'Eu confirmo a hipótese mais recente como situação real. ',
                'Não é mais ficção: a última simulação ocorreu de verdade. ',
            ]
            s.fala([frases[(repeticao + etapa) % 4], pergunta(etapa)])
            real = list(virtual)
            virtual = None
            ativo = False
        elif evento == 'retorno':
            frases = [
                'Use os fatos atuais e encerre apenas a imaginação. ',
                'Volte à realidade, mantendo tudo que foi confirmado. ',
                'Sem alternativas imaginadas: consulte o registro factual atual. ',
                'Desconsidere só a hipótese ainda não confirmada. Use os fatos. ',
            ]
            s.fala([frases[(repeticao + etapa) % 4], pergunta(etapa)])
            virtual = None
            ativo = False
        else:
            assert evento == 'consulta'
            frases = [
                'Sem mudar nada, prossiga com a mesma situação. ',
                'Agora repita a análise; não mude dados ou cenário. ',
                'Só pergunto de novo, mantendo o cenário vigente. ',
                'Use a situação que estamos analisando, sem alteração. ',
            ]
            s.fala([frases[(repeticao + etapa) % 4], pergunta(etapa)])
        emitir(evento, etapa)
    return out


def verificar(es, tok):
    cs = [codificar(tok, e) for e in es]
    for e, c in zip(es, cs):
        assert 4 <= len(es) <= 6
        assert e['resultado_gold']['executavel']
        fontes = e['argumentos'] + [e['referente']]
        for sp, (a, b) in zip(fontes, zip(c['pontos'][::2], c['pontos'][1::2])):
            r = recuperar(c, a, b)
            if sp is None:
                assert r is None
            else:
                assert e['turnos'][sp['turno']][sp['inicio']:sp['fim']] == sp['texto']
                assert r is not None and r['texto'] == sp['texto'] and r['turno'] == sp['turno']
        # Remover todos os rótulos não deve mudar a entrada tokenizada.
        so_input = {'turnos': e['turnos'], 'argumentos': [None] * 3, 'referente': None}
        sem_gold = codificar(tok, so_input)
        assert c['ids'] == sem_gold['ids'] and c['offsets'] == sem_gold['offsets']
        # O mapa deve preservar exatamente nomes, sem exigir NER externo.
        normalizar(e['turnos'])
    return [len(c['ids']) for c in cs]


def main():
    if (SAIDA / 'casos.json').exists() or (SAIDA / 'protocolo.json').exists():
        raise FileExistsError('Painel fechado já existe; não regenerar ou sobrescrever.')
    tok = Tokenizer.from_file(str(TOKENIZER))
    tok.encode_special_tokens = True
    rows, lengths = [], []
    rejeicoes = []
    vistos = set()
    for i in range(80):
        for tentativa in range(200):
            es = montar(i, tentativa)
            try:
                tokens = verificar(es, tok)
            except ValueError as exc:
                rejeicoes.append({'indice': i, 'tentativa': tentativa,
                                  'motivo': str(exc), 'sessoes_descartadas_inteiras': 1})
                continue
            keys = [json.dumps(e['turnos'], ensure_ascii=False) for e in es]
            if any(k in vistos for k in keys):
                rejeicoes.append({'indice': i, 'tentativa': tentativa,
                                  'motivo': 'Contexto duplicado', 'sessoes_descartadas_inteiras': 1})
                continue
            vistos.update(keys)
            rows.extend(es)
            lengths.extend(tokens)
            break
        else:
            raise RuntimeError(f'Não foi possível completar a sessão {i} sem truncar.')
    escrever(SAIDA / 'casos.json', rows)
    contagens = {
        'sessoes': 80, 'exemplos': len(rows), 'tokens_entrada': sum(lengths),
        'max_tokens_por_exemplo': max(lengths),
        'familias': dict(Counter(e['familia'] for e in rows)),
        'eventos': dict(Counter(e['evento'] for e in rows)),
        'hipotese_ativa': dict(Counter(str(e['hipotese']) for e in rows)),
        'trajetorias_sessoes': dict(Counter(e['trajetoria'] for e in rows if e['etapa'] == 0)),
        'tamanhos_sessoes': dict(Counter(len(e['turnos']) for e in rows
                                        if e['etapa'] == len(montar(int(e['sessao'].split('-')[-2]),
                                                                   int(e['sessao'].split('-')[-1]))) - 1)),
        'verificacoes_gold_offsets_sem_truncamento': len(rows),
        'rejeicoes_sessoes_inteiras': len(rejeicoes),
    }
    protocolo = {
        'identificador': 'crivo_memoria_20261009_avaliacao_autoria_prospectiva',
        'criado_utc': datetime.now(timezone.utc).isoformat(),
        'semente_parametrizacao': SEMENTE,
        'uso': 'Teste fechado. Não carregar casos.json nem gerar.py em treino/seleção. '
               'Abrir somente após congelar checkpoint escolhido por validação.',
        'autoria': 'Outro subagente de autoria nesta sessão, sem ver previsões, logs de erros '
                   'ou casos de avaliação antigos. Interfaces e gramática executável foram lidas.',
        'origem_dados': 'Frases autorais e parametrização finita própria. Sem corpus externo, '
                        'pesos externos, conversa privada ou API de modelos.',
        'semantica_declarada': {
            'hipotese': 'Toda nova hipótese parte do último estado factual, não da hipótese anterior.',
            'correcao': 'Uma correção factual atualiza só a fonte citada e encerra a hipótese ativa.',
            'consulta': 'Consulta sem alteração preserva o estado ativo: factual ou hipotético.',
            'confirmacao': 'A última alternativa é incorporada aos fatos sem repetir seus alvos.',
            'retorno': 'Encerra a hipótese ainda ativa e preserva os fatos inclusive os confirmados.',
            'ordem_preco': 'Argumentos seguem a ordem dos dois nomes na consulta; distrator não responde.',
            'requisitos': 'Ausência de um item não prova negação. Quatro estados: provado, refutado, '
                          'indeterminado e contraditório; outro sujeito é distrator.',
        },
        'schema': {
            'entrada_inferencia': ['turnos'],
            'gold_fora_da_inferencia': ['operacao', 'argumentos', 'referente', 'hipotese',
                                       'evento', 'resultado_gold', 'caracteristicas'],
            'span': {'turno': 'índice da fala', 'inicio': 'caractere inicial inclusivo',
                     'fim': 'caractere final exclusivo', 'texto': 'literal suportado na fala'},
            'metadados': ['sessao', 'familia', 'etapa', 'split', 'classe', 'trajetoria', 'painel'],
        },
        'contagens': contagens,
        'sha256': {
            'casos.json': sha(SAIDA / 'casos.json'), 'gerar.py': sha(__file__),
            'tokenizer_proprio': sha(TOKENIZER), 'schema_corpus': sha(CONTEXTUAL / 'corpus.py'),
            'executor_gold': sha(CONTEXTUAL / 'modelo.py'),
            'normalizacao_vigente': sha(EVENTOS / 'normalizacao.py'),
            'normalizacao_base': sha(REPO / 'experimentos/associacao_fatos_20261008/normalizar.py'),
        },
        'rejeicoes': rejeicoes,
        'limites': [
            'Outra autoria dentro da mesma equipe de agentes e gramática, não avaliador externo independente.',
            '80 sessões parametrizam somente dez trajetórias e quatro variantes de frases; exemplos '
            'não são amostras humanas independentes.',
            'Nomes novos de uma palavra maiúscula, preços inteiros, duas entidades consultadas e '
            'requisitos de dois itens; não mede conversa livre, raciocínio geral ou longos contextos.',
            'Não houve inferência, seleção de pesos, interpretação de previsões nem ajuste pós-teste.',
            'Gold e eventos são exclusivos da medição; verificação de IDs mostrou independência '
            'da entrada em relação a todos os rótulos.',
        ],
    }
    escrever(SAIDA / 'protocolo.json', protocolo)
    print(json.dumps({'contagens': contagens, 'sha256_casos': sha(SAIDA / 'casos.json'),
                      'sha256_protocolo': sha(SAIDA / 'protocolo.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
