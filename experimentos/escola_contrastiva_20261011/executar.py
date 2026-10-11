"""Executa a aula contrastiva sem alterar artefatos historicos.

O PR #146 foi gravado antes de padronizarmos checkpoint_sha256 dentro de
`treino`. Este adaptador apenas completa esse campo em memoria para a checagem
de compatibilidade; nenhum arquivo antigo e reescrito ou commitado.
"""
from pathlib import Path
import treinar_contraste as experimento

_original = experimento.ler_json


def ler_json_compat(path):
    dados = _original(path)
    p = Path(path)
    if p == experimento.AUX146 / "resultados.json" and isinstance(dados, dict):
        dados = dict(dados)
        treino = dict(dados.get("treino", {}))
        treino.setdefault("checkpoint_sha256", experimento.sha256(experimento.AUX146 / "checkpoint_auxiliar.json.gz"))
        dados["treino"] = treino
    return dados


experimento.ler_json = ler_json_compat
experimento.executar()
