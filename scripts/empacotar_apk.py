"""Empacota o CRIVO para o app Android (android/): o mesmo conjunto de arquivos do site.

O app leva Python e NumPy (Chaquopy) e roda o mesmo servidor de web_local.py dentro do aparelho,
em 127.0.0.1. A página é a mesma do site (public/). Nada é baixado nem chamado de fora: os pesos
próprios do CRIVO vão dentro do APK.

Os arquivos são os mesmos que a Vercel leva (vercel.json → includeFiles, mais api/ e public/).
Assim, o que funciona no site funciona no app.

Uso:
  python scripts/empacotar_apk.py            # grava android/app/src/main/assets/crivo.zip e crivo_versao.txt
  python scripts/empacotar_apk.py --testar   # extrai o zip numa pasta vazia, sobe o servidor e conversa
"""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ASSETS = RAIZ / "android" / "app" / "src" / "main" / "assets"
ZIP = ASSETS / "crivo.zip"
VERSAO = ASSETS / "crivo_versao.txt"
PYTHON_APP = RAIZ / "android" / "app" / "src" / "main" / "python"


def arquivos():
    padrao = json.loads((RAIZ / "vercel.json").read_text(encoding="utf-8"))["functions"]["api/chat.py"]["includeFiles"]
    globs = padrao.strip("{}").split(",") + ["api/*.py", "public/**/*"]
    achados = set()
    for g in globs:
        achados |= {p for p in RAIZ.glob(g) if p.is_file() and "__pycache__" not in p.parts}
    return sorted(achados)


def empacotar():
    ASSETS.mkdir(parents=True, exist_ok=True)
    lista = arquivos()
    h = hashlib.sha256()
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in lista:
            rel = p.relative_to(RAIZ).as_posix()
            dados = p.read_bytes()
            h.update(rel.encode() + b"\0" + hashlib.sha256(dados).digest())
            info = zipfile.ZipInfo(rel, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED if p.suffix in (".npz", ".npy", ".gz") else zipfile.ZIP_DEFLATED
            z.writestr(info, dados)
    versao = h.hexdigest()[:16]
    try:
        commit = subprocess.check_output(["git", "-C", str(RAIZ), "rev-parse", "--short", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "sem-git"
    VERSAO.write_text(versao + "\n", encoding="utf-8")
    total = sum(p.stat().st_size for p in lista)
    print(f"{len(lista)} arquivos, {total / 1e6:.1f} MB → {ZIP} ({ZIP.stat().st_size / 1e6:.1f} MB) | versão {versao} | commit {commit}")
    return versao


def testar():
    """Igual ao app: extrai numa pasta vazia, sobe o servidor do crivo_app.py e conversa."""
    import urllib.request
    with tempfile.TemporaryDirectory() as pasta:
        with zipfile.ZipFile(ZIP) as z:
            z.extractall(pasta)
        codigo = (
            "import sys, json, urllib.request\n"
            f"sys.path.insert(0, {str(PYTHON_APP)!r})\n"
            "import crivo_app\n"
            "porta = crivo_app.iniciar(sys.argv[1])\n"
            "base = 'http://127.0.0.1:%d' % porta\n"
            "pagina = urllib.request.urlopen(base + '/').read().decode()\n"
            "assert 'app.js' in pagina, 'página não veio'\n"
            "for f in ('/app.js', '/styles.css', '/favicon.svg'):\n"
            "    assert urllib.request.urlopen(base + f).status == 200, f\n"
            "falas = ['oi', 'kkkkk', 'quanto é 2+3?', 'tô com falta de ar']\n"
            "hist = []\n"
            "for fala in falas:\n"
            "    corpo = json.dumps({'message': fala, 'history': hist}).encode()\n"
            "    req = urllib.request.Request(base + '/api/chat', corpo, {'Content-Type': 'application/json'})\n"
            "    r = json.loads(urllib.request.urlopen(req, timeout=120).read())\n"
            "    print(repr(fala), '→', r['response'][:90], '| voz:', (r.get('conversation_voice') or {}).get('used'))\n"
            "    hist.append(fala)\n"
            "    assert r['response']\n"
            "print('APP OK')\n"
        )
        # -I: a pasta extraída não pode carregar nada do repositório por engano.
        r = subprocess.run([sys.executable, "-I", "-c", codigo, pasta], cwd=pasta, capture_output=True, text=True, timeout=600)
        print(r.stdout[-3000:])
        if r.returncode != 0 or "APP OK" not in r.stdout:
            print(r.stderr[-3000:])
            sys.exit("o pacote do app não respondeu")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--testar", action="store_true")
    a = ap.parse_args()
    empacotar()
    if a.testar:
        testar()


if __name__ == "__main__":
    main()
