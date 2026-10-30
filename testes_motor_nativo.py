"""O motor do app em C (android/app/src/main/cpp/motor_crivo.c, via motor_nativo.py) dá as mesmas respostas do NumPy.

Compila a biblioteca com o compilador C da máquina (pula sem compilador ou sem os pesos do 46M) e compara, palavra
por palavra, a conversa do 46M nos dois motores.
"""
import os
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

import conversa_v3d
import motor_nativo

RAIZ = Path(__file__).resolve().parent
FONTE = RAIZ / "android" / "app" / "src" / "main" / "cpp" / "motor_crivo.c"


def compilar(destino):
    cc = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if not cc:
        return None
    lib = Path(destino) / "libcrivo_motor.so"
    r = subprocess.run([cc, "-O3", "-fopenmp-simd", "-fPIC", "-shared", "-o", str(lib), str(FONTE), "-lm", "-lpthread"],
                       capture_output=True, text=True)
    return lib if r.returncode == 0 else None


class MotorNativo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.lib = compilar(cls.tmp)
        if cls.lib is None:
            raise unittest.SkipTest("sem compilador C")
        os.environ.pop("CRIVO_MOTOR_NATIVO", None)
        try:
            cls.ref = conversa_v3d.Conversa46mNumpy()
        except RuntimeError as erro:
            raise unittest.SkipTest("sem os pesos do 46M: %s" % erro)
        npz = conversa_v3d.PASTA_46M / "pesos_numpy.npz"
        arquivo = motor_nativo.exportar(npz, Path(cls.tmp) / "pesos.bin")
        cls.nat = conversa_v3d.Conversa46mNumpy.__new__(conversa_v3d.Conversa46mNumpy)
        cls.nat.__dict__.update(cls.ref.__dict__)
        cls.nat.motor = motor_nativo.MotorNativo(cls.lib, arquivo, threads=2)
        cls.nat._trava = threading.Lock()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_mesmos_logits(self):
        ids = self.ref.prompt_conversa({"quem": conversa_v3d.QUEM}, ["oi", "Oi! Tudo bem?"], "tô triste hoje")
        a = self.ref._logits(ids, 0, {})
        b = self.nat._logits(ids, 0, {})
        self.assertLess(float(abs(a - b).max()), 1e-3)
        self.assertEqual(int(a.argmax()), int(b.argmax()))

    def test_mesmas_respostas(self):
        for historico, fala in (([], "kkkkk"), ([], "tô triste hoje"), (["eae tudo bem", "Tudo bem, sim! E você?"], "legal e voce?"),
                                ([], "você é um robô?"), ([], "tenho dois cachorros"), ([], "qual é o seu nome?")):
            ctx = {"quem": conversa_v3d.QUEM}
            self.assertEqual(self.ref.conversar(ctx, historico, fala, prazo=0), self.nat.conversar(ctx, historico, fala, prazo=0), fala)

    def test_conversa_reaproveita_o_comeco_sem_mudar_as_respostas(self):
        # Cada turno começa igual ao anterior (identidade, lembranças, falas): só a parte nova é calculada, no motor em C
        # e no NumPy, e as respostas são as mesmas de calcular tudo do zero a cada turno.
        ctx = {"quem": conversa_v3d.QUEM, "lembrancas": ["a pessoa disse: meu nome é Ana"]}
        falas = ("oi, tudo bem?", "tô cansado do trabalho", "meu chefe me cobra demais", "você é um robô?")
        for modelo in (self.nat, self.ref):
            with self.subTest(motor="C" if modelo.motor else "NumPy"):
                historico, calculadas = [], []
                for fala in falas:
                    zero = conversa_v3d.Conversa46mNumpy.__new__(conversa_v3d.Conversa46mNumpy)
                    zero.__dict__.update(modelo.__dict__)
                    zero._prefixo, zero._no_motor, zero._trava = None, [], threading.Lock()
                    esperado = zero.conversar(ctx, historico, fala, prazo=0)
                    if modelo.motor:   # o cache do motor voltou a ser o da conversa reaproveitada: refaz o que estava nele
                        modelo.motor.avancar(modelo._no_motor or [modelo.esp["<fim>"]], 0)
                    ids = modelo.prompt_conversa(ctx, historico, fala)
                    calculadas.append(len(ids) - conversa_v3d._comum(modelo._no_motor if modelo.motor else
                                                                     (modelo._prefixo[0] if modelo._prefixo else []), ids))
                    self.assertEqual(modelo.conversar(ctx, historico, fala, prazo=0), esperado, fala)
                    historico += [fala, esperado[0]]
                # a partir do segundo turno, só uma parte do prompt é calculada
                self.assertTrue(all(c < len(modelo.prompt_conversa(ctx, [], falas[0])) for c in calculadas[1:]), calculadas)

    def test_erro_no_motor_esquece_o_cache(self):
        class Quebrado:
            def avancar(self, ids, inicio):
                raise RuntimeError("falhou")
        m = conversa_v3d.Conversa46mNumpy.__new__(conversa_v3d.Conversa46mNumpy)
        m.__dict__.update(self.nat.__dict__)
        m.motor, m._no_motor, m._prefixo = Quebrado(), [1, 2, 3], None
        with self.assertRaises(RuntimeError):
            m._logits([1, 2, 3, 4], 0, {})
        self.assertEqual(m._no_motor, [])

    def test_arquivo_errado_nao_abre(self):
        falso = Path(self.tmp) / "falso.bin"
        falso.write_bytes(b"CRIVOM1\0" + b"\0" * 64)
        with self.assertRaises(RuntimeError):
            motor_nativo.MotorNativo(self.lib, falso)

    def test_sem_biblioteca_segue_no_numpy(self):
        os.environ["CRIVO_MOTOR_NATIVO"] = "/nao/existe/libcrivo_motor.so"
        try:
            self.assertIsNone(motor_nativo.carregar(conversa_v3d.PASTA_46M / "pesos_numpy.npz", "0" * 64))
        finally:
            os.environ.pop("CRIVO_MOTOR_NATIVO", None)

    def test_abertura_que_derrubou_o_app_nao_se_repete(self):
        # Um erro no código nativo derruba o processo: a marca da abertura anterior faz o CRIVO seguir no NumPy.
        pasta = Path(self.tmp) / "marca"
        pasta.mkdir()
        npz = pasta / "pesos_numpy.npz"
        npz.symlink_to(conversa_v3d.PASTA_46M / "pesos_numpy.npz")
        os.environ["CRIVO_MOTOR_NATIVO"] = str(self.lib)
        try:
            (pasta / "motor_nativo_abrindo").write_text("abrindo")
            self.assertIsNone(motor_nativo.carregar(npz, conversa_v3d.NPZ_SHA256_46M))
            (pasta / "motor_nativo_abrindo").unlink()
            self.assertIsNotNone(motor_nativo.carregar(npz, conversa_v3d.NPZ_SHA256_46M))
            self.assertFalse((pasta / "motor_nativo_abrindo").exists())
        finally:
            os.environ.pop("CRIVO_MOTOR_NATIVO", None)


if __name__ == "__main__":
    unittest.main()
