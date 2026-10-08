"""Diálogos sintéticos autorais com alvos de cópia e proveniência.

Não lê controles antigos, exemplos humanos, conversas privadas ou pesos.
As formas linguísticas são separadas por split; não há avaliação independente.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random

FAMILIAS = ['correcao', 'referencia', 'requisitos', 'comparacao', 'duracao',
            'objetivo_restricao', 'esclarecimento']
OPERACOES = ['comparar_custos', 'tempo_restante', 'consultar_valor',
             'verificar_requisitos', 'resumir_objetivos', 'esclarecer']
CLASSES = ['outro', 'custos', 'tempo', 'agenda', 'regra']
NOMES = {
 'treino': ['Ana', 'Beto', 'Dora', 'Leo', 'Iara', 'Caio', 'Rui', 'Lia'],
 'dev': ['Vera', 'Tito', 'Lena', 'Bruno'],
 'teste': ['Nair', 'Zeca', 'Mila', 'Davi'],
}
# Bancos independentes escritos antes do treino. Cada frase é autoral/sintética,
# não representa uma conversa humana real. Números novos não são paráfrases.
PERGUNTAS = {
 'treino': {
 'custos': ['Qual opção custa menos?', 'Compare os custos das opções.',
            'Qual é mais barata e qual a diferença?', 'Entre as opções, onde gasto menos?',
            'Quero a diferença dos valores e a opção econômica.', 'Há empate nos preços?'],
 'tempo': ['Quanto tempo sobra?', 'Tudo cabe no tempo disponível?',
           'Calcule o saldo de minutos.', 'Termino as atividades com esse tempo?',
           'Quantos minutos restam depois das tarefas?', 'Falta tempo para o plano?'],
 'valor': ['Quantos minutos {n} tem?', 'Qual é o tempo disponível de {n}?',
           'Retome o valor de minutos de {n}.', 'Quanto tempo foi reservado por {n}?',
           'Diga o limite de tempo de {n}.', 'Lembre os minutos disponíveis de {n}.'],
 'regra': ['Cumpre os requisitos?', 'Pode entrar pela regra informada?',
          'Essas condições foram satisfeitas?', 'Os objetos permitem a entrada?',
          'Confira se atende à regra.', 'Falta algum requisito para entrar?'],
 'objetivo': ['Resuma meu objetivo e meu limite.', 'O que quero e o que me impede?',
             'Lembre minha intenção e a restrição.', 'Organize o objetivo com a condição.',
             'Retome o que busco e o limite informado.', 'Qual é o objetivo com essa restrição?'],
 'ambiguo': ['Quanto tempo ele tem?', 'Qual é o valor dele?', 'Retome os minutos dele.',
             'Quem tem o tempo que pedi?', 'O que ele reservou de tempo?', 'Quanto sobrou para ele?'],
 },
 'dev': {
 'custos': ['Qual escolha reduz minha despesa e por quanto?', 'Compare o desembolso das duas opções.'],
 'tempo': ['Após cumprir o plano, qual é a folga?', 'A janela disponível comporta as tarefas?'],
 'valor': ['Qual disponibilidade em minutos pertence a {n}?', 'Recupere o tempo que {n} informou.'],
 'regra': ['Os requisitos declarados autorizam a entrada?', 'Essa pessoa reúne as condições de ingresso?'],
 'objetivo': ['Recapitule minha meta junto da limitação.', 'Conserve a intenção e a dificuldade no resumo.'],
 'ambiguo': ['Quantos minutos cabem na agenda dele?', 'Que tempo disponível pertence a ele?'],
 },
 'teste': {
 'custos': ['Ao olhar os gastos finais, qual opção poupa dinheiro e quanto?',
            'Diga se há diferença entre as despesas e quem leva vantagem.',
            'Qual alternativa exige menos dinheiro, considerando os valores?'],
 'tempo': ['Se eu executar as tarefas, termino antes do fim dos minutos livres?',
           'Mostre a diferença entre os minutos livres e os necessários.',
           'Depois desse plano, fico com tempo de sobra ou em falta?'],
 'valor': ['Volte ao número de minutos que {n} declarou.',
           'Sobre {n}: quanto tempo foi dito que tinha?',
           'Na conversa, qual era a disponibilidade de {n}?'],
 'regra': ['Com o que foi dito sobre os objetos, a entrada está liberada?',
          'A situação atual satisfaz o que é exigido para entrar?',
          'Considerando a regra e os itens, consegue ingressar?'],
 'objetivo': ['Junte num resumo o que pretendo e o que limita isso.',
             'O que estou tentando fazer e qual dificuldade mencionei?',
             'Sem escolher por mim, recupere minha intenção e a condição.'],
 'ambiguo': ['Qual tempo disponível foi atribuído a ele?',
             'Você lembra quanto ele teria de tempo?',
             'Diga quantos minutos eram dele.'],
 },
}
OBJETIVOS = {'treino': ['estudar música', 'aprender desenho', 'ler mais', 'cuidar do jardim',
                        'fazer exercícios', 'praticar escrita', 'organizar a casa', 'aprender piano'],
             'dev': ['aprender fotografia', 'voltar a estudar', 'praticar corrida'],
             'teste': ['aprender cerâmica', 'montar uma horta', 'praticar violão']}
LIMITES = {'treino': ['pouco tempo livre', 'dinheiro limitado', 'horário de trabalho',
                      'falta de espaço', 'viagem marcada', 'aulas à noite'],
           'dev': ['um compromisso de manhã', 'uma despesa fixa', 'um turno novo'],
           'teste': ['plantão aos sábados', 'orçamento reduzido', 'uma mudança marcada']}
OBJETOS = {'treino': ['chave', 'selo', 'ticket', 'senha', 'mapa', 'cartão', 'ficha', 'medalha'],
           'dev': ['convite', 'pulseira', 'crachá', 'documento'],
           'teste': ['licença', 'insígnia', 'bilhete', 'emblema']}


def escrever(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


class Sessao:
    def __init__(self, ident, familia, split):
        self.id, self.familia, self.split = ident, familia, split
        self.turnos = []
        self.spans = []

    def fala(self, partes):
        """Partes (chave, literal) anotam somente suportes, fora da entrada."""
        texto = ''; registros = {}
        for p in partes:
            if isinstance(p, tuple):
                k, literal = p; inicio = len(texto); texto += literal
                registros[k] = {'turno': len(self.turnos), 'inicio': inicio,
                                'fim': len(texto), 'texto': literal}
            else:
                texto += p
        self.turnos.append(texto); self.spans.append(registros)
        return registros

    def exemplo(self, op, argumentos=(), referente=None, hipotese=False):
        args = list(argumentos) + [None] * (3 - len(argumentos))
        return {'sessao': self.id, 'familia': self.familia, 'etapa': len(self.turnos)-1,
                'turnos': list(self.turnos), 'operacao': op, 'argumentos': args,
                'referente': referente, 'hipotese': hipotese,
                'classe': {'comparar_custos': 'custos', 'tempo_restante': 'tempo',
                           'verificar_requisitos': 'regra'}.get(op, 'outro')}


def construir(split, indice):
    rng = random.Random({'treino': 4821, 'dev': 7351, 'teste': 9839}[split] + indice*104729)
    familia = FAMILIAS[indice % len(FAMILIAS)]
    s = Sessao(split + '-' + str(indice), familia, split)
    ns = rng.sample(NOMES[split], 2)
    if familia == 'esclarecimento':
        ns = rng.sample({'treino':['Beto','Leo','Caio','Rui'], 'dev':['Tito','Bruno'], 'teste':['Zeca','Davi']}[split], 2)
    vals = rng.sample(range(10, 100) if split != 'teste' else range(101, 180), 6)
    x, y, z, w, j, k = vals
    def q(tipo, etapa=0, nome=None):
        ts = PERGUNTAS[split][tipo]
        return ts[(indice + etapa) % len(ts)].format(n=nome or ns[0])
    out = []
    if familia in ('correcao', 'comparacao'):
        a = s.fala(['A opção A custa ', ('a', str(x)), ' reais. A opção B custa ',
                    ('b', str(y)), ' reais. ', q('custos')])
        out.append(s.exemplo('comparar_custos', [a['a'], a['b']]))
        b = s.fala(['Corrijo o preço da opção A: agora custa ', ('a', str(z)), ' reais. ', q('custos', 1)])
        out.append(s.exemplo('comparar_custos', [b['a'], a['b']]))
        c = s.fala(['E se a opção B custasse ', ('b', str(w)), ' reais, só como hipótese? ', q('custos', 2)])
        out.append(s.exemplo('comparar_custos', [b['a'], c['b']], hipotese=True))
        d = s.fala(['Volte aos preços reais; a hipótese não aconteceu. ', q('custos', 3)])
        out.append(s.exemplo('comparar_custos', [b['a'], a['b']]))
    elif familia == 'duracao':
        a = s.fala(['Tenho ', ('livre', str(x)), ' minutos livres. A leitura leva ',
                    ('t1', str(y)), ' minutos e o treino leva ', ('t2', str(z)), ' minutos. ', q('tempo')])
        out.append(s.exemplo('tempo_restante', [a['livre'], a['t1'], a['t2']]))
        b = s.fala(['Corrijo a leitura: leva ', ('t1', str(w)), ' minutos. ', q('tempo', 1)])
        out.append(s.exemplo('tempo_restante', [a['livre'], b['t1'], a['t2']]))
        c = s.fala(['Se eu tivesse ', ('livre', str(j)), ' minutos livres, numa hipótese, ', q('tempo', 2)])
        out.append(s.exemplo('tempo_restante', [c['livre'], b['t1'], a['t2']], hipotese=True))
        s.fala(['Desconsidere a hipótese e use meu tempo real. ', q('tempo', 3)])
        out.append(s.exemplo('tempo_restante', [a['livre'], b['t1'], a['t2']]))
    elif familia == 'referencia':
        a = s.fala([('n1', ns[0]), ' tem ', ('v1', str(x)), ' minutos livres. ',
                    ('n2', ns[1]), ' tem ', ('v2', str(y)), ' minutos livres. ', q('valor', nome=ns[0])])
        out.append(s.exemplo('consultar_valor', [a['v1']], a['n1']))
        b = s.fala(['Sobre ', ('n', ns[1]), ': o tempo livre agora é ', ('v', str(z)), ' minutos. ', q('valor', 1, ns[1])])
        out.append(s.exemplo('consultar_valor', [b['v']], a['n2']))
        s.fala(['A pessoa mencionada por último, quantos minutos livres tem?'])
        out.append(s.exemplo('consultar_valor', [b['v']], a['n2']))
        s.fala(['Volte à primeira pessoa que citei. ', q('valor', 3, ns[0])])
        out.append(s.exemplo('consultar_valor', [a['v1']], a['n1']))
    elif familia == 'requisitos':
        ob1, ob2 = rng.sample(OBJETOS[split], 2)
        a = s.fala(['Para entrar são exigidos ', ('regra', ob1+' e '+ob2), '. ', ('n', ns[0]),
                    ' ', ('posse', 'tem '+ob2+' e não tem '+ob1), '. ', q('regra')])
        out.append(s.exemplo('verificar_requisitos', [a['regra'], a['posse']], a['n']))
        b = s.fala([ns[0], ' ganhou '+ob1+'; agora ', ('posse', 'tem '+ob1+' e '+ob2), '. ', q('regra', 1)])
        out.append(s.exemplo('verificar_requisitos', [a['regra'], b['posse']], a['n']))
        c = s.fala(['Só no cenário imaginado, ', ns[0], ' ', ('posse', 'tem '+ob1+' e não tem '+ob2), '. ', q('regra', 2)])
        out.append(s.exemplo('verificar_requisitos', [a['regra'], c['posse']], a['n'], True))
        s.fala(['A situação imaginada não ocorreu; use os objetos reais. ', q('regra', 3)])
        out.append(s.exemplo('verificar_requisitos', [a['regra'], b['posse']], a['n']))
    elif familia == 'objetivo_restricao':
        go, alt = rng.sample(OBJETIVOS[split], 2)
        lim = rng.choice(LIMITES[split])
        a = s.fala([('n', 'Eu'), ' quero ', ('objetivo', go), ', mas tenho ', ('limite', lim), '. ', q('objetivo')])
        out.append(s.exemplo('resumir_objetivos', [a['objetivo'], a['limite']], a['n']))
        b = s.fala(['Mudei meu objetivo: agora quero ', ('objetivo', alt), '. ', q('objetivo', 1)])
        out.append(s.exemplo('resumir_objetivos', [b['objetivo'], a['limite']], a['n']))
        c = s.fala(['E se meu objetivo fosse ', ('objetivo', go), ', somente numa hipótese? ', q('objetivo', 2)])
        out.append(s.exemplo('resumir_objetivos', [c['objetivo'], a['limite']], a['n'], True))
        s.fala(['Retire a hipótese; mantenha o objetivo que corrigi. ', q('objetivo', 3)])
        out.append(s.exemplo('resumir_objetivos', [b['objetivo'], a['limite']], a['n']))
    else:
        # Dois sujeitos igualmente possíveis. Uma pergunta não cria fatos.
        s.fala([ns[0], ' tem ', str(x), ' minutos e ', ns[1], ' tem ', str(y), ' minutos. ', q('ambiguo')])
        out.append(s.exemplo('esclarecer'))
        s.fala(['Não escolhi qual pessoa. ', q('ambiguo', 1)])
        out.append(s.exemplo('esclarecer'))
        s.fala(['Há duas pessoas na conversa. ', q('ambiguo', 2)])
        out.append(s.exemplo('esclarecer'))
        s.fala(['Ainda não disse o nome. ', q('ambiguo', 3)])
        out.append(s.exemplo('esclarecer'))
    return out


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('saida', type=Path)
    parser.add_argument('--tokenizer', type=Path, required=True)
    args = parser.parse_args(); args.saida.mkdir(parents=True, exist_ok=False)
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(str(args.tokenizer)); tok.encode_special_tokens = True
    dados = {}; stats = {}
    for split, n in [('treino', 750), ('dev', 75), ('teste', 100)]:
        exemplos = []; vistos = set(); rejeitados = 0
        for i in range(n):
            indice = i
            while True:
                sessao = construir(split, indice)
                textos_s = ['\n'.join(e['turnos']) for e in sessao]
                if not any(t in vistos for t in textos_s):
                    break
                rejeitados += 1; indice += 7 * 10000
                if rejeitados > n * 500:
                    raise ValueError('Banco insuficiente para diversidade; não inflar contagem com IDs.')
            exemplos.extend(sessao); vistos.update(textos_s)
        textos = ['\n'.join(e['turnos']) for e in exemplos]
        # Questões ambíguas e objetivos sem números podem repetir. Acrescentar
        # números só para inflar unicidade não resolve: regenerar cenários.
        unicos = set(textos)
        if len(unicos) != len(textos):
            raise ValueError('Há diálogo literal repetido em ' + split)
        tamanhos = [sum(len(tok.encode(t, add_special_tokens=False).ids)+2 for t in e['turnos'])+1 for e in exemplos]
        if max(tamanhos) > 256:
            raise ValueError('Diálogo inteiro ultrapassou 256 tokens em '+split+': '+str(max(tamanhos)))
        for e in exemplos:
            for s in e['argumentos'] + [e['referente']]:
                if s:
                    assert e['turnos'][s['turno']][s['inicio']:s['fim']] == s['texto']
        dados[split] = exemplos
        stats[split] = dict(exemplos=len(exemplos), entradas_distintas=len(unicos),
            sessoes=n, cenarios_rejeitados_por_repeticao=rejeitados,
            tokens_entrada=sum(tamanhos), max_contexto=max(tamanhos),
            familias={f:sum(e['familia']==f for e in exemplos) for f in FAMILIAS},
            formas_pergunta=sum(len(v) for v in PERGUNTAS[split].values()))
        escrever(args.saida/(split+'.json'), exemplos)
    assert not(set('\n'.join(e['turnos']) for e in dados['treino']) & set('\n'.join(e['turnos']) for e in dados['dev']+dados['teste']))
    assert not(set('\n'.join(e['turnos']) for e in dados['dev']) & set('\n'.join(e['turnos']) for e in dados['teste']))
    escrever(args.saida/'manifesto.json', dict(versao=1, estatisticas=stats,
        fontes='Diálogos sintéticos autorais produzidos por corpus.py; nenhum dado privado, modelo externo ou controle anterior.',
        limite='Textos distintos variam entidades/números/objetivos em um número limitado de formas. Não são 3.000 formulações humanas nem avaliação independente. Atualizações e hipóteses usam molduras compartilhadas entre splits; só perguntas/nome/valores lexicais estão reservados.',
        sha256={s:hashlib.sha256((args.saida/(s+'.json')).read_bytes()).hexdigest() for s in dados},
        codigo_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
