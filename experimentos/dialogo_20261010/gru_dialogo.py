"""Segundo ensaio: GRU existente condicionada ao ato e argumentos da sessão."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path

H = Path(__file__).resolve().parent
ROOT = H.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(H))
import numpy as np
from linguagem_gerativa import (GeradorGRU, ESPECIAIS, tokenizar, renderizar, assinatura_atributos)
from treinar_geracao import inicializar, lote, perda_gradientes, regularizar_contexto, assinatura
from avaliar import baseline_site, pontuar_texto, ler_modelo
from preparar import nome

MAPA = {'capacidades': 'dialogo', 'exemplos': 'ideia', 'funcionamento': 'reflexao',
        'autoria': 'mensagem', 'historia': 'historia', 'história': 'historia',
        'corrigir': 'final', 'correção': 'ajuste', 'preferência': 'resumo',
        'saudação': 'apoio', 'esclarecimento': 'exploracao', 'continuação': 'escuta'}


def delexicalizar(ex):
    fatos, ato = ex['fatos_sessao'], ex['ato']
    slots = {}
    personagem = re.search(r'personagem: ([^;]+)', fatos)
    tema = re.search(r'tema: ([^;]+)', fatos)
    if personagem or tema:
        slots['tema1'] = (personagem or tema)[1]
    if 'final: encontra um amigo' in fatos:
        slots['tema2'] = 'um amigo'
    preferencias = re.findall(r'(\w+) prefere ([^;]+)', fatos)
    for i, (pessoa, valor) in enumerate(preferencias[:2]):
        slots['destinatario' if i == 0 else 'tema2'] = pessoa
        slots['relato' if i == 0 else 'detalhe'] = valor
    participante = re.search(r'pessoa: ([^;]+)', fatos)
    if participante and ato == 'saudação':
        slots['destinatario'] = participante[1]
    limite = re.search(r'limite: (\d+ minutos)', fatos)
    if limite:
        slots['restricao'] = limite[1]
    # O ato do exemplo de perguntas estava rotulado genericamente no ensaio 1.
    # Aqui a anotação corresponde ao pedido autoral, sem consultar o congelado.
    if ex['id_dialogo'].startswith('capacidades-'):
        turno = int(ex['id'].rsplit('-', 1)[1])
        if turno == 3:
            ato = 'exemplos'
        elif turno == 4:
            ato = 'funcionamento'
        slots = {} if turno > 0 else slots
    acao = MAPA.get(ato, 'escuta')
    if personagem and ato == 'continuação':
        acao = 'continuacao'
    contexto = {'acao': acao, 'slots': slots, 'mensagem': ex['contexto']['mensagem'],
                'historico': [h['texto'] for h in ex['contexto']['historico'] if not h['texto'].startswith('Fatos atuais da sessão:')],
                'resposta_anterior': '', 'estilo': 'neutro', 'variante': 0}
    resposta = ex['resposta']
    for chave, valor in sorted(slots.items(), key=lambda item: -len(item[1])):
        resposta = resposta.replace(valor, '@' + chave)
    # Os alvos só podem mencionar valores fornecidos. Não aprendemos nomes globais.
    pendentes = [nome(i) for i in range(960) if re.search(r'(?<!\w)' + nome(i) + r'(?!\w)', resposta)]
    if pendentes:
        # Saídas de preferência podem nomear o interlocutor cujo gosto mudou.
        for n in pendentes:
            if n not in slots.values():
                livre = next((k for k in ('destinatario', 'tema2', 'objetivo') if k not in slots), None)
                if livre is None:
                    raise ValueError('Mais nomes que slots disponíveis')
                slots[livre] = n
            chave = next(k for k, v in slots.items() if v == n)
            resposta = re.sub(r'(?<!\w)' + n + r'(?!\w)', '@' + chave, resposta)
    return {'id': ex['id'], 'dialogo': ex['id_dialogo'], 'familia': ex['familia'], 'split': ex['split'],
            'contexto': contexto, 'resposta': resposta, 'origem': 'Mesmos alvos autorais, argumentos deslexicalizados.'}


def preparar():
    raw = json.loads((H / 'corpus.json').read_text())
    exemplos = [delexicalizar(e) for e in raw['exemplos']]
    dados = {'versao': 1, 'corpus_origem_sha256': hashlib.sha256((H / 'corpus.json').read_bytes()).hexdigest(),
             'exemplos': exemplos, 'limite': 'Mesmos diálogos, sem casos reais de avaliação; não amplia o corpus com alvos do teste.'}
    (H / 'corpus_gru.json').write_text(json.dumps(dados, ensure_ascii=False, indent=2) + '\n')
    return dados


def estado_observado(caso, resposta):
    route = resposta.get('natural_routing') or {}
    ato = route.get('ato') or ('capacidades' if resposta['id'].startswith('social:') else '')
    slots = {}
    if route.get('personagem'):
        slots['tema1'] = route['personagem']
    elif ato == 'corrigir' and route.get('referentes'):
        slots['tema1'] = route['referentes'][0]
        if len(route['referentes']) > 1:
            slots['tema2'] = route['referentes'][1]
    return {'acao': MAPA.get(ato, 'exploracao'), 'mensagem': caso['entrada']['texto'],
            'historico': caso['entrada']['anteriores'], 'slots': slots,
            'estilo': 'neutro', 'variante': 0}


def avaliar(modelo_path, saida):
    modelo = GeradorGRU(ler_modelo(modelo_path))
    baseline = baseline_site()
    respostas = {r['caso']: r['resposta'] for r in baseline['resultados']}
    dados = json.loads((H / 'casos_congelados.json').read_text())
    out = {'checkpoint_sha256': hashlib.sha256(Path(modelo_path).read_bytes()).hexdigest(),
           'casos_sha256': baseline['casos_sha256'], 'aprovado': False,
           'metodo': 'Mesmo juiz e dez casos reais. Ato/slots do trace existente; linguagem prevista palavra por palavra e argumentos copiados.',
           'resultados': []}
    for caso in dados['casos']:
        if 'dialogo_historia_capacidades' not in caso['grupos']:
            continue
        ctx = estado_observado(caso, respostas[caso['id']])
        g = modelo.gerar(ctx)
        texto = renderizar(g, ctx['slots'])
        gerada = dict(g, texto=texto)
        entrada = {'mensagem': ctx['mensagem'], 'historico': [{'papel': 'usuario', 'texto': t} for t in ctx['historico']]}
        # Valores fornecidos são parte da fonte auditável, sem respostas alvo.
        entrada['historico'].append({'papel': 'usuario', 'texto': json.dumps(ctx['slots'], ensure_ascii=False)})
        row = pontuar_texto(caso, gerada, entrada)
        row['contexto_estruturado'] = ctx
        out['resultados'].append(row)
        print(caso['id'], 'PASS' if row['conteudo_minimo_atendido'] else 'FAIL', texto, flush=True)
    rows = out['resultados']
    out['resumo'] = {'total': len(rows), 'conteudo_minimo_atendido': sum(r['conteudo_minimo_atendido'] for r in rows),
                     'completas': sum(r['completa'] for r in rows), 'historias_entregues': sum(r['historia_entregue'] is True for r in rows),
                     'casos_com_referentes_ausentes': sum(bool(r['referentes_ausentes']) for r in rows),
                     'casos_com_inventados': sum(bool(r['nomes_inventados'] or r['numeros_inventados']) for r in rows)}
    Path(saida).write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(out['resumo'], ensure_ascii=False), flush=True)
    return out


def treino(epocas=14):
    dados = json.loads((H / 'corpus_gru.json').read_text())
    tr = [e for e in dados['exemplos'] if e['split'] == 'treino']
    val = [e for e in dados['exemplos'] if e['split'] == 'validacao']
    base_path = ROOT / 'rede_geracao.json'
    base = json.loads(base_path.read_text())
    vocab = list(ESPECIAIS) + sorted({t for e in tr for t in tokenizar(e['resposta'])} - set(ESPECIAIS))
    idx = {t: i for i, t in enumerate(vocab)}
    p = inicializar(vocab, base['ocultos'], base['embeddings'], 20261010)
    oldidx = {t: i for i, t in enumerate(base['vocabulario'])}
    for k in p:
        if k not in ('E', 'O', 'bo'):
            p[k] = np.asarray(base['pesos'][k], dtype='float32')
    for j, t in enumerate(vocab):
        if t in oldidx:
            i = oldidx[t]
            p['E'][j] = base['pesos']['E'][i]
            p['O'][:, j] = np.asarray(base['pesos']['O'], dtype='float32')[:, i]
            p['bo'][j] = base['pesos']['bo'][i]
    parametros = sum(a.size for a in p.values())
    assert parametros <= base['treino']['parametros']
    m, v = ({k: np.zeros_like(a) for k, a in p.items()} for _ in range(2))
    rng = np.random.default_rng(20261010)
    passo, hist, melhor, bestp = 0, [], float('inf'), None
    inicio = time.monotonic()
    def perda_validacao():
        total, tokens = 0., 0
        for pos in range(0, len(val), 48):
            f, x, y, mascara = lote(val[pos:pos+48], idx)
            loss, _ = perda_gradientes(p, f, x, y, mascara)
            n = int(mascara.sum()); total += loss*n; tokens += n
        return total/tokens
    inicial = perda_validacao()
    print('GRU parâmetros', parametros, 'vocab', len(vocab), 'validação inicial', round(inicial, 4), flush=True)
    for ep in range(1, epocas + 1):
        order = rng.permutation(len(tr)); perdas = []
        for pos in range(0, len(tr), 48):
            f, x, y, mascara = lote([tr[i] for i in order[pos:pos+48]], idx)
            f = regularizar_contexto(f, rng, .65, .15)
            loss, grads = perda_gradientes(p, f, x, y, mascara)
            assert math.isfinite(loss) and all(np.isfinite(g).all() for g in grads.values())
            perdas.append(loss)
            escala = min(1., 5/max(1e-9, math.sqrt(sum(float((g*g).sum()) for g in grads.values()))))
            passo += 1
            for k in p:
                g = grads[k]*escala
                m[k] = .9*m[k] + .1*g; v[k] = .999*v[k] + .001*g*g
                p[k] -= .002*(m[k]/(1-.9**passo))/(np.sqrt(v[k]/(1-.999**passo))+1e-8)
        valor = perda_validacao()
        hist.append({'epoca': ep, 'treino': sum(perdas)/len(perdas), 'validacao': valor})
        if valor < melhor:
            melhor = valor; bestp = {k: a.copy() for k, a in p.items()}; selecionada = ep
        print('GRU época', ep, 'validação', round(valor, 4), 'segundos', round(time.monotonic()-inicio, 1), flush=True)
    meta = {'versao': 1, 'arquitetura': 'GRU condicional autoregressiva própria', 'assinatura_atributos': assinatura_atributos(),
            'assinatura_treino': assinatura(tr), 'vocabulario': vocab, 'ocultos': base['ocultos'], 'embeddings': base['embeddings'],
            'pesos': {k: np.round(a.astype('float64'), 7).tolist() for k, a in bestp.items()},
            'controle': {'aprovado': False, 'ativo_no_chat': False}, 'base_sha256': hashlib.sha256(base_path.read_bytes()).hexdigest(),
            'corpus_sha256': hashlib.sha256((H/'corpus_gru.json').read_bytes()).hexdigest(),
            'casos_sha256': hashlib.sha256((H/'casos_congelados.json').read_bytes()).hexdigest(),
            'treino': {'epocas': epocas, 'epoca_selecionada': selecionada, 'parametros': parametros, 'semente': 20261010,
                       'lote': 48, 'taxa': .002, 'dropout_texto': .65, 'mistura_texto': .15, 'clip': 5, 'exemplos': len(tr)},
            'limite': 'Ato e argumentos precisam chegar corretos. Históricos não são interpretados livremente; texto da sessão tem influência residual. Não é conversa geral.'}
    raw = json.dumps(meta, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    destino = H/'checkpoint_gru_dialogo.json.gz'; destino.write_bytes(gzip.compress(raw, mtime=0))
    (H/'treino_gru.json').write_text(json.dumps({'config': meta['treino'], 'inicial_validacao': inicial,
        'historico': hist, 'selecionada': selecionada, 'segundos': round(time.monotonic()-inicio, 2),
        'checkpoint_sha256': hashlib.sha256(destino.read_bytes()).hexdigest(), 'aprovado': False},ensure_ascii=False,indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('acao', choices=['preparar', 'treinar', 'avaliar'])
    parser.add_argument('--modelo', default=str(ROOT/'rede_geracao.json'));parser.add_argument('--saida')
    parser.add_argument('--epocas', type=int, default=14);args=parser.parse_args()
    if args.acao == 'preparar': preparar()
    elif args.acao == 'treinar': treino(args.epocas)
    else: avaliar(args.modelo, args.saida)
