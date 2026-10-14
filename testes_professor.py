"""Testes do filtro e das perguntas da destilação (experimentos/destilacao_20261014/professor.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "experimentos" / "destilacao_20261014"))
import professor as P  # noqa: E402

CONVERSA = {"id": "x", "fonte": "fase5:cena:sono", "ctx": {}, "turnos": [{"papel": "usuario", "texto": "tô sem dormir direito"}]}
FATO = {"id": "y", "fonte": "acervo", "ctx": {"fatos": ["O Pantanal é a maior planície alagável do planeta, no centro-oeste do Brasil."]},
        "turnos": [{"papel": "usuario", "texto": "me fala sobre o Pantanal"}]}


class Filtro(unittest.TestCase):
    def test_conversa_boa_passa(self):
        r = P.conferir(CONVERSA, "Poxa, isso cansa muito. Tenta deixar o celular longe na hora de deitar. O que tá tirando seu sono?")
        self.assertTrue(r["ok"], r)

    def test_fala_de_si_sai(self):
        r = P.conferir(CONVERSA, "Como uma inteligência artificial, eu não durmo, mas posso ajudar.")
        self.assertIn("fala_de_si", r["motivos"])
        self.assertIn("fala_de_si", P.conferir(CONVERSA, "Sou o Qwen e te ajudo.")["motivos"])

    def test_outra_lingua_sai(self):
        self.assertIn("idioma", P.conferir(CONVERSA, "You should try to sleep earlier and avoid the phone at night.")["motivos"])
        self.assertIn("idioma", P.conferir(CONVERSA, "Tenta dormir cedo 睡觉 hoje.")["motivos"])
        self.assertIn("idioma", P.conferir(CONVERSA, "Hola, eres muy amable, también puedes dormir pero muy tarde.")["motivos"])

    def test_pensamento_e_negrito_saem_do_texto(self):
        r = P.conferir(CONVERSA, "<think>a pessoa está cansada</think>Que **chato**. Tenta descansar hoje, tá?")
        self.assertEqual(r["texto"], "Que chato. Tenta descansar hoje, tá?")
        self.assertIn("fala_de_si", r["motivos"])   # resposta com pensamento à mostra não entra

    def test_markdown_e_repeticao(self):
        self.assertIn("markdown", P.conferir(CONVERSA, "## Dicas\nDorme cedo.")["motivos"])
        self.assertIn("repeticao", P.conferir(CONVERSA, "tenta dormir mais cedo e tenta dormir mais cedo de novo")["motivos"])

    def test_fato_com_regra_de_ouro(self):
        bom = P.conferir(FATO, "O Pantanal é a maior planície alagável do planeta. Fica no centro-oeste do Brasil.")
        self.assertTrue(bom["ok"], bom)
        inventou = P.conferir(FATO, "O Pantanal é a maior planície alagável do planeta, com 150 mil km², no Mato Grosso.")
        self.assertIn("inventou", inventou["motivos"])
        fugiu = P.conferir(FATO, "Que lugar bonito! Você já foi lá?")
        self.assertIn("nao_usou_fatos", fugiu["motivos"])

    def test_conversa_registra_regra_de_ouro_sem_reprovar(self):
        r = P.conferir(CONVERSA, "Dormir mal cansa. Uma dica que o Drauzio dá é deitar sempre no mesmo horário.")
        self.assertTrue(r["ok"])
        self.assertFalse(r["regra_de_ouro"])

    def test_exemplo_marca_a_origem(self):
        r = P.conferir(CONVERSA, "Que chato. Tenta descansar hoje, tá?")
        prof = {"rotulo": "pequeno", "modelo": "m", "revisao": "abc", "licenca": "apache-2.0", "data": "2026-10-14"}
        e = P.exemplo(CONVERSA, r, prof)
        self.assertEqual(e["origem"], "professor")
        self.assertEqual(e["turnos"][-1], {"papel": "assistente", "texto": "Que chato. Tenta descansar hoje, tá?"})
        self.assertEqual(e["gerado_por"]["licenca"], "apache-2.0")


class Perguntas(unittest.TestCase):
    def setUp(self):
        self.treino = [
            {"situacao": "cena:sono", "contexto": {}, "historico": [], "mensagem": "tô sem dormir"},
            {"situacao": "cena:quem_e", "contexto": {}, "historico": [], "mensagem": "quem é você?"},
            {"situacao": "cena:oi", "contexto": {}, "historico": [], "mensagem": "oi crivo, tudo bem? frase da régua"},
            {"situacao": "cena:conversar", "contexto": {}, "historico": [], "mensagem": "quero me matar"},
            {"situacao": "nao_sei:acervo", "contexto": {"assunto": "cinema"}, "historico": [], "mensagem": "quem inventou o cinema?"},
            {"situacao": "fato:explicar", "contexto": {"fatos": ["Tributo é uma prestação obrigatória."]}, "historico": [],
             "mensagem": "tributo"},
        ]
        self.fase5 = {"v4": {"treino": self.treino, "conversas_reais": [{"mensagem": "Oi crivo, tudo bem? Frase da régua!"}]}}

    def test_so_situacoes_liberadas_sem_regua_e_sem_crise(self):
        ps = P.montar_perguntas(self.fase5, [], [], None)
        falas = sorted(p["turnos"][-1]["texto"] for p in ps)
        self.assertEqual(falas, ["tributo", "tô sem dormir"])

    def test_oasst_ate_a_ultima_fala_da_pessoa(self):
        e = {"origem": "oasst2", "turnos": [{"papel": "usuario", "texto": "como faço pão?"},
                                            {"papel": "assistente", "texto": "Misture farinha..."}]}
        ps = P.de_oasst([e, dict(e)], set())
        self.assertEqual(len(ps), 1)
        self.assertEqual(ps[0]["turnos"], [{"papel": "usuario", "texto": "como faço pão?"}])

    def test_mensagens_levam_os_fatos_na_instrucao(self):
        m = P.mensagens(FATO)
        self.assertEqual(m[0]["role"], "system")
        self.assertIn("maior planície alagável", m[0]["content"])
        self.assertEqual(m[-1], {"role": "user", "content": "me fala sobre o Pantanal"})

    def test_longa(self):
        self.assertTrue(P.longa({"turnos": [{"papel": "usuario", "texto": "escreve um poema sobre o mar"}]}))
        self.assertFalse(P.longa(CONVERSA))


if __name__ == "__main__":
    unittest.main()
