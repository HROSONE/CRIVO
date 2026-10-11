import ast, importlib.util, json, sys, unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
V2=ROOT/"experimentos"/"escola_transformer17m_slots_v2_20261011"

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m

class TestesEscolaTransformerSlotsV2(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.h=load("hold_v2",V2/"preparar_holdout_v2.py")
  cls.c=load("curr_v2",V2/"curriculo_v2.py")
  cls.p=json.loads((V2/"protocolo_v2.json").read_text(encoding="utf-8"))

 def test_holdout_balanceado_e_unico(self):
  xs=self.h.gerar(); self.assertEqual(len(xs),180); self.assertEqual(set(Counter(x["operacao"] for x in xs).values()),{30})
  self.assertEqual(len({x["id"] for x in xs}),180); self.assertEqual(len({x["mensagem"] for x in xs}),180)

 def test_curriculo_mesmo_tamanho_mas_slots_abertos(self):
  xs=self.c.gerar_treino(); self.assertEqual(len(xs),3072); self.assertEqual(set(Counter(x["operacao"] for x in xs).values()),{512})
  objetos=set(); atividades=set()
  import re
  for x in xs:
   if x["historico"]:
    m=re.search(r"objeto ([^;]+); atividade (.+?)\.",x["historico"][1]["texto"])
    if m: objetos.add(m.group(1)); atividades.add(m.group(2))
  self.assertEqual(len(objetos),512); self.assertEqual(len(atividades),512)

 def test_familias_holdout_nao_estao_no_curriculo(self):
  texto="\n".join(z["texto"] for x in self.c.gerar_treino() for z in x["historico"]).casefold()
  for palavra in ("planetário","aquário","hangar","gráfica","torre meteorológica","pomar"):
   self.assertNotIn(palavra.casefold(),texto)

 def test_protocolo_precomitado(self):
  self.assertTrue(self.p["holdout"]["congelado_antes_do_treino"]); self.assertEqual(self.p["holdout"]["gerador_blob_sha"],"e4e88a0e9f769de465ef6eca592f96f3657ef341")
  self.assertEqual(self.p["baseline"]["candidato_v1_checkpoint_sha256"],"849bc4655820f8cd1f445539a1bd0f01959f03ce38145ece460c0fe27568c661")
  self.assertFalse(self.p["promocao_automatica"]); self.assertFalse(self.p["ativo_no_chat"])

 def test_holdout_abre_depois_do_treino(self):
  arv=ast.parse((V2/"treinar_v2.py").read_text(encoding="utf-8")); linhas_t=[]; linhas_h=[]
  for n in ast.walk(arv):
   if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute):
    if isinstance(n.func.value,ast.Name) and n.func.value.id=="v1" and n.func.attr=="treinar": linhas_t.append(n.lineno)
    if isinstance(n.func.value,ast.Name) and n.func.value.id=="preparar_holdout_v2" and n.func.attr=="gerar": linhas_h.append(n.lineno)
  self.assertTrue(linhas_t and linhas_h); self.assertLess(max(linhas_t),min(linhas_h))

if __name__=="__main__": unittest.main()
