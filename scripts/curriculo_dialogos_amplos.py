"""Diálogos autorais com relações verificáveis, separados por cenário completo.

Nenhuma saída do modelo ou sonda de avaliação entra aqui. Exercícios calculados
continuam sendo sintéticos, não pessoas novas nem prova de conversa geral.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARQUIVO = ROOT / 'dados/dialogos_amplos_autorais.json'


def particao_cenario(grupo):
    bucket = int(hashlib.sha256(('crivo-dialogos-amplos-v2:' + grupo).encode()).hexdigest()[:8], 16) % 10
    return 'validacao' if bucket == 0 else 'teste' if bucket == 1 else 'treino'


def pares_conversa(grupo, familia, turnos, split=None):
    if not turnos or len(turnos) % 2:
        raise ValueError('Conversa exige pares completos')
    historico = []
    for i in range(0, len(turnos), 2):
        q, a = turnos[i:i + 2]
        if q['papel'] != 'usuario' or a['papel'] != 'assistente' or not q['texto'].strip() or not a['texto'].strip():
            raise ValueError('Papéis ou textos inválidos')
        ident = hashlib.sha256(json.dumps([grupo, i, q, a], ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        yield dict(mensagem=q['texto'], resposta=a['texto'], historico=list(historico),
                   grupo=grupo, source_id='autoral:' + ident, familia=familia,
                   split=split or particao_cenario(grupo), origem='sintetico_autoral_assistente')
        historico.extend([q, a])


def exemplos_amplos():
    dados = json.loads(ARQUIVO.read_text(encoding='utf-8'))
    grupos = set()
    for c in dados['conversas']:
        grupo = 'autoral:' + c['id']
        if grupo in grupos:
            raise ValueError('ID de conversa duplicado')
        grupos.add(grupo)
        yield from pares_conversa(grupo, c['familia'], c['turnos'])
    # O número muda o problema, a conclusão e os turnos posteriores, não apenas
    # o prefixo da pergunta. Toda a trajetória de um cenário fica no mesmo split.
    for n in range(180):
        def conversa(familia, *pares):
            turnos = [dict(papel=p, texto=t) for q, a in pares
                      for p, t in (('usuario', q), ('assistente', a))]
            return pares_conversa(f'calculado:{familia}:{n}', familia, turnos)
        tempo = 30 + n
        revisao = 5 + n % 9
        exercicio = 8 + n % 7
        restantes = tempo - revisao
        quantidade, sobra = divmod(restantes, exercicio)
        yield from conversa('planejamento',
            (f'Tenho {tempo} minutos para estudar. Quero revisar por {revisao} minutos e cada exercício leva {exercicio}. Quantos cabem?',
             f'Cabem {quantidade} exercícios completos. Depois da revisão restam {restantes} minutos; os exercícios usam {quantidade * exercicio} e sobram {sobra}.'),
            ('E se eu perder dez minutos antes de começar?',
             f'O tempo total cai para {tempo - 10} minutos. Mantendo a revisão de {revisao}, restam {restantes - 10}; cabem {(restantes - 10) // exercicio} exercícios completos.'),
            ('A revisão foi cancelada. Use o tempo reduzido só para exercícios.',
             f'Sem revisão, os {tempo - 10} minutos disponíveis comportam {(tempo - 10) // exercicio} exercícios de {exercicio} minutos, com {(tempo - 10) % exercicio} minutos restantes.'))
        preco_a, preco_b = 40 + n, 55 + n
        prazo_a, prazo_b = 4 + n % 4, 1 + n % 3
        yield from conversa('decisao',
            (f'A oferta A custa {preco_a} reais e chega em {prazo_a} dias. B custa {preco_b} e chega em {prazo_b}. Quero gastar menos.',
             f'A oferta A é a mais barata: {preco_a} reais, {preco_b - preco_a} a menos que B. Seu prazo é de {prazo_a} dias.'),
            (f'Agora preciso receber em no máximo {prazo_b} dias. Qual atende?',
             f'B atende ao prazo de {prazo_b} dias. A leva {prazo_a}, portanto não atende ao limite, apesar de custar menos.'),
            (f'Tenho apenas {preco_b - 1} reais e o prazo continua igual.',
             f'Nenhuma das duas atende às duas condições: A demora {prazo_a} dias e B custa {preco_b} reais, acima do orçamento de {preco_b - 1}.'))
        minimo, pontos = 12 + n, 11 + n
        yield from conversa('raciocinio',
            (f'No desafio, posso entrar se tiver pelo menos {minimo} pontos e uma autorização. Tenho {pontos} pontos e autorização. Entro?',
             f'Não. Você tem autorização, mas {pontos} é menor que o mínimo de {minimo} pontos. Falta um ponto.'),
            ('Ganhei dois pontos. E agora?',
             f'Agora você tem {pontos + 2} pontos. Como mantém a autorização e supera o mínimo de {minimo}, as duas condições estão satisfeitas.'),
            ('A autorização foi retirada; os pontos continuam.',
             f'Os {pontos + 2} pontos bastam para o requisito numérico, mas sem autorização você não pode entrar pela regra informada.'))
        livro, caderno = 10 + n, 20 + n
        novo = 30 + n
        yield from conversa('memoria',
            (f'Anote neste exemplo: o livro tem {livro} páginas e o caderno tem {caderno}.',
             f'No exemplo, são {livro} páginas no livro e {caderno} no caderno.'),
            (f'Corrigindo só o livro: são {novo} páginas.',
             f'O livro passa a ter {novo} páginas. O caderno continua com {caderno}.'),
            ('Qual é a soma atual e qual informação mudou?',
             f'A soma atual é {novo + caderno} páginas. Mudou o livro, de {livro} para {novo}; o caderno permaneceu com {caderno}.'))
        produzidos, consumidos = 20 + n, 15 + n
        yield from conversa('diagnostico',
            (f'Em cada minuto entram {produzidos} tarefas e são concluídas {consumidos}. A fila cresce. O que esses números explicam?',
             f'Entram {produzidos - consumidos} tarefas a mais por minuto do que saem. Sem outra mudança, essa diferença explica o crescimento da fila; não prova um vazamento de memória.'),
            ('Parei a entrada por dois minutos. A fila tinha cem tarefas. Quantas podem restar?',
             f'Se o ritmo de conclusão permanecer em {consumidos} por minuto, dois minutos permitem concluir até {consumidos * 2}. De cem tarefas, restariam {max(0, 100 - consumidos * 2)}.'),
            ('Isso prova que não existe outro problema?',
             f'Não. A diferença entre entrada de {produzidos} e saída de {consumidos} explica um acúmulo, mas não descarta outros problemas. Precisamos observar fila e memória durante o teste.'))
        inicial, adicao, retirada = 20 + n, 7 + n % 5, 3 + n % 4
        final = inicial + adicao - retirada
        yield from conversa('resumo',
            (f'Registro: havia {inicial} caixas. Chegaram mais {adicao} e saíram {retirada}. Resuma com o saldo.',
             f'Começou com {inicial} caixas, recebeu {adicao} e retirou {retirada}, terminando com {final}.'),
            ('Podemos afirmar que todas foram vendidas?',
             f'Não. O registro explica entradas e saídas, mas não diz que a saída de {retirada} caixas foi uma venda.'),
            ('Qual era a quantidade antes de sair alguma?',
             f'Antes da retirada havia {inicial + adicao} caixas: {inicial} iniciais mais {adicao} recebidas.'))
        arr = [n - 3, n + 1, n + 5]
        dobro = [x * 2 for x in arr]
        filtrados = [x for x in arr if x > n]
        yield from conversa('programacao',
            (f'Em JavaScript, a lista é {arr}. Qual é o resultado de lista.map(x => x * 2)?',
             f'O resultado é {dobro}. map aplica a multiplicação a cada elemento e mantém três posições.'),
            (f'E lista.filter(x => x > {n}), usando a lista original?',
             f'O resultado é {filtrados}. Só entram os valores maiores que {n}; a condição seleciona elementos, em vez de transformá-los.'),
            ('Essas duas operações alteram os números do array original neste exemplo?',
             f'Não. Essas callbacks retornam valores sem alterar a origem. O array original continua sendo {arr}.'))
        temperatura, limite = 10 + n, 11 + n
        yield from conversa('hipotese',
            (f'Num cenário imaginado, o alarme liga sempre acima de {limite} graus e fica desligado nos outros casos. O sensor marca {temperatura}. Ele liga?',
             f'Não. Nesse cenário, {temperatura} graus está abaixo do limite de {limite}.'),
            (f'Imagine agora que a leitura seja exatamente {limite}.',
             f'Também não liga: a regra exige acima de {limite}, e não igual ao limite.'),
            ('Aumente a última leitura em dois graus.',
             f'A leitura hipotética passa a ser {limite + 2} graus. Como supera {limite}, o alarme liga pela regra informada.'))
        nomes = ['azul', 'verde', 'amarelo', 'roxo', 'laranja', 'branco']
        cor = nomes[n % len(nomes)]
        fora = nomes[(n + 1) % len(nomes)]
        limite_itens = 3 + n % 8
        yield from conversa('restricao',
            (f'No catálogo {n + 100}, use a cor {cor} e no máximo {limite_itens} itens. Depois alguém sugeriu usar {fora}. O que vale?',
             f'A sugestão não muda a escolha confirmada: no catálogo {n + 100}, vale {cor}, com no máximo {limite_itens} itens.'),
            (f'Confirmo agora a mudança para {fora}. Mantenha a quantidade.',
             f'A cor do catálogo {n + 100} passa a ser {fora}. O limite permanece em {limite_itens} itens.'))
    # Fatos em formas diferentes, com fonte registrada; sem nomes de componentes
    # inventados substituindo a conversa natural nem recombinação de funções.
    from scripts.preparar_conversa_gerativa import FATOS
    formas = ['Por que {e} é importante?', 'O que {e} faz na prática?',
              'Explique a relação entre {e} e o funcionamento do sistema.',
              'Se eu precisar explicar {e}, qual função devo destacar?']
    for e, f, r, fonte in FATOS:
        for i, q in enumerate(formas):
            turnos = [dict(papel='usuario', texto=q.format(e=e)),
                      dict(papel='assistente', texto=f'{e[0].upper()+e[1:]} atua para {f}. Isso contribui para {r}.')]
            for ex in pares_conversa('fato_amplo:' + e, 'compreensao', turnos, 'treino'):
                ex['fonte'] = fonte
                ex['source_id'] += ':' + str(i)
                yield ex
