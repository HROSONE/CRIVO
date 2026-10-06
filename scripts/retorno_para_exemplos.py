"""Ciclo de retorno: das avaliações compartilhadas a exemplos revisados.

1. A pessoa baixa “crivo-avaliacoes.json” no site e decide compartilhar.
2. `python scripts/retorno_para_exemplos.py fila arquivo.json [...]` lê os
   arquivos e acrescenta candidatos à fila dados/retorno_fila.json, sem
   duplicar e com "revisado": false:
     voz_positiva       👍 numa resposta com a voz própria: a própria resposta
                        pode virar exemplo de tutor;
     voz_corrigir       👎 ou “não era isso” numa resposta com voz: precisa de
                        uma resposta corrigida escrita por quem revisa;
     entendimento_sim   “sim” a uma confirmação da compreensão neural:
                        a fala livre vira exemplo positivo daquele assunto;
     entendimento_nao   “não” a essa confirmação: registro do erro, para medir.
3. Quem revisa edita a fila: marca "revisado": true e, em voz_corrigir,
   preenche "tutor" com a resposta certa (só com fatos do acervo).
4. `python scripts/retorno_para_exemplos.py incorporar` move os itens
   revisados para dados/voz_tutor.json e dados/entendimento_retorno.json,
   sempre pela guarda de fidelidade e longe dos testes congelados.
Nada é treinado sozinho: depois de incorporar, roda-se o treino e as catracas.
"""
import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

FILA = RAIZ / "dados" / "retorno_fila.json"
TUTOR = RAIZ / "dados" / "voz_tutor.json"
ENTENDIMENTO = RAIZ / "dados" / "entendimento_retorno.json"


def _ler(caminho, padrao):
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def _gravar(caminho, dados):
    Path(caminho).write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _chave(item):
    base = "|".join(str(item.get(k, "")) for k in ("tipo", "pergunta", "assunto", "resposta"))
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]


def candidatos(avaliacoes):
    """Converte registros do site em candidatos da fila."""
    saida = []
    for r in avaliacoes:
        if not isinstance(r, dict):
            continue
        if r.get("tipo") == "sinal":
            sinal, especie = r.get("sinal"), r.get("especie")
            assunto = r.get("assunto")
            if isinstance(assunto, list):
                assunto = assunto[0] if len(assunto) == 1 else None
            if especie == "compreensao_neural" and sinal in ("confirmado", "rejeitado") and assunto:
                saida.append({"tipo": "entendimento_sim" if sinal == "confirmado" else "entendimento_nao",
                              "pergunta": r.get("pergunta", ""), "assunto": assunto})
            elif sinal == "contestado":
                saida.append({"tipo": "voz_corrigir", "pergunta": r.get("pergunta", ""),
                              "assunto": assunto, "resposta": "", "tutor": ""})
            continue
        if r.get("voz") != "voz_propria":
            continue
        tipo = "voz_positiva" if r.get("nota") == 1 else "voz_corrigir"
        saida.append({"tipo": tipo, "pergunta": r.get("pergunta", ""), "assunto": None,
                      "resposta": r.get("resposta", ""),
                      "tutor": r.get("resposta", "") if tipo == "voz_positiva" else ""})
    for c in saida:
        c["chave"] = _chave(c)
        c["revisado"] = False
    return saida


def enfileirar(arquivos):
    fila = _ler(FILA, {"versao": 1, "itens": []})
    vistos = {i["chave"] for i in fila["itens"]}
    novos = 0
    for arq in arquivos:
        dados = _ler(arq, {})
        if not isinstance(dados, dict) or dados.get("formato") != "crivo-avaliacoes-v1":
            raise SystemExit("Formato desconhecido: %s" % arq)
        for c in candidatos(dados.get("avaliacoes", [])):
            if c["chave"] not in vistos:
                fila["itens"].append(c)
                vistos.add(c["chave"])
                novos += 1
    _gravar(FILA, fila)
    return novos


def _assuntos_congelados():
    proibidos = set()
    for caminho in ("avaliacoes/voz_v1/teste.json",):
        for c in _ler(RAIZ / caminho, {}).get("casos", []):
            proibidos.update(c.get("assuntos", []))
    perguntas = {normal(c["p"]) for c in _ler(RAIZ / "avaliacoes/entendimento_v1/teste.json", {}).get("positivos", [])}
    perguntas |= {normal(p) for p in _ler(RAIZ / "avaliacoes/entendimento_v1/teste.json", {}).get("negativos", [])}
    return proibidos, perguntas


def normal(texto):
    from linguagem_conversa import normalizar
    return normalizar(texto or "").strip(" ?!.")


def incorporar():
    """Move itens revisados para os dados de treino. Devolve um resumo."""
    from crivo import Crivo
    from curriculo_mundo import texto_fato
    from voz import palavras_inventadas
    fila = _ler(FILA, {"versao": 1, "itens": []})
    tutor = _ler(TUTOR, {"versao": 1, "casos": []})
    entend = _ler(ENTENDIMENTO, {"versao": 1, "uso": "Pares revisados do ciclo de retorno.", "positivos": [],
                                 "erros": []})
    proibidos, perguntas_teste = _assuntos_congelados()
    bot = Crivo()
    bot.usar_voz = False
    resumo = {"voz": 0, "entendimento": 0, "recusados": [], "pendentes": 0}
    restantes = []
    for item in fila["itens"]:
        if not item.get("revisado"):
            restantes.append(item)
            resumo["pendentes"] += 1
            continue
        if item["tipo"] in ("voz_positiva", "voz_corrigir"):
            if not item.get("tutor"):
                resumo["recusados"].append((item["chave"], "sem resposta do tutor"))
                continue
            bot.responder(item["pergunta"])
            ctx = bot.contexto_textual
            assuntos = sorted({e for e, _ in ctx.exibidos}) if ctx is not None and ctx.exibidos else []
            if len(assuntos) != 1 or assuntos[0] in proibidos:
                resumo["recusados"].append((item["chave"], "assunto ausente ou do teste congelado"))
                continue
            it = bot.compositor.itens[assuntos[0]]
            fontes = [item["pergunta"]] + [texto_fato(f) for f in it["fatos"]] + [it["nome"]] + it.get("aliases", [])
            if palavras_inventadas(item["tutor"], fontes):
                resumo["recusados"].append((item["chave"], "guarda de fidelidade"))
                continue
            tutor["casos"].append({"pergunta": item["pergunta"], "assuntos": assuntos, "tutor": item["tutor"],
                                   "origem": "retorno"})
            resumo["voz"] += 1
        elif item["tipo"] in ("entendimento_sim", "entendimento_nao"):
            if normal(item["pergunta"]) in perguntas_teste:
                resumo["recusados"].append((item["chave"], "pergunta do teste congelado"))
                continue
            alvo = entend["positivos"] if item["tipo"] == "entendimento_sim" else entend["erros"]
            alvo.append({"pergunta": item["pergunta"], "assunto": item["assunto"]})
            resumo["entendimento"] += 1
    fila["itens"] = restantes
    _gravar(FILA, fila)
    _gravar(TUTOR, tutor)
    _gravar(ENTENDIMENTO, entend)
    return resumo


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "fila":
        print("novos na fila:", enfileirar(sys.argv[2:]))
    elif len(sys.argv) == 2 and sys.argv[1] == "incorporar":
        print(json.dumps(incorporar(), ensure_ascii=False, indent=1))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
