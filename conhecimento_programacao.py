"""Consulta explicável do catálogo autoral; nenhuma dependência neural."""
import hashlib
import json
from pathlib import Path
import re
import unicodedata


def normalizar(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto.lower())
                   if not unicodedata.combining(c))


def tokens(texto):
    texto = normalizar(texto)
    texto = re.sub(r'\bjs\b', 'javascript', texto)
    texto = re.sub(r'\bts\b', 'typescript', texto)
    return set(re.findall(r'[a-z0-9_$]+', texto)) - {
        'de', 'a', 'o', 'e', 'em', 'no', 'na', 'os', 'as', 'um', 'uma',
        'como', 'que', 'qual', 'para', 'por', 'me', 'explique', 'explica',
        'sobre', 'funciona', 'programacao', 'diferenca', 'entre', 'com', 'do', 'da',
        'dos', 'das', 'ao', 'aos', 'pelo', 'pela', 'usando', 'tomar', 'cuidados',
        'voce', 'poderia', 'explicar', 'definir', 'diga', 'sao', 'eh', 'favor',
        'entender', 'entenda', 'significa', 'significado'}


class ConhecimentoProgramacao:
    def __init__(self, caminho):
        self.caminho = Path(caminho)
        raw = self.caminho.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        self.catalogo = json.loads(raw)
        self.indice = [(u, tokens(u['conceito']), tokens(u['definicao'] + ' ' + u['mecanismo']))
                       for u in self.catalogo['unidades']]

    def buscar(self, pergunta, limite=3):
        if not 1 <= limite <= 10:
            raise ValueError('Limite deve estar entre 1 e 10')
        q = tokens(pergunta)
        linguagem = next((l for l in ('typescript', 'javascript') if l in q), None)
        if not linguagem and q & {'python', 'rust', 'java', 'kotlin', 'ruby', 'golang'}:
            return []
        q -= {'typescript', 'javascript'}
        if not q:
            return []
        encontrados = []
        for u, titulo, corpo in self.indice:
            if linguagem and u['dominio'] != linguagem:
                continue
            alvo = titulo - {'typescript', 'javascript'}
            # Toda palavra de conteúdo precisa estar sustentada pela ficha.
            # "árvore binária" não pode recuperar "busca binária".
            if q - (titulo | corpo):
                continue
            # Pelo menos dois termos ou um termo distintivo e completo do título.
            comum = q & alvo
            if not comum or (len(comum) < 2 and not (alvo <= q or
                    any(len(t) >= 7 for t in comum))):
                continue
            score = 4 * len(comum) + len(q & corpo)
            encontrados.append((score, u))
        encontrados.sort(key=lambda x: (-x[0], x[1]['id']))
        return [dict(u, pontuacao=s, catalogo_sha256=self.sha256,
                     referencias=[self.catalogo['fontes'][f] for f in u['fontes']])
                for s, u in encontrados[:limite]]

    def responder(self, pergunta):
        n = normalizar(pergunta)
        # Não transformar pedidos de código, negações ou relatos em definições.
        if not re.search(r'\b(expli\w*|defin\w*|como|o que|qual|diferenca)\b', n):
            return None
        if re.search(r'\b(nao|gere|crie|implemente|escreva|faca)\b', n):
            return None
        achados = self.buscar(pergunta, 1)
        if not achados:
            return None
        u = achados[0]
        texto = (u['conceito'] + ': ' + u['definicao'] + '\n\n' + u['mecanismo'] +
                 '\n\nCuidados: ' + u['falhas_comuns'] + '\nVerificação: ' + u['verificacao'] +
                 '\nFontes: ' + ', '.join(f['url'] for f in u['referencias']) +
                 '\nConsulta ao acervo autoral; revisão editorial integral pendente.')
        return 'programacao:' + u['id'], texto, u
