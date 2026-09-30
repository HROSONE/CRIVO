"""Gera a bateria autoral versionada. Não consulta respostas do chatbot.

Não é chamado no treino. A saída publicada permite auditoria dos rótulos.
As famílias finais foram escritas pelos mesmos autores: avaliação interna,
sem alegação de teste humano independente ou cegueira do desenvolvedor.
"""
import json
from pathlib import Path

TEMAS = [
    ("neurônio", "mundo_neuronio", "célula nervosa"),
    ("sinapse", "mundo_sinapse", "comunicação"),
    ("memória", "mundo_memoria", "recuperar"),
    ("hipocampo", "mundo_hipocampo", "memórias"),
    ("DNA", "dna", "genética"),
    ("RNA", "rna", "genética"),
    ("Andrômeda", "andromeda", "galáxia"),
    ("gravidade", "gravidade", "massa"),
    ("internet", "internet", "redes"),
    ("neuroplasticidade", "mundo_neuroplasticidade", "conexões"),
]

FAMILIAS = [
    ("direta", "O que é {alvo}?", "definir", ""),
    ("imperativo", "Defina {alvo}.", "definir", ""),
    ("explica", "Me explica o que é {alvo}.", "definir", ""),
    ("desejo", "Eu quero entender {alvo}.", "definir", ""),
    ("significado", "O que significa {alvo}?", "definir", ""),
    ("invertida", "{alvo} é o quê?", "definir", ""),
    ("gentileza", "Por favor, me diga o que seria {alvo}.", "definir", ""),
    ("curiosidade", "Eu queria saber o que é {alvo}.", "definir", ""),
    ("falar", "Fale sobre {alvo}.", "definir", ""),
    ("desconhecimento", "Não sei o que é {alvo}.", "definir", ""),
    ("sem_entender", "Não entendi o significado de {alvo}.", "definir", ""),
    ("duvida_nome", "Tenho uma dúvida: o que é {alvo}?", "definir", ""),
    ("pergunta_nome", "Minha pergunta é: o que significa {alvo}?", "definir", ""),
    ("gostaria", "Gostaria de uma explicação sobre {alvo}.", "definir", ""),
    ("nega_ordem", "Não me explique {alvo}.", "negado", ""),
    ("nega_frontal", "Sobre {alvo}, não quero uma explicação.", "negado", ""),
    ("qualificador", "O que é {alvo} alienígena?", "definir", " alienígena"),
    ("condicional", "Defina {alvo} se tiver memória infinita.", "definir", " se tiver memória infinita"),
    ("valid_ajuda", "Me ajuda a entender o que é {alvo}.", "definir", ""),
    ("valid_termo", "Esse termo, {alvo}, quer dizer o quê?", "definir", ""),
    ("valid_sei", "Eu não faço ideia do que é {alvo}.", "definir", ""),
    ("valid_negar", "Eu não pedi para você explicar {alvo}.", "negado", ""),
    ("valid_qualificador", "Você pode definir {alvo} quântico inventado?", "definir", " quântico inventado"),
    ("valid_erro", "Me esplique o que é {alvo}.", "definir", ""),
    ("teste_duvida", "Tô com uma dúvida sobre {alvo}: o que isso significa?", "definir", ""),
    ("teste_compreender", "Preciso compreender o significado de {alvo}.", "definir", ""),
    ("teste_nome", "O nome {alvo} significa o quê, afinal?", "definir", ""),
    ("teste_negar", "Uma definição de {alvo} não é o que eu pedi.", "negado", ""),
    ("teste_qualificador", "Me conte o que é {alvo} de outro universo desconhecido.", "definir", " de outro universo desconhecido"),
    ("teste_digitacao", "Queria uma esplicação sobre {alvo}.", "definir", ""),
]


def gerar():
    perguntas, dialogos = [], []
    for k, (nome, modelo, ato, sufixo) in enumerate(FAMILIAS):
        split = "treino" if k < 18 else "validacao" if k < 24 else "teste"
        for j, (alvo, ident, trecho) in enumerate(TEMAS):
            texto = modelo.format(alvo=alvo)
            a = texto.index(alvo)
            span = [a, a + len(alvo + sufixo)]
            esperado = {"abster": True} if ato == "negado" or sufixo else {
                "ids": ["conhecimento:" + ident], "trechos": [trecho]}
            perguntas.append(dict(id="q%02d_%02d" % (k, j), familia=nome, split=split,
                                  texto=texto, quadro={"ato": ato, "alvo": alvo + sufixo,
                                  "span": span, "negacao_pedido": ato == "negado",
                                  "condicao": "se tiver memória infinita" if k == 17 else ""},
                                  esperado=esperado))
    for familia in range(6):
        split = "treino" if familia < 3 else "validacao" if familia < 5 else "teste"
        for j, (alvo, ident, trecho) in enumerate(TEMAS):
            direto = {"ids": ["conhecimento:" + ident], "trechos": [trecho]}
            turnos = [{"texto": "O que é " + alvo + "?", "esperado": direto}]
            if familia == 0:
                turnos += [{"texto": "Fale a mesma coisa com outras palavras", "esperado": {
                    "ids": ["escrita:reformulacao"], "trechos": [trecho]}}]
            elif familia == 1:
                turnos += [{"texto": "Mais curto", "esperado": {"ids": ["escrita:resumo"]}},
                           {"texto": "Qual é a fonte?", "esperado": {"ids": ["escrita:fontes"], "trechos": ["https://"]}}]
            elif familia == 2:
                turnos += [{"texto": "Oi!", "esperado": {"ids": ["social:saudacao"]}},
                           {"texto": "Retome " + alvo, "esperado": {"ids": ["escrita:retomada"], "trechos": [trecho]}}]
            elif familia == 3:
                turnos += [{"texto": "Pode explicar sem palavras difíceis?", "esperado": {
                    "ids": ["escrita:simples"]}},
                           {"texto": "Organize em tópicos", "esperado": {"ids": ["escrita:topicos"]}},
                           {"texto": "De onde veio essa informação?", "esperado": {"ids": ["escrita:fontes"], "trechos": ["https://"]}}]
            elif familia == 4:
                outro, outro_id, outro_trecho = TEMAS[(j + 1) % len(TEMAS)]
                turnos += [{"texto": "O que é " + outro + "?", "esperado": {
                    "ids": ["conhecimento:" + outro_id], "trechos": [outro_trecho]}},
                           {"texto": "Vamos voltar à " + alvo, "esperado": {
                    "ids": ["escrita:retomada"], "trechos": [trecho]}}]
            else:
                turnos += [{"texto": "Mudar de assunto", "esperado": {"ids": ["conversa:reinicio"]}},
                           {"texto": "Retome " + alvo, "esperado": {"abster": True}},
                           {"texto": "O que é " + alvo + "?", "esperado": direto},
                           {"texto": "Fala de outro jeito", "esperado": {"ids": ["escrita:reformulacao"]}}]
            dialogos.append(dict(id="d%d_%02d" % (familia, j), familia="dialogo_%d" % familia,
                                 split=split, turnos=turnos))
    return dict(versao=1, revisao=2,
                nota_oraculo="Revisão 2 corrige o trecho de gravidade: massa, presente no fato; a forma verbal atrai não contém a palavra atração. A referência é recalculada com o mesmo oráculo.",
                origem="Autoral, português brasileiro; fontes factuais já cadastradas.",
                politica="300 perguntas / 30 famílias e 60 diálogos / 6 famílias. Separação por família, sem avaliação externa cega. Trechos e IDs vêm do currículo, nunca das respostas medidas.",
                perguntas=perguntas, dialogos=dialogos)


if __name__ == "__main__":
    destino = Path(__file__).resolve().parents[1] / "benchmark_generalizacao.json"
    destino.write_text(json.dumps(gerar(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
