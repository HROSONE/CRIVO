"""Prova prospectiva v2: formulacoes nao presentes no A/B anterior, v1 ou treino.

A prova e escrita DEPOIS do microcircuito v2 ter sido congelado no commit
77a9399. Nao usar para treinamento nem retroajustar o gabarito. Inclui
consultas mais distantes do padrao inicial; falhas sao relatadas, nao
camufladas por ajuste de limites.
"""
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from crivo import Crivo
from curriculo_mundo import carregar_base
from scripts.avaliar_cortex_ab_novo import executar, chave, POSITIVOS, CONTROLES

POSITIVOS_V2 = [
    ("V01","mundo_venus","Como a atmosfera de Vênus conserva calor devido ao dióxido de carbono?","O dióxido de carbono abundante"),
    ("V02","mundo_terra","De que modo o núcleo da Terra gera seu campo magnético?","Movimentos do ferro líquido"),
    ("V03","mundo_jupiter","Qual o mecanismo de produção do campo magnético de Júpiter?","A pressão interna pode transformar"),
    ("V04","mundo_urano","Como a inclinação de Urano influencia suas estações?","A inclinação do eixo de Urano"),
    ("V05","mundo_netuno","Como o metano de Netuno influencia a luz absorvida?","O metano da atmosfera absorve"),
    ("V06","mundo_marte","Qual o mecanismo que dá a Marte sua aparência vermelha?","Óxidos de ferro na poeira"),
    ("V07","mundo_mercurio","Como a gravidade do Sol mantém Mercúrio em seu caminho orbital?","A gravidade do Sol mantém"),
    ("V08","sistema_solar","De que modo o Sistema Solar apresenta órbitas aproximadamente elípticas?","A gravidade solar domina"),
    ("V09","estrela","Como uma estrela irradia energia por suas camadas interiores?","A energia produzida no interior"),
    ("V10","mundo_urano","Como Urano tem aparência azul-esverdeada devido à absorção de luz vermelha?","O metano na atmosfera absorve"),
    ("V11","mundo_jupiter","Como a pressão interna em Júpiter pode tornar o hidrogênio condutor?","A pressão interna pode transformar"),
    ("V12","mundo_netuno","De que modo Netuno movimenta nuvens dinâmicas e tempestades?","A atmosfera de Netuno apresenta"),
    ("V13","mundo_terra","Como Terra modifica fundos oceânicos através do movimento de placas tectônicas?","A superfície terrestre possui placas"),
    ("V14","mundo_saturno","Como Saturno conserva as partículas dos anéis em órbitas individuais?","Os anéis de Saturno são compostos"),
    ("V15","mundo_marte","De que modo Marte ganha tom avermelhado pelos óxidos no solo?","Óxidos de ferro na poeira"),
    ("V16","mundo_venus","Como Vênus diferencia sua rotação da revolução em torno do Sol?","Vênus gira lentamente"),
]
CONTROLES_V2 = [
    "Como a Terra emite lasers de tungstênio com seu núcleo?",
    "De que modo Vênus obtém uma atmosfera inteiramente produzida por Netuno?",
    "Como Saturno produz efeito estufa com partículas mágicas dos anéis?",
    "De que modo Netuno provoca tempestades feitas de chocolate?",
    "Como Urano absorve luz vermelha sem possuir metano?",
    "Como Júpiter cria ouro sem utilizar hidrogênio?",
    "Como Mercúrio gira ao redor de um Sol artificial inventado?",
    "Como a estrela funciona num universo de magia comprovada?",
    "Como a luz de Marte alimenta artificialmente Saturno?",
    "Como Marte e Júpiter criam ferro extraterrestre?",
    "Como o Sistema Solar funciona em órbitas quadradas perfeitas?",
    "Como o planeta Solrot-99 gera energia solar?",
    "Como a Terra usa placas tectônicas para fabricar portais?",
    "Como Vênus e o Sol formam um motor de teletransporte?",
    "Como uma estrela não produz fusão nuclear?",
    "Como Saturno usa anéis de vidro inventado para transmitir pensamentos?",
]

def principal():
    treino = {chave(p) for item in carregar_base(ROOT/"conhecimento.json") for p in item["perguntas"]}
    aval_v1 = {chave(c["pergunta"]) for c in
               json.loads((ROOT/"avaliacoes"/"astronomia_independente_v1.json").read_text(encoding="utf-8"))["casos"]}
    antigo = {chave(c[2]) for c in POSITIVOS} | {chave(c) for c in CONTROLES}
    perguntas = [t[2] for t in POSITIVOS_V2] + CONTROLES_V2
    if len(set(map(chave,perguntas))) != len(perguntas):
        raise ValueError("V2 repetiu uma pergunta")
    if set(map(chave,perguntas)) & (treino | aval_v1 | antigo):
        raise ValueError("V2 contaminada com treino ou avaliacao anterior")
    bot = Crivo()
    if bot.rede is None:
        raise ValueError("Modelo neural nao carregado "+str(bot.erro_rede))
    acertos_on = acertos_off = ativacoes = erros_controle = 0
    resultados = []
    for nome, ident, pergunta, inicio in POSITIVOS_V2:
        on=executar(pergunta,True)
        off=executar(pergunta,False)
        indices = [i for i,f in enumerate(bot.compositor.itens[ident]["fatos"])
                   if inicio.lower() in f["texto"].lower()]
        if len(indices)!=1:
            raise ValueError("Prova v2 com alvo nao unico "+nome)
        # Recuperacao de unidade tipada: conferimos fonte e evidencia no
        # MESMO contexto factual. Sinonimos nao fazem parte dessa rubrica.
        alvo = (ident,indices[0])
        def ok(d):
            return (alvo in d["evidencias"] and inicio.lower() in d["resposta"].lower()
                    and bool(d["fontes"]))
        a,b=ok(on),ok(off)
        acertos_on+=int(a)
        acertos_off+=int(b)
        ativacoes+=int(on["ativacao"] is not None)
        resultados.append({"id":nome,"tipo":"positivo","pergunta":pergunta,
                          "alvo":alvo,"ligado":on,"desligado":off,
                          "acerto_ligado":a,"acerto_desligado":b})
    for i,pergunta in enumerate(CONTROLES_V2,1):
        on=executar(pergunta,True)
        off=executar(pergunta,False)
        erros_controle+=int(on["ativacao"] is not None)
        resultados.append({"id":"C%02d"%i,"tipo":"controle","pergunta":pergunta,
                          "ligado":on,"desligado":off,
                          "acionamento_indevido":on["ativacao"] is not None})
    resumo={"prova":"cortex-prospectivo-v2",
            "prototipo":"cortex 77a9399 antes da publicacao dos itens",
            "positivos":len(POSITIVOS_V2),"controles":len(CONTROLES_V2),
            "acertos_com_cortex":acertos_on,"acertos_sem_cortex":acertos_off,
            "ativacoes_em_positivos":ativacoes,
            "ativacoes_indevidas_em_controles":erros_controle,
            "sem_perguntas_iguais_a_treino_v1_ab":True,
            "criterio":"ID factual na evidencia + texto e URL; nao interpreta livremente",
            "sem_treinamento":True}
    destino=ROOT/"resultado_cortex_prospectivo_v2.json"
    destino.write_text(json.dumps({"resumo":resumo,"casos":resultados},
                                  ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(resumo,ensure_ascii=False,indent=2),flush=True)
    print("FALHAS",json.dumps([x["id"] for x in resultados if x["tipo"]=="positivo" and not x["acerto_ligado"]],ensure_ascii=False),flush=True)
    print("CONTROLES",json.dumps([x["id"] for x in resultados if x["tipo"]=="controle" and x["acionamento_indevido"]],ensure_ascii=False),flush=True)
    print("RELATORIO",str(destino),flush=True)

if __name__=="__main__":
    principal()
