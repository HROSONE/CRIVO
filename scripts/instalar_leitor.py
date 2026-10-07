"""Instala o leitor Transformer treinado no Colab e decide se ele fica.

Uso: python scripts/instalar_leitor.py resultado_leitor.zip [--manter-mesmo-se-piorar]

O zip vem de notebooks/treinar_transformer_leitor_colab.ipynb e traz:
  leitor_transformer/   meta.json, pesos_numpy.npz, tokenizer.json
  leitura_ficha/        meta.json da leitura da ficha (com o traço
                        "transformer" se a prova da validação aprovou)
  relatorio_base.json   relatório do pré-treino

Passos:
  1. mede o CRIVO como está (sem o leitor);
  2. instala: o leitor em artefatos/leitor_transformer/ e, se aprovado na
     validação, o modelo da leitura com o leitor em
     artefatos/leitura_ficha/meta_transformer.json (usado só onde o leitor
     roda; o meta.json de sempre continua para quem não tem NumPy);
  3. mede de novo, com o leitor;
  4. fica só se nada piorar: teste congelado de leitura v1 (catraca de
     testes_leitura_ficha) e v2, perguntas sem o nome do assunto e bateria
     (acertos não caem; erros, invenções e nulos afirmados não sobem) e se
     algo melhorar. Senão, desfaz a instalação.
Só agregados dos testes congelados são lidos.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LEITOR = RAIZ / "artefatos" / "leitor_transformer"
META_TRANSFORMER = RAIZ / "artefatos" / "leitura_ficha" / "meta_transformer.json"


def _medir():
    """Agregados de todos os conjuntos, cada um num processo novo (sem cache)."""
    codigo = r"""
import json, sys
sys.path.insert(0, 'scripts')
from avaliar_leitura_ficha import avaliar as leitura
from avaliar_busca_sem_nome import avaliar as sem_nome
from avaliar_bateria import avaliar as bateria
r = {'v1': leitura('teste')[0], 'v2': leitura('teste_v2')[0], 'sem_nome': sem_nome('teste'),
     'bateria_dev': bateria('dev')[0], 'bateria_retido': bateria('retido')[0]}
print('RESULTADO ' + json.dumps(r, ensure_ascii=False))
"""
    saida = subprocess.run([sys.executable, "-c", codigo], cwd=RAIZ, capture_output=True, text=True, check=True)
    linha = next(l for l in saida.stdout.splitlines() if l.startswith("RESULTADO "))
    return json.loads(linha[len("RESULTADO "):])


def _resumo(m):
    def leit(r):
        resp, nulo = r["respondiveis"], r["sem_resposta"]
        return {"certos": resp.get("afirmou_certo", 0) + resp.get("aproximou_certo", 0),
                "errados": resp.get("afirmou_errado", 0), "nulos_afirmados": nulo.get("afirmou", 0)}
    return {"v1": leit(m["v1"]), "v2": leit(m["v2"]),
            "sem_nome": {k: m["sem_nome"][k] for k in ("certo", "errado", "inventou")},
            "bateria": {"dev": m["bateria_dev"]["acertos_fato"], "retido": m["bateria_retido"]["acertos_fato"],
                        "inventou": m["bateria_dev"]["inventou"] + m["bateria_retido"]["inventou"]}}


def _comparar(antes, depois):
    """(piorou, melhorou) com a lista do que mudou."""
    piorou, melhorou = [], []
    for conj in ("v1", "v2"):
        for chave, sinal in (("certos", 1), ("errados", -1), ("nulos_afirmados", -1)):
            d = (depois[conj][chave] - antes[conj][chave]) * sinal
            (piorou if d < 0 else melhorou if d > 0 else []).append("%s %s %+d" % (conj, chave, d * sinal))
    for chave, sinal in (("certo", 1), ("errado", -1), ("inventou", -1)):
        d = (depois["sem_nome"][chave] - antes["sem_nome"][chave]) * sinal
        (piorou if d < 0 else melhorou if d > 0 else []).append("sem_nome %s %+d" % (chave, d * sinal))
    for chave, sinal in (("dev", 1), ("retido", 1), ("inventou", -1)):
        d = (depois["bateria"][chave] - antes["bateria"][chave]) * sinal
        (piorou if d < 0 else melhorou if d > 0 else []).append("bateria %s %+d" % (chave, d * sinal))
    return piorou, melhorou


def instalar(zip_caminho):
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(zip_caminho) as z:
            z.extractall(tmp)
        tmp = Path(tmp)
        origem = tmp / "leitor_transformer"
        if not (origem / "pesos_numpy.npz").exists():
            raise SystemExit("O zip não traz leitor_transformer/pesos_numpy.npz.")
        meta_leitor = json.loads((origem / "meta.json").read_text(encoding="utf-8"))
        leitura = tmp / "leitura_ficha" / "meta.json"
        meta_leitura = json.loads(leitura.read_text(encoding="utf-8")) if leitura.exists() else {}
        com_transformer = "transformer" in meta_leitura.get("tracos", ())
        if LEITOR.exists():
            shutil.rmtree(LEITOR)
        shutil.copytree(origem, LEITOR)
        if com_transformer and meta_leitor.get("controle", {}).get("aprovado"):
            META_TRANSFORMER.write_text(json.dumps(meta_leitura, ensure_ascii=False, indent=1) + "\n",
                                        encoding="utf-8")
        relatorio = tmp / "relatorio_base.json"
        if relatorio.exists():
            shutil.copy(relatorio, LEITOR / "relatorio_base.json")
    return meta_leitor, com_transformer


def desinstalar():
    if META_TRANSFORMER.exists():
        META_TRANSFORMER.unlink()
    if LEITOR.exists():
        shutil.rmtree(LEITOR)
    subprocess.run(["git", "checkout", "--", "artefatos/leitor_transformer"], cwd=RAIZ,
                   capture_output=True)  # volta ao que estava versionado, se havia


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    manter = "--manter-mesmo-se-piorar" in sys.argv
    print("Medindo sem o leitor...", flush=True)
    antes = _resumo(_medir())
    print(json.dumps(antes, ensure_ascii=False), flush=True)
    meta_leitor, com_transformer = instalar(sys.argv[1])
    controle = meta_leitor.get("controle", {})
    print("Leitor:", "aprovado" if controle.get("aprovado") else "não aprovado", "na validação |",
          json.dumps(controle.get("validacao_leitura", {}), ensure_ascii=False), flush=True)
    if not (controle.get("aprovado") and com_transformer):
        desinstalar()
        raise SystemExit("O leitor não passou na prova da validação (margem de 4 fatos); nada instalado.")
    print("Medindo com o leitor...", flush=True)
    depois = _resumo(_medir())
    print(json.dumps(depois, ensure_ascii=False), flush=True)
    piorou, melhorou = _comparar(antes, depois)
    print("Melhorou:", melhorou or "nada", "| Piorou:", piorou or "nada", flush=True)
    if (piorou or not melhorou) and not manter:
        desinstalar()
        raise SystemExit("Desfeito: o leitor não melhorou sem piorar nada.")
    print("Leitor instalado. Rode a suíte e abra o PR.", flush=True)


if __name__ == "__main__":
    main()
