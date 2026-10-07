"""Framing recebido na Vercel: blocos reais, limites e erros sem esperar EOF."""
import io
import json
import threading
import unittest
from http.client import HTTPConnection
from unittest.mock import Mock

from api.chat import CorpoHTTPInvalido, LIMITE_BODY, ler_chunked
from web_local import criar_servidor


class ChunkedTestes(unittest.TestCase):
    def test_limite_rejeitado_antes_de_ler_payload(self):
        stream = Mock()
        stream.readline.return_value = b'100000000\r\n'
        with self.assertRaises(CorpoHTTPInvalido) as erro:
            ler_chunked(stream)
        self.assertEqual(erro.exception.status, 413)
        stream.read.assert_not_called()

    def test_limite_soma_todos_os_blocos(self):
        metade = LIMITE_BODY // 2
        bloco = format(metade, 'x').encode() + b'\r\n' + b'x' * metade + b'\r\n'
        with self.assertRaises(CorpoHTTPInvalido) as erro:
            ler_chunked(io.BytesIO(bloco*2+b'1\r\ny\r\n0\r\n\r\n'))
        self.assertEqual(erro.exception.status, 413)

    def test_framing_malformado_ou_truncado_e_rejeitado(self):
        for body in (b'', b'-1\r\nx\r\n0\r\n\r\n', b'+1\r\nx\r\n0\r\n\r\n',
                     b'Z\r\n', b'1\nx\n', b'3\r\nx', b'1\r\nxXX', b'0\r\n',
                     b'1'+b';'*128+b'\r\n'):
            with self.subTest(body=body), self.assertRaises(CorpoHTTPInvalido) as erro:
                ler_chunked(io.BytesIO(body))
            self.assertEqual(erro.exception.status, 400)

    def test_extensoes_trailers_e_termino_sem_esperar_eof(self):
        stream = io.BytesIO(b'2;part=1\r\n{}\r\n0\r\nX-Test: yes\r\n\r\nNEXT')
        self.assertEqual(ler_chunked(stream), b'{}')
        self.assertEqual(stream.read(), b'NEXT')

    def test_limites_de_trailers_e_quantidade_de_blocos(self):
        for body in (b'0\r\n'+b'X: y\r\n'*700+b'\r\n', b'1\r\nx\r\n'*1024+b'0\r\n\r\n'):
            with self.assertRaises(CorpoHTTPInvalido) as erro:
                ler_chunked(io.BytesIO(body))
            self.assertEqual(erro.exception.status, 413)


class ChunkedHTTPTestes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = criar_servidor(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, kwargs={'poll_interval': .02}, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def pedido(self, body, headers=None):
        conn = HTTPConnection('127.0.0.1', self.server.server_address[1], timeout=8)
        try:
            conn.putrequest('POST', '/api/chat')
            conn.putheader('Content-Type', 'application/json')
            conn.putheader('Transfer-Encoding', 'chunked')
            for name, value in (headers or {}).items():
                conn.putheader(name, value)
            conn.endheaders()
            conn.send(body)
            result = conn.getresponse()
            return result.status, json.loads(result.read())
        finally:
            conn.close()

    def test_blocos_utf8_reconstroem_conversa_e_correcao(self):
        for message in ('Olá', 'Corrija este código JS:\n```js\nreturn entrada - 2;\n```\nExemplos: [{"entrada":0,"saida":2}]'):
            data = json.dumps(dict(message=message), ensure_ascii=False).encode('utf-8')
            # Blocos de um byte também separam os bytes de caracteres UTF-8.
            body = b''.join(b'1\r\n'+bytes([byte])+b'\r\n' for byte in data)+b'0\r\n\r\n'
            status, result = self.pedido(body)
            self.assertEqual(status, 200)
            if 'Corrija' in message:
                self.assertTrue(result['code_analysis']['atende_desenvolvimento'])
                self.assertIn('entrada + 2', result['response'])
            else:
                self.assertTrue(result['id'].startswith('social:'))

    def test_corpo_grande_vazio_ou_ambiguo_nao_chega_ao_crivo(self):
        self.assertEqual(self.pedido(format(LIMITE_BODY + 1, 'x').encode() + b'\r\n')[0], 413)
        self.assertEqual(self.pedido(b'0\r\n\r\n')[0], 413)
        self.assertEqual(self.pedido(b'2\r\n{}\r\n0\r\n\r\n', {'Content-Length':'2'})[0], 400)
        self.assertEqual(self.pedido(b'1\r\nx\r\n0\r\n\r\n')[0], 400)

    def test_corpo_exatamente_no_limite(self):
        mensagem = json.dumps(dict(message='Oi')).encode()
        data = mensagem+b' '*(LIMITE_BODY-len(mensagem))
        body = format(len(data), 'x').encode()+b'\r\n'+data+b'\r\n0\r\n\r\n'
        status, result = self.pedido(body)
        self.assertEqual(status, 200)
        self.assertTrue(result['id'].startswith('social:'))


if __name__ == '__main__':
    unittest.main()
