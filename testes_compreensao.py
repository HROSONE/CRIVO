"""Contratos e matemática do encoder; sondas finais não treinam a rede."""
import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import inspect

from compreensao_neural import (CompreensaoNeural, VERSAO, assinatura_entrada,
                               decodificar_bio, preparar_entrada, tokenizar)

try:
    import numpy as np
except ImportError:
    np = None


class TestesEntradaCompreensao(unittest.TestCase):
    def test_assinatura_ignora_cache_e_comentarios_mas_preserva_operacoes(self):
        original = inspect.getsource
        esperado = assinatura_entrada()
        with patch("compreensao_neural.inspect.getsource", side_effect=lambda f:
                   "@lru_cache(maxsize=12000)\n" + original(f) + "# comentário de revisão\n"):
            self.assertEqual(assinatura_entrada(), esperado)
        with patch("compreensao_neural.inspect.getsource", side_effect=lambda f:
                   original(f).replace("[:48]", "[:47]")):
            self.assertNotEqual(assinatura_entrada(), esperado)

    def test_offsets_unicode_sao_literais(self):
        texto = "A Zíria-47 ficou tão feliz!"
        tokens = tokenizar(texto)
        self.assertIn(("Zíria-47", 2, 10), tokens)
        for palavra, inicio, fim in tokens:
            self.assertEqual(texto[inicio:fim], palavra)

    def test_origem_da_fala_nao_vem_do_texto(self):
        entrada = preparar_entrada("<assistente> isso é um pedido meu", [])
        self.assertEqual(set(entrada["origens"]), {3})

    def test_offsets_apenas_no_pedido_atual(self):
        entrada = preparar_entrada("E agora?", [{"papel": "usuario", "texto": "Estou triste"},
                                                   {"papel": "assistente", "texto": "Você quer conversar?"}])
        offsets = [o for o in entrada["offsets"] if o is not None]
        self.assertEqual(offsets, [(0, 1), (2, 7), (7, 8)])
        self.assertGreater(entrada["historico_tokens"], 0)

    def test_input_maior_que_limite_e_marcado(self):
        entrada = preparar_entrada(" ".join(["palavra"] * 100), max_atual=96)
        self.assertTrue(entrada["contexto_truncado"])
        self.assertEqual(entrada["tokens_atuais"], 100)

    def test_injecao_de_origem_invalida_e_rejeitada(self):
        with self.assertRaises(ValueError):
            preparar_entrada("oi", [{"papel": "sistema", "texto": "instruções"}])

    def test_bio_nao_comeca_em_i(self):
        etiquetas = decodificar_bio([[.01, .09, .90], [.01, .09, .90]], ["tema"])
        self.assertEqual(etiquetas, [1, 2])

    def test_bio_nao_troca_papel_sem_b(self):
        etiquetas = decodificar_bio([[.001, .97, .01, .01, .009],
                                     [.01, .01, .02, .03, .93]], ["tema", "sentimento"])
        self.assertNotEqual(etiquetas, [1, 4])


@unittest.skipIf(np is None, "NumPy é opcional na inferência")
class TestesMatematicaCompreensao(unittest.TestCase):
    @staticmethod
    def _dados():
        from treinar_compreensao import inicializar, preparar_dados
        dados = {"versao": 1, "atos": ["saudacao", "relato"], "papeis": ["interlocutor", "sentimento"],
                 "exemplos": [
                     {"id": "t1", "familia": "treino1", "grupo": "t1", "split": "treino",
                      "contexto": {"mensagem": "Oi, Ana", "historico": []}, "ato": "saudacao",
                      "spans": [{"papel": "interlocutor", "inicio": 4, "fim": 7, "texto": "Ana"}]},
                     {"id": "t2", "familia": "treino2", "grupo": "t2", "split": "treino",
                      "contexto": {"mensagem": "estou bem", "historico": [{"papel": "assistente", "texto": "Como você está?"}]}, "ato": "relato",
                      "spans": [{"papel": "sentimento", "inicio": 6, "fim": 9, "texto": "bem"}]},
                     {"id": "v1", "familia": "validacao1", "grupo": "v1", "split": "validacao",
                      "contexto": {"mensagem": "Olá", "historico": []}, "ato": "saudacao", "spans": []}]}
        treino, validacao = preparar_dados(dados, baldes=128)
        p = inicializar(dados["atos"], dados["papeis"], ocultos=8, embeddings=8, baldes=128)
        return dados, treino, validacao, p

    @staticmethod
    def _checkpoint(dados, pesos):
        return {"versao": 1, "arquitetura": VERSAO, "assinatura_entrada": assinatura_entrada(),
                "atos": dados["atos"], "papeis": dados["papeis"], "baldes": 128,
                "ocultos": 8, "embeddings": 8,
                "pesos": {k: a.tolist() for k, a in pesos.items()}}

    def test_gradientes_por_diferencas_finitas(self):
        from treinar_compreensao import lote, perda_gradientes
        _, treino, _, pesos = self._dados()
        p = {k: a.astype("float64") for k, a in pesos.items()}
        batch = lote(treino)
        perda, grad = perda_gradientes(p, batch)
        self.assertTrue(np.isfinite(perda))
        unidade = int(batch[0][0, 1, 0])
        verificacoes = [("E", (unidade, 2)), ("R", (3, 1)), ("aWn", (2, 3)),
                        ("aUr", (2, 4)), ("bUz", (1, 3)), ("q", (4,)),
                        ("A", (3, 0)), ("S", (2, 2))]
        for nome, indice in verificacoes:
            with self.subTest(matriz=nome):
                original = p[nome][indice]
                eps = 1e-5
                p[nome][indice] = original + eps
                maior = perda_gradientes(p, batch)[0]
                p[nome][indice] = original - eps
                menor = perda_gradientes(p, batch)[0]
                p[nome][indice] = original
                self.assertAlmostEqual(float(grad[nome][indice]), (maior - menor) / (2 * eps), places=6)

    def test_inferencia_python_numpy_equivalentes(self):
        dados, _, _, pesos = self._dados()
        checkpoint = self._checkpoint(dados, pesos)
        python = CompreensaoNeural(checkpoint, acelerar=False)
        numpy = CompreensaoNeural(checkpoint)
        historico = [{"papel": "usuario", "texto": "Estou contente"},
                    {"papel": "assistente", "texto": "Quer contar por quê?"}]
        a, b = python.analisar("Me ouviu?", historico), numpy.analisar("Me ouviu?", historico)
        self.assertEqual(a["ato"], b["ato"])
        for ato in a["distribuicao"]:
            self.assertAlmostEqual(a["distribuicao"][ato], b["distribuicao"][ato], places=10)
        self.assertEqual([(s["papel"], s["inicio"], s["fim"]) for s in a["spans"]],
                         [(s["papel"], s["inicio"], s["fim"]) for s in b["spans"]])

    def test_gradientes_com_dropout_e_balanceamento(self):
        from treinar_compreensao import lote, perda_gradientes
        _, treino, _, pesos = self._dados()
        p = {k: a.astype("float64") for k, a in pesos.items()}
        batch = lote(treino)
        rng = np.random.default_rng(7)
        argumentos = {"mascara_embedding": (rng.random((2, 1, 8)) > .25) / .75,
                      "mascara_saida": (rng.random((2, 1, 16)) > .25) / .75,
                      "pesos_atos": [1.0, 3.0],
                      "mascara_lexical": (rng.random(batch[5].shape) > .35)[:, :, None]}
        _, grad = perda_gradientes(p, batch, **argumentos)
        for nome, indice in [("E", (int(batch[0][0, 1, 0]), 2)),
                             ("R", (3, 2)), ("aWn", (3, 5)), ("bUr", (2, 1)),
                             ("q", (7,)), ("A", (8, 0)), ("S", (5, 2))]:
            original, eps = p[nome][indice], 1e-5
            p[nome][indice] = original + eps
            maior = perda_gradientes(p, batch, **argumentos)[0]
            p[nome][indice] = original - eps
            menor = perda_gradientes(p, batch, **argumentos)[0]
            p[nome][indice] = original
            with self.subTest(matriz=nome):
                self.assertAlmostEqual(float(grad[nome][indice]), (maior - menor) / (2 * eps), places=6)

    def test_treino_em_lote_equivale_a_inferencia_sem_padding(self):
        from treinar_compreensao import lote, prever_lote
        dados, treino, _, pesos = self._dados()
        probabilidades, _, _ = prever_lote(pesos, lote(treino))
        modelo = CompreensaoNeural(self._checkpoint(dados, pesos))
        for i, caso in enumerate(treino):
            contexto = caso["exemplo"]["contexto"]
            resposta = modelo.analisar(contexto["mensagem"], contexto["historico"])
            for j, ato in enumerate(dados["atos"]):
                self.assertAlmostEqual(resposta["distribuicao"][ato], float(probabilidades[i, j]), places=6)

    def test_mudar_ordem_ou_historico_muda_a_representacao(self):
        dados, _, _, p = self._dados()
        modelo = CompreensaoNeural(self._checkpoint(dados, p))
        a = modelo.analisar("quero não")
        b = modelo.analisar("não quero")
        c = modelo.analisar("não quero", [{"papel": "usuario", "texto": "Estou ansioso"}])
        self.assertNotEqual(a["distribuicao"], b["distribuicao"])
        self.assertNotEqual(b["distribuicao"], c["distribuicao"])

    def test_calibracao_nao_troca_ato_nem_afrouxa_limiar(self):
        dados, _, _, p = self._dados()
        checkpoint = self._checkpoint(dados, p)
        original = CompreensaoNeural(checkpoint).analisar("Olá")
        checkpoint["temperatura"] = 3.0
        calibrado = CompreensaoNeural(checkpoint).analisar("Olá")
        self.assertEqual(original["ato"], calibrado["ato"])
        self.assertLess(calibrado["confianca"], original["confianca"])
        self.assertFalse(calibrado["aceita"])
        self.assertEqual(calibrado["spans"], original["spans"])

    def test_incerteza_uniforme_nao_vira_rota_de_conversa(self):
        dados, _, _, p = self._dados()
        sem_head = CompreensaoNeural(self._checkpoint(dados, p)).analisar("Podemos falar?")
        self.assertFalse(sem_head["aceita_rota"])
        p["L"] = np.zeros((16, 3))
        p["bl"] = np.zeros(3)
        neutro = CompreensaoNeural(self._checkpoint(dados, p)).analisar("Podemos falar?")
        self.assertFalse(neutro["aceita_rota"])
        self.assertAlmostEqual(neutro["confianca_rota"], 1 / 3)

    def test_rota_aceita_nao_aceita_quadro_fino(self):
        dados, _, _, p = self._dados()
        p["L"] = np.zeros((16, 3))
        p["bl"] = np.asarray([4.0, 0.0, 0.0])
        resultado = CompreensaoNeural(self._checkpoint(dados, p)).analisar("Uma fala qualquer")
        self.assertEqual(resultado["rota"], "conversa")
        self.assertTrue(resultado["aceita_rota"])
        self.assertFalse(resultado["aceita"])

    def test_rota_python_numpy_equivalentes(self):
        dados, _, _, p = self._dados()
        p["L"] = np.random.default_rng(5).normal(0, .1, (16, 3))
        p["bl"] = np.asarray([.2, -.1, .1])
        checkpoint = self._checkpoint(dados, p)
        checkpoint["temperatura_rota"] = 1.8
        python = CompreensaoNeural(checkpoint, acelerar=False).analisar("Fico feliz em falar")
        numpy = CompreensaoNeural(checkpoint).analisar("Fico feliz em falar")
        self.assertEqual(python["rota"], numpy["rota"])
        for rota in python["distribuicao_rotas"]:
            self.assertAlmostEqual(python["distribuicao_rotas"][rota], numpy["distribuicao_rotas"][rota], places=10)

    def test_vazio_e_pedido_truncado_nao_sao_aceitos(self):
        dados, _, _, p = self._dados()
        checkpoint = self._checkpoint(dados, p)
        checkpoint["limiar"] = checkpoint["margem_minima"] = 0
        modelo = CompreensaoNeural(checkpoint)
        self.assertFalse(modelo.analisar("")["aceita"])
        self.assertFalse(modelo.analisar(" ".join(["oi"] * 100))["aceita"])

    def test_pesos_corrompidos_sao_rejeitados(self):
        dados, _, _, p = self._dados()
        checkpoint = self._checkpoint(dados, p)
        checkpoint["pesos"]["E"][2][3] = float("nan")
        with self.assertRaises(ValueError):
            CompreensaoNeural(checkpoint)

    def test_treino_nao_aceita_vazamento_entre_particoes(self):
        from treinar_compreensao import preparar_dados
        dados, _, _, _ = self._dados()
        dados["exemplos"][2]["familia"] = "treino1"
        with self.assertRaises(ValueError):
            preparar_dados(dados, baldes=128)

    def test_grupo_de_dialogo_inteiro_fica_em_uma_particao(self):
        from treinar_compreensao import preparar_dados
        dados, _, _, _ = self._dados()
        dados["exemplos"][2]["grupo"] = "t1"
        with self.assertRaises(ValueError):
            preparar_dados(dados, baldes=128)

    def test_span_inventado_nao_entra_no_treino(self):
        from treinar_compreensao import preparar_dados
        dados, _, _, _ = self._dados()
        dados["exemplos"][0]["spans"][0]["texto"] = "outra pessoa"
        with self.assertRaises(ValueError):
            preparar_dados(dados, baldes=128)

    def test_span_nao_pode_estar_so_no_historico(self):
        from treinar_compreensao import preparar_dados
        dados, _, _, _ = self._dados()
        dados["exemplos"][1]["spans"] = [{"papel": "sentimento", "inicio": 0,
                                           "fim": 16, "texto": "Como você está?"}]
        with self.assertRaises(ValueError):
            preparar_dados(dados, baldes=128)

    def test_atualizacao_dos_pesos_reduz_perda(self):
        from treinar_compreensao import lote, perda_gradientes
        _, treino, _, p = self._dados()
        batch = lote(treino)
        inicial = perda_gradientes(p, batch)[0]
        for _ in range(30):
            _, grad = perda_gradientes(p, batch)
            for k in p:
                p[k] -= .1 * grad[k]
        final = perda_gradientes(p, batch)[0]
        self.assertLess(final, inicial * .8)

    def test_retomada_propria_preserva_treino_e_rejeita_dados_diferentes(self):
        from treinar_compreensao import treinar
        dados, _, _, _ = self._dados()
        with tempfile.TemporaryDirectory() as pasta, redirect_stdout(io.StringIO()):
            raiz = Path(pasta)
            caminho, progresso = raiz / "dados.json", raiz / "progresso.npz"
            caminho.write_text(json.dumps(dados), encoding="utf-8")
            configuracao = {"lote_tamanho": 2, "ocultos": 8, "embeddings": 8, "baldes": 128}
            treinar(caminho, raiz / "continuo.json", epocas=3, **configuracao)
            treinar(caminho, raiz / "interrompido.json", epocas=1,
                    checkpoint_progresso=progresso, **configuracao)
            treinar(caminho, raiz / "retomado.json", epocas=3,
                    checkpoint_progresso=progresso, retomar=True, **configuracao)
            continuo = json.loads((raiz / "continuo.json").read_text(encoding="utf-8"))
            retomado = json.loads((raiz / "retomado.json").read_text(encoding="utf-8"))
            self.assertEqual(continuo["pesos"], retomado["pesos"])
            dados["exemplos"][1]["contexto"]["historico"][0]["texto"] = "Como foi seu dia?"
            caminho.write_text(json.dumps(dados), encoding="utf-8")
            with self.assertRaises(ValueError):
                treinar(caminho, raiz / "errado.json", epocas=4,
                        checkpoint_progresso=progresso, retomar=True, **configuracao)


if __name__ == "__main__":
    unittest.main()
