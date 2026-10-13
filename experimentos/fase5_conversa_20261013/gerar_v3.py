"""Gera e congela os dados da fase 5 v3, antes de qualquer treino.

Uso: python gerar_v3.py [--resumo]
Saída nesta pasta: dados_fase5_v3.json.gz e manifesto_v3.json.

O que muda em relação à v2 (gerar_v2.py, que fica intacto):
- entram as falas da parte 2, escritas pelo GPT (formas_gpt.py), nas 68 situações que ficaram em 0%;
- entram contraexemplos para as confusões medidas na v2 (formas_v3.py), incluindo "falta de ar"
  como xingamento × urgência;
- o dev passa a ter falas que o treino nunca viu (10% das do GPT), para escolher o ponto do treino
  pelo SENTIDO em frase nova, e não pelo que ele decorou;
- blind_v3: o último turno usa falas do GPT ou contraexemplos v3 reservados. É o teste limpo da v3.

Os blinds da v1 e da v2 continuam congelados nos arquivos deles e viram testes de não regressão.
Nenhuma fala de nenhum blind (v1, v2 ou v3) aparece no treino; o script confere.
"""
import argparse
import gzip
import hashlib
import json
import random
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import gerar_fase5 as g1  # noqa: E402
import gerar_v2 as g2  # noqa: E402  (traz cenas_grok, formas_v2, formas_grok e ConversaV2)
import formas_grok  # noqa: E402
import formas_gpt  # noqa: E402
import formas_v3  # noqa: E402

SEED = 20261015
CONVERSAS = {"treino": 60000, "dev": 1500, "blind_v3": 3000}
PARTE_DEV = 10  # % das falas do GPT que só aparecem no dev
CONTRA_CHAVES = {formas_grok.chave(f) for f in formas_v3.CONTRA_FALAS} | {formas_grok.chave(f) for f in formas_grok.CONTRA_FALAS}


def _dev(n):
    return int(hashlib.sha256(("dev3:" + n).encode()).hexdigest()[:8], 16) % 100 < PARTE_DEV


def marcar_contraexemplos(casos):
    for c in casos:
        if formas_grok.chave(c["mensagem"]) in CONTRA_CHAVES:
            c["contraexemplo"] = True
    return casos


def principal():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumo", action="store_true")
    a = ap.parse_args()
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(str(g1.TOKENIZER))
    rr = random.Random(SEED)
    from crivo import Crivo
    from curriculo_mundo import texto_fato
    itens = Crivo().compositor.itens
    fatos = {"treino": [], "dev": [], "blind": []}
    for chave, item in sorted(itens.items()):
        fs = [texto_fato(f) for f in item["fatos"] if f.get("natureza") != "religioso"]
        fs = [f for f in fs if 12 <= len(f) <= 260]
        if fs and 2 <= len(item["nome"]) <= 40:
            fatos[g1.parte("assunto:" + chave)].append((item["nome"], fs[:4]))
    nomes = g1.gerar_nomes(tok, rr)
    S = g1.cenas.S
    grok, _ = formas_grok.carregar()
    gpt, rel_gpt = formas_gpt.carregar()
    v2_nomes = sorted(n for n in g2.formas_v2.FORMAS if n in S)
    faltam = sorted((set(gpt) | set(formas_v3.FORMAS)) - set(S))
    if faltam:
        raise SystemExit("situações que não existem: %s" % faltam)

    # Tudo que é de algum blind fica fora do treino (comparação sem acento e sem pontuação).
    ch = formas_grok.chave
    reservadas = {ch(f) for n in v2_nomes for f in g2.formas_v2.FORMAS[n]["blind"]}
    reservadas |= {ch(f) for c in S.values() if len(c["u"]) >= 4 for f in c["u"][max(1, len(c["u"]) - 2):]}
    reservadas |= {ch(f) for d in grok.values() for f in d["blind"]}
    reservadas |= {ch(f) for d in gpt.values() for f in d["blind"]}
    reservadas |= {ch(f) for d in formas_v3.FORMAS.values() for f in d["blind"]}
    v2 = json.loads(gzip.open(AQUI / "dados_fase5_v2.json.gz").read().decode("utf-8"))
    v1 = json.loads(gzip.open(AQUI / "dados_fase5.json.gz").read().decode("utf-8"))
    # Só as cenas: perguntas de nome e de fato repetem moldes de propósito ("qual o nome do meu
    # cachorro?"), e o que o blind mede ali são nomes e assuntos novos, que já são separados por hash.
    mensagens_blind_antigas = {c["mensagem"].casefold() for c in v2["blind_parafrase"] + v2["blind_grok"] + v1["blind"]
                               if c["situacao"].startswith("cena:")}

    def limpar(lista):
        return [f for f in lista if ch(f) not in reservadas]

    dev_formas, tiradas = {}, 0
    formas_treino = {}
    for nome, c in S.items():
        us = c["u"]
        corte = max(1, len(us) - 2) if len(us) >= 4 else len(us)
        gpt_t = gpt.get(nome, {}).get("treino", [])
        dev_formas[nome] = [f for f in gpt_t if _dev(formas_grok.nucleo(f))]
        gpt_t = [f for f in gpt_t if not _dev(formas_grok.nucleo(f))]
        extra = limpar(g2.formas_v2.FORMAS.get(nome, {}).get("treino", []) + grok.get(nome, {}).get("treino", []) +
                       gpt_t + formas_v3.FORMAS.get(nome, {}).get("treino", []))
        tiradas += len(g2.formas_v2.FORMAS.get(nome, {}).get("treino", []) + grok.get(nome, {}).get("treino", []) +
                       gpt_t + formas_v3.FORMAS.get(nome, {}).get("treino", [])) - len(extra)
        formas_treino[nome] = us[:corte] + extra
    chaves_treino = {ch(f) for fs in formas_treino.values() for f in fs}

    def pool(fonte):
        formas, alvos = dict(formas_treino), []
        for nome in sorted(fonte):
            novas = [f for f in fonte[nome] if ch(f) not in chaves_treino]
            if novas:
                formas[nome] = novas
                alvos += [nome] * min(len(novas), 12)
        return formas, alvos

    formas_dev, alvos_dev = pool({n: v for n, v in dev_formas.items() if v})
    blind_v3 = {}
    for nome in set(gpt) | set(formas_v3.FORMAS):
        blind_v3[nome] = gpt.get(nome, {}).get("blind", []) + formas_v3.FORMAS.get(nome, {}).get("blind", [])
    formas_bv3, alvos_bv3 = pool(blind_v3)
    sorteio = sorted(set(v2_nomes) | set(grok) | set(gpt) | set(formas_v3.FORMAS))

    dados, recusados = {}, {}
    for split, n in CONVERSAS.items():
        casos = []
        for i in range(n):
            if split == "treino":
                conv = g2.montar(rr, fatos["treino"], nomes["treino"], formas_treino, sorteio)
            elif split == "dev" and i % 2 == 0:
                conv = g2.montar(rr, fatos["dev"], nomes["dev"], formas_treino, sorteio)  # nomes, fatos, segurança
            else:
                formas, alvos = (formas_dev, alvos_dev) if split == "dev" else (formas_bv3, alvos_bv3)
                base = "dev" if split == "dev" else "blind"
                conv = g2.montar(rr, fatos[base], nomes[base], formas, alvos, so_ultimo_v2=True)
                conv = conv[-1:] if conv and conv[-1]["situacao"][5:] in alvos else []
                for caso in conv:
                    caso["frase_nova"] = True
            for caso in conv:
                ok, motivo = g1.conferir_alvo(caso)
                if not ok:
                    recusados[caso["situacao"]] = recusados.get(caso["situacao"], 0) + 1
                    continue
                casos.append(caso)
        dados[split] = marcar_contraexemplos(casos)

    vistas = {c["mensagem"].casefold() for c in dados["treino"]}
    vazadas = {s: sum(c["mensagem"].casefold() in vistas for c in dados[s] if c.get("frase_nova")) for s in ("dev", "blind_v3")}
    vazadas_antigas = sum(c["situacao"].startswith("cena:") and c["mensagem"].casefold() in mensagens_blind_antigas
                          for c in dados["treino"])
    resumo = {
        "casos": {k: len(v) for k, v in dados.items()},
        "falas_distintas_treino": len({c["mensagem"] for c in dados["treino"]}),
        "gpt": {"falas_brutas": rel_gpt["bruto"], "treino": sum(len(d["treino"]) for d in gpt.values()),
                "blind": sum(len(d["blind"]) for d in gpt.values()), "fase6_guardadas": len(rel_gpt["fase6"]),
                "dev": sum(len(v) for v in dev_formas.values())},
        "contraexemplos_v3": {"grupos": len(formas_v3.CONTRA_V3),
                              "treino": sum(len(t) for _, t, _ in formas_v3.CONTRA_V3),
                              "blind": sum(len(b) for _, _, b in formas_v3.CONTRA_V3)},
        "formas_tiradas_do_treino_por_serem_de_blind": tiradas,
        "situacoes_no_dev_frase_nova": len(set(alvos_dev)), "situacoes_no_blind_v3": len(set(alvos_bv3)),
        "blind_v3_contraexemplos": sum(bool(c.get("contraexemplo")) for c in dados["blind_v3"]),
        "blind_v3_por_situacao": {s: sum(c["situacao"] == "cena:" + s for c in dados["blind_v3"]) for s in sorted(set(alvos_bv3))},
        "vazadas_frase_igual_ao_treino": vazadas,
        "treino_com_frase_de_blind_antigo": vazadas_antigas,
        "alvos_recusados": recusados,
    }
    print(json.dumps(resumo, ensure_ascii=False, indent=1))
    if a.resumo:
        return
    for s in ("dev", "blind_v3"):
        dados[s] = [c for c in dados[s] if not (c.get("frase_nova") and c["mensagem"].casefold() in vistas)]
    dados["treino"] = [c for c in dados["treino"] if not (c["situacao"].startswith("cena:") and
                                                          c["mensagem"].casefold() in mensagens_blind_antigas)]
    bruto = json.dumps(dados, ensure_ascii=False, sort_keys=True).encode("utf-8")
    with gzip.GzipFile(AQUI / "dados_fase5_v3.json.gz", "wb", mtime=0) as f:
        f.write(bruto)
    sha = lambda p: hashlib.sha256((AQUI / p).read_bytes()).hexdigest()
    manifesto = {"seed": SEED, "dados_sha256": hashlib.sha256(bruto).hexdigest(),
                 "arquivo_gz_sha256": sha("dados_fase5_v3.json.gz"), "formato_fase5_sha256": sha("formato_fase5.py"),
                 "v1_arquivo_gz_sha256": sha("dados_fase5.json.gz"), "v2_arquivo_gz_sha256": sha("dados_fase5_v2.json.gz"),
                 "formas_gpt_sha256": sha("formas_gpt.py"), "formas_v3_sha256": sha("formas_v3.py"),
                 "sentido_sha256": sha("sentido.py"),
                 "gpt_bruto_sha256": {p.name: sha("grok/" + p.name) for p in formas_gpt.PARTES}, **resumo}
    manifesto["casos"] = {k: len(v) for k, v in dados.items()}
    (AQUI / "manifesto_v3.json").write_text(json.dumps(manifesto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    principal()
