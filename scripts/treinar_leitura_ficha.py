"""Treina a leitura da ficha com as perguntas do tutor (dados/leitura_ficha_tutor.json).

Modelo logístico em NumPy sobre os traços de leitura_ficha.TRACOS: para cada
par (pergunta, fato da ficha), a probabilidade de o fato responder. O fato de
maior probabilidade é a proposta da leitura; dois limiares dizem o que o
árbitro faz com ela:

  afirmar    prob >= limiar_afirmar, todas as pistas cobertas e fato compatível
             com o tipo de pergunta: responde com o fato;
  aproximar  prob >= limiar_aproximar, no máximo uma pista sem apoio (e outra
             coberta), sem as condições de afirmar: diz que não tem a resposta
             exata e mostra o fato mais próximo da ficha;
  calar      fora disso: a recusa de antes continua.

Validação cruzada agrupada por assunto (5 partes): nenhum assunto aparece no
treino e na validação ao mesmo tempo. Aprovação: na validação, as afirmações
do modelo precisam ter precisão >= 0,9 e acertar mais que a regra sem
aprendizado (todas as pistas cobertas e fato compatível com o tipo).

Com --com-transformer, valida também a leitura com o leitor Transformer
(artefatos/leitor_transformer) como traço a mais e só o aprova se entregar
pelo menos MARGEM_TRANSFORMER fatos certos a mais sem mais erros; senão, fica
a versão sem ele.

Uso: python scripts/treinar_leitura_ficha.py [--saida artefatos/leitura_ficha] [--com-transformer [pasta]]
"""
import argparse
import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

PRECISAO_AFIRMAR = 0.9
MARGEM_TRANSFORMER = 4  # fatos certos a mais, na validação, para aprovar o leitor Transformer
PRECISAO_APROXIMAR = 0.7
SEMENTE = 20261005


def exemplos(compositor, leitura):
    """[{assunto, pergunta, fato, x}] com os traços de cada fato da ficha."""
    dados = json.loads((RAIZ / "dados" / "leitura_ficha_tutor.json").read_text(encoding="utf-8"))["casos"]
    saida, ignorados = [], 0
    for c in dados:
        quadro = compositor.interpretar(c["pergunta"])
        if quadro is None or quadro.recusa or quadro.assunto != c["assunto"]:
            ignorados += 1
            continue
        cands = sorted(leitura.candidatos(quadro), key=lambda s: s[1])
        saida.append({"assunto": c["assunto"], "pergunta": c["pergunta"], "fato": c["fato"],
                      "x": [s[4] for s in cands]})
    return saida, ignorados


def treinar(casos, passos=3000, taxa=0.3, l2=1e-3):
    import numpy as np
    X, y = [], []
    for c in casos:
        for i, x in enumerate(c["x"]):
            X.append(x)
            y.append(1.0 if c["fato"] == i else 0.0)
    X, y = np.array(X), np.array(y)
    peso_pos = (len(y) - y.sum()) / max(1.0, y.sum())
    amostra = np.where(y == 1, peso_pos, 1.0)
    w = np.zeros(X.shape[1])
    for _ in range(passos):
        p = 1 / (1 + np.exp(-(X @ w)))
        w -= taxa * (X.T @ ((p - y) * amostra) / amostra.sum() + l2 * w)
    return w


def propostas(casos, prob):
    """[(prob, fato certo ou None, índice proposto, pode afirmar, pode aproximar)].

    Pode afirmar = todas as pistas cobertas e fato compatível com o tipo de
    pergunta; sem isso, a leitura no máximo aproxima (leitura_ficha.decisao)."""
    from leitura_ficha import TRACOS, pergunta_direta, pode_aproximar
    todas, sem_par = TRACOS.index("todas"), TRACOS.index("tipo_sem_par")
    saida = []
    for c in casos:
        ps = [prob(x) for x in c["x"]]
        melhor = max(range(len(ps)), key=lambda i: (ps[i], -i))
        x = c["x"][melhor]
        saida.append((ps[melhor], c["fato"], melhor, bool(x[todas]) and not x[sem_par],
                      pode_aproximar(dict(zip(TRACOS, x), pergunta_direta=pergunta_direta(c["pergunta"])),
                                     parcial=True)))
    return saida


def politica(linhas, afirmar, aproximar):
    """Separa as propostas em afirmadas, aproximadas e caladas."""
    a = [l[:3] for l in linhas if l[3] and l[0] >= afirmar]
    b = [l[:3] for l in linhas if not (l[3] and l[0] >= afirmar) and l[0] >= aproximar and l[4]]
    c = [l[:3] for l in linhas if not (l[3] and l[0] >= afirmar) and not (l[0] >= aproximar and l[4])]
    return a, b, c


def contar(r):
    """Certos, errados (fato errado) e nulos (pergunta sem resposta)."""
    return {"n": len(r), "certos": sum(1 for p, f, m in r if f == m),
            "errados": sum(1 for p, f, m in r if f is not None and f != m),
            "nulos": sum(1 for p, f, m in r if f is None)}


def precisao(f):
    return f["certos"] / f["n"] if f["n"] else 1.0


def limiares(linhas):
    """Menor limiar de afirmar com precisão >= PRECISAO_AFIRMAR; depois, o
    menor de aproximar cuja faixa mantém PRECISAO_APROXIMAR."""
    grade = [i / 100 for i in range(50, 100)]
    afirmar = next((t for t in grade if contar(politica(linhas, t, t)[0])["n"]
                    and precisao(contar(politica(linhas, t, t)[0])) >= PRECISAO_AFIRMAR), 0.99)
    aproximar = next((t for t in grade if contar(politica(linhas, afirmar, t)[1])["n"]
                      and precisao(contar(politica(linhas, afirmar, t)[1])) >= PRECISAO_APROXIMAR), 0.99)
    return afirmar, aproximar


def regra(x):
    from leitura_ficha import TRACOS
    return 1.0 if x[TRACOS.index("todas")] and not x[TRACOS.index("tipo_sem_par")] else 0.0


def validar(compositor, leitura):
    """Validação cruzada por assunto e modelo final para uma leitura."""
    import numpy as np
    casos, ignorados = exemplos(compositor, leitura)
    assuntos = sorted({c["assunto"] for c in casos})
    random.Random(SEMENTE).shuffle(assuntos)
    fora_da_amostra, validacao_regra = [], []
    for k in range(5):
        parte = set(assuntos[k::5])
        treino = [c for c in casos if c["assunto"] not in parte]
        valid = [c for c in casos if c["assunto"] in parte]
        w = treinar(treino)
        prob = lambda x, w=w: float(1 / (1 + np.exp(-(np.array(x) @ w))))
        fora_da_amostra += propostas(valid, prob)
        validacao_regra += propostas(valid, regra)
    # Os dois limiares saem das probabilidades fora da amostra (cada pergunta
    # avaliada por um modelo que não viu o assunto dela).
    afirmar, aproximar = limiares(fora_da_amostra)
    w = treinar(casos)
    modelo_afirma, modelo_aproxima, calados = (contar(g) for g in politica(fora_da_amostra, afirmar, aproximar))
    regra_afirma = contar(politica(validacao_regra, 1.0, 2.0)[0])
    aprovado = (precisao(modelo_afirma) >= PRECISAO_AFIRMAR
                and modelo_afirma["certos"] > regra_afirma["certos"])
    return {
        "versao": 1,
        "tracos": list(leitura.nomes),
        "pesos": [round(float(v), 5) for v in w],
        "limiar": afirmar,
        "limiar_aproximar": aproximar,
        "dados": {"casos": len(casos), "ignorados_sem_assunto_ou_recusados": ignorados,
                  "assuntos": len(assuntos)},
        "validacao_cruzada_por_assunto": {
            "modelo_afirma": modelo_afirma, "modelo_aproxima": modelo_aproxima,
            "modelo_cala": calados, "regra_afirma": regra_afirma},
        "controle": {"aprovado": aprovado,
                     "criterio": "na validação por assunto, afirmações com precisão >= 0,9 e mais "
                                 "acertos que a regra"},
    }


def _entregues(meta):
    """Fatos certos que chegam à pessoa (afirmados ou aproximados) e erros."""
    v = meta["validacao_cruzada_por_assunto"]
    certos = v["modelo_afirma"]["certos"] + v["modelo_aproxima"]["certos"]
    erros = v["modelo_afirma"]["errados"] + v["modelo_afirma"]["nulos"]
    return certos, erros


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default=str(RAIZ / "artefatos" / "leitura_ficha"))
    parser.add_argument("--com-transformer", nargs="?", const=str(RAIZ / "artefatos" / "leitor_transformer"),
                        help="pasta do leitor Transformer a comparar como traço a mais")
    args = parser.parse_args()
    from crivo import Crivo
    from leitura_ficha import LeituraFicha
    bot = Crivo()
    meta = validar(bot.compositor, LeituraFicha(bot.compositor, caminho_modelo="/nao/existe"))
    if args.com_transformer:
        from leitor_transformer import LeitorTransformer
        lt = LeitorTransformer(args.com_transformer, exigir_aprovacao=False)
        if not lt.disponivel:
            raise SystemExit("Leitor Transformer indisponível: " + lt.motivo)
        com = validar(bot.compositor, LeituraFicha(bot.compositor, caminho_modelo="/nao/existe", transformer=lt))
        (certos_sem, erros_sem), (certos_com, erros_com) = _entregues(meta), _entregues(com)
        # Margem mínima: +2 em ~130 perguntas é ruído (o piloto de 2,6M, que
        # não aprendeu nada no teste congelado, ganhava +2 aqui).
        melhora = (com["controle"]["aprovado"] and certos_com >= certos_sem + MARGEM_TRANSFORMER
                   and erros_com <= erros_sem)
        comparacao = {"sem_transformer": {"certos_entregues": certos_sem, "erros": erros_sem},
                      "com_transformer": {"certos_entregues": certos_com, "erros": erros_com},
                      "transformer_aprovado": melhora}
        print(json.dumps(comparacao, ensure_ascii=False))
        meta_lt_caminho = Path(args.com_transformer) / "meta.json"
        meta_lt = json.loads(meta_lt_caminho.read_text(encoding="utf-8"))
        meta_lt["controle"]["aprovado"] = melhora
        meta_lt["controle"]["validacao_leitura"] = comparacao
        meta_lt_caminho.write_text(json.dumps(meta_lt, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        if melhora:
            meta = dict(com, comparacao_transformer=comparacao)
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: meta[k] for k in ("tracos", "dados", "validacao_cruzada_por_assunto", "controle",
                                            "limiar", "limiar_aproximar")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
