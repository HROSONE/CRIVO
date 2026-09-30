"""Verificação do roteador aprendido e da separação de seus dados."""
import copy
import json
import unittest
from pathlib import Path

from intencao_gerativa import (ACOES, DIMENSAO, IntencaoGerativa, atributos,
                              normalizar_estado, caminho_padrao)
from rede_sequencial import assinatura, softmax
from treinar_intencao_gerativa import preparar_dados, estado_contexto, lexico_treino, temas_treino, tipo_historico


def exemplo(split, familia, texto, acao="escuta", historico=None, slots=None):
    return {"split": split, "familia": familia, "dialogo": familia + ":grupo",
            "contexto": {"acao": acao, "mensagem": texto, "historico": historico or [],
                         "slots": slots or {}}, "resposta": "Texto reservado à outra rede."}


class DadosIntencaoGerativa(unittest.TestCase):
    def test_estado_e_atributos_nao_leem_acao_nem_resposta(self):
        ctx = {"acao": "escuta", "mensagem": "Você entendeu isso?",
               "historico": ["Escreva um poema sobre uma colina"],
               "slots": {"relato": "O encontro foi difícil"}}
        original = estado_contexto(ctx)
        outro = copy.deepcopy(ctx)
        outro["acao"] = "historia"
        outro["resposta"] = "Um rótulo artificial não é atributo."
        self.assertEqual(original, estado_contexto(outro))
        self.assertEqual(original["tipo_escrita"], "poema")
        self.assertEqual(atributos(ctx["mensagem"], original, {"entendeu"}),
                         atributos(outro["mensagem"], estado_contexto(outro), {"entendeu"}))

    def test_estado_exclui_campos_e_valores_estranhos(self):
        for estado in ({"acao": "historia"}, {"relato": "sim"},
                       {"tipo_escrita": "motor_factual"}, None):
            with self.assertRaises(ValueError):
                normalizar_estado(estado)

    def test_estado_nao_confunde_relato_sobre_mensagem_com_escrita_anterior(self):
        for texto in ("Eu queria ajudar, mas minha mensagem ficou confusa",
                      "Quero entender por que minha carta não chegou",
                      "Não escreva uma história agora"):
            self.assertEqual(tipo_historico(texto), "")
        self.assertEqual(tipo_historico("Pode inventar um conto sobre um encontro?"), "historia")
        self.assertEqual(tipo_historico("Imagine uma narrativa breve com um gato"), "historia")
        estado = estado_contexto({"historico": ["Escreva uma mensagem para Lia sobre uma dúvida"],
                                  "slots": {}})
        self.assertEqual(estado["tipo_escrita"], "mensagem")
        self.assertFalse(estado["criacao"])

    def test_deduplica_pedido_estado_sem_usar_variantes_resposta(self):
        primeiro = exemplo("treino", "t1", "Você entendeu isso?", slots={"relato": "A"})
        variante = copy.deepcopy(primeiro)
        variante["resposta"] = "Outro texto produzido pelo gerador"
        ultimo = exemplo("validacao", "v1", "O que você compreendeu?", slots={"relato": "B"})
        treino, validacao = preparar_dados({"versao": 1, "exemplos": [primeiro, variante, ultimo]}, False)
        self.assertEqual((len(treino), len(validacao)), (1, 1))
        self.assertNotIn("resposta", treino[0])

    def test_impede_vazamento_pedido_estado_familia_e_grupo(self):
        t = exemplo("treino", "t1", "Você entendeu isso?", slots={"relato": "A"})
        v = exemplo("validacao", "v1", "O que você compreendeu?", slots={"relato": "B"})
        for campo in ("familia", "dialogo", "texto"):
            ruim = copy.deepcopy(v)
            if campo == "texto":
                ruim["contexto"]["mensagem"] = t["contexto"]["mensagem"]
            else:
                ruim[campo] = t[campo]
            with self.assertRaises(ValueError):
                preparar_dados({"versao": 1, "exemplos": [t, ruim]}, False)

    def test_rejeita_rotulos_conflitantes_no_mesmo_pedido_estado(self):
        t = exemplo("treino", "t1", "Você entendeu isso?", slots={"relato": "A"})
        conflitante = copy.deepcopy(t)
        conflitante["contexto"]["acao"] = "ajuste"
        with self.assertRaises(ValueError):
            preparar_dados({"versao": 1, "exemplos": [t, conflitante]}, False)

    def test_estado_muda_a_representacao_sem_depender_de_conteudo_privado(self):
        neutro = normalizar_estado({})
        pessoal = normalizar_estado({"relato": True, "objetivo": True})
        a, b = atributos("E agora?", neutro, set()), atributos("E agora?", pessoal, set())
        self.assertNotEqual(a, b)
        self.assertEqual({i: v for i, v in a.items() if i < 1152},
                         {i: v for i, v in b.items() if i < 1152})

    def test_abstracao_dos_temas_usa_so_declaracoes_do_treino(self):
        t = exemplo("treino", "t1", "Escreva uma história sobre uma ponte",
                    "historia", slots={"tema1": "uma ponte"})
        v = exemplo("validacao", "v1", "Imagine um conto sobre uma oficina",
                    "historia", slots={"tema1": "uma oficina"})
        termos = temas_treino({"exemplos": [t, v]})
        self.assertEqual(termos, ["ponte"])
        casos = [{"texto": "Escreva uma história sobre uma ponte"}] * 3
        lexico = lexico_treino(casos, termos)
        self.assertIn("uma", lexico)
        self.assertIn("historia", lexico)
        self.assertNotIn("ponte", lexico)
        self.assertNotIn("oficina", lexico)
        a = atributos("Escreva uma história sobre uma ponte", {}, lexico)
        b = atributos("Escreva uma história sobre uma oficina", {}, lexico)
        self.assertEqual({i: x for i, x in a.items() if 768 <= i < 1152},
                         {i: x for i, x in b.items() if 768 <= i < 1152})


class ModeloIntencaoGerativa(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados = json.loads(caminho_padrao().read_text(encoding="utf-8"))
        cls.modelo = IntencaoGerativa(cls.dados)
        cls.curriculo = json.loads(Path(__file__).with_name("curriculo_geracao.json").read_text(encoding="utf-8"))
        cls.treino, cls.validacao = preparar_dados(cls.curriculo)

    def test_checkpoint_corresponde_somente_ao_treino_deduplicado(self):
        self.assertEqual(self.dados["assinatura_treino"], assinatura(self.treino))
        self.assertEqual(self.dados["assinatura_curriculo"], assinatura(self.curriculo))
        termos = temas_treino(self.curriculo)
        self.assertEqual(self.dados["treino"]["termos_temas"], termos)
        self.assertEqual(self.dados["lexico"], lexico_treino(self.treino, termos))
        self.assertEqual(self.modelo.rede.dimensao, DIMENSAO)
        self.assertEqual(tuple(self.modelo.rede.rotulos), ACOES)
        self.assertEqual(self.dados["treino"]["pedidos_unicos"], len(self.treino))

    def test_aprende_supervisao_real_e_abstencao_sem_pesos(self):
        neutralizado = copy.deepcopy(self.dados)
        neutralizado["rede"]["w2"] = [[0.0] * self.modelo.rede.ocultos for _ in ACOES]
        neutralizado["rede"]["b2"] = [0.0] * len(ACOES)
        sem_pesos = IntencaoGerativa(neutralizado)
        observados = set()
        for c in self.treino:
            q = self.modelo.analisar(c["texto"], c["estado"])
            if q["acao"] == c["acao"] and q["aceita"]:
                observados.add(c["acao"])
                neutro = sem_pesos.analisar(c["texto"], c["estado"])
                self.assertFalse(neutro["aceita"])
                self.assertAlmostEqual(neutro["confianca"], 1 / len(ACOES))
            if len(observados) == len(ACOES):
                break
        self.assertEqual(observados, set(ACOES))

    def test_rejeita_assinatura_dimensoes_rotulos_e_pesos_invalidos(self):
        alteracoes = (lambda d: d.update(assinatura_atributos="desatualizada"),
                      lambda d: d["rede"].update(dimensao=12),
                      lambda d: d["rede"]["w1"][0].pop(),
                      lambda d: d["rede"]["w2"][0].__setitem__(0, float("nan")),
                      lambda d: d["rede"]["rotulos"].reverse(),
                      lambda d: d.update(limiar=float("nan")))
        for alterar in alteracoes:
            dados = copy.deepcopy(self.dados)
            alterar(dados)
            with self.assertRaises(ValueError):
                IntencaoGerativa(dados)

    def test_numpy_e_python_concordam_na_inferencia(self):
        try:
            import numpy as np
        except ImportError:
            self.skipTest("NumPy é opcional; a inferência Python continua coberta")
        rede = self.modelo.rede
        w1, b1, w2, b2 = (np.array(getattr(rede, k)) for k in ("w1", "b1", "w2", "b2"))
        for c in self.validacao[:12]:
            esparso = atributos(c["texto"], c["estado"], self.modelo.lexico)
            x = np.zeros(DIMENSAO)
            for i, valor in esparso.items():
                x[i] = valor
            logits = np.tanh(w1 @ x + b1) @ w2.T + b2
            referencia = softmax(logits.tolist(), rede.temperatura)
            puro = self.modelo.analisar(c["texto"], c["estado"])["distribuicao"]
            self.assertLess(max(abs(puro[r] - p) for r, p in zip(ACOES, referencia)), 1e-12)

    def test_estado_participa_da_inferencia_quando_ha_perfis_no_treino(self):
        por_texto = {}
        ha_perfis = False
        for c in self.treino:
            anteriores = por_texto.setdefault(c["texto"], [])
            for outro in anteriores:
                if outro["estado"] != c["estado"]:
                    ha_perfis = True
                    a = self.modelo.analisar(c["texto"], c["estado"])["distribuicao"]
                    b = self.modelo.analisar(outro["texto"], outro["estado"])["distribuicao"]
                    if max(abs(a[r] - b[r]) for r in ACOES) > 1e-8:
                        return
            anteriores.append(c)
        if not ha_perfis:
            self.skipTest("Não há o mesmo pedido com perfis de estado distintos neste currículo")
        self.fail("O currículo contém perfis de estado, mas eles não alteraram os escores aprendidos")

    def test_pedido_vazio_nao_e_aceito(self):
        self.assertFalse(self.modelo.analisar("", {})["aceita"])


if __name__ == "__main__":
    unittest.main()
