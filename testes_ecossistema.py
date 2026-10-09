"""O ecossistema do CRIVO: nenhum mecanismo responde fora do mapa nem sem contrapeso."""
import ast
import unittest
from pathlib import Path

try:
    import numpy  # noqa: F401
    TEM_NUMPY = True
except ImportError:
    TEM_NUMPY = False

import ecossistema
from web_core import responder_web

RAIZ = Path(__file__).resolve().parent


def mecanismos_no_codigo():
    """Todo texto literal gravado como "mecanismo" no código de produção."""
    achados = {}
    for arquivo in sorted(RAIZ.glob("*.py")):
        if arquivo.name.startswith(("testes", "avaliar_", "experimento_")):
            continue
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        valores = []
        for no in ast.walk(arvore):
            if isinstance(no, ast.Dict):
                valores += [v for k, v in zip(no.keys, no.values)
                            if isinstance(k, ast.Constant) and k.value == "mecanismo"]
            elif isinstance(no, ast.Call):
                valores += [k.value for k in no.keywords if k.arg == "mecanismo"]
            elif isinstance(no, ast.Assign):
                for alvo in no.targets:
                    chave = getattr(alvo, "slice", None)
                    if type(chave).__name__ == "Index":  # Python 3.8
                        chave = chave.value
                    if (isinstance(alvo, ast.Subscript) and isinstance(chave, ast.Constant)
                            and chave.value == "mecanismo") or (
                            isinstance(alvo, ast.Name) and alvo.id == "mecanismo"):
                        valores.append(no.value)
        for valor in valores:
            for nome in _textos(valor):
                achados.setdefault(nome, set()).add(arquivo.name)
    return achados


def _textos(valor):
    """Textos que o valor pode assumir: literal ou um dos ramos de um if."""
    if isinstance(valor, ast.Constant) and isinstance(valor.value, str):
        return [valor.value]
    if isinstance(valor, ast.IfExp):
        return _textos(valor.body) + _textos(valor.orelse)
    return []


class MapaDasEspecies(unittest.TestCase):
    def test_mapa_integro(self):
        self.assertEqual(ecossistema.problemas(), [])

    def test_todo_mecanismo_do_codigo_esta_no_mapa(self):
        achados = mecanismos_no_codigo()
        self.assertIn("compreensao_neural", achados)  # a varredura enxerga o código
        fora = {m: sorted(a) for m, a in achados.items() if m not in ecossistema.ESPECIES}
        self.assertEqual(fora, {}, "mecanismo sem papel nem contrapeso no ecossistema.py")

    def test_toda_especie_do_mapa_existe_no_codigo(self):
        sobrando = set(ecossistema.ESPECIES) - set(mecanismos_no_codigo())
        self.assertEqual(sobrando, set())

    def test_redes_nunca_se_regulam_so_entre_si(self):
        # Uma rede neural erra com confiança: precisa de um regulador que não
        # seja outra rede (a pessoa, as fontes, a recusa ou as catracas).
        for e in ecossistema.ESPECIES.values():
            if e.reino == "neural":
                externos = [r for r in e.regulado if r in ecossistema.REGULADORES]
                self.assertTrue(externos, e.nome)

    def test_teia_liga_reguladores_as_especies(self):
        teia = ecossistema.teia()
        self.assertIn("recuperador", teia["compreensao_neural"])
        self.assertIn("compreensao_neural", teia["pessoa"])


class EcossistemaNaApi(unittest.TestCase):
    def test_consumidor_de_sessao_informa_papel_e_reguladores(self):
        r = responder_web({'message': 'Me sugira uma opção para Daneli.',
                           'history': ['Daneli prefere suco de araçá.']})
        self.assertEqual(r['mechanism'], 'conversa_sessao')
        self.assertEqual(r['ecosystem']['species'], 'conversa_sessao')
        self.assertEqual(r['ecosystem']['kingdom'], 'conversa')
        self.assertIn('memoria_sessao_estrutural', r['ecosystem']['regulated_by'])
        self.assertIn('recusa', r['ecosystem']['regulated_by'])
        self.assertFalse(r['has_proof'])

    def test_resposta_informa_a_especie(self):
        r = responder_web({"message": "Oi"})
        self.assertIn(r["mechanism"], ecossistema.ESPECIES)
        self.assertEqual(r["ecosystem"]["species"], r["mechanism"])
        self.assertTrue(r["ecosystem"]["regulated_by"])

    def test_recuperador_e_especie(self):
        r = responder_web({"message": "Como regar uma planta?"})
        self.assertEqual(r["ecosystem"]["species"], r["mechanism"])


class CicloDeRetorno(unittest.TestCase):
    def test_contestar_resposta_vira_sinal_da_especie(self):
        r = responder_web({"message": "não era isso", "history": ["Como regar uma planta?"]})
        self.assertEqual(r["id"], "social:critica")
        self.assertEqual(r["ecosystem_feedback"], [{"especie": "recuperador", "tipo": "contestado",
                                                    "pergunta": "Como regar uma planta?", "assunto": "regar"}])

    def test_contestar_uma_recusa_nao_gera_sinal(self):
        r = responder_web({"message": "sua resposta está errada", "history": ["qual a senha do wifi daqui"]})
        self.assertNotIn("ecosystem_feedback", r)

    def test_fala_comum_nao_gera_sinal(self):
        self.assertNotIn("ecosystem_feedback", responder_web({"message": "Oi"}))

    @unittest.skipUnless(TEM_NUMPY, "NumPy necessário à compreensão neural")
    def test_confirmar_ou_rejeitar_a_rede(self):
        fala = "moro num ap pequeno, que planta da pra ter"
        sim = responder_web({"message": "sim", "history": [fala]})["ecosystem_feedback"]
        nao = responder_web({"message": "não", "history": [fala]})["ecosystem_feedback"]
        self.assertEqual([(s["especie"], s["tipo"]) for s in sim], [("compreensao_neural", "confirmado")])
        self.assertEqual([(s["especie"], s["tipo"]) for s in nao], [("compreensao_neural", "rejeitado")])

    def test_toda_especie_de_sinal_esta_no_mapa(self):
        from crivo import Crivo
        bot = Crivo()
        for fala in ("Como regar uma planta?", "não era isso", "Oi", "isso está errado"):
            bot.responder(fala)
        self.assertTrue(bot.sinais)
        for s in bot.sinais:
            self.assertIn(s["especie"], ecossistema.ESPECIES)


class PainelDeSaude(unittest.TestCase):
    def test_painel_le_os_conjuntos_de_desenvolvimento(self):
        from scripts.saude_ecossistema import casos
        conjuntos = {}
        for conjunto, _, _, _ in casos():
            conjuntos[conjunto] = conjuntos.get(conjunto, 0) + 1
        self.assertEqual(set(conjuntos), {"bateria_dev", "assunto_tom_dev",
                                          "entendimento_positivos", "entendimento_negativos"})
        self.assertNotIn("retido", " ".join(conjuntos))

    def test_especie_do_turno(self):
        from crivo import Crivo
        bot = Crivo()
        ident, _ = bot.responder("Oi")
        self.assertEqual(ecossistema.mecanismo_do_turno(bot, "Oi", ident), "conversa_assistente")


class LigacoesEntreAssuntos(unittest.TestCase):
    def responder(self, fala):
        from crivo import Crivo
        return Crivo().responder(fala)

    def test_relacao_entre_dois_assuntos_usa_ligacao_direta(self):
        for fala in ("Qual a relação entre fotossíntese e ciclo do carbono?",
                     "O que a fotossíntese tem a ver com o ciclo do carbono?"):
            ident, resposta = self.responder(fala)
            self.assertEqual(ident, "escrita:relacao", fala)
            self.assertIn("retira gás carbônico do ar", resposta)

    def test_sem_ligacao_cadastrada_nao_supoe(self):
        ident, resposta = self.responder("Qual a relação entre sono e fotossíntese?")
        self.assertEqual(ident, "fora")
        self.assertIn("não tenho uma ligação direta", resposta)

    def test_teia_de_um_assunto(self):
        ident, resposta = self.responder("Com o que o ciclo da água se relaciona?")
        self.assertEqual(ident, "escrita:ligacoes")
        for nome in ("evaporação", "Amazônia", "Cerrado"):
            self.assertIn(nome, resposta)
        self.assertIn("não deduzo cadeias de causa", resposta)

    def test_o_que_equilibra_usa_ligacoes_que_chegam(self):
        ident, resposta = self.responder("O que regula o efeito estufa?")
        self.assertEqual(ident, "escrita:ligacoes")
        self.assertIn("oceanos absorvem", resposta)

    def test_fato_sem_sujeito_ganha_origem(self):
        _, resposta = self.responder("Com o que a biodiversidade se relaciona?")
        self.assertIn("Floresta tropical → biodiversidade:", resposta)

    def test_ligacoes_ecologicas_tem_fato_de_origem(self):
        import curriculo_mundo
        dados = curriculo_mundo.ler_curriculo(RAIZ / "conhecimento_mundo.json")
        pares = {(r["origem"], r["destino"]) for r in dados["ligacoes"]}
        for par in (("mundo_ciclo_carbono", "mundo_fotossintese"), ("mundo_oceano", "mundo_efeito_estufa"),
                    ("mundo_amazonia", "mundo_ciclo_agua"), ("mundo_floresta_tropical", "mundo_biodiversidade")):
            self.assertIn(par, pares)


if __name__ == "__main__":
    unittest.main()
