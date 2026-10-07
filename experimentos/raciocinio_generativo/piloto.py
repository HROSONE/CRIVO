"""Currículo autoral e protocolo do piloto; sem dependências de treino."""
import hashlib
import json
import random
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from diagnosticar import assinatura, verificar_passos
from raciocinio_ativo import SistemaPremissas, ler_literal, ler_premissa

STATUS = ('sustentado', 'refutado', 'indeterminado', 'conflito')
NOMES = {
    'treino': ['O sensor responde', 'O painel liga', 'A luz acende', 'O motor gira',
               'A porta abre', 'O sinal passa', 'O cabo funciona', 'A roda gira'],
    'dev': ['O cristal brilha', 'A pedra aquece', 'A folha cai', 'O vento sopra',
            'O gelo derrete', 'A água corre', 'A nuvem cresce', 'A chuva começa'],
    'teste': ['O sino toca', 'A nave parte', 'O mapa aparece', 'A ponte abre',
              'O barco chega', 'A chave entra', 'O farol pisca', 'A torre fecha'],
}


def oposto(texto):
    partes = texto.split()
    return ' '.join(partes[:2] + ['não'] + partes[2:])


def oraculo(caso):
    s = SistemaPremissas(tuple(ler_premissa(p) for p in caso['premissas']))
    return s.analisar(ler_literal(caso['objetivo']))['status']


def gerar_casos(split, n=80):
    """Split por linguagem; teste inclui profundidades e grafos inéditos.

    Famílias comuns são medidas à parte como transferência lexical. Não se
    afirma separação estrutural para todos os casos de teste.
    """
    rng = random.Random({'treino': 8101, 'dev': 8102, 'teste': 8103}[split])
    familias = [('cadeia', 1), ('cadeia', 2), ('cadeia', 3), ('juncao', 2)]
    if split == 'teste':
        familias += [('cadeia', 4), ('cadeia', 5), ('diamante', 3)]
    modos = ('positivo', 'negativo', 'ausente', 'conflito')
    casos, vistos = [], set()
    while len(casos) < n:
        i = len(casos)
        familia, profundidade = familias[(i // len(modos)) % len(familias)]
        modo = modos[i % len(modos)]
        nomes = rng.sample(NOMES[split], 8)
        if familia == 'cadeia':
            regras = [([j], j + 1) for j in range(profundidade)]
            base, destino = [0], profundidade
        elif familia == 'juncao':
            regras, base, destino = [([0, 1], 2), ([2], 3)], [0, 1], 3
        else:
            regras = [([0], 1), ([0], 2), ([1, 2], 3), ([3], 4)]
            base, destino = [0], 4
        negativos = {destino} if modo == 'negativo' else set()
        lit = lambda j: oposto(nomes[j]) if j in negativos else nomes[j]
        premissas = [lit(j) for j in base if not (modo == 'ausente' and j == base[0])]
        for antecedentes, consequente in regras:
            premissas.append('Se ' + ' e '.join(lit(a).lower() for a in antecedentes)
                             + ', então ' + lit(consequente).lower())
        if modo == 'conflito':
            premissas.append(oposto(nomes[base[0]]))
        # Distrator sem relação com o objetivo, sempre presente.
        premissas.append(nomes[7])
        rng.shuffle(premissas)
        caso = dict(id='%s-%04d' % (split, i), split=split, familia=familia,
                    profundidade=profundidade, modo=modo, premissas=premissas,
                    objetivo=nomes[destino], ood_estrutura=split == 'teste' and
                    (profundidade > 3 or familia == 'diamante'))
        chave = json.dumps([premissas, caso['objetivo']], ensure_ascii=False)
        if chave in vistos:
            continue
        vistos.add(chave)
        caso['status'] = oraculo(caso)
        esperado = dict(positivo='sustentado', negativo='refutado',
                        ausente='indeterminado', conflito='conflito')[modo]
        if caso['status'] != esperado:
            raise AssertionError('Currículo incorreto: ' + caso['id'])
        casos.append(caso)
    return casos


def contexto(caso, passos, tarefa='passo'):
    linhas = ['Tarefa: ' + tarefa, 'Objetivo: ' + caso['objetivo']]
    linhas += ['p%d: %s' % (i, p) for i, p in enumerate(caso['premissas'])]
    linhas += ['s%d: %s' % (i, p['conclusao']) for i, p in enumerate(passos)]
    return '\n'.join(linhas)


def serializar(passo):
    return passo['regra'] + '|' + ','.join(passo['apoios']) + '|' + passo['conclusao']


def interpretar(texto):
    t = texto.strip().rstrip('.')
    if t in STATUS:
        return t
    m = re.fullmatch(r'(p\d+)\|((?:[ps]\d+)(?:,[ps]\d+)*)\|(.{1,80})', t)
    if not m:
        raise ValueError('Saída fora do protocolo.')
    return dict(regra=m[1], apoios=m[2].split(','), conclusao=m[3])


def exemplos_passos(caso):
    """Professor simbólico usado SOMENTE para construir os alvos do treino."""
    passos, exemplos = [], []
    ps = [ler_premissa(p) for p in caso['premissas']]
    fatos = {assinatura(p.consequente): 'p%d' % i for i, p in enumerate(ps) if not p.antecedentes}
    alvo = ler_literal(caso['objetivo'])
    while True:
        prompt = contexto(caso, passos)
        if caso['status'] == 'conflito' or assinatura(alvo) in fatos or assinatura(alvo.oposto()) in fatos:
            exemplos.append((prompt, caso['status']))
            break
        escolha = None
        for i, p in enumerate(ps):
            if p.antecedentes and all(assinatura(a) in fatos for a in p.antecedentes) and assinatura(p.consequente) not in fatos:
                escolha = dict(regra='p%d' % i, apoios=[fatos[assinatura(a)] for a in p.antecedentes],
                               conclusao=('não é verdade que ' if p.consequente.negativo else '') + p.consequente.rotulo)
                break
        if escolha is None:
            exemplos.append((prompt, caso['status']))
            break
        valido, motivo = verificar_passos(caso['premissas'], passos + [escolha])
        if not valido:
            raise AssertionError(motivo)
        exemplos.append((prompt, serializar(escolha)))
        fatos[assinatura(ler_literal(escolha['conclusao']))] = 's%d' % len(passos)
        passos.append(escolha)
    return exemplos


def executar(caso, gerar, limite=8):
    """Modelo decide; verificador veta. Nunca consulta o oráculo para reparar."""
    passos, saídas = [], []
    for _ in range(limite):
        texto = gerar(contexto(caso, passos))
        saídas.append(texto)
        try:
            proposta = interpretar(texto)
            if isinstance(proposta, str):
                # O acerto desta classificação é medido depois, pelo avaliador.
                # Não substitui resposta neural por classificação simbólica.
                return dict(status=proposta, passos=passos, saidas=saídas, motivo='terminou')
            aceito, motivo = verificar_passos(caso['premissas'], passos + [proposta])
            if not aceito:
                return dict(status=None, passos=passos, saidas=saídas, motivo=motivo)
            if any(assinatura(ler_literal(p['conclusao'])) == assinatura(ler_literal(proposta['conclusao'])) for p in passos):
                return dict(status=None, passos=passos, saidas=saídas, motivo='passo_repetido')
            passos.append(proposta)
        except (ValueError, TypeError, KeyError, AttributeError):
            return dict(status=None, passos=passos, saidas=saídas, motivo='protocolo_invalido')
    return dict(status=None, passos=passos, saidas=saídas, motivo='limite_de_passos')


def corpus():
    dados = {s: gerar_casos(s, n) for s, n in [('treino', 480), ('dev', 32), ('teste', 56)]}
    hashes = {}
    for split, casos in dados.items():
        hashes[split] = hashlib.sha256(json.dumps(casos, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return dados, hashes
