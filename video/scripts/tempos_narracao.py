"""Gera src/narracao/dados.gen.ts: início de cada cena e páginas de legenda.

As cenas começam na primeira palavra de cada trecho do roteiro (abaixo); as
legendas quebram na pontuação ou a cada 5 palavras. Destaques são palavras
que aparecem em cor na legenda.

Uso: python scripts/tempos_narracao.py public/voz/legendas.json src/narracao/dados.gen.ts
"""
import json
import re
import sys

FPS = 30
DURACAO_S = 67.85

# (id da cena, primeiras palavras do trecho)
CENAS = [
    ("clonados", "Na última semana"),
    ("pirataria", "É praticamente"),
    ("comum", "Infelizmente, essa prática"),
    ("assinatura", "só você tem aquele"),
    ("tentacao", "Como é que você"),
    ("parece", "Diga, gente"),
    ("comportamento", "Quando você pede"),
    ("engenharia", "Mas se você pedir"),
    ("perigo", "Isso é um perigo"),
    ("umaHora", "Mas se todo mundo"),
    ("malIntencionada", "E se a pessoa"),
    ("roubo", "Porque imagina: só"),
    ("favorContra", "E aí, você"),
    ("inscreva", "Deixa sua opinião"),
]

DESTAQUES = {
    "clonados", "pirataria", "ia", "comum", "assinatura", "dinheiro", "tentação", "mcp", "zero",
    "clone", "comportamento", "engenharia", "reversa", "estrutura", "perigo", "receber", "clonar",
    "1", "hora", "mal-intencionada", "melhor", "controle", "dados", "banco", "favor", "contra",
    "opinião", "comentários", "inscreve",
}


def limpa(w):
    return re.sub(r"[^\wÀ-ÿ-]", "", w).lower()


def main():
    legendas = json.load(open(sys.argv[1], encoding="utf-8"))
    palavras = [c["text"].strip() for c in legendas]
    inicio = []
    desde = 0
    for cid, frase in CENAS:
        alvo = frase.split()
        for i in range(desde, len(palavras)):
            if [limpa(w) for w in palavras[i:i + len(alvo)]] == [limpa(w) for w in alvo]:
                inicio.append((cid, round(legendas[i]["startMs"] / 1000 * FPS)))
                desde = i + 1
                break
        else:
            raise SystemExit(f"não achei o trecho: {frase}")
    inicio[0] = (inicio[0][0], 0)
    total = round(DURACAO_S * FPS)
    cenas = [
        {"id": cid, "de": de, "dur": (inicio[k + 1][1] if k + 1 < len(inicio) else total) - de}
        for k, (cid, de) in enumerate(inicio)
    ]

    paginas, atual = [], []
    for c in legendas:
        atual.append(c)
        fim_frase = re.search(r"[.,;:?!]$", c["text"]) is not None
        if fim_frase or len(atual) >= 5:
            paginas.append(atual)
            atual = []
    if atual:
        paginas.append(atual)
    saida_paginas = []
    for k, pg in enumerate(paginas):
        prox = paginas[k + 1][0]["startMs"] if k + 1 < len(paginas) else round(DURACAO_S * 1000)
        saida_paginas.append({
            "de": round(pg[0]["startMs"] / 1000 * FPS),
            "ate": round(prox / 1000 * FPS),
            "palavras": [{"t": c["text"].strip(), "d": limpa(c["text"]) in DESTAQUES} for c in pg],
        })

    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write("// Gerado por scripts/tempos_narracao.py a partir de public/voz/legendas.json.\n")
        f.write("// Não edite à mão: ajuste o roteiro ou o alinhamento e gere de novo.\n\n")
        f.write(f"export const TOTAL_NARRACAO = {total};\n\n")
        f.write("export const CENAS_NARRACAO = " + json.dumps(cenas, ensure_ascii=False, indent=2) + " as const;\n\n")
        f.write("export type Pagina = { de: number; ate: number; palavras: { t: string; d: boolean }[] };\n\n")
        f.write("export const PAGINAS: Pagina[] = " + json.dumps(saida_paginas, ensure_ascii=False) + ";\n\n")
        marcas = [{"t": limpa(c["text"]), "f": round(c["startMs"] / 1000 * FPS)} for c in legendas]
        f.write("// Quadro (no vídeo inteiro) em que cada palavra começa.\n")
        f.write("export const PALAVRAS: { t: string; f: number }[] = " + json.dumps(marcas, ensure_ascii=False) + ";\n")
    for c in cenas:
        print(f"{c['id']:16} {c['de'] / FPS:6.2f}s  {c['dur'] / FPS:5.2f}s")
    print(len(saida_paginas), "páginas de legenda")


if __name__ == "__main__":
    main()
