"""Servidor de testes do CRIVO com frontend + a mesma API usada na Vercel.

Uso no próprio computador: python web_local.py
Para acessar pelo celular na mesma rede: python web_local.py --host 0.0.0.0
NÃO encaminhe a porta para a internet sem autenticação/rate limiting.
"""
import argparse
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from api.chat import handler as CrivoAPI

PUBLIC = Path(__file__).resolve().parent / "public"
ARQUIVOS = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/styles.css": ("styles.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    "/favicon.svg": ("favicon.svg", "image/svg+xml"),
}


class LocalHandler(CrivoAPI):
    def do_GET(self):
        caminho = urlsplit(self.path).path
        if caminho == "/api/chat":
            return super().do_GET()
        entrada = ARQUIVOS.get(caminho)
        if entrada is None:
            return self._json(404, {"error": "Rota não encontrada."})
        arquivo, tipo = entrada
        conteudo = (PUBLIC / arquivo).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(conteudo)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; script-src 'self'; style-src 'self'; "
                         "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
                         "base-uri 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(conteudo)


def criar_servidor(host="127.0.0.1", port=8765, usar_dialogo_contextual=False,
                   modelo_linguagem=None, modelo_programacao=None, programacao_experimental=False,
                   relatorio_programacao=None):
    if modelo_linguagem:
        from dialogo_linguagem_profunda import carregar_modelo
        carregar_modelo(modelo_linguagem)  # Falhar no início se pesos/dependências não existem.
    gerador = None
    if modelo_programacao:
        from programacao_neural import GeradorProgramacao, pode_ativar
        if not programacao_experimental and not (relatorio_programacao and pode_ativar(modelo_programacao, relatorio_programacao)):
            raise ValueError("Modelo não aprovado; use --programacao-experimental para o laboratório")
        from conhecimento_programacao import ConhecimentoProgramacao
        catalogo = ConhecimentoProgramacao(Path(__file__).resolve().parent / "docs/pesquisa_conhecimento/programacao/catalogo-avancado.json")
        gerador = GeradorProgramacao(modelo_programacao, catalogo)
    server = ThreadingHTTPServer((host, port), LocalHandler)
    server.dialogo_contextual = usar_dialogo_contextual
    server.modelo_linguagem = modelo_linguagem
    server.gerador_programacao = gerador
    return server


def main():
    parser = argparse.ArgumentParser(description="Interface de chat do CRIVO")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Use 0.0.0.0 somente em rede local confiável.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--dialogo-experimental", action="store_true",
                        help="Usa os modelos contextuais candidatos; desativados por padrão.")
    parser.add_argument("--modelo-linguagem-profunda", metavar="DIRETORIO",
                        help="Usa explicitamente o candidato Transformer treinado do zero.")
    parser.add_argument("--modelo-programacao", metavar="DIRETORIO")
    parser.add_argument("--programacao-experimental", action="store_true")
    parser.add_argument("--relatorio-programacao", metavar="JSON")
    args = parser.parse_args()
    server = criar_servidor(args.host, args.port, args.dialogo_experimental,
                           args.modelo_linguagem_profunda, args.modelo_programacao,
                           args.programacao_experimental, args.relatorio_programacao)
    print("CRIVO web: http://%s:%s" % (args.host, server.server_address[1]))
    print("O endpoint não possui login; evite expor a porta na internet.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
