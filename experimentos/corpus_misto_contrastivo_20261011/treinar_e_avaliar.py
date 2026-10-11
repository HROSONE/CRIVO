"""Treina um único candidato misto-contrastivo e aplica os gates congelados.

O holdout prospectivo só é lido depois que o treinador seleciona a melhor época
usando exclusivamente a validação conhecida do corpus misto.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIR = Path(__file__).resolve().parent
OLD = RAIZ / "experimentos" / "gerador_historico_textual_20261010"
FAT = RAIZ / "experimentos" / "corpus_fatorial_20261011"
sys.path.insert(0, str(RAIZ))

from arquivos_contextuais import ler_json
from dialogo_seq2seq import DialogoSeq2Seq, tokenizar
from treinar_dialogo_seq2seq import avaliar_geracao, avaliar_perda, treinar


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def gravar_json(path: Path, dados) -> None:
    path.write_text(json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def gravar_gz(path: Path, dados) -> None:
    bruto = (json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    path.write_bytes(gzip.compress(bruto, mtime=0))


def texto(ex):
    return {"mensagem": ex["mensagem"], "historico": ex.get("historico", []), "resposta": ex["resposta"]}


def norm(s):
    return re.sub(r"\s+", " ", str(s).casefold().strip())


def score_operacao(ex, gerada):
    g = norm(gerada)
    op = ex["operacao"]
    nome = norm(ex["esperado_nome"])
    objeto = norm(ex["objeto"])
    atividade = norm(ex["atividade"])
    if op == "recordar_pessoa":
        return nome in g
    if op == "recordar_objeto":
        return objeto in g
    if op == "corrigir_pessoa":
        antigo = norm(ex["nome_antes"])
        return nome in g and antigo not in g
    if op == "guardar_hipotese":
        return any(m in g for m in ("possibilidade", "ainda não", "não está confirmado", "não é certeza", "continua incerto"))
    if op == "mensagem_sem_horario":
        proibidos = ("hoje", "amanhã", "ontem", "horário", " horas", "depois de amanhã")
        return nome in g and atividade in g and not any(p in g for p in proibidos)
    if op == "pedir_detalhe":
        return nome in g and "?" in gerada and ("o que" in g or "qual" in g)
    raise ValueError(op)


def avaliar_bloco(dados, exemplos, operacoes=False):
    modelo = DialogoSeq2Seq(dados)
    casos = [texto(e) for e in exemplos]
    perda = avaliar_perda(modelo.pesos, casos, modelo.indices, modelo.buckets, modelo.limite_fonte, 64, lote_tamanho=32)
    livre = avaliar_geracao(dados, casos, limite_resposta=64, maximo=None, semente=179)
    primeiro = 0
    ranks = []
    probs = []
    for e in exemplos:
        alvo = tokenizar(e["resposta"])[0]
        dist = modelo.probabilidades(e["mensagem"], e.get("historico", []))
        ordem = sorted(dist.items(), key=lambda kv:(-kv[1], kv[0]))
        primeiro += ordem[0][0].casefold() == alvo.casefold()
        ranks.append(next((i+1 for i,(t,_) in enumerate(ordem) if t.casefold() == alvo.casefold()), len(ordem)+1))
        probs.append(sum(p for t,p in ordem if t.casefold() == alvo.casefold()))
    out = {
        "perda": perda,
        "geracao": {k:v for k,v in livre.items() if k != "saidas"},
        "primeiro_token": {
            "corretos": primeiro, "total": len(exemplos), "acuracia": primeiro/max(1,len(exemplos)),
            "rank_medio": sum(ranks)/max(1,len(ranks)), "probabilidade_alvo_media": sum(probs)/max(1,len(probs)),
        },
    }
    if operacoes:
        detalhes=[]
        for e,g in zip(exemplos, livre["saidas"]):
            ok = bool(score_operacao(e, g["gerada"]))
            detalhes.append({"id":e["id"], "operacao":e["operacao"], "gerada":g["gerada"], "alvo":e["resposta"], "passou":ok})
        por={}
        for op in sorted(set(e["operacao"] for e in exemplos)):
            ds=[d for d in detalhes if d["operacao"] == op]
            ac=sum(d["passou"] for d in ds)
            por[op]={"acertos":ac, "total":len(ds), "taxa":ac/max(1,len(ds))}
        ac=sum(d["passou"] for d in detalhes)
        out["operacoes"]={"acertos":ac, "total":len(detalhes), "taxa":ac/max(1,len(detalhes)), "por_operacao":por, "detalhes":detalhes}
    return out


def resumo(result):
    c=result["controles"]["controle_1x"]
    f=result["controles"]["fatorial"]
    n=result["candidato"]
    p=result["criterio"]
    linhas=[
        "# Treino misto-contrastivo — resultado", "",
        "Um único candidato; mesma rede de 81.433 parâmetros, vocabulário 720, inicialização e 3.699 exemplos totais.", "",
        "## Preservação", "",
        "| Recorte | Controle 1× | Fatorial puro | Misto |",
        "|---|---:|---:|---:|",
        f"| old334 CE | {c['old334']['perda']['entropia_cruzada']:.3f} | {f['old334']['perda']['entropia_cruzada']:.3f} | {n['old334']['perda']['entropia_cruzada']:.3f} |",
        f"| old334 exatas | {c['old334']['geracao']['iguais_ao_alvo']}/334 | {f['old334']['geracao']['iguais_ao_alvo']}/334 | {n['old334']['geracao']['iguais_ao_alvo']}/334 |",
        f"| known94 CE | {c['known94']['perda']['entropia_cruzada']:.3f} | {f['known94']['perda']['entropia_cruzada']:.3f} | {n['known94']['perda']['entropia_cruzada']:.3f} |",
        f"| known94 exatas | {c['known94']['geracao']['iguais_ao_alvo']}/94 | {f['known94']['geracao']['iguais_ao_alvo']}/94 | {n['known94']['geracao']['iguais_ao_alvo']}/94 |",
        f"| fatorial96 CE | {c['fatorial96']['perda']['entropia_cruzada']:.3f} | {f['fatorial96']['perda']['entropia_cruzada']:.3f} | {n['fatorial96']['perda']['entropia_cruzada']:.3f} |",
        f"| fatorial96 operações | {100*c['fatorial96']['operacoes']['taxa']:.1f}% | {100*f['fatorial96']['operacoes']['taxa']:.1f}% | {100*n['fatorial96']['operacoes']['taxa']:.1f}% |",
        "", "## Prospectivo 120 — não usado na seleção", "",
        "| Medida | Controle 1× | Fatorial puro | Misto |",
        "|---|---:|---:|---:|",
        f"| CE | {c['prospectivo']['perda']['entropia_cruzada']:.3f} | {f['prospectivo']['perda']['entropia_cruzada']:.3f} | {n['prospectivo']['perda']['entropia_cruzada']:.3f} |",
        f"| Exatas | {c['prospectivo']['geracao']['iguais_ao_alvo']}/120 | {f['prospectivo']['geracao']['iguais_ao_alvo']}/120 | {n['prospectivo']['geracao']['iguais_ao_alvo']}/120 |",
        f"| Primeiro token | {100*c['prospectivo']['primeiro_token']['acuracia']:.1f}% | {100*f['prospectivo']['primeiro_token']['acuracia']:.1f}% | {100*n['prospectivo']['primeiro_token']['acuracia']:.1f}% |",
        f"| Operações | {100*c['prospectivo']['operacoes']['taxa']:.1f}% | {100*f['prospectivo']['operacoes']['taxa']:.1f}% | {100*n['prospectivo']['operacoes']['taxa']:.1f}% |",
        "", "## Gate pré-congelado", "",
    ]
    for k in ("old334_exatas", "old334_ce", "known94_exatas", "known94_ce", "fatorial_operacoes", "fatorial_ce", "prospectivo_ce", "prospectivo_primeiro", "prospectivo_operacoes", "prospectivo_total", "prospectivo_por_operacao"):
        linhas.append(f"- {k}: **{'PASSOU' if p[k] else 'FALHOU'}**.")
    linhas += ["", f"**Sucesso conjunto: {'SIM' if p['sucesso_conjunto'] else 'NÃO'}.**", "", "Checkpoint permanece experimental e `ativo_no_chat=false`." ]
    return "\n".join(linhas)+"\n"


def executar():
    p=ler_json(DIR/"protocolo.json")
    m=ler_json(DIR/"manifesto.json")
    corpus=DIR/"corpus_misto.json.gz"
    prospect_path=DIR/"avaliacao_prospectiva.json"
    init=RAIZ/p["origem"]["inicializacao"]
    ctrl_path=RAIZ/p["origem"]["controle_1x"]
    fat_path=RAIZ/p["origem"]["checkpoint_fatorial"]
    old_corpus=RAIZ/p["origem"]["corpus_antigo"]
    fat_final_path=RAIZ/p["origem"]["avaliacao_fatorial_conhecida"]

    if not m.get("aprovado_para_treino"):
        raise ValueError("Corpus não aprovado")
    if sha256(corpus) != m["sha256_corpus"]: raise ValueError("Corpus misto mudou")
    if sha256(prospect_path) != m["sha256_avaliacao_prospectiva"]: raise ValueError("Prospectivo mudou")
    if m["sha256_avaliacao_prospectiva"] != p["avaliacao_prospectiva"]["sha256_esperado"]: raise ValueError("SHA prospectivo não bate protocolo")
    if sha256(init) != p["origem"]["inicializacao_sha256"]: raise ValueError("Inicialização mudou")
    if sha256(old_corpus) != p["origem"]["corpus_antigo_sha256"]: raise ValueError("Corpus antigo mudou")
    if sha256(FAT/"corpus_fatorial.json.gz") != p["origem"]["corpus_fatorial_sha256"]: raise ValueError("Corpus fatorial mudou")
    if sha256(fat_final_path) != p["origem"]["avaliacao_fatorial_conhecida_sha256"]: raise ValueError("Avaliação fatorial mudou")
    fat_protocol=ler_json(FAT/"protocolo.json")
    fat_results=ler_json(FAT/"resultados_treino.json")
    if sha256(ctrl_path) != fat_protocol["controle"]["checkpoint_sha256"]: raise ValueError("Controle 1x mudou")
    if sha256(fat_path) != fat_results["treino"]["checkpoint_sha256"]: raise ValueError("Checkpoint fatorial mudou")

    destino=DIR/"checkpoint_misto.json.gz"
    if destino.exists(): raise ValueError("Checkpoint já existe")
    temp=DIR/".checkpoint_misto.tmp.json"
    inicio=time.monotonic()
    rel=treinar(corpus, temp, checkpoint_inicial=init, **p["hiperparametros"])
    cand=ler_json(temp); temp.unlink()
    if cand["treino"]["parametros"] != p["modelo"]["parametros"]: raise ValueError("Parâmetros mudaram")
    if len(cand["vocabulario"]) != p["modelo"]["vocabulario"]: raise ValueError("Vocabulário mudou")
    cand.update(aprovado=False, ativo_no_chat=False, experimento="corpus-misto-contrastivo-20261011", sha256_corpus=m["sha256_corpus"], sha256_prospectivo=m["sha256_avaliacao_prospectiva"])
    gravar_gz(destino, cand)

    # Só depois da seleção da época abrimos o prospectivo.
    prospect=ler_json(prospect_path)["exemplos"]
    old=ler_json(old_corpus)["exemplos"]
    old334=[e for e in old if e.get("split")=="validacao" and e.get("grupo")!="sessao_completa"]
    known94=[e for e in old if e.get("split")=="validacao" and e.get("grupo")=="sessao_completa"]
    fatorial96=ler_json(fat_final_path)["exemplos"]
    if (len(old334),len(known94),len(fatorial96),len(prospect)) != (334,94,96,120): raise ValueError("Recortes mudaram")

    modelos={"controle_1x":ler_json(ctrl_path), "fatorial":ler_json(fat_path), "misto":cand}
    aval={}
    for nome,dados in modelos.items():
        aval[nome]={
            "old334":avaliar_bloco(dados,old334),
            "known94":avaliar_bloco(dados,known94),
            "fatorial96":avaliar_bloco(dados,fatorial96,operacoes=True),
            "prospectivo":avaliar_bloco(dados,prospect,operacoes=True),
        }

    c=aval["controle_1x"]; f=aval["fatorial"]; n=aval["misto"]
    g=p["portao_candidato"]
    best_ce=min(c["prospectivo"]["perda"]["entropia_cruzada"], f["prospectivo"]["perda"]["entropia_cruzada"])
    best_first=max(c["prospectivo"]["primeiro_token"]["acuracia"], f["prospectivo"]["primeiro_token"]["acuracia"])
    best_ops=max(c["prospectivo"]["operacoes"]["taxa"], f["prospectivo"]["operacoes"]["taxa"])
    cand_ce=n["prospectivo"]["perda"]["entropia_cruzada"]
    cand_first=n["prospectivo"]["primeiro_token"]["acuracia"]
    cand_ops=n["prospectivo"]["operacoes"]["taxa"]
    ganho_ce=(best_ce-cand_ce)/max(1e-12,best_ce)
    ganho_first=cand_first-best_first
    ganho_ops=cand_ops-best_ops
    min_op=min(x["taxa"] for x in n["prospectivo"]["operacoes"]["por_operacao"].values())
    criterio={
        "old334_exatas":n["old334"]["geracao"]["iguais_ao_alvo"] >= g["old334_exatas_min"],
        "old334_ce":n["old334"]["perda"]["entropia_cruzada"] <= g["old334_ce_max"],
        "known94_exatas":n["known94"]["geracao"]["iguais_ao_alvo"] >= g["known94_exatas_min"],
        "known94_ce":n["known94"]["perda"]["entropia_cruzada"] <= g["known94_ce_max"],
        "fatorial_operacoes":n["fatorial96"]["operacoes"]["taxa"] >= g["fatorial_conhecido_operacoes_min"],
        "fatorial_ce":n["fatorial96"]["perda"]["entropia_cruzada"] <= g["fatorial_conhecido_ce_max"],
        "prospectivo_ce":ganho_ce >= g["prospectivo_ce_melhora_relativa_vs_melhor_baseline_min"],
        "prospectivo_primeiro":ganho_first >= g["prospectivo_primeiro_token_ganho_vs_melhor_baseline_min"],
        "prospectivo_operacoes":ganho_ops >= g["prospectivo_operacoes_ganho_vs_melhor_baseline_min"],
        "prospectivo_total":cand_ops >= g["prospectivo_operacoes_total_min"],
        "prospectivo_por_operacao":min_op >= g["prospectivo_operacao_individual_min"],
        "ganho_ce_relativo_vs_melhor_baseline":ganho_ce,
        "ganho_primeiro_pp_vs_melhor_baseline":ganho_first,
        "ganho_operacoes_pp_vs_melhor_baseline":ganho_ops,
        "prospectivo_min_operacao":min_op,
    }
    chaves=["old334_exatas","old334_ce","known94_exatas","known94_ce","fatorial_operacoes","fatorial_ce","prospectivo_ce","prospectivo_primeiro","prospectivo_operacoes","prospectivo_total","prospectivo_por_operacao"]
    criterio["sucesso_conjunto"]=all(criterio[k] for k in chaves)

    result={
        "base_commit":p["base_commit"],
        "integridade":{"um_unico_candidato":True,"parametros":cand["treino"]["parametros"],"vocabulario":len(cand["vocabulario"]),"treino_exemplos":cand["treino"]["exemplos"],"sha_prospectivo":m["sha256_avaliacao_prospectiva"],"prospectivo_aberto_pos_selecao":True,"checkpoint_publico_alterado":False},
        "treino":{"segundos":round(time.monotonic()-inicio,3),"epoca_selecionada":cand["treino"]["epoca_selecionada"],"validacao_selecao":rel["validacao"],"checkpoint_sha256":sha256(destino)},
        "controles":{"controle_1x":aval["controle_1x"],"fatorial":aval["fatorial"]},
        "candidato":aval["misto"],
        "criterio":criterio,
        "aprovado_experimentalmente":bool(criterio["sucesso_conjunto"]),
        "ativo_no_chat":False,
        "limite":"Prospectivo é autoral/sintético e congelado; não prova conversa humana geral.",
    }
    gravar_json(DIR/"resultados_treino.json",result)
    (DIR/"RELATORIO_TREINO.md").write_text(resumo(result),encoding="utf-8")
    print(json.dumps({"criterio":criterio,"prospectivo":{"controle_ce":c["prospectivo"]["perda"]["entropia_cruzada"],"fatorial_ce":f["prospectivo"]["perda"]["entropia_cruzada"],"misto_ce":cand_ce,"controle_ops":c["prospectivo"]["operacoes"]["taxa"],"fatorial_ops":f["prospectivo"]["operacoes"]["taxa"],"misto_ops":cand_ops},"known94":{"controle_ce":c["known94"]["perda"]["entropia_cruzada"],"misto_ce":n["known94"]["perda"]["entropia_cruzada"],"controle_exatas":c["known94"]["geracao"]["iguais_ao_alvo"],"misto_exatas":n["known94"]["geracao"]["iguais_ao_alvo"]}},ensure_ascii=False,indent=2),flush=True)


if __name__ == "__main__":
    executar()
