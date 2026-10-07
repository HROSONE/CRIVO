"""Prepara o codificador de sentido para o site e recalcula os vetores dos fatos.

Uso: python scripts/instalar_sentido.py [--pasta artefatos/sentido_pt]

1. grava no pesos_numpy.npz a chave "meta" que o executor NumPy
   (pontuador_frases.Pontuador) lê, se ainda não houver;
2. codifica todos os fatos do acervo e grava vetores_fatos.npz (por hash do
   texto). Rode de novo sempre que os catálogos mudarem: o teste
   testes_codificador_sentido.py acusa fato sem vetor.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))


def main():
    import numpy as np
    args = sys.argv[1:]
    pasta = Path(args[args.index("--pasta") + 1]) if "--pasta" in args else RAIZ / "artefatos" / "sentido_pt"
    z = np.load(pasta / "pesos_numpy.npz")
    if "meta" not in z.files:
        cfg = json.loads((pasta / "meta.json").read_text(encoding="utf-8"))["base"]["config"]
        arr = {k: z[k].astype(np.float16) for k in z.files}
        arr["meta"] = np.array(json.dumps({k: cfg[k] for k in ("camadas", "cabecas", "contexto", "dimensao",
                                                               "vocabulario")}))
        np.savez_compressed(pasta / "pesos_numpy.npz", **arr)
    from busca_semantica import fatos_do_acervo
    from codificador_sentido import CodificadorSentido, chave
    from crivo import Crivo
    cod = CodificadorSentido(pasta, exigir_aprovacao=False)
    if not cod.disponivel:
        raise SystemExit("codificador indisponível: %s" % cod.motivo)
    textos = list(dict.fromkeys(t for _, _, t in fatos_do_acervo(Crivo().compositor)))
    vetores = cod.codificar(textos, "fato")
    np.savez_compressed(pasta / "vetores_fatos.npz", chaves=np.array([chave(t) for t in textos]),
                        vetores=vetores.astype(np.float16))
    print("vetores de %d fatos em %s" % (len(textos), pasta / "vetores_fatos.npz"))


if __name__ == "__main__":
    main()
