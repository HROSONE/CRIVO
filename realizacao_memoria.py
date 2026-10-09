"""O Transformer próprio realiza fatos ativos já selecionados na sessão.

Não cria memória nem interpreta novas declarações. O seletor existente
continua responsável pelos referentes; a rede recebe cada fato inteiro.
Uma realização incompleta ou diferente conserva a resposta estrutural.
"""
import copy
import hashlib
import json
import re
import unicodedata


def literal(texto):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', texto)).strip(' .')


def realizar(pergunta, memoria, gerador=None):
    trace = dict(usada=False, leu_memoria=False, modo='sessao',
                 origem='memoria_estruturada_da_sessao', tentativas=0,
                 evidencias=[], passagens=[])

    def recuar(motivo):
        trace['motivo'] = motivo
        return None, trace

    quadro = memoria.ultimo or {}
    if quadro.get('acao') != 'consulta':
        return recuar('turno_sem_consulta_de_memoria')
    ids = quadro.get('afirmacoes', [])
    if not ids:
        return recuar('consulta_sem_fatos_ativos')
    if len(ids) > 4:
        return recuar('limite_de_evidencias_da_sessao')
    fatos = []
    for idx in ids:
        if not isinstance(idx, int) or not 0 <= idx < len(memoria.afirmacoes):
            return recuar('referencia_de_memoria_invalida')
        f = memoria.afirmacoes[idx]
        if (f.get('status') != 'ativo' or f.get('fonte', {}).get('origem') != 'usuario'
                or f.get('escopo') not in ('declarado', 'fala_reportada')):
            return recuar('fonte_de_sessao_invalida')
        texto = memoria._frase(f) + '.'
        fatos.append(texto)
        trace['evidencias'].append(dict(afirmacao=idx, sujeito=f['sujeito'],
                                        relacao=f['relacao'], valor=f['valor'],
                                        escopo=f['escopo'], fonte=copy.deepcopy(f['fonte'])))
    from geracao_ancorada import geracao, LIMITE_FATOS, LIMITE_PERGUNTA
    g = gerador if gerador is not None else geracao()
    if not g.disponivel:
        return recuar('modelo_indisponivel')
    trace['modelo'] = 'Transformer causal autoral ancorado'
    if len(g.bpe.codificar(pergunta)) > LIMITE_PERGUNTA:
        return recuar('pergunta_excede_contexto_do_realizador')
    # Valida tudo antes de chamar a rede: nenhum sujeito ou valor é cortado.
    if any(1 + len(g.bpe.codificar(f)) > LIMITE_FATOS for f in fatos):
        return recuar('fato_excede_contexto_do_realizador')
    saidas = []
    for fato in fatos:
        prompt = g.prompt(pergunta, [fato])
        passagem = dict(fato=fato, prompt_sha256=hashlib.sha256(
            json.dumps(prompt).encode('utf-8')).hexdigest())
        trace['leu_memoria'] = True
        diagnostico = {}
        texto = g.gerar(pergunta, [fato], diagnostico=diagnostico)
        trace['tentativas'] += diagnostico.get('tentativas', 0)
        passagem['diagnostico'] = diagnostico
        trace['passagens'].append(passagem)
        if not texto:
            return recuar(diagnostico.get('motivo', 'guarda_rejeitou'))
        if literal(texto) != literal(fato):
            return recuar('fato_da_sessao_nao_preservado')
        saidas.append(texto.rstrip(' .'))
    trace.update(usada=True, motivo='gerada', copia_literal=True)
    return 'Segundo o que você contou, ' + '; '.join(saidas) + '.', trace
