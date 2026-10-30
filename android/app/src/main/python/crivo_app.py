"""Ponte do app Android: sobe, dentro do aparelho, o mesmo servidor de web_local.py.

O app (MainActivity.kt) extrai o CRIVO empacotado (scripts/empacotar_apk.py) numa pasta do
aparelho e chama iniciar(pasta). O servidor escuta só em 127.0.0.1, numa porta livre, e a tela
do app mostra a mesma página do site. Sem internet: nada sai do aparelho.
"""
import os
import platform
import sys
import threading

PORTA = 8765
_servidor = None
_trava = threading.Lock()


def _motor_nativo_seguro(bibliotecas=None):
    """Só habilita o motor C em x86_64, onde há teste registrado.

    O motor C causou encerramento nativo no Android ARM. Como uma falha nativa
    encerra o processo sem exceção Python, em ARM mantemos NumPy até existir
    validação explícita no aparelho real.
    """
    arquitetura = platform.machine().strip().lower()
    # TESTE (branch claude/teste-motor-arm, não vai para a main): o motor novo, com threads simples no lugar do
    # OpenMP, também no celular ARM. Se ele derrubar o app, a marca do motor_nativo faz a próxima abertura voltar
    # ao NumPy, e o app mostra o motivo da queda.
    if arquitetura not in ("x86_64", "amd64", "aarch64", "arm64"):
        return ""
    motor = os.path.join(bibliotecas or "", "libcrivo_motor.so")
    return motor if bibliotecas and os.path.isfile(motor) else "libcrivo_motor.so"


def iniciar(pasta, bibliotecas=None):
    """Porta do servidor local (sobe uma vez por processo). `bibliotecas`: pasta das bibliotecas nativas."""
    global _servidor
    with _trava:
        if _servidor is not None:
            return _servidor.server_address[1]
        os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
        # TESTE: motor C também no ARM (ver _motor_nativo_seguro).
        os.environ["CRIVO_MOTOR_NATIVO"] = _motor_nativo_seguro(bibliotecas)
        if pasta not in sys.path:
            sys.path.insert(0, pasta)
        os.chdir(pasta)
        from web_local import criar_servidor
        try:
            # Porta fixa: o teste no emulador alcança o app por ela (adb forward).
            _servidor = criar_servidor("127.0.0.1", PORTA)
        except OSError:
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
