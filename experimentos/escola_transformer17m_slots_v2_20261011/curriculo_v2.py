"""Currículo V2: mesmos 3.072 exemplos da Escola V1, mas slots abertos.

A única intervenção é elevar a cardinalidade de objeto/atividade de 8/8 para
512/512 combinações. Templates, atos, ordens, tamanho e distribuição permanecem.
"""
from __future__ import annotations
import random, sys
from pathlib import Path

V1=Path(__file__).resolve().parents[1]/"escola_transformer_17m_20261011"
sys.path.insert(0,str(V1))
import curriculo as base  # noqa:E402

SEMENTE=base.SEMENTE
OPERACOES=base.OPERACOES
ROTULOS=base.ROTULOS
OBJ_BASE=("estojo","sensor","placa","suporte","cartucho","bobina","pino","módulo","frasco","medidor","adaptador","painel","chaveiro","conector","amostra","bandeja","cápsula","registro","terminal","moldura","carretel","lacre","cilindro","prisma","rolete","estoque","marcador","calibrador","coletor","porta-amostra","seletor","disco")
OBJ_QUAL=("âmbar","cerâmico","modular","azulado","compacto","magnético","numerado","lacrado","fosco","flexível","térmico","óptico","auxiliar","portátil","graduado","selado")
ATIV_BASE=("catalogação","medição","montagem","revisão","inspeção","organização","calibração","registro","triagem","comparação","separação","limpeza","mapeamento","anotação","verificação","classificação","preparação","contagem","ajuste","documentação","marcação","conferência","avaliação","leitura","ensaio","simulação","rastreamento","amostragem","checagem","ordenação","inventário","monitoramento")
ATIV_QUAL=("comparativa","sequencial","de bancada","de rotina","instrumental","controlada","por etapas","de referência","técnica","visual","cruzada","de precisão","assistida","documental","experimental","periódica")

def _slot(indice):
 return f"{OBJ_BASE[indice%32]} {OBJ_QUAL[indice//32]}", f"{ATIV_BASE[indice%32]} {ATIV_QUAL[indice//32]}"

def _resp(op,estilo,pessoa,nova,objeto,atividade):
 return base.RESPOSTAS[op][estilo%len(base.RESPOSTAS[op])].format(pessoa=pessoa,nova=nova,objeto=objeto,atividade=atividade)

def gerar_treino():
 xs=[]; usados_obj=set(); usados_ativ=set()
 for lidx,lugar in enumerate(base.LUGARES):
  for variante in range(8):
   for rodada in range(4):
    indice=(lidx*8+variante)*4+rodada
    objeto,atividade=_slot(indice); usados_obj.add(objeto); usados_ativ.add(atividade)
    pessoa=base._nome(lidx+variante,rodada,False); nova=base._nome(lidx+variante,rodada,True)
    estilo=(variante+rodada+lidx)%8
    hist=[{"papel":"usuario","texto":f"Contexto: {pessoa} está {lugar} com {objeto} para uma atividade de {atividade}."},{"papel":"assistente","texto":f"Registrado. Pessoa {pessoa}; objeto {objeto}; atividade {atividade}."}]
    ordem=base.ORDENS[(variante+rodada)%len(base.ORDENS)]
    for turno,op in enumerate(ordem,1):
     msg=base.PERGUNTAS[op][estilo].format(pessoa=pessoa,nova=nova,objeto=objeto,atividade=atividade)
     resp=_resp(op,estilo,pessoa,nova,objeto,atividade); acao,foco=base.ROTULOS[op]
     xs.append({"id":f"esc17m-v2tr-{lidx}-{variante}-{rodada}-{turno}","historico":[dict(z) for z in hist],"mensagem":msg,"resposta":resp,"operacao":op,"acao":acao,"foco":foco})
     hist.extend([{"papel":"usuario","texto":msg},{"papel":"assistente","texto":resp}])
     if op=="corrigir_pessoa": pessoa=nova
 assert len(xs)==3072 and len(usados_obj)==512 and len(usados_ativ)==512
 assert {op:sum(x["operacao"]==op for x in xs) for op in OPERACOES}=={op:512 for op in OPERACOES}
 random.Random(SEMENTE).shuffle(xs)
 return xs

if __name__=="__main__":
 xs=gerar_treino(); print(len(xs),len({x['resposta'] for x in xs}),"slots",512,512)
