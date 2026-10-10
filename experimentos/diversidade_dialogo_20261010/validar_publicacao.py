"""Confirma commit e pesos realmente ativos no site; não valida diálogo geral."""
import argparse
import json
import urllib.request
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--saida',required=True);a=p.parse_args()
url='https://crivo-mauve.vercel.app/api/chat'
sha=a.checkpoint
out={'commit_esperado':a.commit,'checkpoint_esperado':sha,'sessoes':[]}
dest=Path(a.saida)
def salvar():dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
def health():
    with urllib.request.urlopen(url+'?verificacao=diversidade20261010',timeout=90) as r:return json.load(r)
def validar_health(h):
    assert h['build_commit']==a.commit,h['build_commit']
    assert h['dialogue_generation']['checkpoint_sha256']==sha
    assert h['dialogue_generation']['ativa']
    assert not h['external_ai'] and not h['experimental_dialogue']
out['health_antes']=health();salvar();validar_health(out['health_antes'])
sondas=[('capacidade_fato',['Nunca usei você. O que consegue fazer?','O que é diferença de potencial?','De onde vem isso?']),
        ('memoria',['Minha amiga Odrélia prefere jabuticaba.','O que Odrélia prefere?']),
        ('escrita',['Conte uma história curta sobre um tatu ilustrador em uma oficina de cobre.',
                   'Quero uma história sem viagem e sem mapa.',
                   'Continue com ele tentando consertar uma mochila.',
                   'Ele pede ajuda a uma vizinha. Continue a partir disso.',
                   'A vizinha trouxe uma linha verde. Use isso na história.',
                   'Não mude a cor da linha.',
                   'Faça um final tranquilo.',
                   'Resuma a história que você escreveu.'])]
for nome,turnos in sondas:
    anteriores=[];rows=[];out['sessoes'].append({'id':nome,'resultados':rows})
    for i,t in enumerate(turnos):
        req=urllib.request.Request(url,data=json.dumps({'message':t,'history':anteriores},ensure_ascii=False).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=90) as r:
            assert r.status==200;resp=json.load(r)
        rows.append({'usuario':t,'resposta':resp});salvar();texto=resp['response'];g=resp['dialogue_generation']
        if nome=='capacidade_fato':
            if i==0:assert resp['id'].startswith('social:') and 'Posso' in texto
            elif i==1:assert resp['id'].startswith('conhecimento:') and resp['mechanism']=='composicao_factual' and 'volts' in texto and not g['usada']
            else:assert 'https://openstax.org/details/books/university-physics-volume-2' in texto
        elif nome=='memoria':assert 'Odrélia' in texto and 'jabuticaba' in texto and not g['usada']
        else:
            assert 'tatu ilustrador' in texto and 'oficina de cobre' in texto
            if i not in (5,7):
                assert g['usada'] and not g['experimental'] and g['checkpoint_sha256']==sha
                assert g['guarda']['aceita']
            else:assert resp['natural_routing']['peca']=='esclarecimento'
            if i>=1:assert 'mapa' not in texto.lower() and 'viagem' not in texto.lower()
            if i>=2:assert 'mochila' in texto
            if i>=3:assert 'vizinha' in texto
            if i==3:assert g['classe_escrita']=='companhia' and 'ajuda' in texto
            if i>=4:assert 'linha verde' in texto and 'linha azul' not in texto
        anteriores.append(t)
        print(nome,i+1,'PASS',texto[:120],flush=True)
out['health_depois']=health();validar_health(out['health_depois']);out['smokes_passaram']=13;out['checkpoint_novo_ativo']=True;salvar()
print(json.dumps({'smokes':13,'build_commit':a.commit,'checkpoint_ativo':sha,'limite':'Treze smokes conhecidos de capacidade/fato/fonte, memória e escrita. Repetição dos smokes anteriores, não entidades inéditas ou avaliação geral de conversa.'}))
