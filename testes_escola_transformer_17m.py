import ast
import hashlib
import importlib.util
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXP = ROOT / "experimentos" / "escola_transformer_17m_20261011"


def modulo(nome, caminho):
    spec = importlib.util.spec_from_file_location(nome, caminho)
    m = importlib.util.module_from_spec(spec)
    sys.modules[nome] = m
    spec.loader.exec_module(m)
    return m


def sha_json(obj):
    bruto = json.dumps(obj, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")).encode()
    return hashlib.sha256(bruto).hexdigest()


class TestesEscolaTransformer17M(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hold = modulo("esc17_hold", EXP / "preparar_holdout.py")
        cls.cur = modulo("esc17_curriculo", EXP / "curriculo.py")
        cls.manifesto = json.loads((EXP / "manifesto_holdout.json").read_text(encoding="utf-8"))
        cls.protocolo = json.loads((EXP / "protocolo.json").read_text(encoding="utf-8"))

    def test_holdout_realmente_congelado_e_balanceado(self):
        exemplos = self.hold.gerar()
        por_op = Counter(x["operacao"] for x in exemplos)
        self.assertEqual(len(exemplos), 120)
        self.assertEqual(set(por_op.values()), {20})
        self.assertEqual(len({x["id"] for x in exemplos}), 120)
        self.assertEqual(len({x["mensagem"] for x in exemplos}), 120)
        pacote = {
            "versao": 1,
            "semente": self.hold.SEMENTE,
            "congelado_antes_do_treino": True,
            "auditoria": {
                "aprovado": True,
                "exemplos": 120,
                "familias": len(self.hold.FAMILIAS),
                "mensagens_exatas_repetidas": 0,
                "por_operacao": {op: por_op[op] for op in self.hold.OPERACOES},
            },
            "exemplos": exemplos,
        }
        self.assertEqual(sha_json(pacote), self.manifesto["holdout_sha256_canonico"])
        self.assertEqual(
            hashlib.sha256((EXP / "preparar_holdout.py").read_bytes()).hexdigest(),
            self.manifesto["gerador_sha256"])

    def test_curriculo_e_separado_e_balanceado(self):
        treino = self.cur.gerar_treino()
        hold = self.hold.gerar()
        self.assertEqual(len(treino), 3072)
        self.assertEqual(set(Counter(x["operacao"] for x in treino).values()), {512})
        self.assertFalse({x["mensagem"] for x in treino} & {x["mensagem"] for x in hold})
        reservados = ("observatório", "viveiro", "oficina", "trilha", "estúdio")
        texto_treino = "\n".join(
            [x["mensagem"] + "\n" + x["resposta"] for x in treino] +
            [t["texto"] for x in treino for t in x["historico"]]
        ).casefold()
        for palavra in reservados:
            self.assertNotIn(palavra.casefold(), texto_treino)

    def test_base_exata_e_sem_pesos_externos(self):
        base = self.protocolo["base"]
        self.assertEqual(base["pesos_sha256"],
                         "16102a72b21031b8bee2b4edfa633a359f7f08c5beab552b05f294e656b0cc67")
        self.assertEqual(base["tokenizer_sha256"],
                         "6e3704ce921851122953b8ac20c05e3a131f9cf0fa3c76d6e2391c4ec3efc88f")
        self.assertEqual(base["parametros"], 17428224)
        self.assertEqual(base["passo"], 20000)
        self.assertFalse(base["pesos_externos"])

    def test_holdout_so_abre_depois_do_treino(self):
        arvore = ast.parse((EXP / "treinar_escola.py").read_text(encoding="utf-8"))
        linhas_treino, linhas_holdout = [], []
        for no in ast.walk(arvore):
            if isinstance(no, ast.Call) and isinstance(no.func, ast.Name):
                if no.func.id == "treinar":
                    linhas_treino.append(no.lineno)
                elif no.func.id == "carregar_holdout":
                    linhas_holdout.append(no.lineno)
        self.assertTrue(linhas_treino)
        self.assertTrue(linhas_holdout)
        self.assertLess(max(linhas_treino), min(linhas_holdout))

    def test_promocao_exige_todos_os_gates_e_nunca_ativa_sozinha(self):
        fonte = (EXP / "treinar_escola.py").read_text(encoding="utf-8")
        self.assertIn("elegivel = all(gs.values())", fonte)
        self.assertIn('"ativo_no_chat": False', fonte)
        self.assertIn('"auxiliares_serializados": False', fonte)
        gates = self.protocolo["avaliacao"]["promocao"]
        self.assertEqual(gates["operacao_min"], 0.60)
        self.assertEqual(gates["cada_operacao_min"], 0.35)
        self.assertEqual(gates["slot_min"], 0.70)
        self.assertEqual(gates["preservacao_ce_relativa_max"], 1.05)

    def test_preservacao_foi_congelada(self):
        p = json.loads((EXP / "preservacao_portugues.json").read_text(encoding="utf-8"))
        self.assertTrue(p["congelado_antes_do_treino"])
        self.assertGreaterEqual(len(p["textos"]), 30)
        self.assertEqual(len(p["textos"]), len(set(p["textos"])))


if __name__ == "__main__":
    unittest.main()
