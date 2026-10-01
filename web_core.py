"""Adaptador HTTP sem estado para conversar com o CRIVO original.

Nenhum serviço de IA, chave, banco de dados ou pacote externo é necessário.
O navegador manda apenas perguntas anteriores (limitadas) para reconstruir
o contexto curto. A resposta do servidor não armazena conversas.
"""
from crivo import Crivo

LIMITE_MENSAGEM = 1200
LIMITE_HISTORICO = 10


class PedidoInvalido(ValueError):
    """Entrada inválida: o endpoint pode responder HTTP 400."""


def responder_web(payload, usar_dialogo_contextual=False, modelo_linguagem=None):
    """Valida o contrato JSON e devolve um resultado serializável.

    Em ambientes serverless os processos podem reiniciar entre mensagens;
    por isso reconstruímos o estado conversacional a partir de mensagens
    anteriores, sem confiar em IDs enviados pelo cliente.
    """
    if not isinstance(payload, dict):
        raise PedidoInvalido("Envie um objeto JSON.")
    if set(payload) - {"message", "history"}:
        raise PedidoInvalido("Campos não reconhecidos no pedido.")
    mensagem = payload.get("message")
    historico = payload.get("history", [])
    if (not isinstance(mensagem, str) or
            not 1 <= len(mensagem.strip()) <= LIMITE_MENSAGEM or
            "\x00" in mensagem):
        raise PedidoInvalido("A pergunta deve ter entre 1 e 1200 caracteres.")
    if (not isinstance(historico, list) or len(historico) > LIMITE_HISTORICO
            or any(not isinstance(p, str) or
                   not 1 <= len(p.strip()) <= LIMITE_MENSAGEM or
                   "\x00" in p for p in historico)):
        raise PedidoInvalido("Histórico inválido ou muito longo.")

    bot = Crivo(usar_dialogo_contextual=usar_dialogo_contextual, modelo_linguagem=modelo_linguagem)
    for anterior in historico:
        bot.responder(anterior)
    identificador, resposta = bot.responder(mensagem)
    mecanismo = "recuperador"
    if bot.historico and bot.historico[-1].get("pergunta") == mensagem:
        mecanismo = bot.historico[-1].get("mecanismo", "recuperador")
    if identificador.startswith("logica:") and mecanismo == "recuperador":
        mecanismo = "raciocinio_relacional"
    provas_efetivas = {
        "logica:fatos",
        "logica:tipo_de", "logica:parte_de", "logica:orbita",
        "logica:tem_caracteristica", "logica:negacao_comprovada",
        "logica:hipotese", "logica:comum", "logica:ligacao",
        "logica:caracteristicas",
        "logica:consulta", "logica:conjuncao", "logica:conjuncao_falsa",
        "logica:consulta_impossivel",
    }
    # Proveniência criada pelo motor durante o replay, jamais pelo cliente.
    origem = (bot.ultimo_turno or {}).get("prova_origem", "")
    ids_editoriais = {e["id"] for e in bot.base}
    prova_editorial = (identificador in ids_editoriais or origem in ids_editoriais)
    provas_plano = (bot.contexto_textual.provas if bot.contexto_textual is not None else ())
    prova_planejada = any((i in provas_efetivas or i in ids_editoriais and "Relações verificadas:" in t)
                         and t in resposta for i,t in provas_plano)
    return {
        "id": identificador,
        "response": resposta,
        "mechanism": mecanismo,
        "neural_active": bot.rede is not None,
        "plan": bot.planejador.ultimo,
        "experimental_dialogue": usar_dialogo_contextual or bool(modelo_linguagem),
        # Uma resposta "não encontrei relação" NÃO é uma prova lógica.
        "has_proof": (identificador in provas_efetivas or origem in provas_efetivas or
                      prova_editorial and "Relações verificadas:" in resposta or prova_planejada),
    }
