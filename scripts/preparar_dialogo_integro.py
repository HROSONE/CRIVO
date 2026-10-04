"""Deriva SFT com pedido, histórico e resposta inteiros, sem mudar as reservas.

Lê apenas o corpus próprio já verificado. Não resume respostas, não inventa
rótulos e não importa pesos. Calculados ficam fora deste ajuste de conversa.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from linguagem_profunda import segmentos_dialogo, codificar_texto


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''): h.update(b)
    return h.hexdigest()


def exemplo_integro(tokenizer, e, contexto):
    segmentos, atual = segmentos_dialogo(tokenizer, e['mensagem'], e.get('historico', []))
    fonte = sum(segmentos, []) + atual
    alvo = codificar_texto(tokenizer, e['resposta']) + [tokenizer.token_to_id('<fim>')]
    if not e['resposta'].strip() or len(fonte) + len(alvo) > contexto + 1:
        return None
    ids = fonte + alvo
    x = ids[:-1]
    y = [-100] * (len(fonte) - 1) + alvo
    return x + [0]*(contexto-len(x)), y + [-100]*(contexto-len(y))


def preparar(origem, saida):
    import numpy as np
    from tokenizers import Tokenizer
    origem, saida = Path(origem), Path(saida)
    if saida.exists(): raise FileExistsError('Use uma pasta nova; corpus original preservado')
    m = json.loads((origem/'manifesto.json').read_text())
    for nome, digest in m['arquivos'].items():
        if Path(nome).name != nome or sha(origem/nome) != digest:
            raise ValueError('Arquivo de corpus incompatível: ' + nome)
    t = Tokenizer.from_file(str(origem/'tokenizer.json')); t.encode_special_tokens = True
    contexto = m['contexto']
    exemplos = [json.loads(l) for l in (origem/'dialogos_treino.jsonl').read_text().splitlines()]
    xs, ys, es = [], [], []
    contagens = collections.Counter()
    for e in exemplos:
        grupo = 'humanos' if e['origem'] == 'humano_oasst2' else 'sinteticos'
        contagens[grupo+'_originais'] += 1
        xy = exemplo_integro(t, e, contexto)
        if xy is None:
            contagens[grupo+'_fora_contexto'] += 1
            continue
        if e['grupo'].startswith('calculado:'):
            contagens['calculados_separados'] += 1
            continue
        es.append(e); xs.append(xy[0]); ys.append(xy[1]); contagens[grupo+'_retidos'] += 1
    if not contagens['humanos_retidos'] or not contagens['sinteticos_retidos']:
        raise ValueError('Ajuste requer humanos e demonstrações autorais inteiras')
    saida.mkdir(parents=True)
    # Reservas e replay são cópias exatas; os exemplos excluídos não mudam de split.
    for nome in m['arquivos']: shutil.copyfile(origem/nome, saida/nome)
    familias = m['particoes']['treino']['familias']
    arrays = dict(x=np.asarray(xs,dtype=np.int32), y=np.asarray(ys,dtype=np.int32),
                  par=np.arange(len(es),dtype=np.int32),
                  origem=np.asarray([int(e['origem']=='humano_oasst2') for e in es],dtype=np.int8),
                  familia=np.asarray([familias[e['familia']] for e in es],dtype=np.int16))
    for nome, a in arrays.items(): np.save(saida/('dialogo_treino_'+nome+'.npy'), a)
    (saida/'dialogos_treino.jsonl').write_text(''.join(json.dumps(e,ensure_ascii=False,sort_keys=True)+'\n' for e in es))
    treino = m['particoes']['treino']
    treino.update(pares=len(es),humanos=contagens['humanos_retidos'],sinteticos=contagens['sinteticos_retidos'],
                  grupos=len({e['grupo'] for e in es}),janelas=len(es),tokens_alvo=int((arrays['y']!=-100).sum()),
                  com_historico=sum(bool(e['historico']) for e in es),descartados_janelas=0,
                  humanos_exportacao_completa=sum(e.get('fonte_exportacao')=='completa' for e in es),
                  familias_contagens=dict(collections.Counter(e['familia'] for e in es)))
    m['derivacao_dialogo_integro'] = dict(corpus_origem_sha256=sha(origem/'manifesto.json'),
        codigo_sha256=sha(__file__),contagens=dict(contagens),
        politica='um par completo por janela; sem calculados; validacao, teste e replay inalterados')
    m['amostragem_dialogo'] = dict(fracao_humana=.75,pares_uniformes=True,sinteticos_por_familia=True)
    m['arquivos'] = {nome:sha(saida/nome) for nome in sorted(m['arquivos'])}
    (saida/'manifesto.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    return m['derivacao_dialogo_integro']


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--origem',required=True);p.add_argument('--saida',required=True)
    a=p.parse_args();print(json.dumps(preparar(a.origem,a.saida),ensure_ascii=False,indent=2))
