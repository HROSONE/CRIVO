import tempfile
import unittest
from pathlib import Path
from rede_neural import RedeCrivo, caracteristicas


class TesteRedeNeural(unittest.TestCase):
    def test_normalizacao(self):
        self.assertEqual(caracteristicas("AÇÃO"), caracteristicas("acao"))

    def test_representacoes_e_compatibilidade(self):
        self.assertEqual(caracteristicas("casa"), caracteristicas("casa", modo="caracteres"))
        self.assertNotEqual(caracteristicas("casa", modo="palavras"), caracteristicas("casa", modo="misto"))
        with self.assertRaises(ValueError):
            caracteristicas("casa", modo="invalido")

    def test_morfologia_portuguesa(self):
        # Equivalencia por flexao e sinonimo codificados explicitamente.
        self.assertEqual(
            caracteristicas("molhar as plantas", modo="portugues"),
            caracteristicas("regar a planta", modo="portugues"))
        # Negacoes e interrogativos nao podem desaparecer como palavras vazias.
        self.assertNotEqual(
            caracteristicas("regar planta", modo="portugues"),
            caracteristicas("nao regar planta", modo="portugues"))
        self.assertNotEqual(
            caracteristicas("como regar planta", modo="portugues"),
            caracteristicas("quando regar planta", modo="portugues"))
        # As duas variantes permitem isolar o efeito de remover ligacoes.
        self.assertNotEqual(
            caracteristicas("regar a planta", modo="portugues"),
            caracteristicas("regar a planta", modo="portugues_sem_filtro"))

    def test_persistencia_modo_portugues(self):
        rede = RedeCrivo(["plantas", "clima"], dimensao=32, ocultos=4,
                          modo="portugues")
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "pesos.json"
            rede.salvar(caminho)
            restaurada = RedeCrivo.carregar(caminho)
            self.assertEqual(restaurada.modo, "portugues")
            self.assertEqual(rede.prever("molhar planta"),
                             restaurada.prever("molhar planta"))

    def test_aprendizado_real(self):
        exemplos = [
            ("regar a planta", "plantas"),
            ("molhar a planta", "plantas"),
            ("regar meu vaso", "plantas"),
            ("a terra do vaso", "plantas"),
            ("cachorro e gato", "animais"),
            ("cuidar do cachorro", "animais"),
            ("o gato e um animal", "animais"),
            ("meu cachorro", "animais"),
        ]
        rede = RedeCrivo(["plantas", "animais"], dimensao=128, ocultos=16)
        antes = [linha[:] for linha in rede.w1]
        rede.treinar(exemplos, epocas=160, taxa=0.3)
        self.assertNotEqual(antes, rede.w1)
        for frase, rotulo in exemplos:
            self.assertEqual(rede.prever(frase)[0], rotulo)

    def test_persistencia(self):
        rede = RedeCrivo(["sim", "nao"], dimensao=32, ocultos=4)
        rede.treinar([("sim sim", "sim"), ("nao nao", "nao")], epocas=25)
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "pesos.json"
            rede.salvar(caminho)
            carregada = RedeCrivo.carregar(caminho)
            self.assertEqual(rede.prever("sim"), carregada.prever("sim"))
            self.assertEqual(carregada.modo, "caracteres")


if __name__ == "__main__":
    unittest.main()
