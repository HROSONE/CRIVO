"""Diagnóstico do gerador: saída livre, sem fornecer prefixo alvo."""
import copy
import gzip
import hashlib
import json
import sys
from pathlib import Path

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parent.parent))
from linguagem_gerativa import GeradorGRU, atributos, tokenizar

def main():
    checkpoint = H / 'checkpoint_gru_dialogo.json.gz'
    dados = json.loads(gzip.decompress(checkpoint.read_bytes()))
    corpus = json.loads((H / 'corpus_gru.json').read_text())
    modelo = GeradorGRU(dados)
    exemplos = [e for e in corpus['exemplos'] if e['split'] == 'validacao' and e['id'].startswith('evento-')]
    # Todas as classes, variantes, estilos e presenças de argumentos.
    rows = []
    for e in exemplos:
        g = modelo.gerar(e['contexto'], max_tokens=128)
        rows.append(dict(id=e['id'], familia=e['familia'], completa=g['completa'],
                         correta=g['tokens']==tokenizar(e['resposta']), tokens=g['tokens']))
    cues = {}
    for e in exemplos:
        c = dict(acao='continuacao', slots={'tema1':'uma personagem'}, estilo='neutro', variante=0,
                 mensagem=e['contexto']['mensagem'], historico=[], resposta_anterior='')
        cues[e['familia']] = atributos(c)
    assert len(set(tuple(v) for v in cues.values())) == len(cues)
    saida = dict(checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                 corpus_sha256=hashlib.sha256((H/'corpus_gru.json').read_bytes()).hexdigest(),
                 total=len(rows),corretas=sum(r['correta'] for r in rows),
                 completas=sum(r['completa'] for r in rows), classes_distintas=len(cues),
                 limite='Padrões autorais compartilhados entre treino e validação. Correspondência de tokens é diagnóstico de aprendizagem controlada, não gate de diálogo ou prova de generalização.', resultados=rows)
    (H/'gerador_validacao_livre.json').write_text(json.dumps(saida,ensure_ascii=False,indent=2)+'\n')
    print({k:v for k,v in saida.items() if k!='resultados'})

if __name__ == '__main__': main()
