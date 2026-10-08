"""Leitor próprio como última tentativa, apenas com resposta aproximada.

O calibrador combina a confiança do leitor com a evidência da ficha. Seu
controle é independente do controle do leitor isolado: sem aprovação do
conjunto, a execução normal mantém a resposta anterior.
"""
import hashlib
import json
import math
import re
import zipfile
from functools import lru_cache
from pathlib import Path

from composicao_textual import normalizar
from leitura_ficha import ABSOLUTOS, Leitura, TRACOS, pergunta_direta

RAIZ = Path(__file__).resolve().parent
PASTA = RAIZ / "artefatos" / "leitor_resgate"
BASE = RAIZ / "experimentos" / "pesos_base" / "leitor_transformer"
TRACOS_RESGATE = (
    "vies", "prob_transformer", "margem_transformer", "prob_lexical", "margem_lexical",
    "relacao", "vetor", "todas", "nenhuma", "uma_pista", "falta_uma", "faltam_duas",
    "quem_nome", "quando_data", "quanto_numero", "onde_lugar", "porque_causa",
    "como_funcionamento", "simnao_negacao", "definicao", "numero_fatos",
)


def evidencias(probabilidades, lexical, indice, tracos):
    """Mesmas grandezas usadas no treinamento, sem identidade do assunto."""
    segunda = max((p for i, p in enumerate(probabilidades) if i != indice), default=0.0)
    return [1.0, probabilidades[indice], probabilidades[indice] - segunda,
            lexical[indice], lexical[indice] - max(lexical)] + [
        tracos[n] for n in TRACOS_RESGATE[5:-1]
    ] + [math.log1p(len(probabilidades)) / 3.0]


class ResgateLeitor:
    def __init__(self, pasta=PASTA, base=BASE, exigir_aprovacao=True):
        self.disponivel = False
        self.motivo = ""
        try:
            pasta, base = Path(pasta), Path(base)
            meta = json.loads((pasta / "meta.json").read_text(encoding="utf-8"))
            if not isinstance(meta, dict):
                raise ValueError("meta.json inválido")
            controle = meta.get("controle")
            if exigir_aprovacao and (not isinstance(controle, dict) or controle.get("aprovado") is not True):
                self.motivo = "resgate não aprovado no controle completo"
                return
            self.verificar_campo = meta.get("verificacao") == "campo_explicito_v1"
            if exigir_aprovacao and not self.verificar_campo:
                raise ValueError("resgate sem verificação do campo pedido")
            if meta.get("escopo") != "resgate_aproximacao" or meta.get("tracos") != list(TRACOS_RESGATE):
                raise ValueError("contrato do calibrador incompatível")
            pesos = [float(p) for p in meta["pesos"]]
            limiar = float(meta["limiar"])
            if len(pesos) != len(TRACOS_RESGATE) or not all(math.isfinite(p) for p in pesos):
                raise ValueError("pesos do calibrador inválidos")
            if not math.isfinite(limiar) or not 0.0 <= limiar <= 1.0:
                raise ValueError("limiar inválido")
            for nome, caminho in (("base_sha256", base / "pesos_numpy.npz"),
                                  ("tokenizer_sha256", base / "tokenizer.json"),
                                  ("cabeca_sha256", pasta / "cabeca_revisada.npz")):
                if hashlib.sha256(caminho.read_bytes()).hexdigest() != meta["fontes"][nome]:
                    raise ValueError("fonte dos pesos incompatível")
            # A aprovação é do conjunto base + cabeça + calibrador, identificado
            # pelos hashes acima. A cabeça experimental da base não é ativada.
            from leitor_transformer import LeitorTransformer
            transformer = LeitorTransformer(base, exigir_aprovacao=False)
            if not transformer.disponivel:
                self.motivo = transformer.motivo
                return
            np = transformer.modelo.np
            with np.load(pasta / "cabeca_revisada.npz", allow_pickle=False) as cabeca:
                if set(cabeca.files) != {"cabeca.weight", "cabeca.bias"}:
                    raise ValueError("cabeça incompatível")
                novos = {}
                for nome in cabeca.files:
                    valor = cabeca[nome]
                    if valor.shape != transformer.modelo.p[nome].shape or not np.isfinite(valor).all():
                        raise ValueError("pesos da cabeça inválidos")
                    novos[nome] = valor.astype(np.float32)
            transformer.modelo.p.update(novos)
            self.transformer, self.pesos, self.limiar = transformer, pesos, limiar
            self.disponivel = True
        except (OSError, ValueError, KeyError, TypeError, ImportError, OverflowError, EOFError, zipfile.BadZipFile):
            self.motivo = "artefato de resgate ausente ou incompatível"

    def sugerir(self, leitor, quadro, assunto=None):
        if not self.disponivel or quadro is None or leitor.nomes != TRACOS:
            return None
        assunto = assunto or quadro.assunto
        if (assunto not in leitor.c.itens or quadro.outros
                or quadro.recusa and quadro.recusa != "sem_pistas"):
            return None
        n = normalizar(quadro.texto)
        if (not pergunta_direta(quadro.texto) or re.search(r"\b(?:nao|nem|nunca|jamais)\b", n)
                or any(ABSOLUTOS.match(p) for p in re.findall(r"[a-z]+", n))):
            return None
        # Nunca muda a política literal, nem disputa uma resposta já aceita.
        if leitor.decisao(leitor.ler(quadro, assunto)) is not None:
            return None
        fatos = leitor.c.itens[assunto]["fatos"]
        if not fatos:
            return None
        probs = self.transformer.probabilidades(quadro.texto, [f["texto"] for f in fatos])
        if (len(probs) != len(fatos)
                or not all(math.isfinite(p) and 0.0 <= p <= 1.0 for p in probs)):
            return None
        indice = max(range(len(probs)), key=lambda i: probs[i])
        if sum(p == probs[indice] for p in probs) != 1:
            return None
        candidatos = {i: (p, cob, tipo, x) for p, i, cob, tipo, x in leitor.candidatos(quadro, assunto)}
        _, cobertura, tipo, x = candidatos[indice]
        tracos = dict(zip(TRACOS, x))
        if tracos["tipo_sem_par"]:
            return None
        campo = None
        if self.verificar_campo:
            from verificacao_campo_factual import verificar_campo
            campo = verificar_campo(quadro.texto, fatos[indice]["texto"], tracos,
                                    leitor.c.itens[assunto].get("area"))
            if campo is None:
                return None
        lexical = [candidatos[i][0] for i in range(len(fatos))]
        atributos = evidencias(probs, lexical, indice, tracos)
        z = sum(w * v for w, v in zip(self.pesos, atributos))
        p = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
        if p < self.limiar:
            return None
        margem = probs[indice] - max((v for i, v in enumerate(probs) if i != indice), default=0.0)
        tracos.update(resgate_semantico=True, prob_transformer=round(probs[indice], 4),
                      margem_transformer=round(margem, 4), pergunta_direta=True, absoluto=False)
        if campo is not None:
            tracos["campo_verificado"] = campo
        return Leitura(assunto, indice, round(p, 4), round(margem, 4), cobertura, tipo, tracos)


@lru_cache(maxsize=1)
def resgate():
    return ResgateLeitor()
