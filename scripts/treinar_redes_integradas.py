"""Retreina redes próprias em candidatos separados, sem promover pesos.

Exemplo: python scripts/treinar_redes_integradas.py --saida /tmp/crivo-treinos
Requer NumPy; não baixa dados nem usa os enunciados das provas finais.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import unicodedata

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))


def verificar_curriculo_factual():
    from curriculo_mundo import carregar_base
    base = carregar_base(RAIZ / "conhecimento.json")
    def normalizar(texto):
        texto = unicodedata.normalize("NFD", texto.casefold())
        return " ".join("".join(c for c in texto if unicodedata.category(c) != "Mn")
                        .strip(" .!?").split())
    perguntas = {normalizar(q) for item in base for q in item["perguntas"]}
    prova = json.loads((RAIZ / "avaliacoes/astronomia_independente_v1.json").read_text(encoding="utf-8"))
    colisoes = [c["id"] for c in prova["casos"] if normalizar(c["pergunta"]) in perguntas]
    if colisoes:
        raise ValueError("Prova retida presente no treino: " + ", ".join(colisoes))
    return {"classes": len(base), "perguntas": sum(len(i["perguntas"]) for i in base),
            "prova_retida_v1": "sem sobreposição literal normalizada"}


def configuracoes():
    return {
        "crivo48": ("rede_neural.py", "rede_crivo.json", None,
                    ["--epocas", "60", "--ocultos", "48", "--dimensao", "512",
                     "--modo", "portugues", "--semente", "42", "--numpy"]),
        "astronomia96": ("rede_neural.py", "rede_astronomia_experimental.json", None,
                         ["--epocas", "100", "--ocultos", "96", "--dimensao", "512",
                          "--modo", "portugues", "--semente", "42", "--numpy"]),
        "dialogo": ("treinar_dialogo.py", "rede_dialogo.json", "avaliacao_dialogo_neural.json",
                    ["--epocas", "90", "--semente", "73", "--numpy"]),
        "linguagem": ("treinar_linguagem.py", "rede_linguagem.json", "avaliacao_linguagem_neural.json",
                      ["--epocas", "70", "--semente", "42", "--numpy"]),
        "intencao_gerativa": ("treinar_intencao_gerativa.py", "rede_intencao_gerativa.json",
                             "avaliacao_intencao_gerativa.json",
                             ["--epocas", "110", "--semente", "107", "--numpy"]),
        "geracao": ("treinar_geracao.py", "rede_geracao.json", "avaliacao_geracao_neural.json",
                    ["--epocas", "40", "--semente", "91"]),
        "compreensao": ("treinar_compreensao.py", "rede_compreensao.json", "avaliacao_compreensao.json",
                        ["--epocas", "15", "--lote", "48", "--ocultos", "40",
                         "--embeddings", "24", "--baldes", "2048", "--semente", "2718",
                         "--dropout", "0.3", "--dropout-trechos", "0.5",
                         "--suavizacao-atos", "0.1", "--paciencia", "2", "--avaliar-cada", "5"]),
        "seq2seq": ("treinar_dialogo_seq2seq.py", "rede_dialogo_seq2seq.json", "avaliacao_seq2seq.json",
                    ["--corpus", "curriculo_compreensao.json", "--dialogos-humanos",
                     "dados/dialogos_humanos.json", "--epocas", "12", "--limite-resposta",
                     "96", "--semente", "173", "--dropout", "0.2", "--dropout-tokens",
                     "0.1", "--amostragem", "0.1", "--aquecimento", "3"]),
    }


def sha256(caminho):
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def rodar(nome, configuracao, pasta):
    script, arquivo, relatorio, argumentos = configuracao
    destino = pasta / arquivo
    comando = [sys.executable, "-u", script, *argumentos, "--saida", str(destino)]
    if relatorio:
        comando += ["--relatorio", str(pasta / relatorio)]
    inicio = time.monotonic()
    print("INICIO " + nome, flush=True)
    ambiente = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    with (pasta / (nome + ".log")).open("w", encoding="utf-8") as log:
        resultado = subprocess.run(comando, cwd=RAIZ, env=ambiente,
                                   stdout=log, stderr=subprocess.STDOUT)
    registro = {"rede": nome, "comando": comando[2:],
                "segundos": round(time.monotonic() - inicio, 3),
                "codigo_saida": resultado.returncode,
                "arquivo": arquivo, "promovido_automaticamente": False}
    if resultado.returncode == 0 and destino.is_file():
        modelo = json.loads(destino.read_text(encoding="utf-8"))
        registro.update(sha256=sha256(destino), bytes=destino.stat().st_size,
                        treino=modelo.get("treino"),
                        assinatura_base=modelo.get("assinatura_base"),
                        assinatura_treino=modelo.get("assinatura_treino"),
                        classes=len(modelo.get("rotulos", [])))
    else:
        registro["codigo_saida"] = resultado.returncode or 1
    print("FIM " + json.dumps({k: registro[k] for k in
          ("rede", "codigo_saida", "segundos")}), flush=True)
    return registro


def principal():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", required=True, type=Path)
    parser.add_argument("--redes", nargs="+", choices=sorted(configuracoes()),
                        default=list(configuracoes()))
    parser.add_argument("--jobs", type=int, choices=(1, 2, 3), default=2)
    args = parser.parse_args()
    pasta = args.saida.resolve()
    if pasta == RAIZ:
        parser.error("Use uma pasta de candidatos: o treino não sobrescreve produção.")
    pasta.mkdir(parents=True, exist_ok=True)
    verificacao = verificar_curriculo_factual()
    entradas = [*RAIZ.glob("curriculo*.json*"), *RAIZ.glob("conhecimento*.json"),
                *RAIZ.glob("*.py"), RAIZ / "dados/dialogos_humanos.json"]
    hashes = {str(p.relative_to(RAIZ)): sha256(p) for p in sorted(entradas) if p.is_file()}
    registros = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futuros = [pool.submit(rodar, n, configuracoes()[n], pasta)
                   for n in dict.fromkeys(args.redes)]
        for futuro in as_completed(futuros):
            registros.append(futuro.result())
            resumo = {"python": platform.python_version(), "entradas_sha256": hashes,
                      "verificacao_curriculo_factual": verificacao,
                      "origem": "Inicialização aleatória própria, sem pesos externos",
                      "avaliacao_final_usada_no_gradiente": False,
                      "promocao_automatica": False,
                      "treinos": sorted(registros, key=lambda r: r["rede"])}
            temporario = pasta / "treinos.json.tmp"
            temporario.write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + "\n",
                                  encoding="utf-8")
            temporario.replace(pasta / "treinos.json")
    return int(any(r["codigo_saida"] for r in registros))


if __name__ == "__main__":
    sys.exit(principal())
