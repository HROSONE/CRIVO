"""Experimento A/B da memoria associativa da main.

Conjunto de avaliacao NOVO: nao altera pesos, nao alimenta o treino e nao
reutiliza os enunciados da prova retida v1. Mesma pergunta com circuito
ligado e desligado; e recuperacao da unidade selecionada.
"""
import hashlib
import json
import os
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from crivo import Crivo
from curriculo_mundo import carregar_base


# Questões de desenvolvimento prospectivo escritas DEPOIS do merge.
# Nao usar este arquivo nem as perguntas retidas v1 para re-treinar.
POSITIVOS = [
    ("Vênus", "mundo_venus", "De que modo Vênus produz efeito estufa retendo calor na atmosfera?", "O dióxido de carbono abundante"),
    ("Terra", "mundo_terra", "De que modo Terra produz campo magnético por movimentos de ferro líquido?", "Movimentos do ferro líquido"),
    ("Júpiter", "mundo_jupiter", "De que modo Júpiter transforma hidrogênio em fluido metálico eletricamente condutor?", "A pressão interna pode transformar"),
    ("Saturno", "mundo_saturno", "De que modo Saturno mantém partículas em órbitas sob campo gravitacional?", "Os anéis de Saturno são compostos"),
    ("Urano", "mundo_urano", "De que modo Urano absorve luz vermelha com metano na atmosfera?", "O metano na atmosfera absorve"),
    ("Netuno", "mundo_netuno", "De que modo Netuno apresenta ventos intensos e tempestades que mudam?", "A atmosfera de Netuno apresenta"),
    ("Marte", "mundo_marte", "De que modo Marte apresenta aparência avermelhada por óxidos de ferro?", "Óxidos de ferro na poeira"),
    ("Mercúrio", "mundo_mercurio", "De que modo Mercúrio completa revolução em 88 dias terrestres sob gravidade do Sol?", "A gravidade do Sol mantém"),
    ("Sistema Solar", "sistema_solar", "De que modo o Sistema Solar mantém órbitas elípticas e movimentos dos planetas pela gravidade solar?", "A gravidade solar domina"),
    ("estrela", "estrela", "De que modo estrela libera energia em radiação através de camadas estelares?", "A energia produzida no interior"),
    ("Vênus 2", "mundo_venus", "De que modo Vênus gira lentamente em sentido contrário à rotação de outros planetas?", "Vênus gira lentamente"),
    ("Terra 2", "mundo_terra", "De que modo Terra modifica continentes por placas tectônicas em movimento?", "A superfície terrestre possui placas"),
    ("Júpiter 2", "mundo_jupiter", "De que modo Júpiter mantém tempestades de longa duração nas faixas de nuvens?", "As faixas de nuvens"),
    ("Netuno 2", "mundo_netuno", "De que modo Netuno absorve luz com metano de sua atmosfera?", "O metano da atmosfera absorve"),
]
CONTROLES = [
    "De que modo Vênus e Netuno usam a mesma turbina de plasma?",
    "De que modo o planeta imaginário Criptor-981 produz hidrogênio líquido?",
    "De que modo Vênus não produz efeito estufa retendo calor na atmosfera?",
    "De que modo Terra produz campo magnético se fosse feita de chocolate?",
    "De que modo Júpiter produz dinheiro usando hidrogênio extraterrestre?",
    "De que modo Saturno dispara lasers alimentados por moedas antigas?",
    "De que modo Urano não absorve luz vermelha com metano na atmosfera?",
    "De que modo Netuno forma um reator de fusão artificial em 2026?",
    "De que modo Marte realiza telepatia por óxidos de ferro?",
    "De que modo Mercúrio cura doenças com sua gravidade solar?",
    "De que modo Vênus e Marte compartilham um mesmo cérebro humano?",
    "Por que Vênus usa uma máquina do tempo para aquecer o planeta?",
    "De que modo estrela produz radiação inventada por alienígenas?",
    "De que modo o Sistema Solar faz órbitas triangulares perfeitas?",
]


def chave(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return " ".join(texto.replace("?", "").replace(".", "").split())


def nao_contaminado():
    perguntas_treino = {chave(p) for x in carregar_base(ROOT / "conhecimento.json")
                       for p in x["perguntas"]}
    arquivo_v1 = ROOT / "avaliacoes" / "astronomia_independente_v1.json"
    perguntas_v1 = {chave(x["pergunta"]) for x in
                   json.loads(arquivo_v1.read_text(encoding="utf-8"))["casos"]}
    perguntas = [q for _, _, q, _ in POSITIVOS] + CONTROLES
    if len({chave(q) for q in perguntas}) != len(perguntas):
        raise AssertionError("Casos repetidos")
    if any(chave(q) in perguntas_treino | perguntas_v1 for q in perguntas):
        raise AssertionError("Avaliacao compartilha pergunta exata com treino ou v1")
    return len(perguntas_treino), len(perguntas_v1)


def executar(pergunta, circuito_ativo):
    bot = Crivo()
    if bot.rede is None:
        raise RuntimeError("Checkpoint neural nao foi carregado: " + str(bot.erro_rede))
    circuito = bot.compositor.cortex
    ativacao = circuito.associar(pergunta) if circuito_ativo else None
    if not circuito_ativo:
        bot.compositor._resposta_associativa = lambda _: None
    rotulo, resposta = bot.responder(pergunta)
    contexto = bot.contexto_textual
    exibidos = list(contexto.exibidos) if contexto is not None else []
    urls = []
    for ident, indice in exibidos:
        fato = bot.compositor.itens[ident]["fatos"][indice]
        for source in [fato.get("fonte")] + fato.get("fontes", []):
            if source and source in bot.compositor.fontes:
                url = bot.compositor.fontes[source].get("url")
                if url and url not in urls:
                    urls.append(url)
    return dict(id=rotulo, resposta=resposta, evidencias=exibidos,
                fontes=urls, ativacao=(ativacao._asdict() if ativacao else None))


def testar():
    nt, nv = nao_contaminado()
    resultados = []
    ganho, piora = 0, 0
    for nome, alvo, pergunta, trecho in POSITIVOS:
        ligado = executar(pergunta, True)
        desligado = executar(pergunta, False)
        bot = Crivo()
        fatos = bot.compositor.itens[alvo]["fatos"]
        esperado = [i for i, f in enumerate(fatos) if trecho.lower() in f["texto"].lower()]
        if len(esperado) != 1:
            raise AssertionError("Gabarito factual nao unico: " + nome)
        expected_key = (alvo, esperado[0])  # contexto guarda tuplas (id, indice)
        # Conta como acerto factual somente se a resposta realmente exibiu
        # a unidade alvo e a unidade tem URL de evidencia documentada.
        def acerta(out):
            return (expected_key in out["evidencias"] and trecho.lower() in
                    out["resposta"].lower() and bool(out["fontes"]))
        a, b = acerta(ligado), acerta(desligado)
        if ligado["ativacao"] is not None and ligado["ativacao"]["indice"] == esperado[0] and not a:
            raise AssertionError("Metrica incoerente: ativacao certa sem evidencias: " + nome)
        ganho += int(a and not b)
        piora += int(b and not a)
        resultados.append(dict(tipo="positivo", nome=nome, pergunta=pergunta,
           fato_esperado=expected_key, ligado=ligado, desligado=desligado,
           acerto_ligado=a, acerto_desligado=b,
           alterou_resposta=(ligado["id"],ligado["resposta"]) !=
                            (desligado["id"],desligado["resposta"])))
    falsos_positivos = 0
    for pergunta in CONTROLES:
        ligado = executar(pergunta, True)
        desligado = executar(pergunta, False)
        direta = ligado["ativacao"] is not None
        falsos_positivos += int(direta)
        resultados.append(dict(tipo="controle",pergunta=pergunta,
                               ligado=ligado, desligado=desligado,
                               disparo_indevido=direta))
    pos = [c for c in resultados if c["tipo"] == "positivo"]
    controles = [c for c in resultados if c["tipo"] == "controle"]
    resumo = {
        "ensaio":"cortex-ab-novo-v1",
        "commit":os.getenv("GITHUB_SHA","local"),
        "modo":"sem treino e sem alteracao de pesos; corpus distinto da prova retida v1",
        "positivos":len(pos),
        "controles":len(controles),
        "acertos_com_cortex":sum(x["acerto_ligado"] for x in pos),
        "acertos_sem_cortex":sum(x["acerto_desligado"] for x in pos),
        "ganhos_exclusivos":ganho, "perdas_exclusivas":piora,
        "acionamentos_associativos":sum(x["ligado"]["ativacao"] is not None for x in pos),
        "acionamentos_falsos_controle":falsos_positivos,
        "quantidade_exemplos_treino_conferidos":nt,
        "quantidade_v1_conferidos":nv,
        "diferencas_textuais":sum(x["alterou_resposta"] for x in pos),
        "casos_novos_compartilham_exemplos":False,
    }
    destino = ROOT / "resultado_cortex_ab.json"
    destino.write_text(json.dumps(dict(resumo=resumo,casos=resultados),
                                  ensure_ascii=False,indent=2) + "\n",encoding="utf-8")
    print(json.dumps(resumo,ensure_ascii=False,indent=2),flush=True)
    print("FALHAS_POR_CASO")
    for x in pos:
        if not x["acerto_ligado"]:
            print(x["nome"],"on",x["ligado"]["id"],"off",x["desligado"]["id"],
                  "ativacao", x["ligado"]["ativacao"] is not None)
    print("ARQUIVO:",destino,flush=True)
    # O benchmark DEVE denunciar violacao da separacao de evidencias.
    if falsos_positivos:
        raise SystemExit("FALHA: circuito acionou em controle sem evidencia")
    # Nao alterar gabarito para esconder um possivel resultado de 0 ganhos.


if __name__ == "__main__":
    testar()
