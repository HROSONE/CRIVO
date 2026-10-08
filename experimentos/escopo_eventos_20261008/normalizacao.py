"""Preserva método anterior, corrigindo palavras funcionais confundidas com nomes.

Heurística limitada a nomes de uma palavra capitalizada. Ambos os braços recebem
o mesmo tratamento; não são usados rótulos/gold para construir a entrada neural.
"""
from base import ASSOC
import importlib.util

spec=importlib.util.spec_from_file_location('norm_eventos',ASSOC/'normalizar.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
mod.FUNCIONAIS=set(mod.FUNCIONAIS)|set(('Estou Está Estamos Estão Estava Estavam '
    'Refaça Refazer Refaço Refaçam Recalcule Recalcular Numa Num Numas Nuns '
    'Neste Nesta Nesse Nessa Nesses Nessas Desfaça Desfazer Atualização Mudança '
    'Confirmo Confirmei Confirmado Confirmada Confirmação Suponha Supondo '
    'Admitamos Admitindo Pensando Projete Projetando Suponhamos Teste Testando '
    'Continuando Continuemos Mantenha Mantendo Retornando Retorne Retornar '
    'Abandone Abandonando Abandonar Cancele Cancelando Cancelar Ignorando Ignore '
    'Mesmo Tanto Porém Entretanto Afinal Apenas Somente Fora Dentro '
    'Contratar Houve Deixe Isto Informação Considere Verifique Confira Inventário '
    'Acabei Encerre Corrijo Corrigindo Continue Retome').casefold().split())
codificar=mod.codificar
normalizar=mod.normalizar
