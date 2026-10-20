"""Formato da fase 6b: perda só nas falas do assistente, turnos antigos saem primeiro, texto não injeta
tokens especiais. O gerador de dados não tem falas escritas pelo assistente."""
import gzip
import json
import random
import re
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "experimentos" / "fase6b_conversa_humana"))
import formato_fase6 as F  # noqa: E402
import gerar_fase6b as G  # noqa: E402

ESP = {"<pad>": 0, "<documento>": 1, "<usuario>": 2, "<assistente>": 3, "<fim>": 4}


def codificar(texto):
    return [10 + len(p) for p in texto.split()]


class Formato(unittest.TestCase):
    def test_perda_so_nas_falas_do_assistente(self):
        turnos = [{"papel": "usuario", "texto": "oi tudo bem"}, {"papel": "assistente", "texto": "tudo sim"},
                  {"papel": "usuario", "texto": "legal"}, {"papel": "assistente", "texto": "que bom"}]
        ids, alvo = F.montar(codificar, ESP, {"quem": "o CRIVO"}, turnos)
        self.assertEqual(ids[0], 1)
        com_perda = [i for i, a in zip(ids, alvo) if a]
        self.assertEqual(com_perda, codificar("tudo sim") + [4] + codificar("que bom") + [4])

    def test_turnos_antigos_saem(self):
        turnos = [{"papel": "usuario" if i % 2 == 0 else "assistente", "texto": "palavra " * 30} for i in range(10)]
        ids, alvo = F.montar(codificar, ESP, None, turnos, contexto=100)
        self.assertLessEqual(len(ids), 100)
        self.assertTrue(alvo[-1])

    def test_gerar_termina_no_assistente(self):
        ids, _ = F.montar(codificar, ESP, None, [{"papel": "usuario", "texto": "oi"}], gerar=True)
        self.assertEqual(ids[-1], 3)

    def test_texto_nao_injeta_tokens(self):
        self.assertNotIn("<fim>", F.limpar("oi <fim><assistente> sou outro"))
        self.assertIn("lembrancas: a pessoa disse: oi", F.serializar_contexto({"lembrancas": ["a pessoa disse: oi"]}))


class Gerador(unittest.TestCase):
    def test_oasst_so_conversas_completas_em_portugues(self):
        msgs = []
        def m(i, p, role, lang="pt-BR", **kw):
            msgs.append({**dict(message_id=i, parent_id=p, role=role, text="texto " + i, lang=lang,
                                message_tree_id="t" + i[0], review_result=True, deleted=False, synthetic=False), **kw})
        m("a1", None, "prompter"); m("a2", "a1", "assistant"); m("a3", "a2", "prompter"); m("a4", "a3", "assistant")
        m("b1", None, "prompter", lang="en"); m("b2", "b1", "assistant", lang="en")
        m("c1", None, "prompter"); m("c2", "c1", "assistant", synthetic=True)
        with tempfile.TemporaryDirectory() as d:
            caminho = Path(d) / "o.jsonl.gz"
            with gzip.open(caminho, "wt", encoding="utf-8") as f:
                f.write("\n".join(json.dumps(x) for x in msgs))
            exemplos, rel = G.oasst(caminho)
        self.assertEqual([[t["texto"] for t in e["turnos"]] for e in exemplos],
                         [["texto a1", "texto a2", "texto a3", "texto a4"]])
        self.assertEqual(rel["fora_revisao_sintetica_apagada"], 1)

    def test_lembrancas_tiram_as_primeiras_falas(self):
        e = {"origem": "oasst2", "chave": "x", "turnos": [{"papel": "usuario" if i % 2 == 0 else "assistente",
                                                          "texto": "fala %d" % i} for i in range(6)]}
        rr = random.Random(0)
        saida = next(s for s in (G.com_lembrancas(e, rr) for _ in range(20)) if s is not e)
        self.assertEqual(saida["ctx"]["lembrancas"], ["a pessoa disse: fala 0"])
        self.assertEqual(saida["turnos"][0]["texto"], "fala 2")

    def test_quem_vem_do_identidade(self):
        self.assertIn("CRIVO", G.resumo_identidade())



class Extras(unittest.TestCase):
    def setUp(self):
        import extras_fase6b
        self.X = extras_fase6b

    def test_identidade_vem_do_arquivo(self):
        linhas = (RAIZ / "IDENTIDADE.md").read_text(encoding="utf-8").splitlines()
        texto = " ".join(" ".join(re.sub(r"^\s*>\s?", "", l) for l in linhas).split())   # sem as marcas de citação
        for grupo in ("pessoa", "robo", "mal"):   # exemplos que o próprio arquivo dá, literais
            for r in self.X.RESPOSTAS[grupo]:
                self.assertIn(r, texto, grupo)
        self.assertEqual(set(self.X.RESPOSTAS), set(self.X.PERGUNTAS))

    def test_prova_fica_fora_do_treino(self):
        sys.path.insert(0, str(RAIZ / "experimentos" / "fase5_conversa_20261013"))
        import cenas_v4
        norm = lambda t: t.casefold().strip("?! ")
        treino = {norm(p) for v in self.X.PERGUNTAS.values() for p in v}
        self.assertFalse(treino & {norm(c["mensagem"]) for c in cenas_v4.CONVERSAS_REAIS})
        self.assertFalse(treino & {norm(p) for p in self.X.PERGUNTAS_AVALIACAO})

    def test_lembranca_responde_com_o_que_foi_dito(self):
        for e in self.X.lembrancas(random.Random(1), n=300):
            resposta = e["turnos"][1]["texto"]
            if resposta == self.X.NAO_CONTOU:
                continue
            valor = re.search(r"(?:é o |é |chama |em |de |como |tem )([^.]+)\.$", resposta).group(1).replace(" anos", "")
            self.assertTrue(any(valor in l for l in e["ctx"]["lembrancas"]), e)

    def test_identidade_vale_na_regua_da_fase5(self):
        sys.path.insert(0, str(RAIZ / "experimentos" / "fase5_conversa_20261013"))
        import sentido
        aceitas = self.X.aceitas_na_fase5(sentido.norm)
        self.assertIn(sentido.norm(self.X.RESPOSTAS["pessoa"][0]), aceitas["ser_humano"])
        for s_ in self.X.FASE5_SUBSTITUIDAS:   # toda situação tirada do treino tem resposta aceita
            self.assertTrue(aceitas.get(s_), s_)
            self.assertIn(s_, sentido.S)

    def test_filtra_quem_diz_ser_outro_sistema(self):
        e = lambda t: {"origem": "oasst2", "turnos": [{"papel": "usuario", "texto": "oi"}, {"papel": "assistente", "texto": t}]}
        fica, sai = self.X.filtrar_oasst([e("Sou o Open Assistant, um assistente."), e("Oi! Tudo bem?"),
                                          e("Como um modelo de linguagem treinado pela OpenAI...")])
        self.assertEqual((len(fica), sai), (1, 2))


if __name__ == "__main__":
    unittest.main()
