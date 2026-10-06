"""Ciclo de retorno: avaliações compartilhadas viram exemplos só depois de revisadas."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import retorno_para_exemplos as retorno

EXPORT = {"formato": "crivo-avaliacoes-v1", "avaliacoes": [
    {"chave": "a", "nota": 1, "pergunta": "O que é inflação?", "voz": "voz_propria", "id": "conhecimento:mundo_inflacao",
     "resposta": "Inflação é o aumento geral e contínuo dos preços, que reduz o poder de compra do dinheiro."},
    {"chave": "b", "nota": -1, "pergunta": "O que é PIB?", "voz": None, "resposta": "..."},
    {"chave": "c", "tipo": "sinal", "sinal": "confirmado", "especie": "compreensao_neural",
     "pergunta": "tenho um ap minusculo, qual planta fica bem", "assunto": "plantas_apartamento"},
    {"chave": "d", "tipo": "sinal", "sinal": "rejeitado", "especie": "compreensao_neural",
     "pergunta": "qual planta pra sala escura", "assunto": ["plantas_apartamento"]},
    {"chave": "e", "tipo": "sinal", "sinal": "contestado", "especie": "recuperador",
     "pergunta": "Como regar uma planta?", "assunto": "regar"},
]}


class CicloDeRetorno(unittest.TestCase):
    def setUp(self):
        self.pasta = Path(tempfile.mkdtemp())
        self.patches = [mock.patch.object(retorno, "FILA", self.pasta / "fila.json"),
                        mock.patch.object(retorno, "TUTOR", self.pasta / "tutor.json"),
                        mock.patch.object(retorno, "ENTENDIMENTO", self.pasta / "entendimento.json")]
        for p in self.patches:
            p.start()
        (self.pasta / "tutor.json").write_text(json.dumps({"versao": 1, "casos": []}), encoding="utf-8")
        self.export = self.pasta / "crivo-avaliacoes.json"
        self.export.write_text(json.dumps(EXPORT), encoding="utf-8")

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_candidatos_por_tipo(self):
        tipos = sorted(c["tipo"] for c in retorno.candidatos(EXPORT["avaliacoes"]))
        self.assertEqual(tipos, ["entendimento_nao", "entendimento_sim", "voz_corrigir", "voz_positiva"])
        self.assertTrue(all(not c["revisado"] for c in retorno.candidatos(EXPORT["avaliacoes"])))

    def test_fila_nao_duplica(self):
        self.assertEqual(retorno.enfileirar([self.export]), 4)
        self.assertEqual(retorno.enfileirar([self.export]), 0)

    def test_nada_entra_sem_revisao(self):
        retorno.enfileirar([self.export])
        resumo = retorno.incorporar()
        self.assertEqual((resumo["voz"], resumo["entendimento"], resumo["pendentes"]), (0, 0, 4))

    def test_revisado_entra_e_guarda_recusa_invencao(self):
        retorno.enfileirar([self.export])
        fila = json.loads((self.pasta / "fila.json").read_text(encoding="utf-8"))
        for item in fila["itens"]:
            item["revisado"] = True
            if item["tipo"] == "voz_corrigir":
                item["tutor"] = "Regar uma planta exige adubo de foguete."  # inventado de propósito
        (self.pasta / "fila.json").write_text(json.dumps(fila), encoding="utf-8")
        resumo = retorno.incorporar()
        self.assertEqual(resumo["voz"], 1)
        self.assertEqual(resumo["entendimento"], 2)
        self.assertEqual(len(resumo["recusados"]), 1)
        tutor = json.loads((self.pasta / "tutor.json").read_text(encoding="utf-8"))
        self.assertEqual(tutor["casos"][0]["assuntos"], ["mundo_inflacao"])
        entend = json.loads((self.pasta / "entendimento.json").read_text(encoding="utf-8"))
        self.assertEqual(entend["positivos"][0]["assunto"], "plantas_apartamento")
        self.assertEqual(len(entend["erros"]), 1)

    def test_pergunta_do_teste_congelado_nunca_entra(self):
        export = {"formato": "crivo-avaliacoes-v1", "avaliacoes": [
            {"chave": "x", "tipo": "sinal", "sinal": "confirmado", "especie": "compreensao_neural",
             "pergunta": "moro num ap pequeno, que planta da pra ter", "assunto": "plantas_apartamento"}]}
        self.export.write_text(json.dumps(export), encoding="utf-8")
        retorno.enfileirar([self.export])
        fila = json.loads((self.pasta / "fila.json").read_text(encoding="utf-8"))
        fila["itens"][0]["revisado"] = True
        (self.pasta / "fila.json").write_text(json.dumps(fila), encoding="utf-8")
        resumo = retorno.incorporar()
        self.assertEqual(resumo["entendimento"], 0)
        self.assertEqual(resumo["recusados"][0][1], "pergunta do teste congelado")

    def test_formato_desconhecido_e_recusado(self):
        ruim = self.pasta / "ruim.json"
        ruim.write_text(json.dumps({"outra": 1}), encoding="utf-8")
        with self.assertRaises(SystemExit):
            retorno.enfileirar([ruim])


if __name__ == "__main__":
    unittest.main()
