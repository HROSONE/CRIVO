"""Dados da v7f (06/11/2026): os dados do v7c mais os casos que reprovaram o 300M v7c (formas_v7f.py).

Correções medidas no resumo da rodada 1 do 300M v7c: frases reais 11/15 (todas as falhas no 2º turno),
identidade 63/84 contra 67/84 do chat, perguntas do dia a dia sem fato caindo em cenas de saúde ou clima.

- casos de dois turnos: o histórico é uma saudação ou pergunta da pessoa e uma resposta real do Crivo daquela situação;
- as respostas vêm das listas existentes no treino do v7c (nunca são escritas aqui);
- a divisão treino/dev/blind_v6 é a do v6 (por fala), e nada igual a uma fala de teste congelada entra.

Uso: python gerar_v7f.py   (escreve dados_v7f.json.gz e manifesto_v7f.json)
"""
import gzip
import hashlib
import json
import random
from collections import Counter, defaultdict

import gerar_v6 as G
import formas_v7f as F7

SEED = 20261106
POR_FALA = {"treino": 8, "dev": 2, "blind_v6": 3}


def principal():
    rr = random.Random(SEED)
    base = json.loads(gzip.open(G.AQUI / "dados_v7c.json.gz").read().decode("utf-8"))
    cong, _ = G.congeladas()
    ch = G.ch
    respostas = defaultdict(list)
    for c in base["treino"]:
        respostas[c["situacao"]].append(c["resposta"])
    respostas = {s: sorted(set(v)) for s, v in respostas.items()}
    saudacoes_crivo = respostas["cena:oi_tudo_bem"]
    respostas_quaisquer = sorted({c["resposta"] for c in base["treino"] if c["situacao"].startswith("cena:")
                                  and c["situacao"] not in F7.F})
    novos, rel = {k: [] for k in POR_FALA}, Counter()
    for sit, falas in F7.F.items():
        assert respostas.get(sit), f"sem respostas nas listas para {sit}"
        for fala in falas:
            if ch(fala) in cong:
                rel["igual_a_teste_congelado_fora"] += 1
                continue
            parte = G.parte(fala)
            for _ in range(POR_FALA[parte]):
                hist = []
                if F7.DEPOIS_DE.get(sit) == "saudacao":
                    hist = [rr.choice(F7.SAUDACOES), rr.choice(saudacoes_crivo)]
                elif F7.DEPOIS_DE.get(sit) == "pergunta":
                    hist = [rr.choice(F7.PERGUNTAS_ANTES), rr.choice(respostas_quaisquer)]
                novos[parte].append({"contexto": {}, "exigir": {"marcas": [], "nao_contem": []}, "fala_nucleo": fala,
                                     "historico": hist, "mensagem": fala, "origem": "assistente_v7f",
                                     "resposta": rr.choice(respostas[sit]), "situacao": sit})
            rel[f"falas_{parte}"] += 1
    treino_novo = {ch(c["fala_nucleo"]) for c in novos["treino"]}
    assert not treino_novo & {ch(c["fala_nucleo"]) for c in novos["dev"] + novos["blind_v6"]}
    dados = {k: base[k] + novos[k] for k in base}
    rr.shuffle(dados["treino"])
    bruto = json.dumps(dados, ensure_ascii=False, sort_keys=True).encode("utf-8")
    arq = G.AQUI / "dados_v7f.json.gz"
    with gzip.GzipFile(arq, "wb", mtime=0) as fz:
        fz.write(bruto)
    manifesto = {"protocolo": "v7f_entendimento", "seed": SEED, "base": "dados_v7c.json.gz",
                 "base_gz_sha256": G.sha(G.AQUI / "dados_v7c.json.gz"), "dados_sha256": hashlib.sha256(bruto).hexdigest(),
                 "tamanhos": {k: len(v) for k, v in dados.items()}, "casos_novos": {k: len(v) for k, v in novos.items()},
                 "casos_novos_por_situacao": dict(Counter(c["situacao"] for c in novos["treino"])), "relatorio": dict(rel),
                 "formas_v7f_sha256": G.sha(G.AQUI / "formas_v7f.py"), "gerar_v7f_sha256": G.sha(G.AQUI / "gerar_v7f.py"),
                 "origem": "falas novas escritas pelo assistente de programação (Claude) com autorização do criador "
                           "(06/11/2026), não são humanas; respostas das listas existentes do v7c"}
    (G.AQUI / "manifesto_v7f.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: manifesto[k] for k in ("tamanhos", "casos_novos", "casos_novos_por_situacao", "relatorio")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    principal()
