"""Compara gerações cruas dos pesos próprios; não escolhe por testes retidos."""
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from gerador_dialogo_numpy import GeradorNumpy

PASTA=Path(__file__).resolve().parent
CASOS=[
    ('precos', ['Um passeio custa 47 reais no parque. O outro custa 31 reais mais 9 de condução. Qual custa menos?',
                'A condução subiu para 18 reais. Ainda escolheria o mesmo pelo preço?']),
    ('agenda', ['Iara consegue terça ou quinta. Caio só consegue quinta. Em que dia podem se encontrar?',
                'Caio agora também consegue terça. Quinta continua sendo a única opção?']),
    ('correcao', ['Eu queria estudar toda noite, mas cuido da minha irmã na quarta. Como considerar isso?',
                 'Corrigindo: é na quinta que cuido dela, não na quarta. O que muda?']),
    ('regra', ['Neste jogo só recebe uma medalha quem tem ficha e selo. Davi tem ficha, mas não tem selo. Ele recebe?',
              'Ele ganhou um selo agora. Pela regra que eu disse, muda alguma coisa?'])
]


def main():
    manifesto=json.loads((PASTA/'protocolo.json').read_text())
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==manifesto['comparador_sha256']
    out=PASTA/'comparacao_bruta.json'
    if out.exists():raise SystemExit('Preserve a execução anterior.')
    resultados=[]
    for nome,rel in [('linguagem_2m6','artefatos/linguagem_profunda'),
                     ('base_leitor_17m','experimentos/pesos_base/leitor_transformer'),
                     ('modular_17m','experimentos/raciocinio_generativo/pesos_modulares')]:
        pasta=ROOT/rel
        m=GeradorNumpy(pasta)
        registro=dict(modelo=nome,pesos_sha256=hashlib.sha256((pasta/'pesos_numpy.npz').read_bytes()).hexdigest(),
                      parametros=sum(v.size for v in m.modelo.p.values()),casos=[])
        resultados.append(registro)
        for cid,perguntas in CASOS:
            historico=[];caso=dict(id=cid,turnos=[]);registro['casos'].append(caso)
            for pergunta in perguntas:
                inicio=time.monotonic()
                try:
                    fonte=m.fonte(pergunta,historico)
                    saida=m.responder(pergunta,historico,max_tokens=64,temperatura=0.)
                    saida['tokens_contexto']=len(fonte)
                except Exception as exc:saida=dict(erro=type(exc).__name__,mensagem=str(exc))
                saida.update(pergunta=pergunta,segundos=round(time.monotonic()-inicio,3))
                caso['turnos'].append(saida)
                historico.extend([dict(papel='usuario',texto=pergunta),dict(papel='assistente',texto=saida.get('texto',''))])
                out.write_text(json.dumps(dict(casos=resultados,limite='Painel autoral de desenvolvimento. Gerações cruas, sem recuperador e sem promoção.'),ensure_ascii=False,indent=2)+'\n')
                print(nome,cid,json.dumps(saida,ensure_ascii=False),flush=True)


if __name__=='__main__':main()
