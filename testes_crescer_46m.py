"""O crescimento do 46M (scripts/crescer_46m.py) preserva o que o modelo diz: sem ruído, os mesmos logits."""
import importlib.util
import sys
import unittest
from pathlib import Path

DISPONIVEL = importlib.util.find_spec("torch") is not None
if DISPONIVEL:
    import torch
    sys.path.insert(0, str(Path(__file__).resolve().parent / "scripts"))
    import crescer_46m  # noqa: E402
    import linguagem_profunda as lp  # noqa: E402


@unittest.skipUnless(DISPONIVEL, "sem PyTorch")
class Crescer46m(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(0)
        self.config = {"vocabulario": 64, "dimensao": 24, "camadas": 6, "cabecas": 4, "contexto": 32, "dropout": 0.0}
        self.original = lp.LinguagemProfunda(lp.Configuracao(**self.config)).eval()
        for p in self.original.parameters():   # pesos não triviais, também nas normas e vieses
            p.data.normal_(0, 0.3)
        self.ids = torch.randint(0, 64, (2, 20), generator=torch.Generator().manual_seed(1))

    def crescido(self, camadas, ruido):
        estado, cfg = crescer_46m.crescer_estado(self.original.state_dict(), self.config, camadas, ruido)
        m = lp.LinguagemProfunda(lp.Configuracao(**cfg)).eval()
        m.load_state_dict(estado)
        return m, cfg

    def test_mesma_saida_sem_ruido(self):
        m, cfg = self.crescido(10, 0.0)
        self.assertEqual((cfg["dimensao"], cfg["cabecas"], cfg["camadas"]), (48, 8, 10))
        with torch.no_grad():
            self.assertLess(float((self.original(self.ids)[0] - m(self.ids)[0]).abs().max()), 1e-4)

    def test_ruido_pequeno_quase_igual(self):
        m, _ = self.crescido(10, 1e-4)
        with torch.no_grad():
            a, b = self.original(self.ids)[0], m(self.ids)[0]
        self.assertGreater(float((a.argmax(-1) == b.argmax(-1)).float().mean()), 0.95)
        self.assertGreater(float((a - b).abs().max()), 0.0)

    def test_camadas_novas_comecam_neutras(self):
        estado, cfg = crescer_46m.crescer_estado(self.original.state_dict(), self.config, 10, 1e-4)
        zerados = [k for k in estado if k.endswith("projecao.weight") and not estado[k].any()]
        self.assertEqual(len(zerados), 4)   # 10 - 6 blocos novos

    def test_tamanho_do_v7c_crescido(self):
        cfg = dict(vocabulario=8192, dimensao=384, camadas=24, cabecas=8, contexto=1024, dropout=0.0)
        estado = lp.LinguagemProfunda(lp.Configuracao(**cfg)).state_dict()
        novo, cfg2 = crescer_46m.crescer_estado(estado, cfg, 40, 0.0)
        self.assertAlmostEqual(sum(v.numel() for v in novo.values()) / 1e6, 290.5, delta=1.0)


if __name__ == "__main__":
    unittest.main()
