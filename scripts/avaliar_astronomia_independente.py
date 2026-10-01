"""Sonda astronomica retida. Nunca treina nem altera pesos.

Os enunciados e a rubrica foram redigidos apos congelar o checkpoint de 193
classes e fora de curriculo_mundo. Avaliacao automatica de ID + termos
necessarios NAO equivale a revisao semantica humana nem auditoria cientifica
externa; respostas completas ficam no relatorio para revisao humana.
"""
import hashlib
import json
import os
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from crivo import Crivo
from curriculo_mundo import carregar_base


def normalizar(texto):
    n = unicodedata.normalize("NFD", texto.casefold())
    return "".join(c for c in n if unicodedata.category(c) != "Mn")


def assinatura(caminho):
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def resolver_modelo(caminho=None):
    destino = Path(caminho).resolve() if caminho else RAIZ / 'rede_crivo.json'
    if caminho and not destino.is_file():
        raise FileNotFoundError('Checkpoint experimental ausente: ' + str(destino))
    return destino


def rodar(caminho_modelo=None, destino_relatorio=None):
    casos_path = RAIZ / "avaliacoes" / "astronomia_independente_v1.json"
    modelo_path = resolver_modelo(caminho_modelo)
    casos = json.loads(casos_path.read_text(encoding="utf-8"))
    if len(casos["casos"]) < 50:
        raise ValueError("A prova independente precisa de pelo menos 50 sondas")
    todos = carregar_base(RAIZ / "conhecimento.json")
    treino = {normalizar(q).strip(" .!?") for item in todos
              for q in item["perguntas"]}
    vistos = set()
    for caso in casos["casos"]:
        q = normalizar(caso["pergunta"]).strip(" .!?")
        if q in treino:
            raise ValueError("Contaminacao: pergunta da prova presente nos exemplos de treino: " + caso["id"])
        if q in vistos:
            raise ValueError("Prova possui pergunta duplicada: " + caso["id"])
        vistos.add(q)
    motor = Crivo()
    if caminho_modelo:
        motor.carregar_rede(modelo_path)
    rede_ativa = motor.rede is not None and motor.erro_rede is None
    resultados = []
    for caso in casos["casos"]:
        # Cada caso isolado, sem contexto de questoes anteriores.
        bot = Crivo()
        if caminho_modelo:
            bot.carregar_rede(modelo_path)
        identificador, resposta = bot.responder(caso["pergunta"])
        abstencao = caso["grupo"] == "controle"
        esperado = caso["esperado"]
        id_ok = (identificador in esperado if isinstance(esperado, list)
                 else identificador == esperado)
        checks = [dict(opcoes=g, encontrado=any(
            normalizar(t) in normalizar(resposta) for t in g))
                  for g in caso["tokens"]]
        termos_ok = all(t["encontrado"] for t in checks)
        exibe = bot.contexto_textual
        # Somente fatos selecionados da ficha canônica são rastreados.
        fontes = []
        if exibe is not None:
            for id_item, indice in exibe.exibidos:
                if id_item not in bot.compositor.itens:
                    continue
                fato = bot.compositor.itens[id_item]["fatos"][indice]
                fonte = fato.get("fonte")
                if fonte and fonte not in fontes:
                    fontes.append(fonte)
        neural = None
        if (not abstencao and rede_ativa and isinstance(esperado, str)
                and esperado.replace("conhecimento:", "") in bot.rede.rotulos):
            previsto, confianca = bot.rede.prever(caso["pergunta"])
            neural = dict(esperado=esperado.replace("conhecimento:", ""),
                          obtido=previsto, confianca=round(confianca, 5),
                          correto=previsto == esperado.replace("conhecimento:", ""))
        resultados.append(dict(
            id=caso["id"], grupo=caso["grupo"], pergunta=caso["pergunta"],
            esperado=esperado, obtido=identificador,
            correto_id=id_ok, rubricados=checks,
            correto=id_ok and termos_ok,
            apresentou_fatos_fora_do_escopo=abstencao and not id_ok,
            fontes_exibidas=fontes, resposta=resposta,
            neural=neural))
    grupos = {}
    for nome in ("vocabulario", "sistema_solar", "controle"):
        lista = [r for r in resultados if r["grupo"] == nome]
        total = len(lista)
        acertos = sum(r["correto"] for r in lista)
        grupos[nome] = dict(total=total, acertos=acertos,
                             taxa=round(acertos/total, 4) if total else None,
                             falhas=[r["id"] for r in lista if not r["correto"]])
    neural = [r["neural"] for r in resultados if r["neural"] is not None]
    limite = casos["criterios"]["min_acerto_por_modulo"]
    apto_vocabulario = (grupos["vocabulario"]["taxa"] >= limite and
                         grupos["controle"]["acertos"] == grupos["controle"]["total"])
    apto_sistema = (grupos["sistema_solar"]["taxa"] >= limite and
                     grupos["controle"]["acertos"] == grupos["controle"]["total"])
    resumo = {
        "versao":casos["versao"],
        "marco":os.getenv("GITHUB_SHA", "execucao-local"),
        "pasta_modelo":modelo_path.name,
        "sha256_modelo":assinatura(modelo_path),
        "sha256_prova":assinatura(casos_path),
        "rede_carregada":rede_ativa,
        "erro_rede":motor.erro_rede,
        "grupos":grupos,
        "rede_isolada": {
            "total":len(neural),
            "acertos":sum(x["correto"] for x in neural),
            "limite":"somente labels com alvo de ID explícito no classificador",
        },
        "apto_pelo_crivo_automatico":{
            "vocabulario":apto_vocabulario,
            "sistema_solar":apto_sistema,
        },
        "independencia":{
            "separada_dos_exemplos_de_treino":True,
            "concebida_depois_do_checkpoint":True,
            "avaliacao_sem_ajustar_pesos":True,
            "avaliacao_humana_ou_terceiro":False,
            "observacao":"ID e fragmentos verificam recuperacao de evidencias, nao compreensao causal livre."
        },
    }
    relatorio = dict(resumo=resumo, resultados=resultados)
    destino = Path(destino_relatorio).resolve() if destino_relatorio else RAIZ / "resultado_astronomia_independente_v1.json"
    destino.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2), flush=True)
    print("RELATORIO " + str(destino),flush=True)
    if not rede_ativa:
        raise SystemExit(2)
    if not apto_vocabulario or not apto_sistema:
        print("GATE DE CERTIFICACAO: NAO APROVADO; manter progresso e revisar falhas SEM treinar nesta prova.",
              flush=True)
        raise SystemExit(1)
    print("GATE DE RECUPERACAO: APROVADO. Revisao editorial e humana ainda exigidas.",flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelo", default=None)
    parser.add_argument("--relatorio", default=None)
    args = parser.parse_args()
    rodar(args.modelo, args.relatorio)
