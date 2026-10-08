"""Mesmo método de cópia limitada, com prefixos explícitos de regra.

Ambas as versões de pesos são avaliadas com este mesmo decodificador. Os
prefixos são ajuda de gramática, não inferência aprendida nem linguagem livre.
"""
from comum import ANTERIOR
import importlib.util

spec=importlib.util.spec_from_file_location('copia_associacao',ANTERIOR/'decodificar_limitado.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
mod.PADROES=dict(mod.PADROES)
mod.PADROES['regra']=r'\b(?:exigidos|exigidas|requeridos|requeridas)\s+(?:(?:para entrar|nesse acesso)\s+)?(?:são\s+)?([^.!?;\n]+)'
proposta_limitada=mod.proposta_limitada
