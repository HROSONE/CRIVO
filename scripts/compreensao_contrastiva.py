"""Currículo contrastivo autoral: fatos do cenário, sem fatos externos ou pesos.

Cada par muda o contexto e inverte a opção correta. Nomes e formulações de
validação/teste são separados antes do treino. Acertar opções não certifica
conversa livre; o avaliador registra as duas medidas separadamente.
"""
import hashlib
import itertools
import json


DOMINIOS = {
    'treino': dict(pessoas=['Ana', 'Bruno', 'Clara', 'Diego', 'Eva', 'Felipe'],
                   objetos=['caderno', 'livro', 'lápis', 'bilhete', 'envelope', 'mapa'],
                   lugares=['gaveta', 'mesa', 'mochila', 'estante', 'caixa', 'sacola']),
    'validacao': dict(pessoas=['Gabi', 'Hugo', 'Iara', 'João'],
                      objetos=['carimbo', 'estojo', 'cartaz', 'recibo'],
                      lugares=['bolsa', 'cômoda', 'prateleira', 'pasta']),
    'teste': dict(pessoas=['Lia', 'Mauro', 'Nina', 'Otávio'],
                  objetos=['pacote', 'botão', 'ticket', 'selo'],
                  lugares=['bandeja', 'bancada', 'mala', 'cesta']),
}


def gerar(split):
    if split not in DOMINIOS:
        raise ValueError('Partição desconhecida')
    d = DOMINIOS[split]
    pares = []
    for n, (i, j) in enumerate(itertools.permutations(range(len(d['objetos'])), 2)):
        objeto, outro = d['objetos'][i], d['objetos'][j]
        local, antigo = d['lugares'][i], d['lugares'][j]
        pessoa, outra = d['pessoas'][i], d['pessoas'][j]
        hist = [dict(papel='usuario', texto=f'O {objeto} está na {antigo}.'),
                dict(papel='assistente', texto='Anotado.')]
        casos = {
            'condicao': (
                ['Pode entrar.', 'Não pode entrar.'],
                [f'Para entrar, {pessoa} precisa da chave e da autorização. Tem as duas. Pode entrar?',
                 f'Para entrar, {pessoa} precisa da chave e da autorização. Só tem '+
                 ('a chave' if n % 2 else 'a autorização')+'. Pode entrar?']),
            'negacao': (
                [f'Pode usar o {objeto}.', f'Não pode usar o {objeto}.'],
                [f'Nesta atividade é permitido usar o {objeto}. Posso usá-lo?',
                 f'Nesta atividade é proibido usar o {objeto}. Posso usá-lo?']),
            'atualizacao': (
                [f'Na {local}.', f'Na {antigo}.'],
                [f'Mudei o {objeto} para a {local}. Onde ele está agora?',
                 f'Mudei o {outro} para a {local}. O {objeto} ficou onde estava. Onde está o {objeto}?']),
            'referencia': (
                [f'{pessoa}.', f'{outra}.'],
                [f'{pessoa} levou o {objeto}; {outra} levou o {outro}. Quem levou o {objeto}?',
                 f'{pessoa} levou o {outro}; {outra} levou o {objeto}. Quem levou o {objeto}?']),
            'evidencia': (
                ['Está confirmado.', 'Não está confirmado.'],
                [f'Eu vi o {objeto} na {local}. Está confirmado que ele estava lá?',
                 f'Talvez o {objeto} esteja na {local}; ainda não conferi. Está confirmado que ele estava lá?']),
        }
        # Formulações reservadas não são paráfrases adicionadas ao treino.
        if split != 'treino':
            casos['condicao'] = (casos['condicao'][0], [
                f'A entrada exige chave junto com autorização. {pessoa} possui ambas. Essa pessoa pode entrar?',
                f'A entrada exige chave junto com autorização. {pessoa} possui apenas '+
                ('chave' if n % 2 else 'autorização')+'. Essa pessoa pode entrar?'])
            casos['negacao'] = (casos['negacao'][0], [
                f'A regra permite o {objeto}. Seu uso está autorizado?',
                f'A regra não permite o {objeto}. Seu uso está autorizado?'])
            casos['atualizacao'] = (casos['atualizacao'][0], [
                f'O {objeto} foi transferido para a {local}. Em que lugar ficou?',
                f'O {outro} foi transferido para a {local}, sem mover o {objeto}. Em que lugar ficou o {objeto}?'])
            casos['referencia'] = (casos['referencia'][0], [
                f'O {objeto} ficou com {pessoa} e o {outro} com {outra}. Quem ficou com o {objeto}?',
                f'O {outro} ficou com {pessoa} e o {objeto} com {outra}. Quem ficou com o {objeto}?'])
            casos['evidencia'] = (casos['evidencia'][0], [
                f'Conferi: o {objeto} estava na {local}. A presença dele foi verificada?',
                f'Suponho que o {objeto} esteja na {local}, mas não verifiquei. A presença dele foi verificada?'])
        if split == 'teste':
            casos['condicao'] = (casos['condicao'][0], [
                f'Sem chave ou sem autorização não há entrada. {pessoa} tem chave e autorização. Pode entrar?',
                f'Sem chave ou sem autorização não há entrada. {pessoa} não tem '+
                ('autorização, mas tem chave' if n % 2 else 'chave, mas tem autorização')+'. Pode entrar?'])
            casos['negacao'] = (casos['negacao'][0], [
                f'O {objeto} está entre os materiais autorizados. Posso usar esse material?',
                f'O {objeto} está entre os materiais vetados. Posso usar esse material?'])
            casos['atualizacao'] = (casos['atualizacao'][0], [
                f'Atualize a localização do {objeto}: agora é a {local}. Qual é a localização atual?',
                f'Atualize apenas o {outro}: agora é a {local}. Qual é a localização atual do {objeto}?'])
            casos['referencia'] = (casos['referencia'][0], [
                f'{pessoa} recebeu o {objeto}, enquanto {outra} recebeu o {outro}. Diga quem recebeu o {objeto}.',
                f'{pessoa} recebeu o {outro}, enquanto {outra} recebeu o {objeto}. Diga quem recebeu o {objeto}.'])
            casos['evidencia'] = (casos['evidencia'][0], [
                f'A presença do {objeto} na {local} foi constatada. Isso é confirmação?',
                f'A presença do {objeto} na {local} é só uma possibilidade. Isso é confirmação?'])
        for familia, (opcoes, mensagens) in casos.items():
            # A ordem alterna para não dar um atalho de posição ao ranqueamento.
            ordem = [1, 0] if n % 2 else [0, 1]
            pares.append(dict(id=f'{split}:{familia}:{i}:{j}', split=split, familia=familia,
                origem='sintetico_autoral_cenario_controlado',
                opcoes=[opcoes[k] for k in ordem],
                casos=[dict(mensagem=m, historico=hist if familia == 'atualizacao' else [],
                            correta=ordem.index(k)) for k, m in enumerate(mensagens)]))
    return pares


def assinatura(pares):
    return hashlib.sha256(json.dumps(pares, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def lote(tokenizer, pares, contexto, dispositivo='cpu'):
    import torch
    from linguagem_profunda import segmentos_dialogo, codificar_texto
    xs, ys, corretas = [], [], []
    for par in pares:
        if len(par['casos']) != 2 or len(par['opcoes']) != 2:
            raise ValueError('Cada contraste requer dois contextos e duas opções')
        for caso in par['casos']:
            seg, atual = segmentos_dialogo(tokenizer, caso['mensagem'], caso['historico'])
            fonte = sum(seg, []) + atual
            corretas.append(caso['correta'])
            for opcao in par['opcoes']:
                alvo = codificar_texto(tokenizer, opcao) + [tokenizer.token_to_id('<fim>')]
                ids = fonte + alvo
                if len(ids) > contexto + 1:
                    raise ValueError('Contraste excede contexto; nenhuma truncagem permitida')
                xs.append(ids[:-1]); ys.append([-100] * (len(fonte)-1) + alvo)
    t = max(map(len, xs))
    x = torch.tensor([s+[0]*(t-len(s)) for s in xs], device=dispositivo)
    y = torch.tensor([s+[-100]*(t-len(s)) for s in ys], device=dispositivo)
    return x, y, torch.tensor(corretas, device=dispositivo)


def pontuar(logits, y):
    import torch.nn.functional as F
    ce = F.cross_entropy(logits.transpose(1, 2), y, ignore_index=-100, reduction='none')
    return -(ce.sum(1) / (y != -100).sum(1)).reshape(-1, 2)


def perdas(scores, corretas, peso=1., margem=.2):
    import torch.nn.functional as F
    bom = scores.gather(1, corretas[:, None]).squeeze(1)
    ruim = scores.gather(1, (1-corretas)[:, None]).squeeze(1)
    lm = -bom.mean()
    contraste = F.softplus(margem - bom + ruim).mean()
    return lm + peso * contraste, lm, contraste


def medir(modelo, tokenizer, pares, dispositivo='cpu', tamanho=8):
    import torch
    familias = {}
    modo = modelo.training
    modelo.eval()
    with torch.no_grad():
        for ini in range(0, len(pares), tamanho):
            ps = pares[ini:ini+tamanho]
            x, y, c = lote(tokenizer, ps, modelo.config.contexto, dispositivo)
            s = pontuar(modelo(x)[0], y)
            margem = s.gather(1, c[:, None]).squeeze(1) - s.gather(1, (1-c)[:, None]).squeeze(1)
            for k, par in enumerate(ps):
                f = familias.setdefault(par['familia'], dict(casos=0, acertos=0, pares=0, pares_corretos=0, margem_soma=0.))
                ms = margem[2*k:2*k+2]
                f['casos'] += 2; f['acertos'] += int((ms > 0).sum())
                f['pares'] += 1; f['pares_corretos'] += int(bool((ms > 0).all()))
                f['margem_soma'] += float(ms.sum())
    modelo.train(modo)
    return dict(familias=familias, casos=sum(f['casos'] for f in familias.values()),
        acertos=sum(f['acertos'] for f in familias.values()),
        pares_corretos=sum(f['pares_corretos'] for f in familias.values()),
        pares=len(pares), corpus_sha256=assinatura(pares),
        limite='Escolha entre dois alvos fornecidos, não geração livre ou conversa geral.')


def geracao_livre(modelo, tokenizer, pares, max_tokens=32):
    from linguagem_profunda import fonte_dialogo, ESPECIAIS
    from geracao_incremental import gerar as gerar_tokens
    respostas = []
    for par in pares:
        for caso in par['casos']:
            fonte = fonte_dialogo(tokenizer, caso['mensagem'], caso['historico'], modelo.config.contexto)
            ids, fim = gerar_tokens(modelo, fonte, tokenizer.token_to_id('<fim>'), max_tokens=max_tokens,
                temperatura=0., proibidos=[tokenizer.token_to_id(t) for t in ESPECIAIS[:-1]])
            texto = tokenizer.decode(ids)
            esperado = par['opcoes'][caso['correta']]
            # Critério estrito e explícito; pode rejeitar paráfrases corretas.
            respostas.append(dict(id=par['id'], familia=par['familia'], mensagem=caso['mensagem'],
                historico=caso['historico'], resposta=texto, referencia=esperado, terminou=fim,
                correspondencia_exata=texto.strip().casefold()==esperado.casefold()))
    return dict(respostas=respostas, casos=len(respostas),
        exatas=sum(r['correspondencia_exata'] for r in respostas),
        criterio='Correspondência integral normalizada; não equivale a julgamento semântico.')
