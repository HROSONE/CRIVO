"""Vercel Python Function: POST /api/chat, GET /api/chat.

Reutiliza o CRIVO em Python; não usa provedores externos de IA.
"""
import json
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


class handler(BaseHTTPRequestHandler):
    """Compatível com o runtime Python /api do Vercel e servidor local."""

    def _json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
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
        return self._json(200, {"status": "ok", "name": "CRIVO",
                                "engine": "python-local", "external_ai": False})

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/chat":
            return self._json(404, {"error": "Rota não encontrada."})
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            return self._json(415, {"error": "Envie application/json."})
        tamanho = self.headers.get("Content-Length", "")
        if not tamanho.isascii() or not tamanho.isdecimal():
            return self._json(411, {"error": "Content-Length obrigatório."})
        tamanho = int(tamanho)
        if not 0 < tamanho <= LIMITE_BODY:
            return self._json(413, {"error": "Pedido maior que o permitido."})
        try:
            bruto = self.rfile.read(tamanho)
            pedido = json.loads(bruto.decode("utf-8"))
            resposta = responder_web(pedido)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._json(400, {"error": "JSON malformado."})
        except PedidoInvalido as exc:
            return self._json(400, {"error": str(exc)})
        except Exception:
            # Não vazar caminhos de arquivos ou detalhes do servidor no HTTP.
            logging.exception("Falha ao responder pelo CRIVO")
            return self._json(500, {"error": "O CRIVO encontrou um erro interno."})
        return self._json(200, resposta)
