"""Ponte do app Android: sobe, dentro do aparelho, o mesmo servidor de web_local.py.

O app (MainActivity.kt) extrai o CRIVO empacotado (scripts/empacotar_apk.py) numa pasta do
aparelho e chama iniciar(pasta). O servidor escuta só em 127.0.0.1, numa porta livre, e a tela
do app mostra a mesma página do site. Sem internet: nada sai do aparelho.
"""
import os
import sys
import threading

PORTA = 8765
_servidor = None
_trava = threading.Lock()


def iniciar(pasta, bibliotecas=None):
    """Porta do servidor local (sobe uma vez por processo). `bibliotecas`: a pasta das bibliotecas nativas do app."""
    global _servidor
    with _trava:
        if _servidor is not None:
            return _servidor.server_address[1]
        os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
        # O motor em C (motor_nativo.py): o caminho completo se a biblioteca estiver extraída; senão, o nome, que o
        # Android acha dentro do APK. Se não carregar, o CRIVO segue no NumPy.
        motor = os.path.join(bibliotecas or "", "libcrivo_motor.so")
        # Em celular ARM o motor ainda não foi visto funcionando (o teste automático roda num emulador x86_64), e o
        # 1.0.20 fechava ao abrir num aparelho real: lá, o 46M segue no NumPy até o motor ser conferido num ARM.
        if os.uname().machine in ("x86_64", "i686") or os.environ.get("CRIVO_MOTOR_ARM") == "1":
            os.environ.setdefault("CRIVO_MOTOR_NATIVO", motor if bibliotecas and os.path.isfile(motor) else "libcrivo_motor.so")
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
