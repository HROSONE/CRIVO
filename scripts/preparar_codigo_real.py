"""Pré-treino nativo com fontes MIT/Apache-2.0 fixas; código externo só é analisado, nunca executado."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import shutil
import sys
import tarfile
import urllib.request
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.preparar_programacao import exemplos, sha

# Excluir fontes que implementam diretamente famílias do pequeno benchmark de teste.
# Isto não demonstra independência semântica: o benchmark anterior já foi observado.
RESERVADOS = re.compile(r'(product|uniq|unique|intersection|palindrom|factorial|binarySearch|rotate|dedup)', re.I)


def particao(grupo):
    n = int(hashlib.sha256(('codigo-real-v1:' + grupo).encode()).hexdigest()[:8], 16) % 10
    return 'validacao' if n == 0 else 'teste' if n == 1 else 'treino'


def permitido(path, prefixo):
    p = PurePosixPath(path)
    return (path.startswith(prefixo) and p.suffix in ('.js', '.ts') and
            not any(x in ('__tests__', 'tests', 'test', '__mocks__') for x in p.parts) and
            not any(x in p.name for x in ('.test.', '.test-', '.spec.', '.d.ts')) and
            not RESERVADOS.search(p.stem) and '..' not in p.parts)


def baixar_fontes(cache, fontes):
    cache.mkdir(parents=True, exist_ok=True)
    documentos, licencas = [], {}
    for f in fontes:
        p = cache / (f['id'] + '.tar.gz')
        if not p.exists():
            url = f.get('url') or 'https://codeload.github.com/{}/tar.gz/{}'.format(f['repositorio'], f['revisao'])
            with urllib.request.urlopen(url, timeout=60) as r:
                data = r.read(64 * 1024 * 1024 + 1)
            if len(data) > 64 * 1024 * 1024: raise ValueError('Arquivo remoto grande demais')
            p.write_bytes(data)
        if sha(p) != f['arquivo_sha256']: raise ValueError('SHA de fonte divergente: ' + f['id'])
        with tarfile.open(fileobj=io.BytesIO(p.read_bytes()), mode='r:gz') as tar:
            for m in tar:
                if not m.isfile() or m.size > 4 * 1024 * 1024: continue
                parts = m.name.split('/', 1)
                if len(parts) != 2: continue
                path = parts[1]
                if path == f['licenca']:
                    licencas[f['id']] = tar.extractfile(m).read().decode('utf-8')
                if not permitido(path, f['prefixo']): continue
                texto = tar.extractfile(m).read().decode('utf-8')
                # Mesmo nome de utilitário em bibliotecas/linguagens distintas não cruza partições.
                grupo = PurePosixPath(path).stem.lstrip('_').lower()
                documentos.append(dict(fonte=f['id'], caminho=path, grupo=grupo,
                    revisao=f['revisao'], licenca=f['spdx'], split=particao(grupo),
                    sha256=hashlib.sha256(texto.encode()).hexdigest(), texto=texto))
        marker = {'MIT':'Permission is hereby granted', 'Apache-2.0':'Apache License'}[f['spdx']]
        if f['id'] not in licencas or marker not in licencas[f['id']]:
            raise ValueError('Licença ausente/incompatível: ' + f['id'])
    # Também excluir duplicatas byte a byte, inclusive entre nomes distintos.
    vistos = set(); unicos = []
    for d in documentos:
        if d['sha256'] not in vistos: vistos.add(d['sha256']); unicos.append(d)
    return unicos, licencas


def validar_sintaxe(docs, out, tsc):
    """Parser TS e node --check. Não importa nem executa módulos do corpus."""
    js = out / 'analisar_fontes.cjs'
    js.write_text('''const fs = require('fs');
const ts = require(process.argv[2]);
const docs = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const result = docs.map(d => {
 const sf = ts.createSourceFile(d.caminho, d.texto, ts.ScriptTarget.Latest, true,
   d.caminho.endsWith('.ts') ? ts.ScriptKind.TS : ts.ScriptKind.JS);
 return {sha256:d.sha256, erros: sf.parseDiagnostics.map(x => ts.flattenDiagnosticMessageText(x.messageText, '\\n'))};
});
fs.writeFileSync(process.argv[4], JSON.stringify(result));
''')
    entrada = out / 'fontes_parser.json'; entrada.write_text(json.dumps(docs))
    resultado = out / 'sintaxe_fontes.json'
    subprocess.run(['node', str(js), str(Path(tsc).resolve().with_name('typescript.js')),
                    str(entrada), str(resultado)], check=True, timeout=60)
    erros = {r['sha256']: r['erros'] for r in json.loads(resultado.read_text())}
    aprovados = []
    for d in docs:
        if erros[d['sha256']]: continue
        if d['caminho'].endswith('.js'):
            alvo = out / 'checagem.mjs'; alvo.write_text(d['texto'])
            p = subprocess.run(['node', '--check', str(alvo)], capture_output=True, timeout=10)
            if p.returncode: continue
        aprovados.append(d)
    for p in (js, entrada, out / 'checagem.mjs'):
        if p.exists(): p.unlink()
    return aprovados


def preparar(saida, cache, tsc, contexto=512, vocabulario=4096, tokenizer_existente=None):
    import numpy as np
    from tokenizers import Tokenizer, models, pre_tokenizers, decoders, trainers
    from linguagem_profunda import ESPECIAIS, codificar_texto
    from scripts.preparar_linguagem_profunda import janelas_dialogo
    out = Path(saida)
    if out.exists() and any(out.iterdir()): raise ValueError('Saída deve estar vazia')
    out.mkdir(parents=True, exist_ok=True)
    if contexto < 16 or not 261 <= vocabulario <= 65535: raise ValueError('Configuração inválida')
    fontes_path = ROOT / 'dados/programacao/fontes_codigo.json'
    fontes = json.loads(fontes_path.read_text())['fontes']
    docs, licencas = baixar_fontes(Path(cache), fontes)
    antes = len(docs); docs = validar_sintaxe(docs, out, tsc)
    for id_, texto in licencas.items(): (out / ('LICENSE-' + id_ + '.txt')).write_text(texto)
    # Ajuste por instrução exclusivamente de código; conceitos não competem pelo alvo.
    es = [e for e in exemplos() if e['grupo'].startswith('codigo:')]
    logica_path = ROOT/'dados/programacao/logica.json'
    es += [dict(mensagem=t['mensagem'],resposta=t['resposta'],grupo='codigo:'+t['familia'],
        split=t['split'],origem='logica_autoral',historico=[],linguagem=t['linguagem'],tipo=t['tipo'])
        for t in json.loads(logica_path.read_text())['tarefas']]
    alvos = {}
    for e in es:alvos.setdefault(e['resposta'].strip(),set()).add(e['split'])
    es = [e for e in es if len(alvos[e['resposta'].strip()])==1]
    tok = Tokenizer(models.BPE()); tok.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tok.decoder = decoders.ByteLevel()
    if tokenizer_existente:
        tok = Tokenizer.from_file(str(tokenizer_existente))
        if tok.get_vocab_size()!=vocabulario:raise ValueError('Vocabulário do tokenizer inicial incompatível')
    else:
        tok.train_from_iterator([d['texto'] for d in docs if d['split'] == 'treino'] +
            [texto for e in es if e['split'] == 'treino' for texto in (e['mensagem'], e['resposta'])],
            trainers.BpeTrainer(vocab_size=vocabulario, min_frequency=2, special_tokens=ESPECIAIS,
                               initial_alphabet=pre_tokenizers.ByteLevel.alphabet()))
    if any(tok.token_to_id(t) is None for t in ESPECIAIS):raise ValueError('Tokenizer sem marcadores próprios')
    if tokenizer_existente:shutil.copyfile(tokenizer_existente,out/'tokenizer.json')
    else:tok.save(str(out/'tokenizer.json'))
    tok.encode_special_tokens = True
    manifesto = dict(versao=1, contexto=contexto, vocabulario=tok.get_vocab_size(),
        natureza='Código MIT/Apache-2.0 real + instruções autorais; pequeno modelo experimental, sem garantia de nível sênior',
        fontes=fontes, fontes_manifesto_sha256=sha(fontes_path),
        instrucao_fontes_sha256={p:sha(ROOT/p) for p in ('dados/programacao/tarefas.json',
            'dados/programacao/curriculo.json','dados/programacao/algoritmos.json','dados/programacao/logica.json')},
        validacao_fontes=dict(candidatos=antes, aprovados=len(docs), criterio='sintaxe; não é verificação funcional ou de tipos externos'),
        limitacoes='Partições por nome de utilitário + deduplicação exata; sem prova de independência semântica. Benchmark de teste já observado.',
        particoes={})
    for split in ('treino', 'validacao', 'teste'):
        ds = [d for d in docs if d['split'] == split]; instrucoes = [e for e in es if e['split'] == split]
        ids = []
        for d in ds:
            ids += [tok.token_to_id('<documento>')] + codificar_texto(tok, d['texto']) + [tok.token_to_id('<fim>')]
        # Gramática da função resolver presente também no pré-treino (na respectiva partição).
        for e in instrucoes:
            ids += [tok.token_to_id('<documento>')] + codificar_texto(tok, e['resposta']) + [tok.token_to_id('<fim>')]
        np.asarray(ids, dtype='<u2').tofile(out / ('linguagem_' + split + '.bin'))
        xs, ys, familias = [], [], []
        mapa_familias = {}
        for e in instrucoes:
            lang = e.get('linguagem') or ('typescript' if 'typescript' in e['mensagem'].lower() else 'javascript')
            chave = e['grupo']+':'+lang
            familia_id = mapa_familias.setdefault(chave,len(mapa_familias))
            for x,y in janelas_dialogo(tok,e,contexto):
                familias.append(familia_id)
                xs.append(x + [0]*(contexto-len(x))); ys.append(y + [-100]*(contexto-len(y)))
        for nome,arr in [('x',xs),('y',ys)]:
            np.save(out/('dialogo_'+split+'_'+nome+'.npy'), np.asarray(arr,dtype=np.int32).reshape(-1,contexto))
        np.save(out/('dialogo_'+split+'_familia.npy'),np.asarray(familias,dtype=np.int32))
        np.save(out/('dialogo_'+split+'_origem.npy'),np.zeros(len(xs),dtype=np.int8))
        for nome,registros in [('fontes',ds),('dialogos',instrucoes)]:
            (out/(nome+'_'+split+'.jsonl')).write_text(''.join(json.dumps(d,ensure_ascii=False)+'\n' for d in registros))
        manifesto['particoes'][split]=dict(arquivos_reais=len(ds),bytes_codigo=sum(len(d['texto'].encode()) for d in ds),
            grupos_fontes=sorted({d['grupo'] for d in ds}), familias_instrucao=sorted({e['grupo'] for e in instrucoes}),
            grupos_amostragem=mapa_familias, instrucoes=len(instrucoes),janelas=len(xs),tokens_linguagem=len(ids))
        if len(ids) <= contexto or not xs: raise ValueError('Partição insuficiente: '+split)
    manifesto['arquivos']={p.name:sha(p) for p in sorted(out.iterdir())}
    (out/'manifesto.json').write_text(json.dumps(manifesto,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:dict((n,v) for n,v in x.items() if isinstance(v,(int,float))) for k,x in manifesto['particoes'].items()},ensure_ascii=False),flush=True)
    return manifesto


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--saida',required=True);p.add_argument('--cache',required=True);p.add_argument('--tsc',required=True)
    p.add_argument('--tokenizer');p.add_argument('--contexto',type=int,default=512);p.add_argument('--vocabulario',type=int,default=4096)
    a=p.parse_args();preparar(a.saida,a.cache,a.tsc,a.contexto,a.vocabulario,a.tokenizer)
