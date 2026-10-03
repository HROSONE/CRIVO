"""Corpus autoral de conceitos e código, reservado por família antes de variantes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def exemplos():
    tarefas = json.loads((ROOT / 'dados/programacao/tarefas.json').read_text())['tarefas']
    # Limitar variantes por família/linguagem evita que padrões simples dominem.
    contagem = {}
    for t in json.loads((ROOT / 'dados/programacao/curriculo.json').read_text())['tarefas']:
        chave = (t['familia'], t['linguagem'])
        n = contagem.get(chave, 0)
        if n < 4:
            tarefas.append(t); contagem[chave] = n + 1
    tarefas += json.loads((ROOT / 'dados/programacao/algoritmos.json').read_text())['tarefas']
    resultado = []
    for t in tarefas:
        resultado.append(dict(mensagem=t['mensagem'], resposta=t['resposta'],
                              grupo='codigo:' + t['familia'], split=t['split'],
                              origem='sintetico_autoral', historico=[]))
    catalogo = json.loads((ROOT / 'docs/pesquisa_conhecimento/programacao/catalogo-avancado.json').read_text())
    for u in catalogo['unidades']:
        # Todas as reformulações da mesma unidade ficam na mesma partição.
        b = int(hashlib.sha256(('programacao-v1:' + u['id']).encode()).hexdigest()[:8], 16) % 10
        split = 'validacao' if b == 0 else 'teste' if b == 1 else 'treino'
        for pergunta, campo in [('Explique ', 'definicao'), ('Como funciona ', 'mecanismo'),
                                ('Quais cuidados tomar com ', 'falhas_comuns'),
                                ('Como verificar ', 'verificacao')]:
            resultado.append(dict(mensagem=pergunta + u['conceito'] + '?', resposta=u[campo],
                                  grupo='conceito:' + u['id'], split=split,
                                  origem='sintese_autoral_nao_revisada_integralmente', historico=[]))
    # Nenhum alvo textual idêntico pode ocorrer em partições distintas.
    splits = {}
    for e in resultado:
        splits.setdefault(e['resposta'].strip(), set()).add(e['split'])
    return [e for e in resultado if len(splits[e['resposta'].strip()]) == 1]


def preparar(saida, contexto=256, tokenizer_existente=None, vocabulario=4096):
    import numpy as np
    from tokenizers import Tokenizer, models, pre_tokenizers, decoders, trainers
    from linguagem_profunda import ESPECIAIS, codificar_texto
    from scripts.preparar_linguagem_profunda import janelas_dialogo
    out = Path(saida)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Saída deve estar vazia; não sobrescreve corpus')
    if contexto < 16 or not 261 <= vocabulario <= 65535:
        raise ValueError('Contexto/vocabulário inválido')
    out.mkdir(parents=True, exist_ok=True)
    dados = exemplos()
    if tokenizer_existente:
        shutil.copyfile(tokenizer_existente, out / 'tokenizer.json')
        tok = Tokenizer.from_file(str(out / 'tokenizer.json'))
    else:
        tok = Tokenizer(models.BPE())
        tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
        tok.decoder = decoders.ByteLevel()
        tok.train_from_iterator((texto for e in dados if e['split'] == 'treino'
                                 for texto in (e['mensagem'], e['resposta'])),
            trainers.BpeTrainer(vocab_size=vocabulario, min_frequency=2,
                special_tokens=ESPECIAIS, initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
        tok.save(str(out / 'tokenizer.json'))
    tok.encode_special_tokens = True
    if tok.get_vocab_size() > 65535 or any(tok.token_to_id(t) is None for t in ESPECIAIS):
        raise ValueError('Tokenizer incompatível')
    m = dict(versao=1, contexto=contexto, vocabulario=tok.get_vocab_size(),
             natureza='curriculo_sintetico_autoral; não comprova capacidade de programador sênior',
             tokenizer_origem='proprio_preservado' if tokenizer_existente else 'somente_treino',
             fontes={str(p.relative_to(ROOT)): sha(p) for p in [ROOT / 'dados/programacao/tarefas.json', ROOT / 'dados/programacao/curriculo.json', ROOT / 'dados/programacao/algoritmos.json',
                 ROOT / 'docs/pesquisa_conhecimento/programacao/catalogo-avancado.json']},
             familias={}, particoes={})
    for split in ('treino', 'validacao', 'teste'):
        es = [e for e in dados if e['split'] == split]
        m['familias'][split] = sorted({e['grupo'] for e in es})
        (out / ('dialogos_' + split + '.jsonl')).write_text(''.join(json.dumps(e, ensure_ascii=False)+'\n' for e in es))
        xs, ys, ids = [], [], []
        for e in es:
            ids += [tok.token_to_id('<documento>')] + codificar_texto(tok, e['mensagem']+'\n'+e['resposta']) + [tok.token_to_id('<fim>')]
            for x,y in janelas_dialogo(tok,e,contexto):
                xs.append(x + [0]*(contexto-len(x)))
                ys.append(y + [-100]*(contexto-len(y)))
        np.asarray(ids,dtype='<u2').tofile(out / ('linguagem_'+split+'.bin'))
        np.save(out / ('dialogo_'+split+'_x.npy'),np.asarray(xs,dtype=np.int32).reshape(-1,contexto))
        np.save(out / ('dialogo_'+split+'_y.npy'),np.asarray(ys,dtype=np.int32).reshape(-1,contexto))
        np.save(out / ('dialogo_'+split+'_origem.npy'),np.zeros(len(xs),dtype=np.int8))
        m['particoes'][split] = dict(exemplos=len(es), janelas=len(xs), tokens_linguagem=len(ids))
    m['arquivos']={p.name:sha(p) for p in sorted(out.iterdir())}
    (out / 'manifesto.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    return m


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--saida',required=True);p.add_argument('--contexto',type=int,default=256)
    p.add_argument('--tokenizer');p.add_argument('--vocabulario',type=int,default=4096)
    a=p.parse_args()
    m=preparar(a.saida,a.contexto,a.tokenizer,a.vocabulario)
    print(json.dumps(dict(contexto=m['contexto'],vocabulario=m['vocabulario'],particoes=m['particoes']),ensure_ascii=False))
