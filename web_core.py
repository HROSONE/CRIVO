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


def responder_web(payload):
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

    bot = Crivo()
    for anterior in historico:
        bot.responder(anterior)
    identificador, resposta = bot.responder(mensagem)
    mecanismo = "recuperador"
    if bot.historico and bot.historico[-1].get("pergunta") == mensagem:
        mecanismo = bot.historico[-1].get("mecanismo", "recuperador")
    if identificador.startswith("logica:") and mecanismo == "recuperador":
        mecanismo = "raciocinio_relacional"
    return {
        "id": identificador,
        "response": resposta,
        "mechanism": mecanismo,
        "neural_active": bot.rede is not None,
        "has_proof": identificador.startswith("logica:") or
                     "Relações verificadas:" in resposta,
    }
