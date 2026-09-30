"""Contratos autorais de escrita e reparo, separados do treino da GRU.

Confere uso de argumentos, continuidade e limites. Não mede compreensão
universal, originalidade literária ou inteligência geral. Registra textos
inteiros para revisão humana, além do resultado do oráculo restrito.
"""
import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path


def turno(pergunta, identificador, trechos=(), **criterios):
    return dict(pergunta=pergunta, id=identificador, trechos=list(trechos), **criterios)


CASOS = [
    ("história e mudança", [
        turno("Invente uma história curta sobre um farol e um robô", "conversa:gerada_historia", ["Ficção:", "um farol", "um robô"], gerada=True),
        turno("Agora dê outro final", "conversa:gerada_final", ["um farol", "um robô"], gerada=True, diferente=True),
        turno("Deixe a história mais leve", "conversa:gerada_historia", ["um farol", "um robô"], gerada=True, diferente=True),
        turno("Troque um robô por uma baleia", "conversa:gerada_historia", ["um farol", "uma baleia"], gerada=True, ausentes=["um robô"]),
        turno("Me explique seu raciocínio", "conversa:justificativa", ["uma baleia", "palavra por palavra"]),
    ]),
    ("poema e versão", [
        turno("Escreva um poema curto sobre chuva e esperança", "conversa:gerada_poema", ["Poema:", "chuva", "esperança"], gerada=True, linhas=4),
        turno("Pode fazer outra versão?", "conversa:gerada_poema", ["chuva", "esperança"], gerada=True, diferente=True, linhas=4),
    ]),
    ("argumentos inéditos", [
        turno("Imagine uma narrativa breve sobre Névia-27 e um relógio de água", "conversa:gerada_historia", ["Névia-27", "um relógio de água"], gerada=True),
        turno("Como essa história poderia terminar de outro jeito?", "conversa:gerada_final", ["Névia-27", "um relógio de água"], gerada=True, diferente=True),
        turno("Escreva uma história simples sobre uma constelação de papel", "conversa:gerada_historia", ["uma constelação de papel"], gerada=True),
        turno("Que outro final daria para imaginar?", "conversa:gerada_final", ["uma constelação de papel"], gerada=True, diferente=True),
    ]),
    ("escuta do relato", [
        turno("Quero conversar sobre um livro que li", "conversa:abertura", ["livro"]),
        turno("Gostei da protagonista, mas o final me decepcionou", "conversa:relato", ["final me decepcionou"]),
        turno("Você entendeu o que me incomodou?", "conversa:gerada_escuta", ["Gostei da protagonista, mas o final me decepcionou"], gerada=True),
    ]),
    ("reparo e restrição", [
        turno("Quero aprender a tocar flauta", "conversa:relato", ["tocar flauta"]),
        turno("Só tenho 15 minutos à noite", "conversa:relato", ["15 minutos"]),
        turno("Você já me perguntou isso", "conversa:gerada_ajuste", ["15 minutos"], gerada=True, algum=["mudar", "abordagem", "outro caminho", "diferente"]),
        turno("Faça uma sugestão diferente", "conversa:gerada_alternativa", ["aprender a tocar flauta", "15 minutos"], gerada=True, algum=["experimento", "teste", "testar", "comparar"]),
    ]),
    ("tentativa e capacidade", [
        turno("Se uma ideia não funcionou, isso significa que sou incapaz?", "conversa:gerada_apoio", ["não", "capacidade"], gerada=True, algum=["tentativa", "próxima", "passo", "resultado"]),
    ]),
    ("combinação declarada", [
        turno("Tenho duas opções: um mapa inventado ou uma chave musical", "conversa:relato", ["mapa inventado", "chave musical"]),
        turno("Combine esses dois elementos numa ideia", "conversa:gerada_ideia", ["um mapa inventado", "uma chave musical"], gerada=True, algum=["possibilidade", "inventada", "experimento"]),
    ]),
    ("esquecimento e fatos", [
        turno("Conte uma história sobre um sino e uma cidade flutuante", "conversa:gerada_historia", ["um sino", "uma cidade flutuante"], gerada=True),
        turno("Esqueça essa conversa", "conversa:reinicio", ["começar"]),
        turno("Agora dê outro final", "duvida", ["Qual texto"]),
        turno("O que é DNA?", "conhecimento:dna", ["genética"]),
        turno("Qual é a fonte?", "escrita:fontes", ["genome.gov"]),
    ]),
    ("limites de contexto", [
        turno("Você entendeu o que me incomodou?", "duvida", ["relato"]),
        turno("Pode fazer outra versão?", "duvida", ["Qual texto"]),
    ]),
]


def avaliar(classe):
    casos=[]
    for nome, perguntas in CASOS:
        bot=classe();turnos=[];anterior=""
        for c in perguntas:
            ident,resposta=bot.responder(c["pergunta"])
            falhas=[]
            if ident!=c["id"]: falhas.append("operação")
            if any(t not in resposta for t in c["trechos"]): falhas.append("argumentos")
            if any(t in resposta for t in c.get("ausentes",[])): falhas.append("substituição")
            if c.get("algum") and not any(t in resposta for t in c["algum"]): falhas.append("ação pertinente")
            if c.get("diferente") and resposta==anterior: falhas.append("repetição integral")
            if c.get("linhas") and len(resposta.splitlines()[1:])!=c["linhas"]: falhas.append("formato")
            quadro=(bot.historico[-1].get("quadro_geracao") or {}) if bot.historico else {}
            if c.get("gerada") and (not quadro or quadro.get("tokens",0)<6): falhas.append("geração concluída")
            if c.get("gerada") and (bot.contexto_textual is not None or "prova_origem" in (bot.ultimo_turno or {})):
                falhas.append("proveniência fictícia")
            turnos.append(dict(pergunta=c["pergunta"],id=ident,resposta=resposta,passou=not falhas,falhas=falhas))
            anterior=resposta
        casos.append(dict(nome=nome,passou=all(t["passou"] for t in turnos),turnos=turnos))
    ts=[t for c in casos for t in c["turnos"]]
    return dict(mensagens=len(ts),acertos=sum(t["passou"] for t in ts),dialogos=len(casos),
                dialogos_completos=sum(c["passou"] for c in casos),casos=casos)


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo",type=Path)
    p.add_argument("--saida",type=Path,default=Path("avaliacao_geracao.json"))
    p.add_argument("--permitir-falhas",action="store_true")
    a=p.parse_args()
    if a.repo: sys.path.insert(0,str(a.repo.resolve()))
    classe=importlib.import_module("crivo").Crivo
    r=avaliar(classe)
    r["assinatura_casos"]=hashlib.sha256(json.dumps(CASOS,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    r["limite"]="Contratos de desenvolvimento autorais; critérios e textos publicados. Não são conversas humanas independentes nem uma avaliação cega de inteligência ou qualidade literária. O treino não lê esta sonda."
    a.saida.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in r.items() if k!="casos"},ensure_ascii=False,indent=2))
    if r["acertos"]!=r["mensagens"] and not a.permitir_falhas: sys.exit(1)
