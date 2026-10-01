"""Contratos de memória, atribuição, expiração e correção entre turnos."""
import json
import unittest

from memoria_dialogo import MemoriaDialogo


def quadro(texto, ato="relato", **papeis):
    spans = []
    for papel, literal in papeis.items():
        inicio = texto.index(literal)
        spans.append({"papel": papel, "inicio": inicio, "fim": inicio + len(literal),
                      "texto": literal, "confianca": .94})
    return {"ato": ato, "confianca": .95, "aceita": True, "spans": spans}


class TestesMemoriaDialogo(unittest.TestCase):
    def test_registra_respostas_reais_e_recusas_sem_promover_sentimentos(self):
        m = MemoriaDialogo()
        m.registrar("Você me entende?", "Não reconheci esse pedido.", "social:nao_entendido")
        m.registrar("Estou triste", "Pode falar.", "conversa:relato")
        c = m.contexto()
        self.assertEqual(c["historico"], [
            {"papel": "usuario", "texto": "Você me entende?"},
            {"papel": "assistente", "texto": "Não reconheci esse pedido."},
            {"papel": "usuario", "texto": "Estou triste"},
            {"papel": "assistente", "texto": "Pode falar."}])
        self.assertEqual(c["emocao_declarada"], [])
        self.assertIsNone(c["evento"])
        self.assertEqual(c["ultima_resposta"]["valor"], "Pode falar.")
        self.assertEqual(c["ultima_resposta"]["origem"], "model")

    def test_estado_isolado_e_resultados_nao_mutam_memoria(self):
        a, b = MemoriaDialogo(), MemoriaDialogo()
        texto = "Quero organizar minha oficina"
        a.registrar(texto, "Qual é a dificuldade?", "conversa:relato",
                    quadro(texto, objetivo="organizar minha oficina"))
        c = a.contexto()
        c["objetivo"]["valor"] = "falso"
        c["historico"][0]["texto"] = "falso"
        self.assertEqual(a.contexto()["objetivo"]["valor"], "organizar minha oficina")
        self.assertIsNone(b.contexto()["objetivo"])
        self.assertEqual(b.contexto()["historico"], [])

    def test_spans_exigem_literal_e_posicoes_reais(self):
        m = MemoriaDialogo()
        texto = "Quero conhecer Évora-42"
        frame = quadro(texto, objetivo="conhecer Évora-42")
        frame["spans"].extend([
            {"papel": "sentimento", "inicio": 0, "fim": 5, "texto": "feliz", "confianca": .99},
            {"papel": "tema", "inicio": -1, "fim": 5, "texto": "Quero", "confianca": .99},
            {"papel": "interlocutor", "inicio": 0, "fim": 5, "texto": "Quero", "confianca": .1}])
        m.registrar(texto, "Vamos pensar nisso.", "conversa:relato", frame)
        c = m.contexto()
        objetivo = c["objetivo"]
        self.assertEqual(objetivo["valor"], "conhecer Évora-42")
        self.assertEqual(objetivo["origem"], "user")
        self.assertEqual(objetivo["turno"], 1)
        f = objetivo["fonte"]
        self.assertEqual(f["texto"][f["inicio"]:f["fim"]], objetivo["valor"])
        self.assertEqual(c["emocao_declarada"], [])
        self.assertIsNone(c["topico"])
        self.assertEqual(c["entidades"], [])

    def test_emoção_propria_nao_vira_emocao_alheia_negada_ou_hipotetica(self):
        casos = [("Estou muito triste", True), ("Minha amiga está triste", False),
                 ("Minha amiga disse “estou triste”", False), ("Não estou triste", False),
                 ("Se estou triste, posso descansar?", False)]
        for texto, declarada in casos:
            with self.subTest(texto=texto):
                m = MemoriaDialogo()
                m.registrar(texto, "Entendi o relato.", "conversa:relato", quadro(texto, sentimento="triste"))
                self.assertEqual(bool(m.contexto()["emocao_declarada"]), declarada)

    def test_hipotese_nao_substitui_objetivo_declarado(self):
        m = MemoriaDialogo()
        real = "Quero consertar a bicicleta"
        m.registrar(real, "Entendi.", "conversa:relato", quadro(real, objetivo="consertar a bicicleta"))
        hipotese = "Se eu quiser comprar um barco, quanto preciso?"
        m.registrar(hipotese, "Isso é uma hipótese diferente.", "conversa:reflexao",
                    quadro(hipotese, objetivo="comprar um barco"))
        c = m.contexto()
        self.assertEqual(c["objetivo"]["valor"], "consertar a bicicleta")
        self.assertEqual(c["hipoteses"][0]["valor"], "comprar um barco")
        self.assertEqual(c["hipoteses"][0]["estatuto"], "hipotese")

    def test_objetivo_recusado_nao_substitui_declaracao_e_negacao_tem_escopo(self):
        m = MemoriaDialogo()
        original = "Quero estudar pintura"
        m.registrar(original, "Entendi.", "conversa:objetivo", quadro(original, objetivo="estudar pintura"))
        recusado = "Não quero abandonar o curso"
        m.registrar(recusado, "Entendi o limite.", "conversa:objetivo", quadro(recusado, objetivo="abandonar o curso"))
        self.assertEqual(m.contexto()["objetivo"]["valor"], "estudar pintura")
        pedido = "Não quero um plano, quero não desistir"
        m.registrar(pedido, "Podemos conversar.", "conversa:objetivo", quadro(pedido, objetivo="não desistir"))
        self.assertEqual(m.contexto()["objetivo"]["valor"], "não desistir")

    def test_pessoa_recusada_nao_vira_referente_ativo(self):
        m = MemoriaDialogo()
        texto = "Não foi Lia"
        m.registrar(texto, "Entendi.", "conversa:correcao", quadro(texto, ato="correcao", interlocutor="Lia"))
        self.assertEqual(m.contexto()["entidades"], [])

    def test_correcao_de_modo_considera_o_pedido_atual_sem_mutar(self):
        m = MemoriaDialogo()
        texto = "Não quero um plano, quero conversar sobre isso"
        frame = quadro(texto, ato="escuta", modo="conversar sobre isso", modo_recusado="um plano")
        c = m.contexto(texto, frame)
        self.assertEqual(c["modo"]["valor"], "conversar sobre isso")
        self.assertEqual(c["focos_recusados"][0]["valor"], "um plano")
        self.assertTrue(c["modo"]["provisorio"])
        self.assertEqual(m.turno, 0)
        m.registrar(texto, "Podemos conversar sobre o que aconteceu.", "conversa:reparo", frame)
        c = m.contexto()
        self.assertEqual(c["modo"]["valor"], "conversar sobre isso")
        self.assertEqual(c["focos_recusados"][0]["origem"], "user")
        self.assertEqual(c["focos_recusados"][0]["turno"], 1)

    def test_mudanca_de_assunto_desativa_objetivo_sem_apagar_dialogo(self):
        m = MemoriaDialogo()
        texto = "Quero terminar um desenho"
        m.registrar(texto, "Como você quer começar?", "conversa:relato",
                    quadro(texto, objetivo="terminar um desenho", tema="desenho"))
        mudanca = quadro("Vamos mudar de assunto", ato="mudar_assunto")
        self.assertIsNone(m.contexto("Vamos mudar de assunto", mudanca)["objetivo"])
        m.registrar("Vamos mudar de assunto", "Pode trazer outro tema.", "conversa:mudanca_assunto", mudanca)
        self.assertIsNone(m.contexto()["objetivo"])
        self.assertEqual(len(m.contexto()["historico"]), 4)
        self.assertEqual(m.contexto()["ultima_resposta"]["valor"], "Pode trazer outro tema.")

    def test_retomada_explicita_recupera_segmento_fonte_sem_mesclar_objetivos(self):
        m = MemoriaDialogo()
        primeiro = "Quero desenhar minha oficina"
        m.registrar(primeiro, "Entendi.", "conversa:relato",
                    quadro(primeiro, objetivo="desenhar minha oficina", tema="oficina"))
        novo = "Agora quero falar de música"
        m.registrar(novo, "O que chama sua atenção?", "conversa:tema", quadro(novo, ato="mudar_assunto", tema="música"))
        segundo = "Quero aprender violino"
        m.registrar(segundo, "Entendi.", "conversa:relato",
                    quadro(segundo, objetivo="aprender violino", tema="violino"))
        pedido = "Retome o assunto sobre oficina"
        retomada = m.contexto(pedido, quadro(pedido, ato="retomar", referencia="oficina"))
        self.assertEqual(retomada["objetivo"]["valor"], "desenhar minha oficina")
        self.assertEqual(retomada["objetivo"]["turno"], 1)
        self.assertEqual(m.contexto()["objetivo"]["valor"], "aprender violino")

    def test_reset_remove_tambem_fontes_e_memoria_antiga(self):
        m = MemoriaDialogo()
        texto = "Meu colega se chama Kairo"
        m.registrar(texto, "Entendi.", "conversa:relato", quadro(texto, interlocutor="Kairo"))
        pedido = "Esqueça essa conversa"
        self.assertEqual(m.contexto(pedido, quadro(pedido, ato="reset"))["historico"], [])
        m.registrar("Esqueça essa conversa", "Vamos recomeçar.", "conversa:reinicio")
        c = m.contexto()
        self.assertEqual(c["entidades"], [])
        self.assertEqual(len(c["historico"]), 2)
        self.assertEqual(c["fontes"]["user"][0]["valor"], "Esqueça essa conversa")
        m.limpar()
        self.assertEqual(m.contexto()["historico"], [])
        self.assertEqual(m.turno, 0)

    def test_expira_pelo_numero_de_turnos_incluindo_recusas(self):
        m = MemoriaDialogo(max_turnos=3)
        texto = "Quero montar uma estante"
        m.registrar(texto, "Entendi.", "conversa:relato", quadro(texto, objetivo="montar uma estante"))
        m.registrar("Você ouviu?", "Não entendi.", "fora")
        m.registrar("Como assim?", "Não entendi.", "duvida")
        self.assertIsNotNone(m.contexto()["objetivo"])
        self.assertIsNone(m.contexto("Vamos continuar?")["objetivo"])
        m.registrar("Outra coisa", "Pode falar.", "conversa:relato")
        self.assertEqual(len(m.contexto()["historico"]), 6)
        self.assertIsNone(m.contexto()["objetivo"])

    def test_retificacao_preserva_fontes_e_atualiza_evento_e_entidade(self):
        m = MemoriaDialogo()
        texto = "Eu e Lia discutimos por causa do aniversário"
        m.registrar(texto, "O que aconteceu depois?", "conversa:relato",
                    quadro(texto, evento=texto, interlocutor="Lia"))
        correcao = "Não foi Lia, foi Nara."
        m.registrar(correcao, "Entendi a correção.", "conversa:reparo", quadro(correcao, ato="correcao", interlocutor="Nara"))
        c = m.contexto("Ela não respondeu ainda")
        self.assertEqual(c["entidades_referidas"][0]["valor"], "Nara")
        self.assertEqual(c["evento"]["valor"], "Eu e Nara discutimos por causa do aniversário")
        self.assertEqual(c["evento"]["estatuto"], "retificado")
        self.assertEqual(c["evento"]["origem"], "user")
        self.assertEqual(c["evento"]["fontes"][0]["valor"], texto)
        self.assertEqual(c["evento"]["fontes"][1]["valor"], "Nara")
        self.assertEqual(c["fontes"]["user"][0]["valor"], texto)

    def test_referencia_ambigua_nao_escolhe_pessoa_arbitrariamente(self):
        m = MemoriaDialogo()
        for nome in ("Lia", "Nara"):
            texto = nome + " chegou mais cedo"
            m.registrar(texto, "Entendi.", "conversa:relato", quadro(texto, interlocutor=nome))
        c = m.contexto("Ela falou comigo")
        self.assertTrue(c["referencia_ambigua"])
        self.assertEqual({i["valor"] for i in c["entidades_referidas"]}, {"Lia", "Nara"})
        self.assertFalse(m.contexto("Nara falou comigo")["referencia_ambigua"])

    def test_fontes_modelo_nunca_se_promovem_sem_evidencia(self):
        m = MemoriaDialogo()
        m.registrar("O que aconteceu?", "Lia estava com raiva.", "logica:desconhecido")
        self.assertEqual(m.contexto()["fontes"]["verified"], [])
        self.assertEqual(m.contexto()["emocao_declarada"], [])
        m.registrar("Explique o dado", "A Lua orbita a Terra.", "logica:orbita", {
            "evidencias": [
                {"texto": "A Lua orbita a Terra.", "fonte": {"id": "relacao_17"}, "verificada": True},
                {"texto": "Não está na resposta", "fonte": "fonte_ausente", "verificada": True},
                {"texto": "A Lua", "fonte": "boato", "verificada": False}]})
        verificada = m.contexto()["fontes"]["verified"]
        self.assertEqual(len(verificada), 1)
        self.assertEqual(verificada[0]["origem"], "verified")
        self.assertEqual(verificada[0]["evidencia"], {"id": "relacao_17"})

    def test_pergunta_pendente_e_inspecao_se_referem_a_resposta_real(self):
        m = MemoriaDialogo()
        texto = "Quero reformar meu quarto"
        m.registrar(texto, "Entendi. Você já escolheu as cores?", "conversa:relato",
                    quadro(texto, objetivo="reformar meu quarto"))
        c = m.contexto()
        self.assertEqual(c["questao_pendente"]["valor"], "Você já escolheu as cores?")
        self.assertEqual(c["questao_pendente"]["origem"], "model")
        q = m.quadro_resumido()
        self.assertEqual(q["ato"], "relato")
        self.assertEqual(q["alvos"][0]["texto"], "reformar meu quarto")
        json.dumps(q, ensure_ascii=False, allow_nan=False)
        m.registrar("Sim, escolhi azul.", "Certo.", "conversa:relato")
        self.assertIsNone(m.contexto()["questao_pendente"])

    def test_sem_analise_aceita_nao_extrai_comandos_por_palavras(self):
        m = MemoriaDialogo()
        original = "Quero terminar meu desenho com Lia"
        m.registrar(original, "Pode continuar.", "conversa:relato",
                    quadro(original, objetivo="terminar meu desenho", interlocutor="Lia"))
        for texto in ("Não quero um plano, quero conversar sobre isso",
                      "Vamos mudar de assunto", "Não foi Lia, foi Nara.",
                      "Esqueça essa conversa"):
            m.registrar(texto, "Pode continuar.", "conversa:relato")
        c = m.contexto()
        self.assertEqual(c["objetivo"]["valor"], "terminar meu desenho")
        self.assertEqual(c["entidades"][0]["valor"], "Lia")
        self.assertIsNone(c["modo"])
        self.assertEqual(c["focos_recusados"], [])
        self.assertEqual(len(c["historico"]), 10)

    def test_quadro_rejeitado_e_spans_invalidos_nao_promovem_relato(self):
        for confianca in (None, True, float("nan"), float("inf"), -1, 2):
            with self.subTest(confianca=confianca):
                m = MemoriaDialogo()
                texto = "Quero viajar para Évora"
                frame = quadro(texto, objetivo="viajar para Évora")
                frame["confianca"] = confianca
                m.registrar(texto, "Entendi.", "conversa:relato", frame)
                c = m.contexto()
                self.assertIsNone(c["objetivo"])
                self.assertIsNone(c["evento"])
                json.dumps(c, ensure_ascii=False, allow_nan=False)
        m = MemoriaDialogo()
        texto = "Quero viajar para Évora"
        frame = quadro(texto, objetivo="viajar para Évora")
        frame["aceita"] = False
        m.registrar(texto, "Entendi.", "conversa:relato", frame)
        self.assertIsNone(m.contexto()["objetivo"])
        frame = quadro(texto, evento=texto)
        frame["spans"][0]["texto"] = "um relato inventado"
        m.registrar(texto, "Entendi.", "conversa:relato", frame)
        self.assertIsNone(m.contexto()["evento"])

    def test_citacoes_e_hipoteses_nao_criam_transicao_de_segmento(self):
        for texto in ('"Vamos mudar de assunto"', "Se quisermos mudar de assunto, o que ocorre?"):
            with self.subTest(texto=texto):
                m = MemoriaDialogo()
                original = "Quero estudar pintura"
                m.registrar(original, "Pode continuar.", "conversa:relato",
                            quadro(original, objetivo="estudar pintura"))
                m.registrar(texto, "Entendi a frase.", "conversa:tema", quadro(texto, ato="mudar_assunto"))
                self.assertEqual(m.contexto()["objetivo"]["valor"], "estudar pintura")
                self.assertEqual(m.segmento, 0)

    def test_span_citado_nao_se_torna_objetivo_do_usuario(self):
        texto = "Minha amiga disse 'quero aprender dança', eu só estava ouvindo"
        m = MemoriaDialogo()
        m.registrar(texto, "Você relatou a fala dela.", "conversa:relato",
                    quadro(texto, objetivo="aprender dança"))
        self.assertIsNone(m.contexto()["objetivo"])
        self.assertEqual(m.contexto()["historico"][0]["texto"], texto)

    def test_pedido_atual_enriquece_contexto_sem_alterar_memoria(self):
        m = MemoriaDialogo()
        texto = "Quero organizar minha viagem"
        c = m.contexto(texto, quadro(texto, objetivo="organizar minha viagem"))
        self.assertEqual(c["objetivo"]["valor"], "organizar minha viagem")
        self.assertTrue(c["objetivo"]["provisorio"])
        self.assertEqual(c["objetivo"]["fonte"]["texto"], texto)
        self.assertEqual(c["historico"], [])
        self.assertIsNone(m.contexto()["objetivo"])
        self.assertEqual(m.turno, 0)

    def test_correcao_sem_alvo_anterior_preserva_as_alternativas(self):
        m = MemoriaDialogo()
        original = "Eu e Lia discutimos"
        m.registrar(original, "O que aconteceu?", "conversa:relato",
                    quadro(original, interlocutor="Lia", evento=original))
        correcao = "Na verdade foi Nara, não a outra pessoa"
        m.registrar(correcao, "Entendi a correção.", "conversa:correcao",
                    quadro(correcao, ato="correcao", interlocutor="Nara"))
        self.assertEqual(m.contexto()["evento"]["valor"], "Eu e Lia discutimos")
        self.assertEqual({i["valor"] for i in m.contexto()["entidades"]}, {"Lia", "Nara"})
        self.assertTrue(m.contexto("Ela veio falar comigo")["referencia_ambigua"])
        ambiguo = MemoriaDialogo()
        for nome in ("Lia", "Nara"):
            texto = nome + " veio conversar"
            ambiguo.registrar(texto, "Entendi.", "conversa:relato", quadro(texto, interlocutor=nome))
        novo = "Na verdade foi Bia, não a outra pessoa"
        ambiguo.registrar(novo, "Não sei qual pessoa você corrigiu.", "conversa:correcao",
                         quadro(novo, ato="correcao", interlocutor="Bia"))
        self.assertEqual(ambiguo.contexto()["retificacoes"], [])

    def test_detalhe_acrescentado_nao_substitui_pessoa_do_evento(self):
        m = MemoriaDialogo()
        original = "Eu e Lia discutimos"
        m.registrar(original, "Pode continuar.", "conversa:relato",
                    quadro(original, evento=original, interlocutor="Lia"))
        adicional = "Esqueci de dizer que Nara também estava lá"
        m.registrar(adicional, "Você trouxe outro detalhe.", "conversa:correcao",
                    quadro(adicional, ato="correcao", interlocutor="Nara", evento="também estava lá"))
        self.assertEqual(m.contexto()["retificacoes"], [])
        self.assertEqual(m.contexto()["eventos"][0]["valor"], original)

    def test_historico_ativo_muda_e_retomada_nao_recupera_fonte_expirada(self):
        m = MemoriaDialogo(max_turnos=3)
        texto = "Quero terminar uma oficina"
        m.registrar(texto, "Entendi.", "conversa:relato",
                    quadro(texto, objetivo="terminar uma oficina", tema="oficina"))
        novo = "Vamos falar sobre música"
        m.registrar(novo, "Pode continuar.", "conversa:tema", quadro(novo, ato="mudar_assunto", tema="música"))
        self.assertEqual(len(m.contexto()["historico"]), 4)
        self.assertEqual(len(m.contexto()["historico_ativo"]), 2)
        for i in range(3):
            m.registrar("Outra observação " + str(i), "Entendi.", "conversa:relato")
        retomar = "Voltemos à oficina"
        c = m.contexto(retomar, quadro(retomar, ato="retomar", referencia="oficina"))
        self.assertIsNone(c["objetivo"])
        self.assertEqual(m.fontes_relevantes(retomar, quadro(retomar, ato="retomar", referencia="oficina")), [])

    def test_fontes_relevantes_recuperam_falas_literais_sem_falas_do_modelo(self):
        m = MemoriaDialogo()
        texto = "Quero montar uma oficina com Lia"
        m.registrar(texto, "Você poderia comprar um barco.", "conversa:relato",
                    quadro(texto, objetivo="montar uma oficina", interlocutor="Lia", evento=texto))
        for i in range(4):
            m.registrar("Observação " + str(i), "O modelo sugeriu uma viagem.", "conversa:relato")
        pedido = "Lembra o que eu queria?"
        fontes = m.fontes_relevantes(pedido, quadro(pedido, ato="memoria"))
        self.assertEqual(fontes, [{"papel": "usuario", "texto": texto}])
        self.assertEqual(m.fontes_relevantes(pedido), [])
        self.assertEqual(m.fontes_relevantes(pedido, quadro(pedido, ato="opiniao")), [])
        self.assertEqual(m.turno, 5)

    def test_fontes_relevantes_incluem_relato_e_correcao_sem_texto_derivado(self):
        m = MemoriaDialogo()
        texto = "Eu e Lia discutimos por causa do aniversário"
        m.registrar(texto, "Pode continuar.", "conversa:relato", quadro(texto, evento=texto, interlocutor="Lia"))
        correcao = "Não foi Lia, foi Nara."
        m.registrar(correcao, "Entendi.", "conversa:correcao", quadro(correcao, ato="correcao", interlocutor="Nara"))
        pedido = "O que aconteceu mesmo?"
        fontes = m.fontes_relevantes(pedido, quadro(pedido, ato="memoria"))
        self.assertEqual(fontes, [{"papel": "usuario", "texto": texto},
                                 {"papel": "usuario", "texto": correcao}])
        self.assertNotIn("Eu e Nara discutimos por causa do aniversário", [i["texto"] for i in fontes])

    def test_fontes_relevantes_conservam_restricao_e_emocao_declaradas(self):
        m = MemoriaDialogo()
        limite = "Só consigo estudar nas quartas-feiras"
        m.registrar(limite, "Entendi sua disponibilidade.", "conversa:objetivo",
                    quadro(limite, restricao="Só consigo estudar nas quartas-feiras"))
        sentimento = "Estou frustrada com essa situação"
        m.registrar(sentimento, "Pode continuar.", "conversa:desabafo",
                    quadro(sentimento, sentimento="frustrada"))
        for i in range(6):
            m.registrar("Outra observação " + str(i), "Pode continuar.", "conversa:relato")
        pedido = "O que eu declarei aqui?"
        self.assertEqual(m.fontes_relevantes(pedido, quadro(pedido, ato="memoria")), [
            {"papel": "usuario", "texto": limite},
            {"papel": "usuario", "texto": sentimento}])

    def test_limites_e_retorno_de_fontes_nao_compartilham_mutacoes(self):
        for limite in (0, 13, True, 1.5):
            with self.assertRaises(ValueError):
                MemoriaDialogo(limite)
        m = MemoriaDialogo()
        for i in range(15):
            texto = "Minha meta " + str(i)
            m.registrar(texto, "Entendi.", "conversa:objetivo", quadro(texto, objetivo=texto))
        self.assertEqual(len(m.turnos), 12)
        self.assertEqual(len(m.contexto()["historico"]), 24)
        pedido = "Lembra minha meta?"
        fontes = m.fontes_relevantes(pedido, quadro(pedido, ato="memoria"))
        fontes[0]["texto"] = "inventado"
        self.assertEqual(m.contexto()["objetivo"]["valor"], "Minha meta 14")
        with self.assertRaises(ValueError):
            m.fontes_relevantes(pedido, quadro(pedido, ato="memoria"), limite=3)


if __name__ == "__main__":
    unittest.main()
