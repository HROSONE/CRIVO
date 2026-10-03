"""Vercel Python Function: POST /api/chat, GET /api/chat.

Reutiliza o CRIVO em Python; não usa provedores externos de IA.
"""
import json
import io
import logging
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Funciona com import local, Vercel Function e pacote Python implícito api/.
RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from web_core import PedidoInvalido, responder_web  # noqa: E402

LIMITE_BODY = 16 * 1024


class CorpoHTTPInvalido(ValueError):
    def __init__(self, status, mensagem):
        super().__init__(mensagem)
        self.status = status


def ler_chunked(stream):
    """Decodifica framing HTTP sem ler até EOF nem exceder o limite do chat."""
    partes = []
    total = 0
    for _ in range(1024):
        linha = stream.readline(129)
        if len(linha) > 128 or not linha.endswith(b"\r\n"):
            raise CorpoHTTPInvalido(400, "Corpo HTTP malformado.")
        token = linha[:-2].split(b";", 1)[0]
        if not token or any(c not in b"0123456789abcdefABCDEF" for c in token):
            raise CorpoHTTPInvalido(400, "Corpo HTTP malformado.")
        tamanho = int(token, 16)
        if tamanho == 0:
            trailers = 0
            while True:
                linha = stream.readline(129)
                trailers += len(linha)
                if trailers > 4096:
                    raise CorpoHTTPInvalido(413, "Pedido maior que o permitido.")
                if len(linha) > 128 or not linha.endswith(b"\r\n"):
                    raise CorpoHTTPInvalido(400, "Corpo HTTP malformado.")
                if linha == b"\r\n":
                    return b"".join(partes)
        total += tamanho
        if total > LIMITE_BODY:
            raise CorpoHTTPInvalido(413, "Pedido maior que o permitido.")
        parte = stream.read(tamanho)
        if len(parte) != tamanho or stream.read(2) != b"\r\n":
            raise CorpoHTTPInvalido(400, "Corpo HTTP malformado.")
        partes.append(parte)
    raise CorpoHTTPInvalido(413, "Pedido com blocos demais.")


class handler(BaseHTTPRequestHandler):
    """Compatível com o runtime Python /api do Vercel e servidor local."""

    def _json(self, status, data):
        body = json.dumps(data, ensure_ascii=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?", 1)[0] != "/api/chat":
            return self._json(404, {"error": "Rota não encontrada."})
        # Confirma que a função recebeu os arquivos de conhecimento.
        # Sem isso o frontend poderia exibir "online" mas todo POST falharia.
        if not (RAIZ / "conhecimento.json").is_file() or not (
                RAIZ / "relacoes.json").is_file():
            return self._json(503, {"status": "unavailable",
                                    "error": "Arquivos de conhecimento ausentes."})
        from modelo_efeitos_chat import status_modelo
        return self._json(200, {"status": "ok", "name": "CRIVO",
                                "programming_active": True,
                                "programming_effects_model": status_modelo(),
                                "engine": "python-local", "external_ai": False,
                                "experimental_dialogue": getattr(self.server, "dialogo_contextual", False)
                                or bool(getattr(self.server, "modelo_linguagem", None)),
                                "experimental_programming": bool(getattr(self.server, "gerador_programacao", None))})

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/chat":
            return self._json(404, {"error": "Rota não encontrada."})
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            return self._json(415, {"error": "Envie application/json."})
        tamanho = self.headers.get("Content-Length", "")
        encoding = self.headers.get("Transfer-Encoding", "").strip().lower()
        bruto = None
        if encoding:
            # O runtime da Vercel encaminha HTTP em chunked para handlers
            # nativos; BaseHTTPRequestHandler não decodifica esses blocos.
            if tamanho or encoding != "chunked":
                self.close_connection = True
                return self._json(400, {"error": "Enquadramento HTTP inválido."})
            try:
                bruto = ler_chunked(self.rfile)
            except CorpoHTTPInvalido as exc:
                self.close_connection = True
                return self._json(exc.status, {"error": str(exc)})
            tamanho = len(bruto)
        elif not tamanho and self.rfile.seekable():
            # O adaptador serverless pode remover Content-Length após receber
            # o corpo. Uma entrada seekable permite medir sem esperar por EOF
            # de um socket; conexões HTTP normais continuam exigindo o cabeçalho.
            inicio = self.rfile.tell()
            self.rfile.seek(0, io.SEEK_END)
            tamanho = self.rfile.tell() - inicio
            self.rfile.seek(inicio)
        elif not tamanho.isascii() or not tamanho.isdecimal():
            return self._json(411, {"error": "Content-Length obrigatório."})
        else:
            tamanho = int(tamanho)
        if not 0 < tamanho <= LIMITE_BODY:
            return self._json(413, {"error": "Pedido maior que o permitido."})
        try:
            if bruto is None:
                bruto = self.rfile.read(tamanho)
            if len(bruto) != tamanho:
                self.close_connection = True
                return self._json(400, {"error": "Corpo HTTP incompleto."})
            pedido = json.loads(bruto.decode("utf-8"))
            resposta = responder_web(pedido, usar_dialogo_contextual=getattr(
                self.server, "dialogo_contextual", False), modelo_linguagem=getattr(
                self.server, "modelo_linguagem", None), gerador_programacao=getattr(
                self.server, "gerador_programacao", None))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._json(400, {"error": "JSON malformado."})
        except PedidoInvalido as exc:
            return self._json(400, {"error": str(exc)})
        except Exception:
            # Não vazar caminhos de arquivos ou detalhes do servidor no HTTP.
            logging.exception("Falha ao responder pelo CRIVO")
            return self._json(500, {"error": "O CRIVO encontrou um erro interno."})
        return self._json(200, resposta)
