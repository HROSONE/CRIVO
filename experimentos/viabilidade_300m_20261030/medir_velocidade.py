"""Velocidade do motor do chat (NumPy e C) para o 46M real e um modelo do tamanho do 300M (pesos aleatórios:
a velocidade só depende das formas). Uso: python medir.py <repo> <pasta_saida> [threads_c]"""
import json, os, sys, time, resource
import numpy as np

REPO, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, REPO)
os.chdir(REPO)
import conversa_v3d as cv
import motor_nativo

NOVOS = 40


def sintetico(destino, V=8192, D=768, L=40, H=16, C=1024):
    """npz no formato do chat (int8 por linha + escala float16), pesos aleatórios pequenos."""
    if os.path.exists(destino):
        return destino
    g = np.random.default_rng(0)
    p = {}
    def mat(nome, linhas, cols):
        p[nome + ".q8"] = g.integers(-127, 128, size=(linhas, cols), dtype=np.int8)
        p[nome + ".escala"] = np.full((linhas, 1), 0.02 / 127, np.float16)
    mat("embedding.weight", V, D); mat("posicao.weight", C, D)
    for c in range(L):
        b = "blocos.%d." % c
        for n in ("norm1", "norm2"):
            p[b + n + ".weight"] = np.ones(D, np.float16); p[b + n + ".bias"] = np.zeros(D, np.float16)
        mat(b + "qkv.weight", 3 * D, D); mat(b + "projecao.weight", D, D)
        mat(b + "mlp.0.weight", 4 * D, D); p[b + "mlp.0.bias"] = np.zeros(4 * D, np.float16)
        mat(b + "mlp.2.weight", D, 4 * D); p[b + "mlp.2.bias"] = np.zeros(D, np.float16)
    p["norm.weight"] = np.ones(D, np.float16); p["norm.bias"] = np.zeros(D, np.float16)
    p["meta"] = np.array(json.dumps({"vocabulario": V, "dimensao": D, "camadas": L, "cabecas": H, "contexto": C}))
    np.savez(destino, **p)
    return destino


def numpy_engine(npz):
    """Um Conversa46mNumpy sem a conferência de SHA, com os pesos do npz (o mesmo caminho NumPy do chat)."""
    pesos = np.load(npz)
    meta = json.loads(str(pesos["meta"]))
    m = cv.Conversa46mNumpy.__new__(cv.Conversa46mNumpy)
    m.np, m.p, m.motor, m._prefixo = np, {}, None, None
    for k in pesos.files:
        if k == "meta" or k.endswith(".escala"):
            continue
        if k.endswith(".q8"):
            m.p[k[:-3]] = pesos[k].astype(np.float32) * pesos[k[:-3] + ".escala"].astype(np.float32)
        else:
            m.p[k] = pesos[k].astype(np.float32)
    m.camadas, m.cabecas, m.contexto = meta["camadas"], meta["cabecas"], meta["contexto"]
    return m


def cronometrar(logits, n_prompt):
    ids = list(np.random.default_rng(1).integers(10, 8000, size=n_prompt))
    cache = {}
    t0 = time.perf_counter(); lg = logits(ids, 0, cache); t1 = time.perf_counter()
    for i in range(NOVOS):
        lg = logits([int(lg.argmax()) % 8000 + 10], n_prompt + i, cache)
    t2 = time.perf_counter()
    return {"prompt_s": round(t1 - t0, 2), "por_token_s": round((t2 - t1) / NOVOS, 3),
            "resposta_40_tokens_s": round(t2 - t0, 1)}


def rss_mb():
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)


qual, motor = sys.argv[3], sys.argv[4]          # 46m|300m, numpy|c
npz = "artefatos/conversa46m_v7c_pt/pesos_numpy.npz" if qual == "46m" else sintetico(os.path.join(OUT, "sintetico_300m.npz"))
res = {"modelo": qual, "motor": motor, "npz_mb": round(os.path.getsize(npz) / 1e6)}
if motor == "numpy":
    m = numpy_engine(npz)
    res["parametros_M"] = round(sum(v.size for v in m.p.values()) / 1e6, 1)
    f = lambda ids, ini, cache: m._passo(ids, ini, cache)[-1] @ m.p["embedding.weight"].T
else:
    os.environ["CRIVO_MOTOR_NATIVO"] = sys.argv[5]
    arq = os.path.join(OUT, f"motor_{qual}.bin")
    motor_nativo.exportar(npz, arq)
    mn = motor_nativo.MotorNativo(sys.argv[5], arq, threads=int(sys.argv[6]))
    f = lambda ids, ini, cache: mn.avancar(ids, ini)
for n in (150, 400):
    res[f"prompt_{n}"] = cronometrar(f, n)
res["memoria_pico_mb"] = rss_mb()
print(json.dumps(res, ensure_ascii=False))
