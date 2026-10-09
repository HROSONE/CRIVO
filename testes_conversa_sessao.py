"""Contratos de ligação, escopo e continuidade do consumidor da sessão."""
import copy
import unittest
from unittest.mock import patch

from crivo import Crivo
from conversa_sessao import responder


class TestesConversaSessao(unittest.TestCase):
    def bot(self, *declaracoes):
        b = Crivo(usar_geracao=False, usar_linguagem_neural=False)
        for d in declaracoes:
            b.responder(d)
        return b

    def test_mesmo_pedido_com_valores_opostos_muda_escolha(self):
        for valor, proibido in [('suco de araçá', 'creme de cajá'), ('creme de cajá', 'suco de araçá')]:
            b = self.bot('Daneli prefere ' + valor + '.', 'Luzerno prefere ' + proibido + '.')
            _, r = b.responder('Me sugira uma opção para Daneli.')
            self.assertIn('oferecer ' + valor, r)
            self.assertNotIn(proibido, r)

    def test_correcao_antes_da_continuacao_resolve_estado_atual(self):
        b = self.bot('Daneli prefere suco.', 'Me sugira uma opção para Daneli.',
                     'Corrigindo: Daneli prefere mingau.')
        _, r = b.responder('Me sugira uma opção para Daneli.')
        self.assertIn('mingau', r)
        self.assertNotIn('suco', r)
        _, r = b.responder('Como eu explico essa escolha?')
        self.assertIn('mingau', r)

    def test_sugestao_nao_vira_nova_declaracao(self):
        b = self.bot('Daneli prefere suco.')
        estado = b.memoria_sessao.exportar()
        b.responder('Me sugira uma opção para Daneli.')
        depois = b.memoria_sessao.exportar()
        self.assertEqual(estado['afirmacoes'], depois['afirmacoes'])
        self.assertEqual(estado['entidades'], depois['entidades'])

    def test_pronome_ambiguo_nao_escolhe_ultima_pessoa(self):
        b = self.bot('Daneli é minha irmã.', 'Yorina é minha prima.',
                     'Daneli prefere suco.', 'Yorina prefere mingau.')
        ident, r = b.responder('Me sugira algo que ela goste.')
        self.assertTrue(ident.startswith('conversa:sessao_'))
        self.assertIn('qual pessoa', r.lower())
        self.assertNotIn('suco', r)
        self.assertNotIn('mingau', r)

    def test_pessoa_desconhecida_nao_herda_preferencia(self):
        b = self.bot('Daneli prefere suco.')
        _, r = b.responder('Me sugira algo que Yorina goste.')
        self.assertNotIn('suco', r)
        self.assertIn('não informou', r)

    def test_multiplas_pessoas_exigem_foco(self):
        b = self.bot('Daneli prefere suco.', 'Yorina prefere mingau.')
        _, r = b.responder('Me sugira uma opção para Daneli e Yorina.')
        self.assertIn('Qual pessoa', r)
        self.assertNotIn('suco', r)

    def test_fala_reportada_continua_atribuida(self):
        b = self.bot('Daneli disse que prefere suco.', 'Eu prefiro mingau.')
        _, r = b.responder('Me sugira uma opção para Daneli.')
        self.assertIn('Daneli disse que prefere suco', r)
        self.assertNotIn('mingau', r)

    def test_hipotese_nao_substitui_preferencia_real(self):
        b = self.bot('Daneli prefere suco.', 'Se Daneli preferisse mingau, seria uma hipótese.')
        _, r = b.responder('Vamos usar o gosto real de Daneli para uma sugestão.')
        self.assertIn('suco', r)
        self.assertNotIn('mingau', r)

    def test_retracao_nao_pode_ser_reutilizada(self):
        b = self.bot('Daneli prefere suco.')
        f = b.memoria_sessao._atual('pessoa:daneli', 'preferência')
        f['status'] = 'retirado'
        _, r = b.responder('Me sugira uma opção para Daneli.')
        self.assertNotIn('suco', r)
        self.assertIn('não informou', r)

    def test_esquecimento_interrompe_continuacao(self):
        b = self.bot('Daneli prefere suco.', 'Me sugira uma opção para Daneli.',
                     'Agora esqueça tudo que eu contei aqui.')
        _, r = b.responder('Me sugira algo que Daneli goste.')
        self.assertNotIn('suco', r)
        _, r = b.responder('O que você precisa saber de mim?')
        self.assertIn('preferências', r)
        self.assertNotIn('suculentas', r)

    def test_tempo_e_permissao_nao_sao_trocados_por_valores_padrao(self):
        b = self.bot('Daneli quer terminar uma maquete.', 'Daneli tem 13 minutos.',
                     'Daneli não pode usar cola quente.')
        _, r = b.responder('Me sugira um próximo passo para Daneli.')
        self.assertIn('13 minutos', r)
        self.assertIn('não pode usar cola quente', r)
        self.assertIn('restrição', r)
        self.assertNotIn('uma hora', r)
        _, r = b.responder('Como eu explico essa escolha?')
        self.assertIn('objetivo', r)
        self.assertNotIn('preferência', r)

    def test_preferencia_com_proibicao_nao_vira_recomendacao(self):
        b = self.bot('Daneli prefere chá mate.', 'Daneli não pode tomar chá mate.')
        _, r = b.responder('Me sugira uma opção para Daneli.')
        self.assertIn('não pode tomar chá mate', r)
        self.assertNotIn('Uma opção é oferecer chá mate', r)
        self.assertIn('conferir', r)

    def test_disponibilidade_sem_objetivo_nao_inventa_atividade(self):
        b = self.bot('Daneli tem 13 minutos.')
        _, r = b.responder('Me sugira um próximo passo para Daneli.')
        self.assertIn('13 minutos', r)
        self.assertIn('Qual objetivo', r)
        self.assertNotIn('escolha uma parte pequena desse objetivo', r)

    def test_descricao_nao_inventa_local_do_objeto(self):
        b = self.bot('Daneli é minha irmã.', 'A mochila de Daneli é roxa.')
        _, r = b.responder('Me ajude a descrever a mochila de Daneli.')
        self.assertIn('roxa', r)
        _, r = b.responder('Onde eu encontro a mochila de Daneli?')
        self.assertIn('não informou', r)
        self.assertNotIn('quarto', r)

    def test_pedido_de_sugestao_nao_vira_consulta_por_oracao_relativa(self):
        b = self.bot('Daneli prefere suco.')
        ident, r = b.responder('Quero escolher algo para Daneli usando o que contei.')
        self.assertEqual(ident, 'conversa:sessao_sugerir')
        self.assertIn('oferecer suco', r)

    def test_pergunta_factual_com_mudanca_de_tema_conserva_fonte(self):
        b = self.bot('Daneli prefere suco.', 'Me sugira uma opção para Daneli.')
        ident, r = b.responder('Mudando de assunto: o que é DNA?')
        self.assertNotIn('suco', r)
        self.assertIn('genéticas', r)
        _, r = b.responder('Qual é a fonte dessa informação?')
        self.assertIn('genome.gov', r)

    def test_consumidor_nao_intercepta_ficcao_codigo_e_fatos(self):
        b = self.bot('Daneli prefere suco.')
        for t in ('Escreva um poema para Daneli.', 'Me sugira um algoritmo Python para Daneli.',
                  'Por que o céu é azul?', 'Onde fica o Japão?', 'Se A implica B e A, qual conclusão?'):
            self.assertIsNone(responder(t, b), t)

    def test_sem_geracao_consulta_preserva_memoria_ultimo(self):
        b = self.bot('Daneli prefere suco.')
        snapshot = copy.deepcopy(b.memoria_sessao.ultimo)
        responder('Me sugira uma opção para Daneli.', b)
        self.assertEqual(snapshot, b.memoria_sessao.ultimo)

    def test_pesos_rejeitados_nao_sao_carregados(self):
        b = self.bot('Daneli prefere suco.')
        with patch('pathlib.Path.read_text', side_effect=AssertionError('não ler pesos experimentais')):
            resultado = responder('Me sugira uma opção para Daneli.', b)
        self.assertIsNotNone(resultado)


if __name__ == '__main__':
    unittest.main()
