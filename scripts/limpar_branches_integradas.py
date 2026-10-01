"""Limpeza limitada ao inventário aprovado, com prova de merge e lease atômico.

O modo padrão apenas relata. --aplicar usa as credenciais do checkout do CI.
Não lê credenciais locais nem apaga branches que avançaram desde o inventário.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

REPOSITORIO = "HROSONE/CRIVO"


def api(caminho):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "crivo-integracao"}
    token = os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    pedido = urllib.request.Request("https://api.github.com/repos/" + REPOSITORIO +
                                    "/" + caminho, headers=headers)
    with urllib.request.urlopen(pedido, timeout=30) as resposta:
        return json.load(resposta)


def ancestral(sha, main_sha):
    return subprocess.run(["git", "merge-base", "--is-ancestor", sha, main_sha],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def avaliar(registro, main_sha, consultar=api):
    nome, sha = registro.get("branch"), registro.get("sha")
    if (not isinstance(nome, str) or nome == "main" or nome.startswith("archive/") or
            not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha) or
            subprocess.run(["git", "check-ref-format", "refs/heads/" + nome],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode):
        return "preservada: registro inválido ou branch protegida"
    try:
        atual = consultar("git/ref/heads/" + urllib.parse.quote(nome, safe=""))
    except urllib.error.HTTPError as erro:
        if erro.code == 404:
            return "ausente"
        raise
    if atual.get("object", {}).get("sha") != sha:
        return "preservada: SHA mudou"
    if ancestral(sha, main_sha):
        return "integrada: ancestral da main"
    numero = registro.get("pr_integrado")
    if type(numero) is int and numero > 0:
        pr = consultar("pulls/" + str(numero))
        if (pr.get("merged") is True and pr.get("base", {}).get("ref") == "main" and
                pr.get("head", {}).get("sha") == sha and
                pr.get("merge_commit_sha") == registro.get("merge_sha") and
                ancestral(pr["merge_commit_sha"], main_sha)):
            return "integrada: PR mesclada na main"
    return "preservada: integração não comprovada"


def excluir(nome, sha):
    # O servidor recusa se a branch avançar entre a consulta e o push.
    return subprocess.run(["git", "push",
                           "--force-with-lease=refs/heads/" + nome + ":" + sha,
                           "origin", ":refs/heads/" + nome],
                          capture_output=True, text=True).returncode == 0


def principal():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifesto", type=Path, required=True)
    parser.add_argument("--main-sha", required=True)
    parser.add_argument("--aplicar", action="store_true")
    parser.add_argument("--saida", type=Path, default=Path("/tmp/limpeza-crivo.json"))
    args = parser.parse_args()
    manifesto = json.loads(args.manifesto.read_text(encoding="utf-8"))
    if manifesto.get("repositorio") != REPOSITORIO or not re.fullmatch(r"[0-9a-f]{40}", args.main_sha):
        parser.error("Repositório ou commit fora do inventário aprovado")
    registros = list(manifesto["branches"])
    if args.aplicar:
        origem = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
        origem = origem.rstrip("/")
        if origem.endswith(".git"):
            origem = origem[:-4]
        if origem.lower() != "https://github.com/hrosone/crivo":
            parser.error("Origin incompatível com o repositório aprovado")
        # A branch desta integração não pode guardar seu próprio SHA no manifesto.
        # Incluí-la somente se a PR de integração foi mesclada neste exato push.
        for pr in api("pulls?state=closed&per_page=100"):
            if (pr.get("merged_at") and pr.get("merge_commit_sha") == args.main_sha and
                    pr.get("base", {}).get("ref") == "main" and
                    pr.get("head", {}).get("ref", "").startswith("codex/integracao-pendencias-")):
                registros.append({"branch": pr["head"]["ref"], "sha": pr["head"]["sha"]})
    resultados = []
    for registro in registros:
        estado = avaliar(registro, args.main_sha)
        if args.aplicar and estado.startswith("integrada:"):
            estado = "excluída" if excluir(registro["branch"], registro["sha"]) else "preservada: push recusado"
        resultados.append({"branch": registro["branch"], "sha": registro["sha"], "estado": estado})
        print(json.dumps(resultados[-1], ensure_ascii=False), flush=True)
    args.saida.write_text(json.dumps({"main_sha": args.main_sha, "aplicado": args.aplicar,
                                     "branches": resultados}, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    return int(any(r["estado"] == "preservada: push recusado" for r in resultados))


if __name__ == "__main__":
    raise SystemExit(principal())
