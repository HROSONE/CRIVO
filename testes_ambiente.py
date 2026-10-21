"""O ambiente à volta do modelo (ambiente.py): casa, alimento e moradia segura.

Conversa real do criador (19/10/2026): "Corrija esta palavra: Palarerepípedo" passou sem correção,
"Me mande a palavra corrigida" virou "Corrigir / Agradecer", "Quer saber o quê?" virou "Oi, oi!" e
"O meu é Henrique" virou "Fico feliz que você me contou sobre seu pai"."""
import unittest
from unittest import mock

import ambiente
import conversa_v3d
from correcao_texto import corrigir, sugerir
from crivo import Crivo
from web_core import responder_web


class Falso:
    """Modelo de teste: devolve as frases da lista, uma por tentativa."""
    def __init__(self, *textos):
        self.textos, self.chamadas = list(textos), []

    def conversar(self, ctx, historico, mensagem, primeiro=0, prazo=None):
        self.chamadas.append((ctx, historico, mensagem))
        return self.textos[min(primeiro, len(self.textos) - 1)], True


class Dicionario(unittest.TestCase):
    def test_palavra_da_conversa_real(self):
        r = corrigir('"Palarerepípedo"')
        self.assertEqual(r["corrigido"], '"Paralelepípedo"')
        self.assertTrue(any("Palarerepípedo → Paralelepípedo" in n for n in r["avisos"]))

    def test_erros_comuns(self):
        for errada, certa in [("chatiado", "chateado"), ("bagunsa", "bagunça"), ("exelente", "excelente"),
                              ("bicicreta", "bicicleta"), ("cumputador", "computador"), ("pesoas", "pessoas")]:
            self.assertEqual(sugerir(errada), certa, errada)

    def test_palavras_certas_e_nomes_ficam(self):
        for certa in ["abacaxi", "cronogramas", "simplificadas", "dedicarmos", "indisponibilidade", "tô", "vc",
                      "kkkk", "Henrique"]:
            self.assertIsNone(sugerir(certa), certa)
        self.assertEqual(corrigir("a Joana chegou")["corrigido"], "A Joana chegou.")


class Casa(unittest.TestCase):
    def test_tarefa_continua_no_turno_seguinte(self):
        h = ['Corrija esta palavra: "Palarerepípedo"']
        r = responder_web({"message": "Me mande a palavra corrigida", "history": h})
        self.assertEqual(r["id"], ambiente.IDENT_TAREFA)
        self.assertIn("paralelepípedo", r["response"])
        r = responder_web({"message": "Você não me deu a palavra certa", "history": h + ["Me mande a palavra corrigida"]})
        self.assertTrue(r["response"].startswith("Desculpa."))
        self.assertIn("paralelepípedo", r["response"])

    def test_sem_tarefa_nao_inventa_resultado(self):
        r = responder_web({"message": "Me mande a palavra corrigida"})
        self.assertNotEqual(r["id"], ambiente.IDENT_TAREFA)

    def test_pergunta_do_crivo_vale_mais_um_turno(self):
        fio = ambiente.Fio()
        fio.observar(Crivo(), "Oi, tudo bem?", "social:tudobem", "Tudo bem, sim! E você? Como foi o seu dia?")
        fio.observar(Crivo(), "Nem começou ainda", "fora", "Entendo. Fica à vontade.")
        self.assertEqual(ambiente.ato_do_turno(fio, "Quer saber o que?"), "explicar_minha_pergunta")
        fio.observar(Crivo(), "ok", "fora", "Certo.")
        self.assertIsNone(ambiente.ato_do_turno(fio, "Quer saber o que?"))

    def test_nome_eliptico_depois_da_pergunta(self):
        fio = ambiente.Fio()
        fio.observar(Crivo(), "Qual é o seu nome?", "social:quem", "Meu nome é CRIVO. E o seu?")
        self.assertEqual(ambiente.completar(fio, "O meu é Henrique"), "Meu nome é Henrique")
        self.assertEqual(ambiente.completar(ambiente.Fio(), "O meu é Henrique"), "O meu é Henrique")
        bot = Crivo()
        bot.conversa_v3d = Falso("Meu nome é CRIVO. E o seu?")
        bot.responder("Qual é o seu nome?")
        bot.conversa_v3d = None
        bot.responder("O meu é Henrique")
        self.assertIn("Henrique", bot.responder("Qual é o meu nome?")[1])

    def test_atos(self):
        fio = ambiente.Fio()
        self.assertEqual(ambiente.ato_do_turno(fio, "Você me entende, sim ou não?"), "sim_ou_nao")
        self.assertEqual(ambiente.ato_do_turno(fio, "Você consegue me entender?"), "sim_ou_nao")
        self.assertIsNone(ambiente.ato_do_turno(fio, "Você sabe o que é um buraco negro?"))
        self.assertIsNone(ambiente.ato_do_turno(fio, "Você gosta de quê?"))


class Juiz(unittest.TestCase):
    def test_parente_inventado(self):
        fontes = ["Meu nome é Henrique"]
        self.assertEqual(ambiente.julgar(None, "Meu nome é Henrique", "Fico feliz que você me contou sobre seu pai.",
                                         fontes), ["inventou_parente:pai"])
        self.assertEqual(ambiente.julgar(None, "Meu pai é médico", "Que legal, seu pai cuida das pessoas.",
                                         ["Meu pai é médico"]), [])
        self.assertEqual(ambiente.podar("Prazer, Henrique! Fico feliz que você me contou sobre seu pai.", None,
                                        "Meu nome é Henrique", fontes), "Prazer, Henrique!")

    def test_sim_ou_nao(self):
        f = "Você me entende, sim ou não?"
        self.assertEqual(ambiente.julgar("sim_ou_nao", f, "Sim, entendo.", [f]), [])
        self.assertEqual(ambiente.julgar("sim_ou_nao", f, "Gosto do seu jeito.", [f]), ["nao_respondeu_sim_ou_nao"])
        self.assertEqual(ambiente.julgar("sim_ou_nao", "Você pensa?", "Penso no que vou dizer.", []), [])
        self.assertEqual(ambiente.julgar("sim_ou_nao", "Você consegue me entender?", "Penso no que vou dizer.", []),
                         ["nao_respondeu_sim_ou_nao"])

    def test_eco_e_pergunta_contraria(self):
        anterior = "Me mande a palavra corrigida"
        self.assertIn("eco", ambiente.julgar(None, "Você entende?", "Você trouxe “%s”." % anterior, [anterior]))
        self.assertEqual(ambiente.julgar(None, "Nem começou ainda", "Quero saber! O que aconteceu?", []),
                         ["pergunta_contraria"])

    def test_resultado_exigido_fica_fiel(self):
        bot = Crivo()
        bot.conversa_v3d = Falso("Ah, Corrija! Bonito nome.")
        bot.responder('Corrija esta palavra: "Palarerepípedo"')
        ident, resposta = bot.responder("Me mande a palavra corrigida")
        self.assertEqual(resposta, "A palavra corrigida é paralelepípedo.")
        self.assertFalse(bot.ultima_conversa_v3d["usada"])

    def test_frase_inventada_sai_e_o_resto_e_dele(self):
        bot = Crivo()
        bot.conversa_v3d = Falso("Prazer, Henrique! Fico feliz que você me contou sobre seu pai.")
        bot.responder("Qual é o seu nome?")
        ident, resposta = bot.responder("O meu é Henrique")
        self.assertEqual(resposta, "Prazer, Henrique!")
        self.assertTrue(bot.ultima_conversa_v3d.get("podada"))

    def test_escolhe_a_frase_que_passa(self):
        bot = Crivo()
        bot.conversa_v3d = Falso("Quero saber! O que aconteceu?", "Entendo. Fica à vontade.")
        bot.responder("Oi, tudo bem?")
        self.assertEqual(bot.responder("Nem começou ainda")[1], "Entendo. Fica à vontade.")


class ConversaFreud(unittest.TestCase):
    """Conversa real do criador no app (20/10/2026): "Quem é freud" → "Sou o CRIVO…"; "Que é Lacan" →
    "Lacan é um nome bonito"; "O que é prossímio" → "uma estrutura celular"; "E o símio?" → "O…"."""

    def test_pergunta_sobre_outro_nao_vira_fala_de_si(self):
        self.assertIn("falou_de_si", ambiente.julgar(None, "Quem é freud", "Sou o CRIVO, uma IA curiosa.", []))
        self.assertNotIn("falou_de_si", ambiente.julgar(None, "Quem é você?", "Sou o CRIVO, uma IA curiosa.", []))

    def test_sem_saber_tem_que_dizer_que_nao_sabe(self):
        self.assertIn("inventou_sem_fonte", ambiente.julgar(None, "Que é Lacan", "Pelo que eu sei: Lacan é um nome bonito.",
                                                            [], nao_sabe=True))
        self.assertEqual(ambiente.julgar(None, "Que é Lacan", "Não sei quem é Lacan.", [], nao_sabe=True), [])

    def test_frase_inventada_fica_fora_quando_nao_sabe(self):
        bot = Crivo()
        bot.conversa_v3d = Falso("Pelo que eu sei: O prossímio é uma estrutura celular.")
        ident, resposta = bot.responder("O que é prossímio")
        self.assertNotIn("celular", resposta)

    def test_e_o_x_continua_a_pergunta(self):
        fio = ambiente.Fio()
        fio.observar(Crivo(), "O que são primatas", "enciclopedia:wikipedia", "A ordem dos primatas é um grupo.")
        self.assertEqual(ambiente.completar(fio, "E o símio?"), "O que é símio?")
        fio.observar(Crivo(), "Quem é freud", "enciclopedia:wikipedia", "Sigmund Freud foi um neurologista.")
        self.assertEqual(ambiente.completar(fio, "E o Lacan?"), "Quem é Lacan?")

    def test_freud_pelo_sobrenome_na_enciclopedia(self):
        import enciclopedia
        self.assertEqual(enciclopedia.consultar("Quem é freud")[0], "Sigmund Freud")
        self.assertEqual(enciclopedia.consultar("Que é Lacan")[0], "Jacques Lacan")
        r = responder_web({"message": "Quem é freud"})
        self.assertIn("Freud", r["response"])
        self.assertIn("Wikipédia", r["response"])

    def test_pergunta_que_nao_sabe_nao_vira_mensagem_de_logica(self):
        r = responder_web({"message": "Quem é psicopata"})
        self.assertNotIn("condições da consulta", r["response"])
        self.assertIn("não sei", r["response"])


class PesosDoSite(unittest.TestCase):
    def test_prompt_lido_uma_vez_da_o_mesmo_texto(self):
        modelo = conversa_v3d.numpy_do_site()
        ctx = {"quem": conversa_v3d.QUEM}
        # Sem o prazo do site: numa máquina ocupada ele corta a frase, e o teste é sobre as palavras.
        with mock.patch.object(modelo, "prazo", None):
            modelo._prefixo = None
            frases = [modelo.conversar(ctx, [], "Oi, tudo bem?", primeiro=k) for k in range(3)]
            for k in range(3):
                modelo._prefixo = None
                self.assertEqual(modelo.conversar(ctx, [], "Oi, tudo bem?", primeiro=k), frases[k])
            texto, _ = modelo.conversar(ctx, [], "Você me entende?", comecos=["Sim", "Não"])
        self.assertTrue(texto.startswith(("Sim", "Não")))


if __name__ == "__main__":
    unittest.main()
