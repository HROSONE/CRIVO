"""Seleção de textos sintéticos públicos; não importa modelos nem frameworks."""
import collections
import hashlib
import heapq
import re
import unicodedata

FONTE = 'https://huggingface.co/datasets/cnmoro/GPT4-500k-Augmented-PTBR-Clean'
IDENTIDADE = re.compile(r'\b(?:chatgpt|openai|openassistant|open assistant)\b', re.I)


def normalizar(texto):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', texto).casefold()).strip()


def digest(texto):
    return hashlib.sha256(normalizar(texto).encode()).hexdigest()


def selecionar(registros, limite=50000, reservados=()):
    """Agrupa por primeiro pedido; conserva textos integrais e procedência.

    O limite é de conversas, não janelas. Augmentações semanticamente próximas
    podem sobreviver em partições diferentes: este corpus não é avaliação cega.
    """
    if limite < 1:
        raise ValueError('Limite de conversas deve ser positivo')
    bloqueados = {normalizar(t) for t in reservados}
    vistos, heap, contagens = set(), [], collections.Counter()
    for registro in registros:
        contagens['lidos'] += 1
        if registro.get('metadata') != FONTE:
            contagens['outra_fonte_licenca'] += 1
            continue
        turnos = registro.get('conversations')
        if (not isinstance(turnos, list) or not turnos or len(turnos) % 2
                or any(not isinstance(t, dict) or t.get('role') != ('user' if i % 2 == 0 else 'assistant')
                       or not isinstance(t.get('content'), str) or not t['content'].strip()
                       for i, t in enumerate(turnos))):
            contagens['estrutura_recusada'] += 1
            continue
        textos = [t['content'] for t in turnos]
        if any(normalizar(t) in bloqueados for t in textos):
            contagens['sobreposicao_avaliacao_humana'] += 1
            continue
        if any(IDENTIDADE.search(t) for t in textos):
            contagens['identidade_externa'] += 1
            continue
        chave = hashlib.sha256('\0'.join(normalizar(t) for t in textos).encode()).hexdigest()
        if chave in vistos:
            contagens['duplicados'] += 1
            continue
        vistos.add(chave)
        grupo = digest(textos[0])
        bucket = int(grupo[:8], 16) % 100
        doc = {'conversations': turnos, 'source_id': chave, 'grupo': grupo,
               'split': 'validacao' if bucket < 3 else 'teste' if bucket < 5 else 'treino',
               'origem': 'sintetico_publico_tucano', 'fonte': FONTE, 'licenca_declarada': 'MIT'}
        item = (-int(chave, 16), chave, doc)
        if len(heap) < limite:
            heapq.heappush(heap, item)
        elif item[0] > heap[0][0]:
            heapq.heapreplace(heap, item)
    docs = [d for _, _, d in sorted(heap, key=lambda item: item[1])]
    # Recusar respostas repetidas entre partições, inclusive entre raízes.
    alvos = collections.defaultdict(set)
    for d in docs:
        for t in d['conversations'][1::2]:
            alvos[normalizar(t['content'])].add(d['split'])
    limpos = [d for d in docs if all(len(alvos[normalizar(t['content'])]) == 1
                                   for t in d['conversations'][1::2])]
    contagens['conversas_alvos_entre_particoes'] = len(docs) - len(limpos)
    contagens['conversas_selecionadas'] = len(limpos)
    return limpos, dict(contagens)


def pares(conversa):
    historico = []
    for i in range(0, len(conversa['conversations']), 2):
        pedido, resposta = conversa['conversations'][i:i + 2]
        yield {'mensagem': pedido['content'], 'resposta': resposta['content'],
               'historico': list(historico), 'grupo': conversa['grupo'],
               'source_id': conversa['source_id'] + ':' + str(i // 2),
               'origem': conversa['origem'], 'split': conversa['split']}
        historico.extend([{'papel': 'usuario', 'texto': pedido['content']},
                          {'papel': 'assistente', 'texto': resposta['content']}])


def selecionar_parquet(caminho, limite, reservados):
    import pyarrow.parquet as pq
    registros = (r for b in pq.ParquetFile(caminho).iter_batches(batch_size=512)
                 for r in b.to_pylist())
    return selecionar(registros, limite, reservados)
