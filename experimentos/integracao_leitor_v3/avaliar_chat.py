"""Compara o chat completo, sem geração; grava somente agregados.

Os artefatos experimentais são injetados em memória. Este programa não altera
aprovação, pesos instalados, limiares nem rótulos dos conjuntos.
"""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

PASTA = Path(__file__).resolve().parent
RAIZ = PASTA.parents[1]
sys.path[:0] = [str(RAIZ), str(RAIZ / "scripts"), str(PASTA)]

from avaliar_leitura_ficha import CONJUNTOS, classificar
from crivo import Crivo
from estado_interno import REVISAVEIS, recusou
from leitura_ficha import LeituraFicha
from resgate_leitor import ResgateLeitor


def transformer_torch(resgate, pasta):
    """Backend opcional rápido; compara com NumPy antes do controle."""
    import numpy as np
    import torch
    from apoio_treino import carregar
    from scripts.treinar_leitor_transformer import lote_tensores

    torch.set_num_threads(2)
    model, bpe, _ = carregar(RAIZ / "experimentos/pesos_base/leitor_transformer", "cpu")
    with np.load(pasta / "cabeca_revisada.npz", allow_pickle=False) as cabeca, torch.no_grad():
        model.cabeca.weight.copy_(torch.from_numpy(cabeca["cabeca.weight"].copy()))
        model.cabeca.bias.copy_(torch.from_numpy(cabeca["cabeca.bias"].copy()))
    model.eval()

    class TransformerLaboratorio:
        def probabilidades(self, pergunta, fatos):
            ids, mascara = lote_tensores([(pergunta, f) for f in fatos], bpe, 256, "cpu")
            with torch.no_grad():
                return torch.sigmoid(model(ids, mascara)).tolist()

    rapido = TransformerLaboratorio()
    compositor = Crivo(usar_geracao=False).compositor
    for pergunta in ("Que aparelhos usam indução eletromagnética?",
                     "Quem escreveu Memórias Póstumas de Brás Cubas?"):
        quadro = compositor.interpretar(pergunta)
        fatos = [f["texto"] for f in compositor.itens[quadro.assunto]["fatos"]]
        a = np.array(resgate.transformer.probabilidades(pergunta, fatos))
        b = np.array(rapido.probabilidades(pergunta, fatos))
        if float(np.max(np.abs(a - b))) > 1e-4:
            raise ValueError("Inferências NumPy/PyTorch divergentes")
    return rapido


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("conjunto", choices=("teste", "teste_v2", "prospectivo", "prospectivo_campo"))
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument("--candidato", choices=("classificador", "campo"), default="campo")
    parser.add_argument("--backend", choices=("numpy", "torch"), default="numpy")
    args = parser.parse_args()
    conjuntos = dict(CONJUNTOS, prospectivo=PASTA / "prospectivo.json",
                     prospectivo_campo=PASTA / "prospectivo_campo.json")
    casos = json.loads(conjuntos[args.conjunto].read_text(encoding="utf-8"))["casos"]
    pasta = PASTA / ("candidato_campo" if args.candidato == "campo" else "candidato")
    caminho = args.saida / ("controle_chat_" + args.candidato + "_" + args.conjunto + ".json")
    if caminho.exists():
        raise SystemExit("Resultado já existe. Use outra pasta para preservar o controle anterior.")
    args.saida.mkdir(parents=True, exist_ok=True)
    resgate = ResgateLeitor(pasta, exigir_aprovacao=False)
    if not resgate.disponivel:
        raise RuntimeError(resgate.motivo)
    if args.backend == "torch":
        resgate.transformer = transformer_torch(resgate, pasta)
    fontes = [RAIZ / p for p in ("crivo.py", "estado_interno.py", "leitura_ficha.py",
                                "resgate_leitor.py", "verificacao_campo_factual.py")]
    fontes.extend([pasta / "meta.json", pasta / "cabeca_revisada.npz"])
    resultado = {
        "conjunto": args.conjunto, "casos": len(casos), "aprovado": False,
        "backend": args.backend,
        "protocolo": "Chat completo pareado sem geração; artefato experimental só em memória; somente agregados.",
        "fontes_sha256": {str(p.relative_to(RAIZ)): hashlib.sha256(p.read_bytes()).hexdigest() for p in fontes},
        "baseline": {"respondiveis": Counter(), "sem_resposta": Counter()},
        "candidato": {"respondiveis": Counter(), "sem_resposta": Counter()},
        "respostas_anteriores_alteradas": 0, "resgates": 0,
        "aproximacoes_erradas": {"baseline": 0, "candidato": 0},
    }
    for k, caso in enumerate(casos):
        anterior = None
        for modo in ("baseline", "candidato"):
            bot = Crivo(usar_geracao=False)
            bot._leitura_ficha = LeituraFicha(bot.compositor, resgate=False if modo == "baseline" else resgate)
            ident, resposta = bot.responder(caso["pergunta"])
            classe = classificar(bot, caso, ident, resposta)
            # Alternativas declaradas no segundo prospectivo antes da avaliação.
            # Os conjuntos anteriores mantêm seus rótulos originais.
            if caso.get("fatos_aceitos"):
                alternativas = [classificar(bot, dict(caso, fato=i), ident, resposta) for i in caso["fatos_aceitos"]]
                if "aproximou_certo" in alternativas:
                    classe = "aproximou_certo"
                elif "afirmou_certo" in alternativas:
                    classe = "afirmou_certo"
            categoria = "sem_resposta" if caso["fato"] is None else "respondiveis"
            resultado[modo][categoria][classe] += 1
            if ident == "leitura:aproximacao" and classe != "aproximou_certo":
                resultado["aproximacoes_erradas"][modo] += 1
            if modo == "baseline":
                anterior = (ident, resposta)
            else:
                if anterior[0] not in REVISAVEIS or not recusou(*anterior):
                    resultado["respostas_anteriores_alteradas"] += int(anterior != (ident, resposta))
                if bot.historico and bot.historico[-1].get("leitura", {}).get("semantic_rescue"):
                    resultado["resgates"] += 1
        if (k + 1) % 15 == 0:
            print("avaliados", args.conjunto, k + 1, flush=True)
    caminho.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resultado, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
