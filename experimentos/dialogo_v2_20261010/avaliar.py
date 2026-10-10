"""Mesmos critérios de #127, seis falhas reais adicionais e dez sessões intactas."""
import argparse
import copy
import hashlib
import importlib.util
import json
import re
import sys
import threading
import urllib.request
from pathlib import Path

H=Path(__file__).resolve().parent;ROOT=H.parent.parent
sys.path.insert(0,str(ROOT))
from crivo import Crivo
from ecossistema import mecanismo_do_turno
spec=importlib.util.spec_from_file_location('juiz',H.parent/'roteamento_natural_20261009/avaliar.py')
juiz=importlib.util.module_from_spec(spec);spec.loader.exec_module(juiz)

def avaliar(modo,saida,candidato=None,url=None,exigir=False,so_congelado=False):
    f=H/'casos_congelados.json'
    assert hashlib.sha256(f.read_bytes()).hexdigest()==(H/'SHA256').read_text().split()[0]
    servidor=None
    if modo=='http':
        from web_local import criar_servidor
        servidor=criar_servidor(port=0);servidor.checkpoint_dialogo_candidato=candidato
        threading.Thread(target=servidor.serve_forever,daemon=True).start()
        url='http://127.0.0.1:%s/api/chat'%servidor.server_address[1]
    def motor(bot,texto):
        ident,resposta=bot.responder(texto)
        return dict(id=ident,response=resposta,mechanism=mecanismo_do_turno(bot,texto,ident),
            natural_routing=copy.deepcopy(bot.ultima_rota_natural),dialogue_generation=copy.deepcopy(bot.dialogo_conversa.trace),
            has_proof=bool(ident.startswith(('conhecimento:','logica:'))))
    def chamar(texto,anteriores):
        if modo=='motor':
            b=Crivo(checkpoint_dialogo_candidato=candidato)
            for t in anteriores:b.responder(t)
            return motor(b,texto)
        pedido=urllib.request.Request(url,data=json.dumps({'message':texto,'history':anteriores},ensure_ascii=False).encode(),
                                     headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(pedido,timeout=90) as r:
            assert r.status==200;return json.load(r)
    out={'modo':modo,'experimental':bool(candidato),'casos_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),
        'resultados':[],'conversas':[]}
    def guardar():Path(saida).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    try:
        for c in json.loads(f.read_text())['casos']:
            r=chamar(c['entrada']['texto'],c['entrada']['anteriores']);row=juiz.pontuar(c,r)
            if c['resposta_minima_aceitavel'].get('exige_historia'):
                quantidade=c['resposta_minima_aceitavel'].get('frases') or (5 if c['id']=='real-19' else 3)
                row['historia_entregue']=(len(re.findall(r'[^.!?]+[.!?](?:\s|$)',r['response']))>=quantidade
                    and r['dialogue_generation']['usada'] and not row['referentes_ausentes'])
                row['peca_correta_com_evidencia'] &= row['historia_entregue']
            out['resultados'].append(row);out['resumo']=juiz.resumo(out['resultados']);guardar()
            print(c['id'],'PASS' if row['peca_correta_com_evidencia'] else 'FAIL',r['response'][:130],flush=True)
        for sessao in ([] if so_congelado else json.loads((H.parent/'integracao_dialogo_20261010/conversas_congeladas.json').read_text())['sessoes']):
            anteriores=[];rows=[];bot=Crivo(checkpoint_dialogo_candidato=candidato) if modo=='motor' else None
            for texto in sessao['turnos']:
                r=motor(bot,texto) if bot else chamar(texto,anteriores)
                rows.append({'usuario':texto,'resposta':r});anteriores.append(texto)
            out['conversas'].append({'sessao':sessao['id'],'criterio':sessao['criterio'],'resultados':rows});guardar()
            print('sessao',sessao['id'],'concluida',flush=True)
        if exigir:
            assert out['resumo']['pecas_corretas_com_evidencia']>=39
            assert out['resumo']['trocas_dominio']==out['resumo']['casos_com_referentes_ausentes']==0
            assert all(r.get('historia_entregue') for r in out['resultados'] if r['caso'] in ('real-19','real-20','pos127-03','pos127-05'))
        print(json.dumps(out['resumo']),flush=True);return out
    finally:
        if servidor:servidor.shutdown();servidor.server_close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--modo',choices=['motor','http','site'],required=True)
    p.add_argument('--saida',required=True);p.add_argument('--candidato');p.add_argument('--url')
    p.add_argument('--exigir-meta',action='store_true');p.add_argument('--so-congelado',action='store_true')
    a=p.parse_args();avaliar(a.modo,a.saida,a.candidato,a.url,a.exigir_meta,a.so_congelado)
