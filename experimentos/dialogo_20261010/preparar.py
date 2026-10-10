"""Congela casos observados e escreve demonstrações autorais; não usa modelos."""
import copy
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parent.parent
BASE = '9ed051bf2b74668073e0ac480b43c652314b88e7'


def escrever(nome, dados):
    (H / nome).write_text(json.dumps(dados, ensure_ascii=False, indent=2) + '\n')


def congelar():
    original = H.parent / 'roteamento_natural_v2_20261009/casos_congelados.json'
    casos = copy.deepcopy(json.loads(original.read_text())['casos'])
    novos = [
        ('pos125-so-isso', 'so_isso_site.json', None, 'esclarecimento', 'capacidades', ['posso']),
        ('pos125-definicao', 'definicao_comparacao_site.json', 0, 'fato', 'definir', ['potencial elétrico']),
    ]
    for ident, arquivo, indice, peca, ato, minimo in novos:
        raw = json.loads((H / 'evidencias' / arquivo).read_text())
        row = raw if indice is None else raw['resultados'][indice]
        casos.append({'id': ident, 'origem': {'arquivo': 'evidencias/' + arquivo, 'commit': BASE},
                      'entrada': {'texto': row['pedido']['message'], 'anteriores': row['pedido']['history']},
                      'usuario_queria': 'Retomar capacidades' if indice is None else 'Definição do alias completo',
                      'crivo_fez': {'id': row['resposta']['id'], 'resposta': row['resposta']['response']},
                      'esperado': {'peca': peca, 'ato': ato, 'referentes': [], 'conteudo_minimo': minimo,
                                   'desvios_proibidos': ['negação com segurança'] if indice is None else ['Pode esclarecer']}})
    conversacionais = {'real-01', 'real-02', 'real-03', 'real-04', 'real-19', 'real-20',
                       'real-21', 'pos-01', 'pos-04', 'pos125-so-isso'}
    for c in casos:
        c['grupos'] = ['roteamento']
        if c['entrada']['anteriores'] or c['esperado']['referentes']:
            c['grupos'].append('tarefa_referente')
        if c['id'] in conversacionais:
            c['grupos'].append('dialogo_historia_capacidades')
        c['resposta_minima_aceitavel'] = {'termos': c['esperado']['conteudo_minimo'],
                                       'referentes': c['esperado']['referentes'],
                                       'parafrase_permitida': True,
                                       'exige_historia': c['id'] in ('real-19', 'real-20')}
    dados = {'versao': 1, 'base': BASE, 'origem': '35 casos reais anteriores + 2 consultas HTTP pós-125',
             'originais_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
             'criterios': {'peca_correta_minimo': 34, 'trocas_dominio': 0, 'referentes_preservados': '100%',
                           'historia_entregue': True, 'conversas_manuais': '6 de 10, com 6–8 turnos'},
             'casos': casos}
    path = H / 'casos_congelados.json'
    texto = json.dumps(dados, ensure_ascii=False, indent=2) + '\n'
    if path.exists() and path.read_text() != texto:
        raise ValueError('O conjunto já foi congelado; não alterar após medir.')
    path.write_text(texto)
    (H / 'SHA256').write_text(hashlib.sha256(path.read_bytes()).hexdigest() + '  casos_congelados.json\n')


def nome(i):
    partes = ['Al', 'Dal', 'Lor', 'Mir', 'Nar', 'Pel', 'Sir', 'Tal', 'Ver', 'Zel']
    meios = ['a', 'e', 'i', 'o', 'u', 'ae', 'ei', 'io', 'ou', 'ia']
    fins = ['nela', 'vira', 'lino', 'rava', 'selo', 'mino', 'lora', 'nira', 'velo', 'rina']
    return partes[i % 10] + meios[(i // 10) % 10] + fins[(i // 100) % 10]


def demonstracao(tipo, n, m, x, y, personagem, limite, validacao):
    # Alvos escritos pelo autor do experimento, não extraídos dos casos reais.
    oi = f'Olá, sou {n}.' if validacao else f'Oi, eu me chamo {n}.'
    pares = [(oi, f'Oi, {n}. Sobre o que você quer conversar?', f'pessoa: {n}', 'saudação')]
    if tipo == 'capacidades':
        pares += [
            ('Quais são suas funções aqui?' if validacao else 'Em que você consegue ajudar?',
             'Posso conversar, usar o que você contou, explicar fatos com fontes e ajudar com textos curtos.', '', 'capacidades'),
            ('Tem mais alguma coisa?' if validacao else 'E além disso?',
             'Também posso ajudar com cálculos e código simples. Você quer um exemplo ou prefere começar por um pedido?', '', 'capacidades'),
            ('Me mostre algumas perguntas.' if validacao else 'Quero exemplos de pedidos.',
             'Você pode pedir uma explicação, uma história ou ajuda para organizar seu tempo. Qual deles quer experimentar?', '', 'capacidades'),
            ('Você sabe tudo que acontece?' if validacao else 'Você inventa o que não sabe?',
             'Quando faltam dados, devo dizer isso e pedir esclarecimento. Perguntas sobre fatos precisam de fontes.', '', 'esclarecimento'),
            ('Vamos falar do meu dia.' if validacao else 'Quero conversar sobre o meu dia.',
             'Pode contar. O que aconteceu e qual parte você quer explorar primeiro?', '', 'continuação'),
        ]
    elif tipo == 'preferencias':
        estado = f'{n} prefere {x}; {m} prefere {y}'
        pares += [
            (f'Eu prefiro {x}. Minha amiga {m} prefere {y}.', f'Entendi: você prefere {x}, e {m} prefere {y}.', estado, 'preferência'),
            ('E a preferência da minha amiga?' if validacao else 'O que minha amiga prefere?', f'{m} prefere {y}, segundo o que você contou.', estado, 'preferência'),
            (f'Correção: minha preferência agora é {y}.' if validacao else f'Mudei de ideia: agora prefiro {y}.', f'Sua preferência agora é {y}. A informação de {m} continua igual.', f'{n} prefere {y}; {m} prefere {y}', 'correção'),
            ('O que escolho para mim?' if validacao else 'Qual opção combina comigo?', f'Pela sua correção, a opção é {y}.', f'{n} prefere {y}', 'preferência'),
            ('Você lembrou das duas pessoas?' if validacao else 'E o que ficou sobre nós?', f'Você e {m} preferem {y}. Estou usando o que foi dito nesta conversa.', f'{n} prefere {y}; {m} prefere {y}', 'continuação'),
        ]
    elif tipo == 'historias':
        estado = f'personagem: {personagem}'
        historia = f'Ficção: {personagem} encontrou um caminho. O caminho parecia diferente. A viagem começou com uma pergunta. Depois veio uma surpresa. No fim, a personagem decidiu continuar.'
        final = f'Ficção: {personagem} encontrou um amigo. Eles conversaram sobre a viagem. O amigo tinha uma pergunta. A personagem escutou com calma. Os dois continuaram juntos.'
        pares += [
            (f'Inventei uma personagem: {personagem}.', f'Podemos escrever uma história com {personagem}. Que tipo de aventura você quer?', estado, 'continuação'),
            ('Conte uma história de cinco frases usando a personagem.' if validacao else 'Escreva cinco frases de história com a personagem.', historia, estado, 'história'),
            ('O que vem depois?' if validacao else 'Continue a aventura.', f'Ficção: {personagem} seguiu pelo caminho. Uma nova pergunta apareceu. A personagem decidiu pensar antes de continuar.', estado, 'continuação'),
            ('Reescreva o final com um amigo.' if validacao else 'No final, a personagem encontra um amigo.', final, estado + '; final: encontra um amigo', 'corrigir'),
            ('De onde veio esse texto?' if validacao else 'Foi você que fez a história?', 'É uma ficção feita nesta conversa, com a personagem que você informou e meus pesos próprios. Não é um fato do acervo.', estado, 'autoria'),
        ]
    elif tipo == 'continuidade':
        estado = f'{n} quer desenhar; objeto: caderno'
        pares += [
            ('Quero desenhar no meu caderno.', 'Podemos começar com um desenho pequeno. Que ideia você quer colocar no caderno?', estado, 'continuação'),
            (f'Quero desenhar {personagem}.', f'Vamos manter {personagem} como tema. Você prefere começar pela personagem ou pelo lugar?', estado + f'; tema: {personagem}', 'continuação'),
            ('Preciso fazer uma pausa.' if validacao else 'Vou descansar um pouco.', 'Pode fazer uma pausa. Quando voltar, podemos retomar o desenho no caderno.', estado + f'; tema: {personagem}', 'continuação'),
            ('Estou de volta. Qual era a ideia?' if validacao else 'Voltei. O que estávamos fazendo?', f'Estávamos pensando em desenhar {personagem} no seu caderno.', estado + f'; tema: {personagem}', 'continuação'),
            ('Vamos manter essa ideia.' if validacao else 'Quero continuar com o mesmo tema.', f'Vamos continuar com {personagem}. Qual parte do desenho você quer fazer agora?', estado + f'; tema: {personagem}', 'continuação'),
        ]
    elif tipo == 'esclarecimento':
        estado = f'amigas: {n} e {m}; {n} prefere {x}; {m} prefere {y}'
        pares += [
            (f'{n} prefere {x}. {m} prefere {y}.', f'Entendi as duas preferências: {x} para {n}, e {y} para {m}.', estado, 'preferência'),
            ('O que ela prefere?', f'Você está perguntando por {n} ou por {m}? Há duas pessoas no contexto.', estado, 'esclarecimento'),
            (f'Estou falando de {m}.', f'{m} prefere {y}, de acordo com o que você contou.', estado, 'preferência'),
            ('E qual delas não gosta de café?', 'Você ainda não contou essa informação. De qual pessoa quer falar e o que sabe sobre essa preferência?', estado, 'esclarecimento'),
            ('Não quero que você adivinhe.', 'Tudo bem. Vou usar apenas as informações da conversa e perguntar quando houver dúvida.', estado, 'esclarecimento'),
        ]
    else:
        estado = f'{n} quer desenhar; limite: {limite} minutos'
        pares += [
            (f'Tenho {limite} minutos para desenhar.', f'Podemos organizar o desenho dentro de {limite} minutos. Que parte você quer fazer primeiro?', estado, 'continuação'),
            ('Quero começar pela personagem.', 'Vamos começar pela personagem e manter o limite que você informou. Qual personagem quer desenhar?', estado, 'continuação'),
            (f'Vou desenhar {personagem}.', f'O tema do desenho é {personagem}. Podemos fazer um rascunho antes dos detalhes.', estado + f'; tema: {personagem}', 'continuação'),
            ('Não ultrapasse o tempo que eu disse.' if validacao else 'Lembre do meu limite de tempo.', f'O limite continua sendo {limite} minutos. Podemos deixar os detalhes para outra conversa.', estado + f'; tema: {personagem}', 'continuação'),
            ('E se eu preferir parar agora?' if validacao else 'Vou parar por aqui.', f'Podemos parar. Se quiser retomar depois, o tema era {personagem}, com limite de {limite} minutos.', estado + f'; tema: {personagem}', 'continuação'),
        ]
    return pares


def condicionar(mensagem, historico, fatos='', ato=''):
    # Só serializa o estado já fornecido; não coleta nem infere memória nova.
    contexto = list(historico[-3:])
    if fatos or ato:
        contexto.append({'papel': 'usuario', 'texto': f'Fatos atuais da sessão: {fatos}. Tipo de pedido: {ato}.'})
    return {'mensagem': mensagem, 'historico': contexto}


def corpus():
    tipos = ['capacidades', 'preferencias', 'historias', 'continuidade', 'esclarecimento', 'tempo']
    treino_alimentos = ['pera', 'aveia', 'tomate', 'melancia', 'batata', 'morango', 'pão', 'chá']
    validacao_alimentos = ['caju', 'jabuticaba', 'cenoura', 'erva-doce']
    treino_personagens = ['uma lontra viajante', 'um coelho leitor', 'um pássaro pintor', 'um peixe músico']
    validacao_personagens = ['uma raposa jardineira', 'um texugo aprendiz']
    exemplos = []
    for t, tipo in enumerate(tipos):
        for i in range(80):
            validacao = i >= 64
            split = 'validacao' if validacao else 'treino'
            alimentos = validacao_alimentos if validacao else treino_alimentos
            personagens = validacao_personagens if validacao else treino_personagens
            n, m = nome(t * 80 + i), nome(t * 80 + i + 480)
            x, y = alimentos[i % len(alimentos)], alimentos[(i + 1) % len(alimentos)]
            personagem = personagens[i % len(personagens)]
            limite = 41 + i
            historico = []
            dialogo = f'{tipo}-{i:03d}'
            for turno, (mensagem, resposta, fatos, ato) in enumerate(demonstracao(tipo, n, m, x, y, personagem, limite, validacao)):
                fatos = f'pessoa: {n}; {fatos}'
                contexto = condicionar(mensagem, historico, fatos, ato)
                exemplos.append({'id': f'{dialogo}-{turno}', 'id_dialogo': dialogo,
                                 'familia': tipo + ('-parafrase-validacao' if validacao else '-demonstracao-treino'),
                                 'split': split, 'contexto': contexto, 'fatos_sessao': fatos, 'ato': ato,
                                 'resposta': resposta, 'origem': 'sintético autoral, combinador escrito à mão'})
                historico += [{'papel': 'usuario', 'texto': mensagem}, {'papel': 'assistente', 'texto': resposta}]
    frozen = json.loads((H / 'casos_congelados.json').read_text())
    entradas = {c['entrada']['texto'] for c in frozen['casos']}
    assert not entradas & {e['contexto']['mensagem'] for e in exemplos}
    assert len(exemplos) == 2880
    escrever('corpus.json', {'versao': 1, 'origem': 'Demonstrações sintéticas autorais; não são sessões do dono nem conversas humanas.',
                            'fontes_externas': False, 'dialogos': 480, 'turnos_usuario_assistente': 5760,
                            'exemplos': exemplos})


if __name__ == '__main__':
    congelar()
    corpus()
    print('Congelados 37 casos reais; corpus autoral: 480 diálogos, 5760 turnos, 2880 respostas alvo.')
