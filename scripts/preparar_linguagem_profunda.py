"""Prepara corpus amplo rastreável, sem modelos externos nem dados de avaliação.

Wikipedia PT (CC-BY-SA/GFDL) e OASST2 humano (Apache-2.0). Seleção
determinística por hash, deduplicação e partições por documento/árvore.
"""
import argparse
import collections
import hashlib
import heapq
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from arquivos_contextuais import ler_json
from linguagem_profunda import ESPECIAIS, segmentos_dialogo, codificar_texto
from scripts.curar_dialogos_humanos import (ler_mensagens, revisada, caminho_revisado,
    etiquetas, erros_humanos, referencias_ou_contatos, SEMENTE_SPLIT, REVISION)


def sha(caminho):
    h = hashlib.sha256()
    with open(caminho, 'rb') as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b''):
            h.update(bloco)
    return h.hexdigest()


def normalizar(texto):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', texto).casefold()).strip()


def particao(grupo, humano=False):
    if humano:
        # Compatível com a validação humana anterior; acrescenta teste em árvores
        # antes destinadas ao treino, sem reutilizar nenhum peso anterior.
        b = int(hashlib.sha256((SEMENTE_SPLIT + grupo).encode()).hexdigest()[:8], 16) % 10
        return 'validacao' if b == 0 else 'teste' if b == 1 else 'treino'
    b = int(grupo[:8], 16) % 100
    return 'validacao' if b < 3 else 'teste' if b < 5 else 'treino'


def selecionar_wikipedia(caminho, limite):
    import pyarrow.parquet as pq
    vistos, heap = set(), []
    contagens = collections.Counter()
    for batch in pq.ParquetFile(caminho).iter_batches(batch_size=1024):
        for doc in batch.to_pylist():
            contagens['lidos'] += 1
            texto = doc['text']
            if not 256 <= len(texto) <= 100000:
                contagens['comprimento_recusado'] += 1
                continue
            chave = hashlib.sha256(normalizar(texto).encode()).hexdigest()
            if chave in vistos:
                contagens['duplicados'] += 1
                continue
            vistos.add(chave)
            doc = {'id': str(doc['id']), 'url': doc['url'], 'titulo': doc['title'],
                   'texto': texto, 'grupo': chave, 'split': particao(chave)}
            item = (-int(chave, 16), chave, doc)
            if len(heap) < limite:
                heapq.heappush(heap, item)
            elif item[0] > heap[0][0]:
                heapq.heapreplace(heap, item)
    return [d for _, _, d in sorted(heap, key=lambda i: i[1])], dict(contagens)


def selecionar_humanos(caminho):
    mensagens = ler_mensagens(caminho)
    indice = {m['message_id']: m for m in mensagens}
    exemplos, vistos = [], set()
    recusas = collections.Counter()
    for resposta in mensagens:
        if resposta['role'] != 'assistant':
            continue
        pedido = indice.get(resposta.get('parent_id'))
        caminho = caminho_revisado(pedido, indice, resposta['message_tree_id']) if pedido else None
        if not revisada(resposta) or not caminho:
            recusas['revisao_estrutura'] += 1
            continue
        textos = [m['text'] for m in caminho] + [resposta['text']]
        if any(m['message_id'] in erros_humanos for m in caminho + [resposta]):
            recusas['erro_ja_revisado'] += 1
            continue
        qualidade = etiquetas(resposta).get('quality')
        if (qualidade is not None and qualidade < .5) or any(referencias_ou_contatos.search(t) for t in textos):
            recusas['qualidade_contato'] += 1
            continue
        # Não ensinar identidade ou promessas de capacidades de outro assistente.
        if any(re.search(r'\b(?:openassistant|open assistant|chatgpt|openai)\b', t, re.I) for t in textos):
            recusas['identidade_externa'] += 1
            continue
        chave = tuple(normalizar(t) for t in textos)
        if chave in vistos:
            recusas['duplicado'] += 1
            continue
        vistos.add(chave)
        grupo = resposta['message_tree_id']
        exemplos.append({'mensagem': pedido['text'], 'resposta': resposta['text'],
            'historico': [{'papel': 'usuario' if m['role'] == 'prompter' else 'assistente',
                          'texto': m['text']} for m in caminho[:-1]],
            'grupo': grupo, 'source_id': resposta['message_id'], 'origem': 'humano_oasst2',
            'split': particao(grupo, humano=True)})
    # O mesmo alvo normalizado nunca passa de uma partição para outra, inclusive
    # quando os autores duplicaram respostas entre árvores distintas.
    splits_alvos = collections.defaultdict(set)
    for ex in exemplos:
        splits_alvos[normalizar(ex['resposta'])].add(ex['split'])
    limpos = [e for e in exemplos if len(splits_alvos[normalizar(e['resposta'])]) == 1]
    recusas['alvos_duplicados_entre_particoes'] = len(exemplos) - len(limpos)
    return sorted(limpos, key=lambda e: (e['grupo'], e['source_id'])), dict(recusas)


def escrever_jsonl(caminho, exemplos):
    with open(caminho, 'w', encoding='utf-8') as f:
        for ex in exemplos:
            f.write(json.dumps(ex, ensure_ascii=False, sort_keys=True) + '\n')


def janelas_dialogo(tokenizer, ex, contexto):
    segmentos, atual = segmentos_dialogo(tokenizer, ex['mensagem'], ex.get('historico', []))
    fonte = sum(segmentos, []) + atual
    resposta = codificar_texto(tokenizer, ex['resposta']) + [tokenizer.token_to_id('<fim>')]
    ids = fonte + resposta
    if len(ids) > 8192 or not ex['resposta'].strip():
        return []
    # Janelas sobrepostas preservam todos os tokens do alvo, cada um com perda
    # exatamente uma vez. Texto do usuário e histórico nunca são alvos do SFT.
    resultado = []
    stride = max(1, contexto // 2)
    for primeiro in range(len(fonte), len(ids), stride):
        ultimo = min(len(ids), primeiro + stride)
        inicio = max(0, ultimo - contexto - 1)
        x = ids[inicio:ultimo - 1]
        y = [-100 if p < primeiro else ids[p] for p in range(inicio + 1, ultimo)]
        resultado.append((x, y))
    return resultado


def main():
    from tokenizers import Tokenizer, models, trainers, pre_tokenizers, decoders
    import numpy as np
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--wikipedia', required=True)
    p.add_argument('--origem-wikipedia', required=True)
    p.add_argument('--oasst2', required=True)
    p.add_argument('--saida', required=True)
    p.add_argument('--documentos', type=int, default=20000)
    p.add_argument('--vocabulario', type=int, default=4096)
    p.add_argument('--contexto', type=int, default=256)
    p.add_argument('--dialogos-publicos', help='Shard Tucano-SFT opcional, textos sintéticos públicos')
    p.add_argument('--limite-dialogos-publicos', type=int, default=50000)
    args = p.parse_args()
    if not 261 <= args.vocabulario <= 65535 or args.documentos < 1 or args.contexto < 8:
        p.error('Tamanho de corpus/vocabulário/contexto inválido')
    out = Path(args.saida); out.mkdir(parents=True, exist_ok=True)
    origem = json.loads(Path(args.origem_wikipedia).read_text())
    if sha(args.wikipedia) != origem['sha256']:
        raise ValueError('Hash da Wikipedia difere do manifesto de origem')
    docs, contagens = selecionar_wikipedia(args.wikipedia, args.documentos)
    humanos, recusas = selecionar_humanos(args.oasst2)
    curriculo = ler_json(ROOT / 'curriculo_compreensao.json')
    alvos_reservados = {normalizar(e['resposta']) for e in humanos if e['split'] != 'treino'}
    sinteticos = [dict(mensagem=e['contexto']['mensagem'],
                      historico=e['contexto'].get('historico', []), resposta=e['resposta'],
                      origem='sintetico_autoral', split='treino')
                  for e in curriculo['exemplos'] if e['split'] == 'treino'
                  and normalizar(e['resposta']) not in alvos_reservados]
    publicos, pares_publicos, contagens_publicos = [], [], {}
    if args.dialogos_publicos:
        from scripts.baixar_fontes_linguagem import FONTES
        from scripts.curar_instrucoes_publicas import selecionar_parquet, pares
        if sha(args.dialogos_publicos) != FONTES['tucano']['sha256']:
            raise ValueError('Hash dos diálogos públicos difere da revisão fixada')
        reservados = [t for e in humanos if e['split'] != 'treino'
                      for t in [e['mensagem'], e['resposta']] + [h['texto'] for h in e['historico']]]
        publicos, contagens_publicos = selecionar_parquet(
            args.dialogos_publicos, args.limite_dialogos_publicos, reservados)
        pares_publicos = [p for d in publicos if d['split'] == 'treino' for p in pares(d)]
        print('Conversas sintéticas públicas', len(publicos), 'pares de treino', len(pares_publicos), flush=True)
    print('Documentos', len(docs), 'diálogos humanos', len(humanos), 'sintéticos', len(sinteticos), flush=True)
    tokenizer = Tokenizer(models.BPE())
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tokenizer.decoder = decoders.ByteLevel()
    treinador = trainers.BpeTrainer(vocab_size=args.vocabulario, min_frequency=2,
                      special_tokens=ESPECIAIS, initial_alphabet=pre_tokenizers.ByteLevel.alphabet())
    textos = (d['texto'] for d in docs if d['split'] == 'treino')
    def texto_treino():
        yield from textos
        for e in humanos + sinteticos + pares_publicos:
            if e['split'] == 'treino':
                yield e['mensagem']; yield e['resposta']
                for h in e.get('historico', []): yield h['texto']
    tokenizer.train_from_iterator(texto_treino(), treinador)
    tokenizer.encode_special_tokens = True
    tokenizer.save(str(out / 'tokenizer.json'))
    manifesto = {'versao': 1, 'wikipedia': origem,
        'oasst2': {'revisao': REVISION, 'licenca': 'Apache-2.0', 'filtro_recusas': recusas,
                  'arquivo_sha256': sha(args.oasst2)},
        'selecao_wikipedia': contagens, 'contexto': args.contexto,
        'vocabulario': tokenizer.get_vocab_size(), 'particoes': {},
        'sintetico_sha256': sha(ROOT / 'curriculo_compreensao.json.gz'),
        'tokenizador_aprendeu_somente_treino': True, 'pesos_pre_treinados': False}
    if args.dialogos_publicos:
        manifesto['dialogos_publicos'] = dict(FONTES['tucano'], contagens=contagens_publicos,
            natureza='textos sintéticos gerados por modelos externos; nenhum peso externo',
            pares_treino=len(pares_publicos),
            particoes={s: sum(d['split'] == s for d in publicos) for s in ('treino','validacao','teste')},
            avaliacao_primaria='Somente humanos OASST2; públicos reservados não entram nas métricas humanas')
    for split in ('treino', 'validacao', 'teste'):
        ds = [d for d in docs if d['split'] == split]
        hs = [h for h in humanos if h['split'] == split]
        escrever_jsonl(out / ('documentos_' + split + '.jsonl'), ds)
        escrever_jsonl(out / ('dialogos_' + split + '.jsonl'), hs)
        if args.dialogos_publicos:
            escrever_jsonl(out / ('instrucoes_publicas_' + split + '.jsonl'),
                           [d for d in publicos if d['split'] == split])
        n = 0
        with open(out / ('linguagem_' + split + '.bin'), 'wb') as f:
            for d in ds:
                ids = [tokenizer.token_to_id('<documento>')] + codificar_texto(tokenizer, d['texto'])
                ids.append(tokenizer.token_to_id('<fim>'))
                np.asarray(ids, dtype='<u2').tofile(f); n += len(ids)
        sx, sy, so = [], [], []
        descartados = collections.Counter()
        for e in hs + (sinteticos + pares_publicos if split == 'treino' else []):
            janelas = janelas_dialogo(tokenizer, e, args.contexto)
            if not janelas: descartados[e['origem']] += 1
            for x, y in janelas:
                sx.append(x + [0] * (args.contexto - len(x)))
                sy.append(y + [-100] * (args.contexto - len(y)))
                so.append(1 if e['origem'] == 'humano_oasst2' else 0)
        x = np.asarray(sx, dtype=np.int32).reshape(-1, args.contexto)
        y = np.asarray(sy, dtype=np.int32).reshape(-1, args.contexto)
        np.save(out / ('dialogo_' + split + '_x.npy'), x)
        np.save(out / ('dialogo_' + split + '_y.npy'), y)
        np.save(out / ('dialogo_' + split + '_origem.npy'), np.asarray(so, dtype=np.int8))
        manifesto['particoes'][split] = {'documentos': len(ds), 'tokens_linguagem': n,
             'pares_humanos': len(hs), 'arvores_humanas': len({e['grupo'] for e in hs}),
             'janelas_dialogo': len(x), 'tokens_alvo_dialogo': int((y != -100).sum()),
             'janelas_humanas': sum(so), 'descartados_comprimento': dict(descartados)}
        print(split, manifesto['particoes'][split], flush=True)
    manifesto['arquivos'] = {p.name: sha(p) for p in sorted(out.iterdir())
                            if p.is_file() and p.name != 'manifesto.json'}
    (out / 'manifesto.json').write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + '\n')
    print('Corpus pronto', out, flush=True)


if __name__ == '__main__': main()
