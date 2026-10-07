"""O CRIVO como ecossistema: cada mecanismo é uma espécie com papel e contrapeso.

Na natureza, nada se sustenta sozinho: o CO₂ em excesso é absorvido pelas
árvores, os predadores regulam as presas e os decompositores devolvem ao solo
o que sobra. Aqui vale o mesmo. Cada mecanismo que pode responder no chat
declara:

  papel       o que ele faz;
  nicho       quando entra na conversa;
  alimento    os recursos de que depende (acervo, pesos, grafos);
  regulado    quem corrige o excesso dele (outras espécies ou reguladores);
  guardioes   os testes que medem a saúde dele.

``testes_ecossistema.py`` garante que nenhum mecanismo responde sem estar
neste mapa, que toda espécie tem pelo menos um contrapeso e um guardião, e
que as referências apontam para coisas que existem.
"""
from collections import namedtuple
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

Especie = namedtuple("Especie", "nome reino papel nicho alimento regulado guardioes")

# Reguladores que não são mecanismos de resposta, mas equilibram todos eles.
REGULADORES = {
    "crise": "Detecta risco à vida antes de qualquer resposta e passa na frente de todas as espécies.",
    "fontes": "Toda afirmação de conhecimento sai de uma entrada com fonte; sem fonte, não há resposta.",
    "catracas": "Testes congelados e conjuntos retidos: uma mudança que piora o agregado não entra.",
    "estado_conversa": "Guarda objetivos, preferências e restrições e ajusta a resposta ao que a pessoa disse.",
    "pessoa": "A confirmação ou correção de quem conversa: um “não” desfaz uma suposição.",
    "recusa": "Dizer “não sei” quando nada no acervo sustenta a resposta, em vez de inventar.",
}

REINOS = {
    "conhecimento": "Acervo editorial e catálogos com fontes: a memória de longo prazo.",
    "raciocinio": "Inferência sobre relações comprováveis: liga fatos sem inventar novos.",
    "linguagem": "Leitura da forma do português: frases, pedidos e ambiguidades.",
    "conversa": "Ritmo social, memória do diálogo e cuidado com a pessoa.",
    "neural": "Redes treinadas do zero: flexíveis com formulações novas, mas propensas a errar com confiança.",
    "programacao": "Código: explicar, analisar e executar com rastreio.",
}

_LISTA = (
    # --- conhecimento -------------------------------------------------------
    Especie("recuperador", "conhecimento",
            "Encontra a entrada editorial mais próxima da pergunta pelas palavras.",
            "Quando nenhuma espécie mais específica respondeu.",
            ("conhecimento.json",),
            ("compreensao_neural", "fontes", "recusa", "catracas"),
            ("testes_bateria.py", "testes_assunto_tom.py")),
    Especie("lista_editorial", "conhecimento",
            "Responde consultas de lista quando exatamente uma lista editorial cobre o pedido.",
            "Pedidos de enumeração (“quais são os planetas”).",
            ("conhecimento.json",),
            ("consulta_relacional", "fontes"),
            ("testes_consultas_relacionais.py",)),
    Especie("consulta_pratica", "conhecimento",
            "Dá orientação prática do dia a dia quando o recuperador não entendeu.",
            "Depois de uma recusa do recuperador, em pedidos práticos.",
            ("conhecimento.json",),
            ("recusa", "estado_conversa", "catracas"),
            ("testes_compreensao_intencao.py",)),
    Especie("conhecimento_frutas", "conhecimento",
            "Responde sobre frutas a partir de uma tabela estruturada.",
            "Perguntas que citam frutas e seus atributos.",
            ("frutas.py",),
            ("fontes", "recusa"),
            ("testes_frutas.py", "testes_relacoes_frutas.py")),
    Especie("busca_factual", "conhecimento",
            "Procura um fato documentado que trate exatamente da pergunta.",
            "Quando o raciocínio não acha relação, mas um fato do acervo pode responder.",
            ("conhecimento.json", "relacoes.json"),
            ("raciocinio_relacional", "fontes", "recusa"),
            ("testes_busca_factual.py",)),
    Especie("composicao_factual", "conhecimento",
            "Compõe a resposta a partir das fichas dos conceitos e dos catálogos; a voz própria "
            "(voz.py) dá forma de conversa à composição pura de um assunto.",
            "Perguntas sobre conceitos com ficha (pessoas, história, ciência).",
            ("curriculo_mundo.py", "composicao_textual.py", "voz.py", "artefatos/voz_pt"),
            ("fontes", "recusa", "catracas"),
            ("testes_composicao_textual.py", "testes_conhecimento_mundo.py", "testes_voz.py")),
    Especie("composicao_definicional", "conhecimento",
            "Monta uma definição a partir de partes já documentadas.",
            "“O que é X?” quando X não tem entrada própria, mas as partes têm.",
            ("conhecimento.json",),
            ("fontes", "recusa"),
            ("testes_intencao_definicao.py", "testes_definicoes_genericas.py")),
    # --- raciocinio ---------------------------------------------------------
    Especie("raciocinio_relacional", "raciocinio",
            "Prova relações (tipo de, parte de, órbita) sobre o grafo de fatos.",
            "Perguntas de relação entre entidades conhecidas.",
            ("relacoes.json", "raciocinio.py"),
            ("busca_factual", "recusa", "catracas"),
            ("testes_raciocinio.py", "testes_regras_mistas.py")),
    Especie("raciocinio_e_base", "raciocinio",
            "Junta uma prova do grafo à entrada editorial que a explica.",
            "Quando a relação comprovada tem uma fonte editorial explícita.",
            ("relacoes.json", "conhecimento.json"),
            ("fontes", "raciocinio_relacional"),
            ("testes_raciocinio.py",)),
    Especie("consulta_relacional", "raciocinio",
            "Responde consultas estruturadas (filtros, conjunções) sobre fatos.",
            "Perguntas com condições (“quais planetas têm anéis e luas”).",
            ("relacoes.json", "consultas_relacionais.py"),
            ("recusa", "catracas"),
            ("testes_consultas_relacionais.py",)),
    Especie("raciocinio_ativo", "raciocinio",
            "Raciocina passo a passo sobre o problema que a pessoa descreve.",
            "Pedidos de investigação ou cálculo dentro da conversa.",
            ("raciocinio_ativo.py",),
            ("estado_conversa", "pessoa", "catracas"),
            ("testes_raciocinio_ativo.py", "testes_integracao_raciocinio_ativo.py")),
    Especie("exploracao_conhecimento", "raciocinio",
            "Percorre o acervo para mostrar ligações entre assuntos.",
            "Pedidos de exploração (“o que isso tem a ver com…”).",
            ("conhecimento.json", "exploracao_conhecimento.py"),
            ("fontes", "recusa"),
            ("testes_exploracao_conhecimento.py",)),
    # --- linguagem ----------------------------------------------------------
    Especie("compreensao_textual", "linguagem",
            "Lê textos colados pela pessoa e responde sobre eles.",
            "Quando a conversa traz um texto para interpretar.",
            ("compreensao_textual.py",),
            ("recusa", "catracas"),
            ("testes_compreensao_textual.py",)),
    Especie("interpretacao_geral", "linguagem",
            "Interpreta pedidos gerais pela estrutura da frase.",
            "Frases que as regras específicas não cobrem, antes do recuperador.",
            ("interpretacao_geral.py",),
            ("recusa", "catracas"),
            ("testes_interpretacao_geral.py",)),
    Especie("interpretacao_pedido", "linguagem",
            "Separa pedidos compostos e resolve cada parte.",
            "Mensagens com mais de um pedido.",
            ("interpretacao_pedidos.py",),
            ("estado_conversa", "catracas"),
            ("testes_interpretacao_pedidos.py",)),
    Especie("analise_portugues", "linguagem",
            "Analisa a gramática do português e responde pela estrutura.",
            "Depois das regras exatas, quando a frase tem estrutura reconhecível.",
            ("analisador_portugues.py",),
            ("fontes", "recusa"),
            ("testes_analisador_portugues.py",)),
    # --- conversa -----------------------------------------------------------
    Especie("conversa_assistente", "conversa",
            "Cuida da parte social: cumprimentos, agradecimentos e o próprio CRIVO.",
            "Falas sociais e perguntas sobre o assistente.",
            ("conversa_assistente.py",),
            ("crise", "estado_conversa"),
            ("testes_autoconversa.py", "testes_conversa_informal.py")),
    Especie("linguagem_conversa", "conversa",
            "Reage a relatos do dia a dia com o tom certo.",
            "Quando a pessoa conta algo que aconteceu.",
            ("linguagem_conversa.py",),
            ("crise", "estado_conversa", "catracas"),
            ("testes_linguagem_conversa.py", "testes_assunto_tom.py")),
    Especie("memoria_relatos", "conversa",
            "Lembra o que a pessoa contou e responde sobre isso.",
            "Perguntas sobre algo dito antes na conversa.",
            ("investigacao_memoria.py",),
            ("pessoa", "estado_conversa"),
            ("testes_memoria_navegador.py",)),
    Especie("nocao", "conversa",
            "Reconhece noções vagas e pede o que falta, sem supor.",
            "Falas ambíguas que dependem de uma suposição.",
            ("nocoes.py",),
            ("pessoa", "recusa"),
            ("testes_conversa_nocoes.py",)),
    # --- neural -------------------------------------------------------------
    Especie("compreensao_neural", "neural",
            "Reconhece o assunto de formulações novas e pergunta se entendeu.",
            "Só quando as regras dizem “não entendi”, e nunca com negação.",
            ("artefatos/entendimento_pt", "entendimento_neural.py"),
            ("pessoa", "recusa", "catracas"),
            ("testes_entendimento_neural.py",)),
    Especie("leitura_ficha", "neural",
            "Lê a ficha do conceito citado e propõe o fato que responde, com a probabilidade "
            "de um modelo treinado com perguntas do tutor; o árbitro do estado interno decide.",
            "Quando a espécie que respondeu recusou, a pergunta cita um único conceito com ficha "
            "e não há negação, relação entre conceitos nem pedido de escrita.",
            ("leitura_ficha.py", "estado_interno.py", "artefatos/leitura_ficha",
             "dados/relacoes_pergunta_fato.json"),
            ("fontes", "recusa", "catracas"),
            ("testes_leitura_ficha.py", "testes_bateria.py")),
    Especie("busca_aprendida", "neural",
            "Procura no acervo inteiro o fato que responde, pesando evidências (palavras, sentido, "
            "tipo de pergunta e aspecto) com pesos aprendidos, mais a proximidade de sentido dada pelo "
            "Transformer próprio (codificador_sentido.py); a leitura da ficha confirma.",
            "Quando a espécie que respondeu recusou e a pergunta não cita o nome de nenhum "
            "conceito; só afirma se a busca e a leitura apontam o mesmo fato.",
            ("busca_semantica.py", "estado_interno.py", "artefatos/busca_semantica",
             "codificador_sentido.py", "artefatos/sentido_pt"),
            ("fontes", "recusa", "catracas"),
            ("testes_busca_semantica.py", "testes_bateria.py", "testes_codificador_sentido.py")),
    Especie("geracao_ancorada", "neural",
            "Escreve a resposta com o Transformer próprio a partir das evidências escolhidas pelo "
            "leitor/compositor; decodificação restrita aos tokens da fonte e da pergunta e guarda de fidelidade, "
            "números, nome próprio e repetição.",
            "No CRIVO, API e servidor local, em perguntas factuais e composição de evidências "
            "selecionadas (resumo, tópicos, continuação e comparação). Recusas e respostas "
            "incertas preservam seu limite; a redação conserva toda a evidência. Recuos "
            "têm diagnóstico explícito.",
            ("geracao_ancorada.py", "artefatos/geracao_pt"),
            ("fontes", "recusa", "catracas"),
            ("testes_geracao_ancorada.py",)),
    Especie("geracao_neural", "neural",
            "Escreve respostas com o gerador próprio (desligado por padrão).",
            "Só em modo experimental, quando ligado explicitamente.",
            ("geracao_conversa.py",),
            ("catracas", "fontes"),
            ("testes_geracao.py",)),
    Especie("dialogo_contextual_neural", "neural",
            "Continua a conversa com o modelo contextual (desligado por padrão).",
            "Só em modo experimental, quando ligado explicitamente.",
            ("dialogo_contextual.py",),
            ("catracas", "estado_conversa"),
            ("testes_dialogo_contextual.py",)),
    Especie("programacao_neural_experimental", "neural",
            "Gera código com o modelo próprio (desligado por padrão).",
            "Só em modo experimental, quando ligado explicitamente.",
            ("programacao_neural.py",),
            ("motor_programacao_proprio", "catracas"),
            ("testes_programacao_profunda.py",)),
    # --- programacao --------------------------------------------------------
    Especie("motor_programacao_proprio", "programacao",
            "Analisa e executa código com rastreio, sem modelo externo.",
            "Pedidos com código ou sobre um programa.",
            ("programacao_chat.py", "execucao_rastreada.py"),
            ("catracas", "recusa"),
            ("testes_motor_programacao_chat.py",)),
    Especie("conhecimento_programacao", "programacao",
            "Explica conceitos de programação a partir do acervo técnico.",
            "Perguntas conceituais sobre linguagens e técnicas.",
            ("conhecimento_programacao.py",),
            ("fontes", "recusa"),
            ("testes_programacao_profunda.py",)),
)

ESPECIES = {e.nome: e for e in _LISTA}


def especie(mecanismo):
    """A espécie de um mecanismo, ou None se ele não estiver no mapa."""
    return ESPECIES.get(mecanismo)


def mecanismo_do_turno(bot, fala, ident):
    """A espécie que respondeu à última fala de um Crivo."""
    mecanismo = "recuperador"
    if bot.historico and bot.historico[-1].get("pergunta") == fala:
        mecanismo = bot.historico[-1].get("mecanismo", "recuperador")
    if ident.startswith("logica:") and mecanismo == "recuperador":
        mecanismo = "raciocinio_relacional"
    return mecanismo


def descrever(mecanismo):
    """Resumo público da espécie que respondeu, para a API."""
    e = ESPECIES.get(mecanismo)
    if e is None:
        return None
    return {"species": e.nome, "kingdom": e.reino, "role": e.papel, "regulated_by": list(e.regulado)}


def problemas():
    """Lista de incoerências no mapa (vazia quando o ecossistema está íntegro)."""
    saida = []
    for e in _LISTA:
        if e.reino not in REINOS:
            saida.append("%s: reino desconhecido %s" % (e.nome, e.reino))
        if not e.regulado:
            saida.append("%s: nenhuma espécie age sozinha, falta contrapeso" % e.nome)
        for r in e.regulado:
            if r == e.nome:
                saida.append("%s: não pode ser o próprio contrapeso" % e.nome)
            elif r not in ESPECIES and r not in REGULADORES:
                saida.append("%s: contrapeso desconhecido %s" % (e.nome, r))
        if not e.guardioes:
            saida.append("%s: sem guardião" % e.nome)
        for caminho in e.guardioes + e.alimento:
            if not (RAIZ / caminho).exists():
                saida.append("%s: %s não existe" % (e.nome, caminho))
    if len(ESPECIES) != len(_LISTA):
        saida.append("nomes de espécie repetidos")
    return saida


def teia():
    """Quem regula quem: {regulador: [espécies que ele equilibra]}."""
    saida = {}
    for e in _LISTA:
        for r in e.regulado:
            saida.setdefault(r, []).append(e.nome)
    return saida


if __name__ == "__main__":
    import json
    print(json.dumps({"especies": len(ESPECIES), "reinos": sorted({e.reino for e in _LISTA}),
                      "problemas": problemas(), "teia": teia()}, ensure_ascii=False, indent=1))
