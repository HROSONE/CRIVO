"""Regressões de programação; perguntas de desenvolvimento fora do cadastro."""
import json
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from crivo import Crivo, PASTA, chave_pergunta


# Fixadas antes de escrever o conteúdo. Não adicionar estas frases ao treino.
CASOS = [
    ("Explique programação para um iniciante", "prog_programar"),
    ("Qual é a ideia de um algoritmo?", "prog_algoritmo"),
    ("O que significa variável num programa?", "prog_variavel"),
    ("Por que existem tipos de dados?", "prog_tipos"),
    ("Como exibir uma mensagem usando Python?", "py_print"),
    ("Python: ler uma resposta pelo teclado", "py_input"),
    ("Me ensine uma condição if no Python", "py_if"),
    ("Python: repetir uma tarefa com for", "py_for"),
    ("Preciso entender o while do Python", "py_while"),
    ("Definir uma função que soma em Python", "py_funcao"),
    ("Quero acrescentar um item numa lista Python", "py_lista"),
    ("Como guardar chaves e valores no Python?", "py_dicionario"),
    ("No Python, qual a diferença entre = e ==?", "py_comparacao"),
    ("Como capturar uma exceção em Python?", "py_excecao"),
    ("Python apresentou SyntaxError", "py_syntaxerror"),
    ("Meu Python mostrou IndentationError", "py_indentacao"),
    ("Recebi NameError usando Python", "py_nameerror"),
    ("Apareceu TypeError no meu script Python", "py_typeerror"),
    ("Como resolver ValueError no Python?", "py_valueerror"),
    ("Minha lista deu IndexError no Python", "py_indexerror"),
    ("Meu dicionário Python deu KeyError", "py_keyerror"),
    ("Como abrir um arquivo de texto usando Python?", "py_arquivo"),
    ("Transformar texto JSON num objeto Python", "py_json"),
    ("Mostre uma classe simples no Python", "py_classe"),
    ("Como importar um módulo Python?", "py_import"),
    ("Python: para que criar um ambiente virtual?", "py_venv"),
    ("Como escrever um teste automatizado Python?", "py_teste"),
    ("Me mostra uma página básica em HTML", "web_html"),
    ("Quero mudar a cor do texto com CSS", "web_css"),
    ("Para que eu usaria JavaScript numa página?", "js_intro"),
    ("Qual diferença existe entre let e const?", "js_variavel"),
    ("Faça um exemplo de função de soma em JavaScript", "js_funcao"),
    ("JavaScript: percorrer os itens de um array", "js_for"),
    ("Como selecionar um elemento com querySelector?", "js_dom"),
    ("Explique async await no JavaScript", "js_async"),
    ("Para que serve a linguagem SQL?", "sql_intro"),
    ("Como filtrar uma consulta com WHERE no SQL?", "sql_select"),
    ("Como unir duas tabelas com JOIN?", "sql_join"),
    ("Como evitar SQL injection usando parâmetros?", "sql_parametros"),
    ("Pra que serve controle de versão Git?", "git_intro"),
    ("Como salvar alterações num commit Git?", "git_commit"),
    ("Como criar outra branch no Git?", "git_branch"),
    ("Quero comparar alterações usando git diff", "git_diff"),
    ("O que é uma API HTTP?", "prog_http"),
    ("Como depurar um programa com bug?", "prog_debug"),
    ("O que faz a raiz de uma planta?", "partes_planta"),
]

FORA = [
    "Crie um compilador Rust completo",
    "Quero uma função Java para ordenar objetos",
    "Faça um driver em C++",
    "Me dê um sistema bancário completo em Python",
]


def avaliar_programacao(classe=Crivo):
    resultados = []
    for pergunta, esperado in CASOS:
        obtido = classe().responder(pergunta)[0]
        resultados.append({"pergunta": pergunta, "esperado": esperado,
                           "obtido": obtido, "passou": obtido == esperado})
    return {"total": len(resultados),
            "acertos": sum(c["passou"] for c in resultados), "casos": resultados}


class TestesProgramacao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads((PASTA / 'conhecimento.json').read_text(encoding='utf-8'))

    def test_perguntas_fora_do_treino(self):
        cadastradas = {q for e in Crivo().base for q in e["perguntas"]}
        for c in avaliar_programacao()["casos"]:
            with self.subTest(pergunta=c["pergunta"]):
                self.assertNotIn(c["pergunta"], cadastradas)
                self.assertEqual(c["obtido"], c["esperado"])

    def test_nao_promete_programas_que_nao_sabe_criar(self):
        for pergunta in FORA:
            with self.subTest(pergunta=pergunta):
                self.assertIn(Crivo().responder(pergunta)[0], ("fora", "duvida"))

    def test_curriculo_sem_colisoes_e_com_cobertura(self):
        ids = [e['id'] for e in self.base]
        self.assertEqual(len(ids), len(set(ids)))
        perguntas = {}
        for e in self.base:
            for pergunta in e['perguntas']:
                chave = chave_pergunta(pergunta)
                self.assertIn(perguntas.get(chave), (None, e['id']), pergunta)
                perguntas[chave] = e['id']
        areas = {e['area'] for e in self.base if e['topico'] == 'programacao'}
        self.assertTrue({'fundamentos', 'python', 'javascript', 'html', 'css', 'sql', 'git'} <= areas)

    def test_todas_as_perguntas_ensinadas(self):
        for e in self.base:
            if e['topico'] != 'programacao':
                continue
            for pergunta in e['perguntas']:
                with self.subTest(pergunta=pergunta):
                    id_obtido, resposta = Crivo().responder(pergunta)
                    self.assertEqual(id_obtido, e['id'])
                    if 'exemplo' in e:
                        self.assertIn(e['exemplo']['codigo'], resposta)

    def test_operadores_nao_viram_a_mesma_pergunta(self):
        # A normalização antiga apagava operadores e confundia esses cadastros.
        with tempfile.TemporaryDirectory() as pasta:
            base = []
            for id, q in [('igual', 'o que significa x == 2'),
                          ('diferente', 'o que significa x != 2'),
                          ('atribuir', 'o que significa x = 2')]:
                base.append(dict(id=id, topico='programacao', perguntas=[q], resposta=id))
            arquivo = Path(pasta) / 'base.json'
            arquivo.write_text(json.dumps(base), encoding='utf-8')
            for e in base:
                self.assertEqual(Crivo(arquivo).responder(e['perguntas'][0])[0], e['id'])
        self.assertNotEqual(chave_pergunta('o que é C++?'), chave_pergunta('o que é C#?'))

    def test_linguagem_explicita_nao_recebe_exemplo_de_outra(self):
        for linguagem, prefixo in [('Python', 'py_'), ('JavaScript', 'js_')]:
            with self.subTest(linguagem=linguagem):
                id_obtido, resposta = Crivo().responder('função de soma em ' + linguagem)
                self.assertEqual(id_obtido, prefixo + 'funcao')
                self.assertIn('```' + linguagem.lower(), resposta)
        self.assertIn(Crivo().responder('TypeError em JavaScript')[0], ('fora', 'duvida'))

    def test_exemplos_python_executam_e_produzem_saida_esperada(self):
        for e in self.base:
            exemplo = e.get('exemplo', {})
            if exemplo.get('linguagem') != 'python':
                continue
            with self.subTest(id=e['id']), tempfile.TemporaryDirectory() as pasta:
                Path(pasta, 'dados.txt').write_text('Texto de teste\n', encoding='utf-8')
                resultado = subprocess.run(
                    [sys.executable, '-I', '-X', 'utf8', '-c', exemplo['codigo']],
                    input=exemplo.get('entrada', ''), text=True, encoding='utf-8',
                    cwd=pasta, capture_output=True, timeout=5)
                self.assertEqual(resultado.returncode, 0, resultado.stderr)
                self.assertEqual(resultado.stdout, exemplo['saida'])

    @unittest.skipUnless(shutil.which('node'), 'Node.js necessário para verificar JavaScript')
    def test_exemplos_javascript(self):
        for e in self.base:
            exemplo = e.get('exemplo', {})
            if exemplo.get('linguagem') != 'javascript':
                continue
            with self.subTest(id=e['id']):
                verificado = subprocess.run(['node', '--check'], input=exemplo['codigo'],
                    text=True, capture_output=True, timeout=5)
                self.assertEqual(verificado.returncode, 0, verificado.stderr)
                if 'saida' in exemplo:
                    resultado = subprocess.run(['node'], input=exemplo['codigo'],
                        text=True, capture_output=True, timeout=5)
                    self.assertEqual(resultado.returncode, 0, resultado.stderr)
                    self.assertEqual(resultado.stdout, exemplo['saida'])

    def test_exemplos_sql_em_banco_temporario(self):
        with sqlite3.connect(':memory:') as banco:
            banco.executescript('''
                CREATE TABLE cidades (id INTEGER PRIMARY KEY, nome TEXT);
                CREATE TABLE pessoas (nome TEXT, idade INTEGER, cidade_id INTEGER);
                INSERT INTO cidades VALUES (1, 'Natal'), (2, 'Mossoró');
                INSERT INTO pessoas VALUES ('Ana', 23, 1), ('Lia', 31, 2), ('Noé', 12, 1);
            ''')
            for e in self.base:
                exemplo = e.get('exemplo', {})
                if exemplo.get('linguagem') == 'sql':
                    with self.subTest(id=e['id']):
                        linhas = [list(l) for l in banco.execute(exemplo['codigo'])]
                        self.assertEqual(linhas, exemplo['saida'])

    def test_exemplos_do_menu_e_ensino_na_nova_categoria(self):
        bot = Crivo()
        self.assertIn('programação', bot.responder('assuntos')[1])
        self.assertIn('programação', bot.responder('oi')[1])
        bot.ensinar('py_dobro', 'programacao', ['o dobro em python'], 'Multiplique por dois.', salvar=False)
        self.assertEqual(bot.responder('o dobro em python')[0], 'py_dobro')
        self.assertEqual(bot.responder('explique dobro python')[0], 'py_dobro')

    def test_curriculo_novo_preserva_ranking_dos_assuntos_gerais(self):
        completo = Crivo()
        gerais = [e for e in self.base if e['topico'] != 'programacao']
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / 'base.json'
            arquivo.write_text(json.dumps(gerais), encoding='utf-8')
            anterior = Crivo(arquivo)
            for pergunta in ('planta', 'nomes dos planetas em ordem', 'planta para iniciante',
                             'como ler a etiqueta da roupa', 'teste do ovo na água',
                             'nomes das estações', 'tipos de clima brasileiro'):
                with self.subTest(pergunta=pergunta):
                    antes = [(s, anterior.base[i]['id']) for s, i in anterior._ranking(pergunta)]
                    depois = [(s, completo.base[i]['id']) for s, i in completo._ranking(pergunta)]
                    self.assertEqual(antes, depois)


if __name__ == "__main__":
    unittest.main()
