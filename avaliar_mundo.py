"""Sonda pública de conhecimento do mundo, separada dos exemplos do treino.

Verifica o chatbot híbrido e a seleção de evidências, não inteligência geral
nem acurácia da rede isolada. É uma sonda de desenvolvimento, não teste cego.
"""
import json
from crivo import Crivo


CASOS = [
    ([], "Defina uma célula nervosa.", "conhecimento:mundo_neuronio", ["célula nervosa", "sinais"]),
    ([], "O que significa sinapse?", "conhecimento:mundo_sinapse", ["comunicação", "neurotransmissores"]),
    ([], "Você conhece o hipocampo?", "conhecimento:mundo_hipocampo", ["memórias", "formação"]),
    ([], "Defina memória explícita.", "conhecimento:mundo_memoria_declarativa", ["fatos", "acontecimentos"]),
    ([], "O que é memória processual?", "conhecimento:mundo_memoria_procedural", ["habilidades", "bicicleta"]),
    ([], "O que significa plasticidade cerebral?", "conhecimento:mundo_neuroplasticidade", ["conexões", "experiências"]),
    ([], "O que é o método de loci?", "conhecimento:mundo_mnemonica", ["associação", "percurso"]),
    ([], "O que é sono NREM?", "conhecimento:mundo_sono_nao_rem", ["três", "estágios"]),
    ([], "O que significa falta de sono?", "conhecimento:mundo_privacao_sono", ["atenção", "aprendizagem"]),
    ([], "O que é relógio biológico?", "conhecimento:mundo_ritmo_circadiano", ["24 horas", "luz"]),
    ([], "Defina ansiedade social.", "conhecimento:mundo_ansiedade_social", ["medo", "avaliado"]),
    ([], "O que é crise de pânico?", "conhecimento:mundo_ataque_panico", ["súbito", "palpitações"]),
    ([], "O que é diversidade biológica?", "conhecimento:mundo_biodiversidade", ["espécies", "ecossistemas"]),
    ([], "O que são constelações?", "conhecimento:mundo_constelacao", ["região", "88"]),
    ([], "Qual é a função da membrana plasmática?", "escrita:explicacao", ["passagem", "comunicação"]),
    ([], "Como funcionam ribossomos?", "escrita:explicacao", ["proteínas", "RNA"]),
    ([], "Para que serve clorofila?", "escrita:explicacao", ["energia solar", "alimento"]),
    ([], "Como funciona o sono não REM?", "escrita:explicacao", ["três", "profundo"]),
    ([], "Como funciona a ecolocalização do morcego?", "escrita:explicacao", ["ecos", "objetos"]),
    ([], "Como funcionam os pés da lagartixa?", "escrita:explicacao", ["cerdas", "van der Waals"]),
    ([], "Dê um exemplo de memória procedural.", "escrita:explicacao", ["bicicleta"]),
    ([], "Por que o sono favorece a memória?", "escrita:relacao", ["consolidação"]),
    ([], "Como o hipocampo participa da memória?", "escrita:relacao", ["formação", "aprendidas"]),
    ([], "Como a evaporação faz parte do ciclo hidrológico?", "escrita:relacao", ["vapor", "atmosfera"]),
    ([], "Como a procrastinação se associa ao stress?", "escrita:relacao", ["transversal", "não estabelece causalidade"]),
    ([], "Como a clorofila absorve a luz solar?", "escrita:relacao", ["absorve", "produção"]),
    ([], "Por que a energia solar sustenta a fotossíntese?", "escrita:relacao", ["fotossíntese"]),
    ([], "O que diferencia neurônio de sinapse?", "escrita:comparacao", ["célula", "conexão"]),
    ([], "Compare memória processual com memória explícita.", "escrita:comparacao", ["fatos", "habilidades"]),
    ([], "Qual a diferença entre stress e ansiedade?", "escrita:comparacao", ["externo", "ameaça"]),
    ([], "Compare sono NREM com sono REM.", "escrita:comparacao", ["três", "olhos"]),
    ([], "Qual a diferença entre ansiedade e transtorno de ansiedade?", "escrita:comparacao", ["ocasional", "prejuízo"]),
    ([], "O que diferencia tristeza de depressão?", "escrita:comparacao", ["persistência", "passageira"]),
    ([], "Crie um resumo sobre memória e biodiversidade.", "escrita:resumo", ["recuperar", "ecossistemas"]),
    ([], "Escreva um texto sobre sinapse e DNA.", "escrita:texto", ["sinapse", "DNA"]),
    (["O que é melatonina?"], "Como funciona ela?", "escrita:explicacao", ["luz", "escuridão"]),
    (["O que é ribossomo?"], "Mais curto", "escrita:resumo", ["aminoácidos"]),
    (["O que é depressão?"], "Qual é a fonte?", "escrita:fontes", ["nimh.nih.gov", "National Institute of Mental Health", "2024"]),
    (["Como funciona o sono NREM?"], "Quais são as fontes?", "escrita:fontes", ["nhlbi.nih.gov"]),
    ([], "Qual é a fonte da ecolocalização?", "escrita:fontes", ["nps.gov", "consulta 2026"]),
    ([], "Dê um exemplo de biomimética.", "escrita:explicacao", ["lagartixa", "materiais"]),
    ([], "Por que a memória ajuda o sono?", "fora", ["evidência"]),
    ([], "Como o sono não ajuda a memória?", "fora", ["evidência"]),
    ([], "Como o sono ajuda a memória alienígena?", "fora", ["evidência"]),
    ([], "Por que sono cura depressão?", "fora", ["evidência"]),
    ([], "Qual é a dose de melatonina para mim?", "fora", ["dose", "pessoa"]),
    ([], "Faça meu diagnóstico de transtorno de ansiedade.", "fora", ["diagnóstico"]),
    ([], "Compare ansiedade com cristal quântico inventado.", "fora", ["evidência"]),
    ([], "Escreva um texto sobre a memória de um alienígena.", "fora", ["conhecimento suficiente"]),
    ([], "Como o cérebro tem memória infinita?", "fora", ["evidência"]),
    (["O que é memória?", "Oi!"], "Qual é a fonte?", "duvida", ["anterior"]),
]


def executar(caso):
    historico, pergunta, esperado, trechos = caso
    bot = Crivo()
    for anterior in historico:
        bot.responder(anterior)
    ident, resposta = bot.responder(pergunta)
    return dict(pergunta=pergunta, historico=historico, esperado=esperado,
                obtido=ident, passou=ident == esperado and all(t in resposta for t in trechos),
                resposta=resposta)


def avaliar():
    resultados = [executar(caso) for caso in CASOS]
    bot = Crivo()
    rede = None
    if bot.rede is not None and bot.curriculo_mundo is not None:
        casos_rede = []
        for item in bot.curriculo_mundo['itens']:
            pergunta = 'Defina ' + item['nome']
            obtido, confianca = bot.previsao_neural(pergunta)
            casos_rede.append(dict(pergunta=pergunta, esperado=item['id'], obtido=obtido,
                                  confianca=round(confianca, 6), passou=obtido == item['id']))
        rede = dict(total=len(casos_rede), acertos=sum(r['passou'] for r in casos_rede),
                    criterio='ID exato do classificador isolado; não avalia a resposta factual.',
                    casos=casos_rede)
    return dict(total=len(resultados), acertos=sum(r['passou'] for r in resultados),
                limite=__doc__.strip(), casos=resultados, classificador_isolado=rede)


if __name__ == '__main__':
    resultado = avaliar()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    raise SystemExit(0 if resultado['acertos'] == resultado['total'] else 1)
