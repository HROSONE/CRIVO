"""Regressões de integridade, busca, paths e exportação do acervo."""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
import acervo_programacao as acervo

@contextmanager
def isolated_acervo():
    # Copiar só o acervo, sem modelos/dados/.git da aplicação inteira.
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)/"repo"
        base=root/"docs/pesquisa_conhecimento/programacao"
        base.parent.mkdir(parents=True)
        shutil.copytree(acervo.BASE,base)
        (root/"scripts").mkdir()
        for name in ("acervo_programacao.py","test_acervo_programacao.py"):
            shutil.copy2(acervo.ROOT/"scripts"/name,root/"scripts"/name)
        yield root

class TestAcervo(unittest.TestCase):
    def setUp(self):
        self.catalog=acervo.load(acervo.CATALOG)
    def test_tokens_preservam_linguagens_e_operadores(self):
        self.assertEqual(acervo.tokens("C++ C# == != ?? ?."),{"c++","c#","==","!=","??","?."})
        self.assertEqual(acervo.tokens("Explique JS e TS"),{"javascript","typescript"})
        self.assertEqual(acervo.tokens("coerção"),{"coercao"})
    def test_busca_filtra_host_linguagem_explicitamente(self):
        result=acervo.search("unknown narrowing",5,"typescript")
        self.assertTrue(result)
        self.assertTrue(all(u["dominio"]=="typescript" for u in result))
        self.assertIn("ts_unknown-any",{u["id"] for u in result})
        self.assertEqual(acervo.search("de para e",5),[])
    def test_id_duplicado_e_referencia_inexistente_rejeitados(self):
        duplicate=copy.deepcopy(self.catalog)
        duplicate["unidades"].append(copy.deepcopy(duplicate["unidades"][0]))
        with self.assertRaisesRegex(acervo.InvalidCorpus,"duplicado"):acervo.check_catalog(duplicate)
        wrong=copy.deepcopy(self.catalog)
        wrong["unidades"][0]["relacoes"]=["nao_existe"]
        with self.assertRaisesRegex(acervo.InvalidCorpus,"Relação"):acervo.check_catalog(wrong)
    def test_ciclo_de_pre_requisito_rejeitado(self):
        c=copy.deepcopy(self.catalog);a,b=c["unidades"][:2]
        a["pre_requisitos"]=[b["id"]];b["pre_requisitos"]=[a["id"]]
        with self.assertRaisesRegex(acervo.InvalidCorpus,"Ciclo"):acervo.check_catalog(c)
    def test_fontes_e_schema_sao_verificados(self):
        c=copy.deepcopy(self.catalog);c["fontes"]["ecma"]["url"]="file:///etc/passwd"
        with self.assertRaisesRegex(acervo.InvalidCorpus,"URL"):acervo.check_catalog(c)
        c=copy.deepcopy(self.catalog);c["schema_versao"]="999"
        with self.assertRaisesRegex(acervo.InvalidCorpus,"Schema"):acervo.check_catalog(c)
    def test_path_absoluto_traversal_e_symlink_rejeitados(self):
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as outside:
            root=Path(d)
            for bad in ["../outside","/etc/passwd"]:
                with self.assertRaises(acervo.InvalidCorpus):acervo.safe_path(bad,root)
            (root/"link").symlink_to(Path(outside),target_is_directory=True)
            with self.assertRaisesRegex(acervo.InvalidCorpus,"Symlink"):
                acervo.safe_path("link/file",root)
    def test_relacoes_respeitam_profundidade_e_nao_duplicam(self):
        self.assertEqual(len(acervo.related("js_task-group",0)),1)
        links=acervo.related("js_task-group",2)
        self.assertEqual(len(links),len({u["id"] for u in links}))
        self.assertTrue(any(u["id"]=="fronteira_structured-concurrency" for u in links))
        with self.assertRaises(acervo.InvalidCorpus):acervo.related("ausente",1)
    def test_validacao_detecta_markdown_alterado_e_hash_alterado(self):
        with isolated_acervo() as root:
            base=root/"docs/pesquisa_conhecimento/programacao"
            with patch.multiple(acervo,ROOT=root,BASE=base,CATALOG=base/"catalogo-avancado.json"):
                acervo.rebuild()
                md=base/"fichas/javascript.md";original=md.read_text()
                md.write_text(original+"alteração")
                with self.assertRaisesRegex(acervo.InvalidCorpus,"Markdown"):acervo.validate()
                md.write_text(original);acervo.validate()
                sample=base/"exemplos/engenharia.mjs"
                sample.write_text(sample.read_text()+"\n// alteração\n")
                with self.assertRaisesRegex(acervo.InvalidCorpus,"Manifesto"):acervo.validate()
    def test_otimizacao_python_nao_desativa_validacao(self):
        with isolated_acervo() as root:
            p=root/"docs/pesquisa_conhecimento/programacao/catalogo-avancado.json"
            c=json.loads(p.read_text());c["unidades"].append(copy.deepcopy(c["unidades"][0]))
            p.write_text(json.dumps(c))
            result=subprocess.run([sys.executable,"-O",str(root/"scripts/acervo_programacao.py"),"--validar"],
                                  capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,1)
            self.assertIn("duplicado",result.stderr)
    def test_reconstrucao_deterministica_e_exportacao_jsonl(self):
        with isolated_acervo() as root:
            script=root/"scripts/acervo_programacao.py"
            for _ in range(2):
                result=subprocess.run([sys.executable,str(script),"--reconstruir"],capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,0,result.stderr)
                current=(root/"docs/pesquisa_conhecimento/programacao/manifesto.json").read_bytes()
                if _==0:first=current
                else:self.assertEqual(current,first)
            result=subprocess.run([sys.executable,str(script),"--jsonl","--dominio","typescript"],
                                  capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            records=[json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(len(records),61)
            self.assertTrue(all(r["dominio"]=="typescript" and r["referencias"] for r in records))

if __name__=="__main__":unittest.main()
