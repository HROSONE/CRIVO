"""Avaliação sintética do controlador; não certifica diagnóstico ou linguagem."""
import argparse
from dataclasses import asdict
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from investigacao_memoria import criar_investigacao, explicar


def avaliar(saida):
    casos=[];inicio=time.perf_counter()
    for pos_gc,cache,fila in itertools.product(('cresce','estavel'),repeat=3):
        dados=dict(pos_gc=pos_gc,cache=cache,fila=fila)
        i=criar_investigacao();i.observar(dict(runtime='node',metrica='heap'),'ambiente_informado')
        passos=[]
        for turno in range(4):
            antes=i.memoria.episodios();r=i.investigar()
            assert i.memoria.episodios()==antes,'Simulação não pode virar observação'
            assert len(r['passos'])<=6 and not r['comprovado']
            if r['campo'] is None:break
            assert r['campo'] not in i.memoria.observacoes(),'Não repetir medição conhecida'
            valor=dados[r['campo']]
            passos.append(dict(campo=r['campo'],valor_informado=valor,pergunta=r['pergunta']))
            i.observar({r['campo']:valor},'observacao_sintetica:'+str(turno))
        else:raise AssertionError('Investigação ultrapassou o orçamento')
        compativeis=[h['id'] for h in r['workspace']['hipoteses'] if not h['contradicoes']]
        if pos_gc=='estavel':
            assert passos[0]['campo']=='pos_gc' and len(passos)==1
            assert compativeis==['transitorio']
        if pos_gc==cache==fila=='cresce':assert set(compativeis)=={'retencao','cache','fila'}
        assert not any(h['comprovada'] for h in r['workspace']['hipoteses'])
        casos.append(dict(entradas_sinteticas=dados,perguntas=passos,
            perguntas_checklist=3,hipoteses_compativeis=compativeis,
            acao_final=r['acao'],resposta=explicar(r)))
    total=sum(len(c['perguntas']) for c in casos);checklist=3*len(casos)
    r=dict(versao=1,casos=casos,total_casos=len(casos),perguntas_controlador=total,
        perguntas_checklist=checklist,economia_perguntas_somente_neste_modelo=1-total/checklist,
        segundos=time.perf_counter()-inicio,
        codigo_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in
            ('workspace_cognitivo.py','investigacao_memoria.py','scripts/avaliar_workspace_cognitivo.py')},
        natureza='Combinações sintéticas de categorias do modelo editorial; não são medições reais.',
        limites=['Não mede compreensão de texto, conversa, diagnóstico real ou cognição humana.',
                 'Economia depende do modelo, dos custos e das respostas informadas.',
                 'Perguntas editoriais; regras e controle procedurais, sem novo treino neural.',
                 'Nenhuma hipótese é promovida a fato ou ao chat público.'])
    Path(saida).parent.mkdir(parents=True,exist_ok=True)
    Path(saida).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:r[k] for k in ('total_casos','perguntas_controlador','perguntas_checklist','economia_perguntas_somente_neste_modelo')},ensure_ascii=False))
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--saida',required=True)
    a=p.parse_args();avaliar(a.saida)
