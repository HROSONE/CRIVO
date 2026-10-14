"""Gera a trilha e os efeitos sonoros do vídeo, sintetizados do zero com NumPy.

Nada é baixado: cada som é feito de senoides, ondas dente-de-serra e ruído.
Uso: python scripts/gerar_sons.py  (grava em public/sfx/)
"""
from pathlib import Path
import wave

import numpy as np

SR = 44100
RNG = np.random.default_rng(7)
SAIDA = Path(__file__).resolve().parent.parent / "public" / "sfx"


def t(seg):
    return np.arange(int(seg * SR)) / SR


def gravar(nome, x, ganho=0.9):
    x = np.asarray(x, dtype=np.float64)
    if x.ndim == 1:
        x = np.stack([x, x], axis=1)
    pico = np.max(np.abs(x)) or 1.0
    x = np.tanh(1.2 * x / pico) / np.tanh(1.2) * ganho
    dados = (x * 32767).astype("<i2")
    SAIDA.mkdir(parents=True, exist_ok=True)
    with wave.open(str(SAIDA / nome), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(dados.tobytes())


def filtro_fft(x, baixo=None, alto=None):
    """Passa-faixa ideal (bom o bastante para sons curtos)."""
    espectro = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / SR)
    mascara = np.ones_like(freqs)
    if baixo:
        mascara *= 1 / (1 + (baixo / np.maximum(freqs, 1)) ** 4)
    if alto:
        mascara *= 1 / (1 + (freqs / alto) ** 4)
    return np.fft.irfft(espectro * mascara, n=len(x))


def varredura(x, centros, largura=0.6):
    """Filtro que se move no tempo: mistura faixas por blocos com janela."""
    n = len(x)
    blocos = len(centros)
    tam = n // blocos * 2
    saida = np.zeros(n + tam)
    janela = np.hanning(tam)
    passo = n // blocos
    preenchido = np.concatenate([x, np.zeros(tam)])
    for i, c in enumerate(centros):
        ini = i * passo
        trecho = preenchido[ini:ini + tam] * janela
        saida[ini:ini + tam] += filtro_fft(trecho, c * (1 - largura), c * (1 + largura))
    return saida[:n]


def env(n, ataque, queda):
    tt = np.arange(n) / SR
    a = np.clip(tt / max(ataque, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(tt - ataque, 0) / queda)


def seno_varrido(f0, f1, seg, curva=3.0):
    tt = t(seg)
    f = f1 + (f0 - f1) * np.exp(-curva * tt / seg)
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


# ---------- efeitos ----------

def whoosh(seg=0.55, subir=True):
    n = int(seg * SR)
    ruido = RNG.standard_normal(n)
    centros = np.geomspace(400, 5000, 24) if subir else np.geomspace(5000, 400, 24)
    x = varredura(ruido, centros)
    forma = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    esq = x * forma * np.linspace(1.2, 0.6, n)
    dir_ = x * forma * np.linspace(0.6, 1.2, n)
    return np.stack([esq, dir_], axis=1)


def boom(seg=1.6):
    corpo = seno_varrido(120, 38, seg, curva=6) * env(int(seg * SR), 0.002, 0.45)
    sub = np.sin(2 * np.pi * 45 * t(seg)) * env(int(seg * SR), 0.01, 0.7) * 0.6
    estalo = filtro_fft(RNG.standard_normal(int(seg * SR)), 200, 4000) * env(int(seg * SR), 0.0005, 0.04)
    return corpo + sub + 0.5 * estalo


def clique():
    seg = 0.06
    ruido = filtro_fft(RNG.standard_normal(int(seg * SR)), 2500, 9000) * env(int(seg * SR), 0.0003, 0.004)
    blip = np.sin(2 * np.pi * 1800 * t(seg)) * env(int(seg * SR), 0.0005, 0.012)
    return ruido + 0.5 * blip


def tique():
    seg = 0.04
    return np.sin(2 * np.pi * 3200 * t(seg)) * env(int(seg * SR), 0.0003, 0.006)


def pop():
    seg = 0.12
    return seno_varrido(300, 1100, seg, curva=-1.5) * env(int(seg * SR), 0.002, 0.04)


def glitch(seg=0.45):
    n = int(seg * SR)
    x = np.zeros(n)
    pos = 0
    while pos < n:
        tam = int(RNG.uniform(0.01, 0.05) * SR)
        f = RNG.choice([80, 160, 440, 880, 1760, 3520])
        tt = np.arange(tam) / SR
        if RNG.random() < 0.5:
            trecho = np.sign(np.sin(2 * np.pi * f * tt))
        else:
            trecho = RNG.standard_normal(tam)
        trecho = np.round(trecho * 4) / 4
        x[pos:pos + tam] = trecho[: n - pos] * RNG.uniform(0.3, 1.0)
        pos += tam
    return x * np.linspace(1, 0.4, n)


def riser(seg=3.5):
    n = int(seg * SR)
    ruido = varredura(RNG.standard_normal(n), np.geomspace(300, 9000, 40), largura=0.4)
    tom = seno_varrido(110, 880, seg, curva=-1.0)
    cres = np.linspace(0, 1, n) ** 2.5
    return (ruido * 0.8 + tom * 0.35) * cres


def ding():
    seg = 2.0
    tt = t(seg)
    x = sum(a * np.sin(2 * np.pi * 1318.5 * r * tt) * np.exp(-tt / d)
            for r, a, d in [(1, 1.0, 0.9), (2.76, 0.4, 0.4), (5.4, 0.2, 0.2), (0.5, 0.3, 1.2)])
    return x * env(len(tt), 0.002, 10)


def scratch(seg=0.7):
    tt = t(seg)
    vel = np.sin(2 * np.pi * 3.5 * tt) * np.exp(-tt * 1.5)
    fase = np.cumsum(300 + 900 * vel) / SR
    serra = 2 * (fase * 1.0 % 1) - 1
    ruido = filtro_fft(RNG.standard_normal(len(tt)), 800, 6000) * np.abs(vel)
    return (serra * 0.6 + ruido) * env(len(tt), 0.005, 0.35)


def erro(seg=0.45):
    tt = t(seg)
    x = np.sign(np.sin(2 * np.pi * 110 * tt)) + 0.5 * np.sign(np.sin(2 * np.pi * 116 * tt))
    tremolo = (np.sin(2 * np.pi * 14 * tt) > 0).astype(float) * 0.7 + 0.3
    return filtro_fft(x * tremolo, None, 3000) * env(len(tt), 0.003, 0.3)


def digitacao(seg=1.6):
    n = int(seg * SR)
    x = np.zeros(n)
    pos = 0
    while pos < n - SR // 10:
        c = clique() * RNG.uniform(0.4, 1.0)
        x[pos:pos + len(c)] += c[: n - pos]
        pos += int(RNG.uniform(0.05, 0.13) * SR)
    return x


# ---------- trilha (120 BPM, 30 fps → 15 quadros por tempo) ----------

BPM = 120
TEMPO = 60 / BPM


def kick():
    seg = 0.45
    return seno_varrido(160, 45, seg, curva=9) * env(int(seg * SR), 0.001, 0.16)


def chimbal(aberto=False):
    seg = 0.25 if aberto else 0.06
    x = np.diff(RNG.standard_normal(int(seg * SR) + 1))
    x = filtro_fft(x, 7000, None)
    return x * env(len(x), 0.0005, 0.08 if aberto else 0.015)


def palma():
    seg = 0.3
    n = int(seg * SR)
    x = filtro_fft(RNG.standard_normal(n), 900, 5000)
    e = sum(np.roll(env(n, 0.0005, 0.01), int(d * SR)) for d in (0, 0.01, 0.02))
    return x * (e + env(n, 0.03, 0.09) * 0.6)


def nota_baixo(freq, seg):
    tt = t(seg)
    fase = freq * tt
    serra = 2 * (fase % 1) - 1 + 0.5 * (2 * ((fase * 1.005) % 1) - 1)
    return filtro_fft(serra, None, 900) * env(len(tt), 0.004, seg * 0.55)


def acorde_pad(freqs, seg):
    tt = t(seg)
    x = np.zeros((len(tt), 2))
    for f in freqs:
        for d, lado in ((-0.004, 0), (0.004, 1), (0.0, 0), (0.0, 1)):
            x[:, lado] += np.sin(2 * np.pi * f * (1 + d) * tt + RNG.uniform(0, 6.28))
    forma = np.minimum(1, np.minimum(tt / 0.4, (seg - tt) / 0.4))
    return x * forma[:, None] / (len(freqs) * 2)


def colar(destino, som, inicio, ganho=1.0):
    i = int(inicio * SR)
    if som.ndim == 1:
        som = np.stack([som, som], axis=1)
    fim = min(len(destino), i + len(som))
    if fim > i:
        destino[i:fim] += som[: fim - i] * ganho


def nota(nome):
    tabela = {"A": 0, "B": 2, "C": 3, "D": 5, "E": 7, "F": 8, "G": 10}
    letra, oit = nome[0], int(nome[-1])
    semis = tabela[letra] + (1 if "#" in nome else 0) + 12 * (oit - 4)
    if letra in "CDEFG":
        semis -= 12
    return 440 * 2 ** (semis / 12)


def trilha(cortes):
    """cortes: dict com os segundos de cada seção."""
    total = cortes["fim"]
    mix = np.zeros((int(total * SR) + SR, 2))
    menor = [["A3", "C4", "E4"], ["F3", "A3", "C4"], ["C4", "E4", "G4"], ["G3", "B3", "D4"]]
    baixo_menor = ["A1", "F1", "C2", "G1"]
    maior = [["C4", "E4", "G4"], ["G3", "B3", "D4"], ["A3", "C4", "E4"], ["F3", "A3", "C4"]]
    baixo_maior = ["C2", "G1", "A1", "F1"]

    def compasso_pad(ini, acorde, ganho):
        colar(mix, acorde_pad([nota(n) for n in acorde], 4 * TEMPO), ini, ganho)

    # intro: pad e subida
    s = 0.0
    i = 0
    while s < cortes["batida"]:
        compasso_pad(s, menor[i % 4], 0.35)
        s += 4 * TEMPO
        i += 1
    colar(mix, riser(cortes["batida"]), 0, 0.25)

    def batida(ini, fim, prog, baixos, meia=False, ganho=1.0):
        s = ini
        k = 0
        while s < fim - 0.01:
            barra = int(round((s - ini) / (4 * TEMPO)))
            if k % 4 == 0:
                compasso_pad(s, prog[barra % 4], 0.22 * ganho)
            if not meia or k % 2 == 0:
                colar(mix, kick(), s, 0.95 * ganho)
            if not meia:
                colar(mix, chimbal(k % 8 == 7), s + TEMPO / 2, 0.22 * ganho)
                colar(mix, chimbal(), s + TEMPO / 4 * 3, 0.1 * ganho)
                if k % 2 == 1:
                    colar(mix, palma(), s, 0.45 * ganho)
            elif k % 4 == 2:
                colar(mix, palma(), s, 0.35 * ganho)
            f = nota(baixos[barra % 4])
            for sub in (0, 0.5) if not meia else (0,):
                colar(mix, nota_baixo(f * (2 if (k + sub * 2) % 3 == 2 else 1), TEMPO / (2 if not meia else 1)),
                      s + sub * TEMPO, 0.32 * ganho)
            s += TEMPO
            k += 1

    batida(cortes["batida"], cortes["pausa"], menor, baixo_menor)
    batida(cortes["volta"], cortes["crivo"], menor, baixo_menor, meia=True, ganho=0.8)
    batida(cortes["crivo"], cortes["final"], maior, baixo_maior, ganho=1.0)
    compasso_pad(cortes["final"], ["C4", "E4", "G4", "B4"], 0.45)
    colar(mix, acorde_pad([nota("C3"), nota("G3")], total - cortes["final"]), cortes["final"], 0.3)

    n = int(total * SR)
    mix = mix[:n]
    queda = np.ones(n)
    fim_q = int(2.5 * SR)
    queda[-fim_q:] = np.linspace(1, 0, fim_q) ** 2
    return mix * queda[:, None]


def moeda():
    seg = 0.5
    tt = t(seg)
    x = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt / d)
            for f, a, d in [(2637, 1.0, 0.18), (3951, 0.6, 0.12), (5274, 0.3, 0.08)])
    segundo = np.roll(x, int(0.07 * SR)) * 0.8
    segundo[: int(0.07 * SR)] = 0
    return (x + segundo) * env(len(tt), 0.001, 10)


def alarme(seg=1.6):
    tt = t(seg)
    f = 700 + 350 * (np.sin(2 * np.pi * 2.5 * tt) > 0)
    x = np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.6 + np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4
    return filtro_fft(x, None, 4000) * env(len(tt), 0.01, 3) * np.minimum(1, (seg - tt) / 0.2)


def sino():
    seg = 1.5
    tt = t(seg)
    x = sum(a * np.sin(2 * np.pi * f * tt) * np.exp(-tt / d)
            for f, a, d in [(880, 1.0, 0.6), (1760, 0.5, 0.35), (2640, 0.25, 0.2), (1318.5, 0.6, 0.5)])
    return x * env(len(tt), 0.002, 10)


def tictac(seg=2.0, bpm=240):
    n = int(seg * SR)
    x = np.zeros(n)
    passo = int(60 / bpm * SR)
    for k, ini in enumerate(range(0, n, passo)):
        c = tique() * (1.0 if k % 2 == 0 else 0.6)
        if k % 2:
            c = filtro_fft(c, None, 2500)
        x[ini:ini + len(c)] += c[: n - ini]
    return x


def carimbo():
    seg = 0.5
    corpo = seno_varrido(140, 60, seg, curva=10) * env(int(seg * SR), 0.001, 0.08)
    papel = filtro_fft(RNG.standard_normal(int(seg * SR)), 400, 3000) * env(int(seg * SR), 0.0005, 0.03)
    return corpo + 0.7 * papel


def trilha_narracao(cortes):
    """Cama discreta para baixo da voz: pulso grave, chimbal leve e pad menor."""
    total = cortes["fim"]
    mix = np.zeros((int(total * SR) + SR, 2))
    menor = [["A3", "C4", "E4"], ["F3", "A3", "C4"], ["D3", "F3", "A3"], ["E3", "G#3", "B3"]]
    baixos = ["A1", "F1", "D2", "E1"]
    s, k = 0.0, 0
    while s < total - 0.01:
        barra = k // 4
        tenso = s >= cortes["tensao"]
        if k % 4 == 0:
            colar(mix, acorde_pad([nota(n) for n in menor[barra % 4]], 4 * TEMPO), s, 0.3)
        if s >= cortes["batida"]:
            colar(mix, kick(), s, 0.7 if tenso else 0.5)
            colar(mix, chimbal(), s + TEMPO / 2, 0.12 if tenso else 0.07)
            if tenso and k % 2 == 1:
                colar(mix, palma(), s, 0.22)
        colar(mix, nota_baixo(nota(baixos[barra % 4]), TEMPO), s, 0.22)
        s += TEMPO
        k += 1
    colar(mix, riser(3.5), cortes["tensao"] - 3.5, 0.15)
    n = int(total * SR)
    mix = mix[:n]
    queda = np.ones(n)
    q = int(1.5 * SR)
    queda[-q:] = np.linspace(1, 0, q) ** 2
    return mix * queda[:, None]


if __name__ == "__main__":
    import json
    import sys

    gravar("whoosh.wav", whoosh())
    gravar("whoosh-desce.wav", whoosh(0.45, subir=False))
    gravar("boom.wav", boom())
    gravar("clique.wav", clique(), 0.7)
    gravar("tique.wav", tique(), 0.5)
    gravar("pop.wav", pop(), 0.7)
    gravar("glitch.wav", glitch(), 0.6)
    gravar("riser.wav", riser())
    gravar("ding.wav", ding(), 0.7)
    gravar("scratch.wav", scratch())
    gravar("erro.wav", erro(), 0.6)
    gravar("digitacao.wav", digitacao(), 0.6)
    gravar("moeda.wav", moeda(), 0.5)
    gravar("alarme.wav", alarme(), 0.5)
    gravar("sino.wav", sino(), 0.6)
    gravar("tictac.wav", tictac(), 0.5)
    gravar("carimbo.wav", carimbo(), 0.8)

    cortes = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.loads(
        (Path(__file__).parent / "cortes.json").read_text())
    gravar("trilha.wav", trilha(cortes), 0.75)
    cortes_n = json.loads((Path(__file__).parent / "cortes_narracao.json").read_text())
    gravar("trilha_narracao.wav", trilha_narracao(cortes_n), 0.6)
    print("sons gravados em", SAIDA)
