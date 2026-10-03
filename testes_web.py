"""Teste de ponta a ponta da interface, sem instalar bibliotecas.

O mesmo handler HTTP roda localmente e como Vercel Function. Nenhum serviço
externo ou modelo de terceiros é chamado durante esses testes.
"""
import json
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from web_core import PedidoInvalido, responder_web
from web_local import criar_servidor


class TestesWebCore(unittest.TestCase):
    def test_responde_usando_mesmo_crivo(self):
        dado = responder_web({"message": "Por que um pinguim é um ser vivo?"})
        self.assertEqual(dado["id"], "logica:tipo_de")
        self.assertIn("pinguim → ave → vertebrado → animal → ser vivo",
                      dado["response"])
        self.assertTrue(dado["has_proof"])
        self.assertEqual(dado["mechanism"], "raciocinio_relacional")

    def test_mensagem_invalida(self):
        entradas = [
            None, [], {}, {"message": ""}, {"message": 42},
            {"message": "x" * 1201}, {"message": "oi", "history": "oi"},
            {"message": "oi", "history": ["x"] * 11},
            {"message": "oi", "history": [123]},
            {"message": "oi", "history": [""]},
            {"message": "oi", "secret": "não usar"},
            {"message": "olá\x00"},
        ]
        for invalida in entradas:
            with self.subTest(entrada=str(invalida)[:60]):
                with self.assertRaises(PedidoInvalido):
                    responder_web(invalida)

    def test_reconstroi_contexto_em_vez_de_salvar_no_servidor(self):
        isolada = responder_web({"message": "1"})
        self.assertEqual(isolada["id"], "duvida")
        # Agora o sistema solar tem uma resposta factual: nao deve gerar
        # uma escolha pendente artificial. Verificar a memoria HTTP com
        # uma ambiguidade REAL entre dois assuntos.
        historica = responder_web({
            "message": "1",
            "history": ["O que são DNA e RNA?", "Pode desenvolver essa ideia?"]
        })
        self.assertNotEqual(historica["id"], "duvida")
        self.assertIn("DNA", historica["response"])

    def test_conhecimento_e_provas_de_fatos(self):
        dado = responder_web({"message": "Por que a aranha é um inseto?"})
        self.assertEqual(dado["id"], "insetos")
        self.assertIn("Relações verificadas", dado["response"])
        self.assertTrue(dado["has_proof"])

    def test_payload_nao_escreve_em_arquivos_de_conhecimento(self):
        base = Path(__file__).resolve().with_name("conhecimento.json")
        antes = base.read_bytes()
        responder_web({"message": "ensine outra coisa"})
        self.assertEqual(base.read_bytes(), antes)


class TestesWebHTTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = criar_servidor("127.0.0.1", 0)
        cls.thread = threading.Thread(target=cls.server.serve_forever,
                                      kwargs={"poll_interval": 0.02}, daemon=True)
        cls.thread.start()
        cls.root = "http://127.0.0.1:%s" % cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    @classmethod
    def fazer_requisicao(cls, route, dados=None, method="GET", content_type="application/json"):
        raw = None if dados is None else json.dumps(dados).encode("utf-8")
        request = Request(cls.root + route, data=raw, method=method)
        if raw is not None:
            request.add_header("Content-Type", content_type)
        try:
            with urlopen(request, timeout=8) as resposta:
                return resposta.status, resposta.headers, resposta.read()
        except HTTPError as exc:
            return exc.code, exc.headers, exc.read()

    def test_home_assets_and_health(self):
        for rota, tipo, termo in [
            ("/", "text/html", b"CRIVO"),
            ("/styles.css", "text/css", b".welcome"),
            ("/app.js", "javascript", b"fetch(API"),
            ("/favicon.svg", "svg", b"<svg"),
        ]:
            with self.subTest(rota=rota):
                status, headers, body = self.fazer_requisicao(rota)
                self.assertEqual(status, 200)
                self.assertIn(tipo, headers.get("Content-Type"))
                self.assertIn(termo, body)
                self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        status, _, body = self.fazer_requisicao("/api/chat")
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(body)["external_ai"])

    def test_http_post_retorna_resposta_real(self):
        status, headers, body = self.fazer_requisicao(
            "/api/chat", {"message": "Uma abelha tem seis patas?"}, "POST"
        )
        self.assertEqual(status, 200)
        self.assertIn("application/json", headers.get("Content-Type"))
        self.assertEqual(headers.get("Cache-Control"), "no-store")
        dado = json.loads(body.decode("utf-8"))
        self.assertEqual(dado["id"], "logica:tem_caracteristica")
        self.assertTrue(dado["has_proof"])

    def test_http_gerador_reconstroi_poema_e_personagens(self):
        status, headers, body = self.fazer_requisicao("/api/chat", {
            "history": ["Escreva um poema sobre Névia e Lúna", "Pode fazer outra versão?"],
            "message": "Troque Névia por Maíra",
        }, "POST")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Cache-Control"), "no-store")
        dado = json.loads(body.decode("utf-8"))
        self.assertEqual(dado["id"], "conversa:gerada_poema")
        self.assertEqual(dado["mechanism"], "geracao_neural")
        self.assertIn("Maíra", dado["response"])
        self.assertNotIn("Névia", dado["response"])
        self.assertFalse(dado["has_proof"])

    def test_rejeita_content_type_e_json_ruins(self):
        status, _, _ = self.fazer_requisicao(
            "/api/chat", {"message": "oi"}, "POST", "text/plain"
        )
        self.assertEqual(status, 415)
        status, _, body = self.fazer_requisicao(
            "/api/chat", {"message": "oi", "history": [""]}, "POST"
        )
        self.assertEqual(status, 400)
        self.assertIn("error", json.loads(body))
        status, _, _ = self.fazer_requisicao("/api/nao-existe")
        self.assertEqual(status, 404)

    def test_frontend_texto_seguro(self):
        app = (Path(__file__).resolve().parent / "public" / "app.js").read_text(
            encoding="utf-8")
        self.assertIn("textContent", app)
        self.assertNotIn("innerHTML", app)
        self.assertIn("AbortController", app)
        self.assertIn("state.history", app)
        self.assertIn("generation !== state.generation", app)


class TestesCorpoServerless(unittest.TestCase):
    def pedido(self, corpo, tamanho=None, seekable=True):
        import io
        from types import SimpleNamespace
        from email.message import Message
        from unittest.mock import Mock
        from api.chat import handler
        h=object.__new__(handler)
        h.path='/api/chat';h.headers=Message();h.headers['Content-Type']='application/json'
        if tamanho is not None:h.headers['Content-Length']=tamanho
        h.rfile=io.BytesIO(corpo)
        if not seekable:
            h.rfile.seekable=lambda:False
            h.rfile.read=Mock(side_effect=AssertionError('não esperar pelo socket'))
        h.server=SimpleNamespace();h._json=Mock()
        h.do_POST()
        return h._json.call_args.args

    def test_corpo_ja_recebido_sem_length_preserva_conversa(self):
        corpo=json.dumps(dict(message='Péssimo',history=['Oi'])).encode()
        status,r=self.pedido(corpo)
        self.assertEqual(status,200);self.assertEqual(r['id'],'social:acolhimento')

    def test_sem_length_socket_nao_e_lido_e_cabecalho_invalido_nao_e_ignorado(self):
        self.assertEqual(self.pedido(b'{}',seekable=False)[0],411)
        self.assertEqual(self.pedido(b'{}',tamanho='invalido')[0],411)

    def test_limite_vazio_e_json_invalido_mesmo_sem_length(self):
        self.assertEqual(self.pedido(b'x'*16385)[0],413)
        self.assertEqual(self.pedido(b'')[0],413)
        self.assertEqual(self.pedido(b'{')[0],400)


if __name__ == "__main__":
    unittest.main()
