"""Ponte do app Android: sobe, dentro do aparelho, o mesmo servidor de web_local.py.

O app (MainActivity.kt) extrai o CRIVO empacotado (scripts/empacotar_apk.py) numa pasta do
aparelho e chama iniciar(pasta). O servidor escuta só em 127.0.0.1, numa porta livre, e a tela
do app mostra a mesma página do site. Sem internet: nada sai do aparelho.
"""
import os
import sys
import threading

_servidor = None
_trava = threading.Lock()


def iniciar(pasta):
    """Porta do servidor local (sobe uma vez por processo)."""
    global _servidor
    with _trava:
        if _servidor is not None:
            return _servidor.server_address[1]
        os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
        if pasta not in sys.path:
            sys.path.insert(0, pasta)
        os.chdir(pasta)
        from web_local import criar_servidor
        _servidor = criar_servidor("127.0.0.1", 0)
        threading.Thread(target=_servidor.serve_forever, name="crivo-servidor", daemon=True).start()
        threading.Thread(target=_aquecer, name="crivo-aquecer", daemon=True).start()
        return _servidor.server_address[1]


def _aquecer():
    """Carrega os pesos em segundo plano, para a primeira resposta não esperar por eles."""
    try:
        import conversa_v3d
        import realizador_17m
        conversa_v3d.numpy_do_site()
        realizador_17m.numpy_do_site()
    except Exception as erro:  # sem os pesos, o CRIVO responde com o texto de sempre
        print("crivo_app: aquecimento falhou:", type(erro).__name__, erro, flush=True)
