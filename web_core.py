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


TONS = ("pos", "neg", "saude", "luto", "neutro")


def _texto_curto(valor, limite):
    return isinstance(valor, str) and 0 < len(valor.strip()) <= limite and "\x00" not in valor


def _validar_memoria(memoria):
    """Memória entre conversas, guardada SÓ no navegador de quem optou por
    ela e reenviada a cada pedido. O servidor valida, usa e devolve a versão
    atualizada; não guarda nada."""
    if not isinstance(memoria, dict) or set(memoria) - {"nome", "nomes", "relatos", "temas"}:
        raise PedidoInvalido("Memória inválida.")
    limpa = {}
    if "nome" in memoria:
        if not _texto_curto(memoria["nome"], 40):
            raise PedidoInvalido("Memória inválida.")
        limpa["nome"] = memoria["nome"].strip()
    nomes = memoria.get("nomes", {})
    if (not isinstance(nomes, dict) or len(nomes) > 10
            or not all(_texto_curto(k, 40) and _texto_curto(v, 40) for k, v in nomes.items())):
        raise PedidoInvalido("Memória inválida.")
    limpa["nomes"] = dict(nomes)
    relatos = memoria.get("relatos", [])
    if (not isinstance(relatos, list) or len(relatos) > 8
            or not all(_texto_curto(r, 300) for r in relatos)):
        raise PedidoInvalido("Memória inválida.")
    limpa["relatos"] = list(relatos)
    temas = memoria.get("temas", [])
    if (not isinstance(temas, list) or len(temas) > 6 or not all(
            isinstance(t, list) and len(t) == 3 and _texto_curto(t[0], 40) and t[1] in TONS
            and isinstance(t[2], str) and len(t[2]) <= 60 for t in temas)):
        raise PedidoInvalido("Memória inválida.")
    limpa["temas"] = [list(t) for t in temas]
    return limpa


def responder_web(payload, usar_dialogo_contextual=False, modelo_linguagem=None, gerador_programacao=None):
    """Valida o contrato JSON e devolve um resultado serializável.

    Em ambientes serverless os processos podem reiniciar entre mensagens;
    por isso reconstruímos o estado conversacional a partir de mensagens
    anteriores, sem confiar em IDs enviados pelo cliente.
    """
    if not isinstance(payload, dict):
        raise PedidoInvalido("Envie um objeto JSON.")
    if set(payload) - {"message", "history", "memory"}:
        raise PedidoInvalido("Campos não reconhecidos no pedido.")
    memoria = _validar_memoria(payload["memory"]) if "memory" in payload else None
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

    bot = Crivo(usar_dialogo_contextual=usar_dialogo_contextual, modelo_linguagem=modelo_linguagem, gerador_programacao=gerador_programacao)
    if memoria:
        bot.carregar_memoria(memoria)
    bot.motor_codigo.reconstruindo = True
    try:
        for anterior in historico:
            bot.responder(anterior)
    finally:
        bot.motor_codigo.reconstruindo = False
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
    extra = {"memory": bot.exportar_memoria()} if memoria is not None else {}
    return {
        **extra,
        **({"code_analysis": bot.motor_codigo.ultimo} if bot.motor_codigo.ultimo is not None else {}),
        "id": identificador,
        "response": resposta,
        "mechanism": mecanismo,
        "neural_active": bot.rede is not None,
        "plan": bot.planejador.ultimo,
        "experimental_dialogue": usar_dialogo_contextual or bool(modelo_linguagem),
        "experimental_programming": bool(gerador_programacao),
        "programming_active": True,
        "programming_effects_model": bot.motor_codigo.status()["modelo_efeitos"],
        # Uma resposta "não encontrei relação" NÃO é uma prova lógica.
        "has_proof": (identificador in provas_efetivas or origem in provas_efetivas or
                      prova_editorial and "Relações verificadas:" in resposta or prova_planejada),
    }
