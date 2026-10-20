"""Ponte para o motor do CRIVO em C (android/app/src/main/cpp/motor_crivo.c), usado no app Android.

O motor faz a mesma conta do NumPy (conversa_v3d.Conversa46mNumpy._passo), mas guarda os pesos em int8 na memória
(o NumPy multiplica tudo de volta para float32: 4 vezes mais RAM) e usa vários núcleos. São só os pesos próprios do
CRIVO: o arquivo do motor é feito aqui, uma vez, a partir do pesos_numpy.npz que o conversa_v3d já conferiu pelo SHA.

Liga quando CRIVO_MOTOR_NATIVO aponta para a biblioteca (o app faz isso; o site e o PC seguem no NumPy). Qualquer
falha (biblioteca ausente, arquivo que não bate) devolve None, e quem chamou continua no NumPy.
"""
import ctypes
import os
import struct
from pathlib import Path

MAGICO = b"CRIVOM1\0"


def _vet(np, a):
    return np.ascontiguousarray(np.asarray(a, dtype=np.float32).reshape(-1)).tobytes()


def _mat(np, p, nome):
    q = np.ascontiguousarray(p[nome + ".q8"], dtype=np.int8)
    bruto = q.tobytes()
    bruto += b"\0" * ((-len(bruto)) % 4)
    return bruto + _vet(np, p[nome + ".escala"])


def exportar(npz, destino):
    """Escreve o arquivo do motor (int8 por linha + escala float32; vetores em float32) a partir do npz int8."""
    import json
    import numpy as np
    p = np.load(npz)
    meta = json.loads(str(p["meta"]))
    V, D = p["embedding.weight.q8"].shape
    L, H, C = meta["camadas"], meta["cabecas"], meta["contexto"]
    partes = [MAGICO, struct.pack("<5i", V, D, L, H, C), _mat(np, p, "embedding.weight"), _mat(np, p, "posicao.weight")]
    for c in range(L):
        b = "blocos.%d." % c
        partes += [_vet(np, p[b + "norm1.weight"]), _vet(np, p[b + "norm1.bias"]), _mat(np, p, b + "qkv.weight"),
                   _mat(np, p, b + "projecao.weight"), _vet(np, p[b + "norm2.weight"]), _vet(np, p[b + "norm2.bias"]),
                   _mat(np, p, b + "mlp.0.weight"), _vet(np, p[b + "mlp.0.bias"]),
                   _mat(np, p, b + "mlp.2.weight"), _vet(np, p[b + "mlp.2.bias"])]
    partes += [_vet(np, p["norm.weight"]), _vet(np, p["norm.bias"])]
    destino = Path(destino)
    tmp = destino.with_suffix(".tmp")
    with open(tmp, "wb") as f:
        for b in partes:
            f.write(b)
    tmp.replace(destino)
    return destino


class MotorNativo:
    def __init__(self, biblioteca, arquivo, threads=None):
        import numpy as np
        self.np = np
        lib = ctypes.CDLL(str(biblioteca))
        lib.crivo_abrir.restype = ctypes.c_void_p
        lib.crivo_abrir.argtypes = [ctypes.c_char_p, ctypes.c_int]
        lib.crivo_info.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int)]
        lib.crivo_avancar.restype = ctypes.c_int
        lib.crivo_avancar.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int,
                                      ctypes.POINTER(ctypes.c_float)]
        lib.crivo_fechar.argtypes = [ctypes.c_void_p]
        threads = threads or min(4, os.cpu_count() or 2)
        self.lib, self.m = lib, lib.crivo_abrir(str(arquivo).encode(), threads)
        if not self.m:
            raise RuntimeError("o motor não abriu o arquivo de pesos")
        info = (ctypes.c_int * 5)()
        lib.crivo_info(self.m, info)
        self.vocabulario, self.dimensao, self.camadas, self.cabecas, self.contexto = list(info)
        self._logits = np.zeros(self.vocabulario, dtype=np.float32)

    def avancar(self, ids, inicio):
        """Logits (float32, cópia) da última de `ids`, nas posições inicio…; inicio=0 recomeça o cache."""
        ids = (ctypes.c_int * len(ids))(*ids)
        r = self.lib.crivo_avancar(self.m, ids, len(ids), inicio,
                                   self._logits.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))
        if r != 0:
            raise ValueError("motor: posição ou palavra fora do modelo (%d)" % r)
        return self._logits.copy()

    def __del__(self):
        if getattr(self, "m", None):
            self.lib.crivo_fechar(self.m)
            self.m = None


def carregar(npz, npz_sha256):
    """MotorNativo para o npz já conferido, ou None (sem a biblioteca ou em qualquer falha: segue o NumPy)."""
    biblioteca = os.environ.get("CRIVO_MOTOR_NATIVO")
    # Caminho completo, ou só o nome (no Android, a biblioteca pode estar dentro do APK, sem arquivo extraído).
    if not biblioteca or ("/" in biblioteca and not Path(biblioteca).is_file()):
        return None
    try:
        arquivo = Path(npz).with_name("pesos_motor_%s.bin" % npz_sha256[:16])
        if not arquivo.is_file():
            exportar(npz, arquivo)
        return MotorNativo(biblioteca, arquivo)
    except Exception as erro:
        print("motor_nativo: segue no NumPy:", type(erro).__name__, erro, flush=True)
        return None
