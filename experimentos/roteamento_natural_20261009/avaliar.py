"""Replay congelado pelo adaptador da API, sem memória preenchida pelo teste."""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

H=Path(__file__).resolve().parent
ROOT=H.parent.parent
sys.path.insert(0,str(ROOT))
from web_core import responder_web
from composicao_textual import normalizar

def contem(texto, termo):
    return re.search(r'(?<!\w)'+re.escape(normalizar(termo))+r'(?!\w)',normalizar(texto)) is not None

def peca(r):
    route=r.get('natural_routing')
    if route and route.get('executor'):
        return route['peca']
    ident=r['id'];m=r.get('mechanism','')
    if 'memoria_sessao' in m or m=='conversa_sessao':return 'memoria'
    if ident=='conversa:raciocinio' or ident.startswith('calculo:'):return 'calculo'
    if ident.startswith('programacao:'):return 'programacao'
    if ident.startswith(('escrita:','conversa:gerada_')):return 'escrita'
    if ident.startswith('social:') or ident in ('fora','duvida') or 'esclarecer' in ident:return 'esclarecimento'
    return 'fato' if r.get('has_proof') or m in ('composicao_factual','busca_factual','leitura_ficha','recuperador','geracao_ancorada') else 'outro'

def main():
    p=argparse.ArgumentParser();p.add_argument('--saida',required=True);a=p.parse_args()
    f=H/'casos_congelados.json'
    sha=hashlib.sha256(f.read_bytes()).hexdigest()
    assert sha==(H/'SHA256').read_text().split()[0]
    cases=json.loads(f.read_text())['casos'];rows=[]
    out={'codigo':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
         'casos_sha256':sha,'metodo':'adaptador da API padrão; replay de no máximo dois turnos de usuário; sem memory injetada','resultados':rows}
    for c in cases:
        r=responder_web({'message':c['entrada']['texto'],'history':c['entrada']['anteriores']})
        e=c['esperado'];text=r['response'];route=peca(r)
        desvios=[v for v in e['desvios_proibidos'] if contem(text,v)]
        faltam=[v for v in e['conteudo_minimo'] if not contem(text,v)]
        # A rota não ganha crédito só por atribuir um rótulo: exige evidência
        # de resposta útil do executor e ausência de desvios observados.
        ok=route==e['peca'] and not faltam and not desvios
        rows.append({'caso':c['id'],'peca_observada':route,'peca_esperada':e['peca'],
                     'peca_correta_com_evidencia':ok,'faltam':faltam,'desvios':desvios,'resposta':r})
        out['resumo']={'pecas_corretas_com_evidencia':sum(x['peca_correta_com_evidencia'] for x in rows),
                       'total':len(rows),'desvios':sum(bool(x['desvios']) for x in rows)}
        Path(a.saida).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
        print(c['id'],route,'PASS' if ok else 'FAIL','faltam='+repr(faltam),'desvios='+repr(desvios),flush=True)
    print(json.dumps(out['resumo'],ensure_ascii=False),flush=True)

if __name__=='__main__':main()
