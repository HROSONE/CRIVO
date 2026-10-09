"""Símbolos locais preservam fontes e aceitam consultas explícitas com ponto.

Heurística autoral limitada; usa somente turnos, sem evento, trajetória ou alvo.
"""
import re
from apoio import EVENTOS_DIR
import importlib.util
spec=importlib.util.spec_from_file_location('preparo_anterior',EVENTOS_DIR/'normalizacao.py')
ant=importlib.util.module_from_spec(spec);spec.loader.exec_module(ant)
mod=ant.mod

def normalizar(turnos):
    nomes={}
    for texto in turnos:
        for m in re.finditer(r'(?<!\w)[A-ZÀ-ÖØ-Þ][^\W\d_]+(?!\w)',texto):
            n=m[0].casefold()
            if n in mod.FUNCIONAIS or n in nomes:continue
            if len(nomes)==len(mod.SIMBOLOS):raise ValueError('Mais de oito nomes candidatos.')
            nomes[n]=mod.SIMBOLOS[len(nomes)]
    pat=re.compile(r'(?<!\w)(?:'+'|'.join(re.escape(n) for n in sorted(nomes,key=len,reverse=True))+r')(?!\w)',re.I) if nomes else None
    prioridade=[]
    if pat:
        for texto in turnos:
            for frase in re.findall(r'[^.!?\n]+[.!?]?',texto):
                ns=list(dict.fromkeys(m[0].casefold() for m in pat.finditer(frase)))
                consulta=frase.rstrip().endswith('?') or re.match(r'\s*(?:Compare|Calcule|Diga|Entre|Verifique|Quanto|Qual|Mostre|Confira)\b',frase)
                # Pergunta nominal sem números explícitos; preserva última ordem.
                nominal=len(ns)>=2 and not re.search(r'\d',frase)
                if len(ns)>=2 and (consulta or nominal):prioridade=ns
        ordem=prioridade+[n for n in nomes if n not in prioridade]
        nomes={n:mod.SIMBOLOS[i] for i,n in enumerate(ordem)}
    saida=[];mapas=[]
    for texto in turnos:
        novo=[];mapa=[];ultimo=0
        for m in pat.finditer(texto) if pat else []:
            novo.append(texto[ultimo:m.start()]);mapa.extend((i,i+1) for i in range(ultimo,m.start()))
            s=nomes[m[0].casefold()];novo.append(s);mapa.extend([(m.start(),m.end())]*len(s));ultimo=m.end()
        novo.append(texto[ultimo:]);mapa.extend((i,i+1) for i in range(ultimo,len(texto)))
        saida.append(''.join(novo));mapas.append(mapa)
    return saida,mapas,nomes

mod.normalizar=normalizar
codificar=mod.codificar
