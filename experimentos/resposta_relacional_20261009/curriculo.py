"""Trajetórias procedurais autorais: relações diferentes, não humanos novos.

Não lê sondas nem respostas do Crivo. Todas as respostas são especificadas
por regras locais, revisáveis, sem modelo/API externa. Não prova diálogo livre.
"""
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from linguagem_profunda import carregar
from scripts.curriculo_dialogos_amplos import pares_conversa


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def salvar(p, d):
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')


def conversa(familia, ident, pares, split):
    return {'id': ident, 'familia': familia, 'split': split,
            'turnos': [{'papel': papel, 'texto': texto}
                       for q, a in pares
                       for papel, texto in (('usuario', q), ('assistente', a))]}


def gerar():
    nomes = ['Mara', 'Ivo', 'Cora', 'Beto', 'Nara', 'Davi', 'Rui', 'Eva']
    objetos = ['pasta', 'caixa', 'bolsa', 'capa', 'caneca', 'camisa', 'toalha', 'tigela']
    cores = ['verde', 'azul', 'amarela', 'branca', 'vermelha', 'preta', 'roxa', 'cinza']
    atividades = ['pintura', 'leitura', 'corrida', 'costura', 'música', 'jardinagem', 'cerâmica', 'escrita']
    rng = random.Random(20261009)
    for i in range(360):
        # Hash de trajetória, não de turno. Permutações de léxico NÃO são
        # consideradas cenários humanos distintos nem teste independente.
        # Incluir os dois ramos de cada contraste na validação. Reservar
        # apenas números pares selecionaria sempre confirmação/autorização.
        split = 'validacao' if i % 60 in (0, 1) else 'treino'
        n, outro = rng.sample(nomes, 2)
        ob, ob2 = rng.sample(objetos, 2)
        c1, c2, c3 = rng.sample(cores, 3)
        at, at2, at3 = rng.sample(atividades, 3)
        def add(f, pares):
            return conversa(f, f'{f}:{i}', pares, split)
        yield add('vinculo', [
            (f'A {ob} de {n} é {c1}. A de {outro} é {c2}.',
             f'As cores são {c1} para {n} e {c2} para {outro}.'),
            (f'{n} também tem uma {ob2}. Não informei a cor dela.',
             f'A cor da {ob2} de {n} ainda não foi informada.'),
            (f'Qual cor pertence à {ob} de {outro}?',
             f'A {ob} de {outro} é {c2}.'),
            (f'Agora diga a cor da {ob2} de {n}, sem inventar.',
             f'Não sei: você não informou a cor da {ob2} de {n}.')])
        # Metade confirma a informação antiga; metade a altera. Assim a
        # presença de "corrigindo" não basta para aprender a resposta.
        atual = c1 if i % 2 else c3
        yield add('correcao', [
            (f'Minha {ob} é {c1}.', f'Você informou que sua {ob} é {c1}.'),
            (f'Corrigindo: minha {ob} é {atual}.', f'A informação atual é {atual} para sua {ob}.'),
            (f'{outro} disse que a {ob} dele é {c2}.', f'Isso descreve a {ob} de {outro}, não a sua.'),
            ('Qual é a cor da minha agora?', f'Sua {ob} é {atual}. O relato de {outro} não altera sua informação.')])
        pos = i % 3
        ordinal = ['primeira', 'segunda', 'terceira'][pos]
        escolhido = [at, at2, at3][pos]
        outra_pos = (pos + 1) % 3
        yield add('referencia', [
            (f'As opções, nessa ordem, são {at}, {at2} e {at3}.', f'Entendi a ordem: {at}, {at2} e {at3}.'),
            (f'A {ordinal} depende de uma autorização.', f'A opção {escolhido} depende de autorização.'),
            (f'A { ["primeira", "segunda", "terceira"][outra_pos]} já está disponível.',
             f'A opção {[at, at2, at3][outra_pos]} já está disponível.'),
            ('Qual delas ainda depende de autorização?', f'{escolhido} ainda depende de autorização.')])
        confirmado = i % 2 == 0
        sentimento, outro_estado = rng.choice([
            ('triste', 'concentrado'), ('irritado', 'cansado'),
            ('preocupado', 'atento'), ('animado', 'distraído')])
        if outro in ('Mara', 'Cora', 'Nara', 'Eva'):
            sentimento = sentimento[:-1] + 'a' if sentimento.endswith('o') else sentimento
            outro_estado = outro_estado[:-1] + 'a' if outro_estado.endswith('o') else outro_estado
        observacao = rng.choice(['ficou em silêncio', 'saiu cedo', 'olhou para o chão', 'fechou o caderno'])
        yield add('hipotese', [
            (f'Acho que {outro} ficou {sentimento}, mas não tenho confirmação.', f'Isso é uma hipótese sobre {outro}, ainda não confirmada.'),
            (f'A única observação é que {outro} {observacao}.', f'Você observou que {outro} {observacao}; isso não confirma sozinho que estava {sentimento}.'),
            (f'{outro} confirmou que estava {sentimento}.' if confirmado else f'{outro} disse que não estava {sentimento}; estava {outro_estado}.',
             f'Agora {outro} confirmou que estava {sentimento}.' if confirmado else f'{outro} negou que estava {sentimento} e relatou que estava {outro_estado}.'),
            ('O que posso concluir sobre o motivo desse comportamento?',
             f'{outro} confirmou que estava {sentimento}, mas não confirmou a causa do comportamento.' if confirmado else f'{outro} relatou que estava {outro_estado} e negou que estava {sentimento}. O comportamento não prova a hipótese inicial.')])
        liberado = i % 2 == 0
        yield add('condicao', [
            (f'Posso fazer {at} agora. {at2} depende de uma autorização.', f'{at} está disponível; {at2} depende de autorização.'),
            (f'Ainda não pedi a autorização para {at2}.', f'Então a condição para {at2} ainda não foi atendida.'),
            (f'Recebi autorização para {at2}.' if liberado else f'A autorização para {at2} foi negada.',
             f'A condição para {at2} foi atendida.' if liberado else f'{at2} continua indisponível, pois a autorização foi negada.'),
            ('Quais opções estão disponíveis agora?', f'Agora {at} e {at2} estão disponíveis.' if liberado else f'Apenas {at} está disponível agora. A opção {at2} não foi autorizada.')])
        mudou = i % 2 == 0
        yield add('intencao', [
            (f'Quero escrever uma mensagem sobre {at}.', f'Você quer escrever uma mensagem sobre {at}.'),
            (f'Corrigindo: não quero enviar mensagem; quero conversar sobre {at}.' if mudou else f'Confirmo: quero uma mensagem curta sobre {at}.',
             f'O pedido agora é conversar sobre {at}, sem redigir mensagem.' if mudou else f'O pedido continua sendo uma mensagem curta sobre {at}.'),
            (f'{outro} prefere falar sobre {at2}, mas eu mantenho meu pedido.', f'A preferência de {outro} não substitui seu pedido sobre {at}.'),
            ('Qual tarefa eu pedi?', f'Você pediu uma conversa sobre {at}, não uma mensagem para enviar.' if mudou else f'Você pediu uma mensagem curta sobre {at}.')])


def codificar(tok, e):
    seq = []
    for t in e['historico'] + [{'papel': 'usuario', 'texto': e['mensagem']}]:
        seq += [tok.token_to_id('<' + t['papel'] + '>')] + tok.encode(t['texto']).ids + [tok.token_to_id('<fim>')]
    seq += [tok.token_to_id('<assistente>')]
    inicio = len(seq)
    seq += tok.encode(e['resposta']).ids + [tok.token_to_id('<fim>')]
    if len(seq) > 256:
        raise ValueError('Exemplo completo excede 256 tokens; não cortar.')
    y = [-100] * (len(seq) - 1)
    for j in range(inicio - 1, len(y)):
        y[j] = seq[j + 1]
    return {'x': seq[:-1], 'y': y, 'exemplo': e}


if __name__ == '__main__':
    out = Path(__file__).parent / 'dados'
    out.mkdir(exist_ok=False)
    _, tok, _ = carregar(ROOT / 'artefatos/linguagem_profunda')
    conjuntos = {'treino': [], 'validacao': []}
    trajetorias = list(gerar())
    for c in trajetorias:
        for e in pares_conversa('relacional:' + c['id'], c['familia'], c['turnos'], c['split']):
            codificar(tok, e)
            conjuntos[c['split']].append(e)
    # Uma trajetória lexical pode reaparecer nas permutações. Deduplicar
    # entradas entre splits, priorizando o reservado, e dentro de cada split.
    chave = lambda e: json.dumps([e['historico'], e['mensagem']], ensure_ascii=False)
    reservadas = {chave(e) for e in conjuntos['validacao']}
    for split in conjuntos:
        vistos = set()
        conjuntos[split] = [e for e in conjuntos[split]
                           if (split != 'treino' or chave(e) not in reservadas)
                           and not (chave(e) in vistos or vistos.add(chave(e)))]
        salvar(out / (split + '.json'), conjuntos[split])
    salvar(out / 'trajetorias.json', trajetorias)
    salvar(out / 'manifesto.json', {'origem': 'Exercícios procedurais autorais do assistente; não humanos. Seis famílias com formas compartilhadas entre treino e validação; diagnóstico de aprendizagem no domínio, não independência.',
        'historico_maximo_turnos': 6, 'turnos_por_trajetoria': 8,
        'pares': {s: len(es) for s, es in conjuntos.items()},
        'sha256': {s: sha(out / (s + '.json')) for s in conjuntos},
        'codigo_sha256': sha(__file__), 'sondas_diagnostico_lidas': False,
        'aprovado_para_chat': False})
    print({s: len(es) for s, es in conjuntos.items()})
