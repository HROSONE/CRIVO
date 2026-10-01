"""Gate conservador de certificação de módulos de Astronomia.

Não executa testes nem cria evidências: apenas valida medições previamente
registradas. A aprovação requer auditoria humana e CI no commit avaliado.
"""
from math import isfinite

CAMPOS_BOOLEANOS = ("editorial", "ci", "revisao", "prova_independente")
CAMPOS_METRICAS = ("simbolico", "neural", "controles")


def certificar_modulo(evidencias):
    """Aprova somente evidência explícita, sem converter catálogo em competência.

    simbólico e neural exigem >= 90%; controles exigem 100% de abstenção.
    Valores ausentes, booleanos disfarçados de nota, NaN e infinitos reprovam.
    """
    if not isinstance(evidencias, dict):
        return False
    if not all(evidencias.get(chave) is True for chave in CAMPOS_BOOLEANOS):
        return False
    for chave in CAMPOS_METRICAS:
        valor = evidencias.get(chave)
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            return False
        if not isfinite(valor) or not 0 <= valor <= 1:
            return False
        if valor < (1.0 if chave == "controles" else 0.9):
            return False
    return True
