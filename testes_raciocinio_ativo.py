"""Oráculo independente por atribuições booleanas, contradições e memória."""
import itertools
import random
import unittest

from raciocinio_ativo import Literal, Premissa, RaciocinioAtivo, SistemaPremissas, ler_literal, ler_premissa, LimiteRaciocinio


def mundos_oraculo(premissas, nomes):
    mundos = []
    for bits in itertools.product((False, True), repeat=len(nomes)):
        valores = dict(zip(nomes, bits))
        valido = True
        for p in premissas:
            antecedentes = [valores[l.nome] != l.negativo for l in p.antecedentes]
            exige = (any(antecedentes) if p.operador == 'ou' else all(antecedentes))
            if exige and valores[p.consequente.nome] == p.consequente.negativo:
                valido = False
                break
        if valido:
            mundos.append(valores)
    return mundos


class TestesSistemaPremissas(unittest.TestCase):
    def test_teorias_sorteadas_contra_oraculo_independente(self):
        rng = random.Random(402611)
        nomes = ['evento azur', 'evento brin', 'evento cendal', 'evento doria', 'evento estel']
        for _ in range(45):
            premissas = []
            for i in range(rng.randint(2, 8)):
                antes = tuple(Literal(n, rng.choice((False, True)), n)
                              for n in rng.sample(nomes, rng.randint(0, 3)))
                n = rng.choice(nomes)
                premissas.append(Premissa(antes, Literal(n, rng.choice((False, True)), n), rng.choice(('e', 'ou')) if antes else 'e', 'premissa ' + str(i)))
            sistema = SistemaPremissas(premissas)
            usados = list(sistema.nomes)
            mundos = mundos_oraculo(premissas, usados)
            self.assertEqual(len(sistema.mundos), len(mundos))
            for nome in usados:
                for negativo in (False, True):
                    alvo = Literal(nome, negativo, nome)
                    valores = [m[nome] != negativo for m in mundos]
                    esperado = ('conflito' if not mundos else 'sustentado' if all(valores)
                                else 'refutado' if not any(valores) else 'indeterminado')
                    obtido = sistema.analisar(alvo)
                    self.assertEqual(obtido['status'], esperado)
                    if esperado in ('sustentado', 'refutado'):
                        provas = [premissas[p['indice']] for p in obtido['provas']]
                        restantes = mundos_oraculo(provas, usados)
                        self.assertTrue(restantes)
                        self.assertTrue(all((m[nome] != negativo) == (esperado == 'sustentado') for m in restantes))

    def test_condicoes_negativas_disjuncao_e_contrapositiva(self):
        for textos, pergunta, esperado in [
            (['chove', 'se chove ou a rega liga, então o jardim molha'], 'o jardim molha', 'sustentado'),
            (['não chove', 'se não chove, então o jardim seca'], 'o jardim seca', 'sustentado'),
            (['o painel não liga', 'se o sensor responde, então o painel liga'], 'o sensor não responde', 'sustentado'),
            (['o painel liga', 'se o sensor responde, então o painel liga'], 'o sensor responde', 'indeterminado'),
            (['não chove', 'se chove, então a rua molha'], 'a rua não molha', 'indeterminado'),
        ]:
            s = SistemaPremissas([ler_premissa(t) for t in textos])
            self.assertEqual(s.analisar(ler_literal(pergunta))['status'], esperado)

    def test_conflito_nao_prova_qualquer_coisa(self):
        p = [ler_premissa(t) for t in ['chove', 'não chove', 'o painel liga']]
        s = SistemaPremissas(p)
        resultado = s.analisar(ler_literal('o jardim seca'))
        self.assertEqual(resultado['status'], 'conflito')
        self.assertEqual({i['indice'] for i in resultado['provas']}, {0, 1})

    def test_abducao_e_somente_hipotese_coerente(self):
        p = [ler_premissa(t) for t in ['se o sensor responde e o painel liga, então o alarme funciona', 'se a bateria tem carga, então o alarme funciona']]
        s = SistemaPremissas(p)
        alvo = ler_literal('o alarme funciona')
        resultado = s.abduzir(alvo)
        self.assertGreaterEqual(len(resultado['propostas']), 2)
        for proposta in resultado['propostas']:
            suposicoes = [Literal(d['nome'], d['negativo'], d['texto']) for d in proposta['suposicoes']]
            self.assertTrue(all(l.nome != alvo.nome for l in suposicoes))
            novos = p + [Premissa((), l, 'e', l.texto()) for l in suposicoes]
            m = mundos_oraculo(novos, list(s.nomes))
            self.assertTrue(m)
            self.assertTrue(all(v[alvo.nome] for v in m))
            self.assertFalse(proposta['comprovada_no_mundo'])

    def test_abducao_tambem_explora_negacoes_logicas(self):
        s = SistemaPremissas([ler_premissa('se o sensor responde, então o painel liga')])
        propostas = s.abduzir(ler_literal('o sensor não responde'))['propostas']
        self.assertTrue(any(p['suposicoes'][0]['nome'] == 'painel liga' and p['suposicoes'][0]['negativo'] for p in propostas))

    def test_limites_sem_estado_parcial(self):
        with self.assertRaises(LimiteRaciocinio):
            SistemaPremissas([ler_premissa('evento ' + str(i)) for i in range(11)])
        with self.assertRaises(ValueError):
            ler_premissa('se chove e faz frio ou venta, então a rua molha')
        with self.assertRaises(ValueError):
            ler_literal('talvez chove')


class TestesMemoriaRaciocinio(unittest.TestCase):
    def setUp(self):
        self.r = RaciocinioAtivo()
        self.t = 0

    def responder(self, texto):
        self.t += 1
        return self.r.preparar(texto, self.t)

    def test_revisao_retracao_e_recomputacao(self):
        self.responder('Considere estas premissas: chove; se chove, então a rua molha')
        self.responder('Posso concluir que a rua molha?')
        self.assertEqual(self.r.ultimo['status'], 'sustentado')
        self.responder('Corrija a premissa: não chove')
        self.responder('Posso concluir que a rua molha?')
        self.assertEqual(self.r.ultimo['status'], 'indeterminado')
        self.responder('Acrescente a premissa: chove')
        self.assertEqual(self.r.ultimo['status'], 'conflito')
        self.responder('Retire a premissa: não chove')
        self.responder('Posso concluir que a rua molha?')
        self.assertEqual(self.r.ultimo['status'], 'sustentado')

    def test_contrafactual_nao_muda_base(self):
        self.responder('Considere estas premissas: chove; se chove, então a rua molha')
        self.responder('Posso concluir que a rua molha?')
        antes = self.r.premissas
        self.responder('E se não chove?')
        self.assertEqual(self.r.ultimo['operacao'], 'contrafactual')
        self.assertEqual(self.r.ultimo['status'], 'indeterminado')
        self.assertEqual(self.r.premissas, antes)
        self.responder('Posso concluir que a rua molha?')
        self.assertEqual(self.r.ultimo['status'], 'sustentado')

    def test_entrada_incompleta_e_orcamento_nao_corrompem_base(self):
        self.responder('Considere estas premissas: chove')
        antes = self.r.premissas
        for texto in ['Considere estas premissas: se chove então', 'Posso concluir que ' + 'z' * 81,
                      'Corrija a premissa: o avião voa', 'Considere estas premissas: ' + '; '.join('evento ' + str(i) for i in range(11))]:
            self.responder(texto)
            self.assertEqual(self.r.premissas, antes)
            self.assertIn(self.r.ultimo['status'], ('nao_interpretado', 'limite'))

    def test_hipoteses_novas_e_nao_fatos(self):
        self.responder('Considere estas premissas: se o sensor responde e o painel liga, então o alarme funciona')
        antes = self.r.premissas
        self.responder('Que hipóteses você sugere?')
        self.assertTrue(self.r.ultimo['propostas'])
        self.assertEqual(self.r.premissas, antes)
        self.assertFalse(self.r.ultimo['comprovado_no_mundo'])

    def test_expiracao_e_limpeza(self):
        self.responder('Considere estas premissas: chove')
        self.t += 11
        self.responder('Posso concluir que chove?')
        self.assertEqual(self.r.ultimo['status'], 'sem_premissas')
        self.responder('Considere estas premissas: chove')
        self.responder('Limpar hipótese')
        self.assertFalse(self.r.premissas)

    def test_nao_intercepta_relato_codigo_ou_citacao(self):
        for texto in ['Estou com fome', 'O que é DNA?', '```Considere estas premissas: chove```', 'Ele disse "hipótese: chove"']:
            self.assertIsNone(self.responder(texto))


if __name__ == '__main__':
    unittest.main()
