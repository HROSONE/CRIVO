"""Retração conservadora de uma relação nominal explícita da sessão.

Não transforma hipóteses ou citações em dados pessoais. Só substitui uma
cláusula declarada quando há uma única referência nominal correspondente.
O histórico original do chat permanece intacto para auditoria.
"""
import re
from composicao_textual import normalizar

LETRAS = r"[^\W\d_]"
NOME = LETRAS + r"[\wÀ-ÿ .-]{0,59}?"
CORRECAO = re.compile(
    r"(?:quer dizer|corrigindo|na verdade),?\s+(" + NOME + r")\s+é\s+"
    r"(?:meu|minha)\s+(" + LETRAS + r"[\wÀ-ÿ -]{0,59}?)"
    r"(?:,\s*(?:eu )?escrevi errado)?[.! ]*", re.I)


def pedido_lembranca(texto):
    if not isinstance(texto, str) or len(texto) > 600 or any(c in texto for c in ('`', '"', '“', '”')):
        return False
    n = normalizar(texto).strip(' .?!')
    return bool(re.fullmatch(r'(?:do que|o que) eu (?:queria|disse|falei|contei)(?: .+)?', n)
                and not re.search(r'\b(?:saber|entender|explicar|definir|como funciona|o que e)\b', n))


def pedido_reinicio(texto):
    if not isinstance(texto, str) or len(texto) > 160 or any(c in texto for c in ('?', '`', '"', '“', '”')):
        return False
    return bool(re.fullmatch(r'(?:agora )?(?:esqueca|apague) tudo(?: o)? que eu '
                             r'(?:contei|disse|falei)(?: aqui)?', normalizar(texto).strip(' .!')))


def corrigir_relatos(texto, relatos):
    if not isinstance(texto, str) or len(texto) > 240 or any(x in texto for x in ('?', '`', '"', '“', '”')):
        return None
    if re.search(r"\b(?:se|caso|talvez|nao|hipotese|imagine)\b", normalizar(texto)):
        return None
    correcao = CORRECAO.fullmatch(texto.strip())
    if correcao is None:
        return None
    nome = normalizar(correcao.group(1)).strip()
    encontrados = []
    partes_por_relato = []
    for i, relato in enumerate(relatos):
        partes = re.split(r",\s*e\s+|;\s*", relato)
        partes_por_relato.append(partes)
        for j, parte in enumerate(partes):
            if any(c in parte for c in ('?', '`', '"', '“', '”')) or re.search(
                    r'\b(?:nao|se(?! chama\b)|caso|talvez|hipotese|imagine)\b', normalizar(parte)):
                continue
            original = normalizar(parte).strip(" .!")
            declaracao = re.fullmatch(r"(?:meu|minha) .+? se chama (.+)", original)
            anterior = CORRECAO.fullmatch(parte.strip())
            if ((declaracao and declaracao.group(1).strip() == nome) or
                    (anterior and normalizar(anterior.group(1)).strip() == nome)):
                encontrados.append((i, j))
    if len(encontrados) != 1:
        return None
    i, j = encontrados[0]
    partes_por_relato[i][j] = ""
    restantes = [", e ".join(p for p in partes if p) for partes in partes_por_relato]
    return [r for r in restantes if r] + [texto.strip()]
