#!/usr/bin/env python3
"""Aplica o patch de roteamento em conversa_v3d.py.

Uso (na raiz do repositório, nesta branch):
    python scripts/aplicar_roteamento.py
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ALVO = RAIZ / "conversa_v3d.py"


def main():
    texto = ALVO.read_text(encoding="utf-8")
    if "conversa_roteamento" in texto and "MAX_PARES_RAPIDO" in texto:
        print("Já aplicado.")
        return 0

    old_freio = (
        'FREIO = {"penalidade": 1.3, "sem_repetir_ngrama": 3}   # o mesmo da prova da 6b v4\n'
        "MAX_NOVOS_46M = 110\n"
        "MAX_LEMBRANCAS = 8\n"
        "MAX_PARES_46M = 12"
    )
    new_freio = (
        'FREIO = {"penalidade": 1.45, "sem_repetir_ngrama": 3}   # um pouco mais agressivo que a prova (1.3)\n'
        "MAX_NOVOS_46M = 110\n"
        "MAX_PARES_RAPIDO = 4\n"
        "MAX_LEMBRANCAS = 8\n"
        "MAX_PARES_46M = 12"
    )
    if old_freio not in texto:
        raise SystemExit("Bloco FREIO não encontrado — conversa_v3d.py mudou?")
    texto = texto.replace(old_freio, new_freio, 1)

    old_aplicar = '''def aplicar(bot, fala, ident, resposta, modelo):
    """(ident, resposta, trace). Sem modelo, fora da conversa ou reprovada: o texto de sempre."""
    trace = {"ligada": modelo is not None, "usada": False, "motivo": None,
             "modelo": getattr(modelo, "nome", "fase5_v4_F"),
             "decisao": "criador; 46M em teste, empata com a v4 F" if getattr(modelo, "formato6", False) else "criador; v4 F reprovada"}
    if modelo is None:
        trace["motivo"] = "desligada"
        return ident, resposta, trace
    ctx, exigir = contexto_do_turno(bot, fala, ident, resposta)
'''

    new_aplicar = '''def aplicar(bot, fala, ident, resposta, modelo):
    """(ident, resposta, trace). Sem modelo, fora da conversa ou reprovada: o texto de sempre.

    Melhorias sem treino (17/10/2026): categorias zero com resposta fixa; mensagens rápidas
    preferem a v4 F (17M); 46M quando memória/identidade/contexto longo agregam.
    """
    import conversa_roteamento as _rot
    cat = _rot.detectar_categoria_zero(fala)
    if cat and cat in _rot.RESPOSTAS_FIXAS and not (ident or "").startswith("crise"):
        return ident, _rot.RESPOSTAS_FIXAS[cat], {
            "ligada": True, "usada": True, "conferida": True, "motivo": "resposta_fix:" + cat,
            "modelo": "regra_fix", "decisao": "categorias zero sem treino", "tentativas": 0,
        }
    # Roteamento 17M × 46M
    if modelo is not None and not quer_a_f():
        quer46 = _rot.precisa_46m(bot, fala, ident, lembrancas_de, quer_a_f)
        if quer46 and not getattr(modelo, "formato6", False):
            modelo = _carregar("46m") or modelo
        elif not quer46 and getattr(modelo, "formato6", False):
            modelo = _carregar("f") or modelo
    trace = {"ligada": modelo is not None, "usada": False, "motivo": None,
             "modelo": getattr(modelo, "nome", "fase5_v4_F") if modelo else None,
             "decisao": ("criador; 46M em teste, empata com a v4 F" if getattr(modelo, "formato6", False)
                         else "criador; v4 F / roteamento rapido")}
    if modelo is None:
        trace["motivo"] = "desligada"
        return ident, resposta, trace
    ctx, exigir = contexto_do_turno(bot, fala, ident, resposta)
'''

    if old_aplicar not in texto:
        raise SystemExit("Bloco aplicar() não encontrado — conversa_v3d.py mudou?")
    texto = texto.replace(old_aplicar, new_aplicar, 1)

    old_hist = '''    historico = []
    for f, r in (getattr(bot, "pares_conversa", None) or [])[-getattr(modelo, "max_pares", MAX_PARES):]:
        historico += [f, r]
'''
    new_hist = '''    historico = []
    max_pares = getattr(modelo, "max_pares", MAX_PARES)
    import conversa_roteamento as _rot
    if not getattr(modelo, "formato6", False) and _rot.mensagem_rapida(fala, ident):
        max_pares = min(max_pares, MAX_PARES_RAPIDO)
    for f, r in (getattr(bot, "pares_conversa", None) or [])[-max_pares:]:
        historico += [f, r]
'''
    if old_hist not in texto:
        raise SystemExit("Bloco historico não encontrado — conversa_v3d.py mudou?")
    texto = texto.replace(old_hist, new_hist, 1)

    old_st = '''    return {"site": {"ligada": m is not None, "modelo": getattr(m, "nome", "fase5_v4_F") if m else None,
                     "desligar": "CRIVO_DISABLE_CONVERSA_V3D=1", "voltar_para_a_f": "CRIVO_CONVERSA=f",
                     "npz_sha256": NPZ_SHA256_46M if e46 else NPZ_SHA256},
'''
    new_st = '''    import conversa_roteamento as _rot
    return {"site": {"ligada": m is not None, "modelo": getattr(m, "nome", "fase5_v4_F") if m else None,
                     "desligar": "CRIVO_DISABLE_CONVERSA_V3D=1", "voltar_para_a_f": "CRIVO_CONVERSA=f",
                     "npz_sha256": NPZ_SHA256_46M if e46 else NPZ_SHA256,
                     "roteamento": "mensagens rápidas → v4 F; memória/identidade → 46M",
                     "categorias_zero": list(_rot.RESPOSTAS_FIXAS.keys())},
'''
    if old_st not in texto:
        raise SystemExit("Bloco status() não encontrado — conversa_v3d.py mudou?")
    texto = texto.replace(old_st, new_st, 1)

    ALVO.write_text(texto, encoding="utf-8")
    print("OK: conversa_v3d.py atualizado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
