"""Controles locais selecionados depois da auditoria pública; não teste cego."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("root")
p.add_argument("output")
a = p.parse_args()
root = Path(a.root).resolve()
sys.path.insert(0, str(root))
from crivo import Crivo

cases = {
    "descoberta": ["Oi, nunca usei você. O que você consegue fazer por mim?"],
    "ciencia": ["Por que o céu fica vermelho quando o sol está se pondo?",
                "Eu sou leigo. Explica isso com um exemplo do dia a dia."],
    "plano": ["Tenho 35 minutos livres agora. Quero estudar inglês e lavar a louça. Me ajuda a dividir esse tempo?",
              "A louça leva 12 minutos. Quanto tempo sobra para o inglês?",
              "E se eu deixar 5 minutos para descansar?"],
    "memoria": ["Brena é minha irmã.", "Tácio é meu primo.", "Brena prefere tapioca.",
                "Tácio prefere bolo de fubá.", "Me sugira uma opção para Brena."]
}
out = {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
       "method": "comparação local de casos já observados, API pública auditada separadamente", "cases": {}}
for case, turns in cases.items():
    bot = Crivo()
    out["cases"][case] = []
    for text in turns:
        ident, response = bot.responder(text)
        record = {"message": text, "id": ident, "response": response,
                  "generation": bot.ultima_geracao}
        out["cases"][case].append(record)
        print(json.dumps({"case": case, **record}, ensure_ascii=False), flush=True)
        Path(a.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
