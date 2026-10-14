"""Alinha o roteiro à narração sem modelo de reconhecimento de voz.

Ideia: cada sílaba falada tem um núcleo vocálico, que aparece como um pico de
energia na faixa das vogais (250–1500 Hz). Fala rápida junta sílabas, então
os picos não batem um a um com o texto: o script mapeia a fração de sílabas
do roteiro na fração de picos do áudio e prende os fins de frase aos respiros
reais, linear por trechos entre essas âncoras. Sai no formato Caption do
@remotion/captions. É uma estimativa: a precisão fica perto da sílaba.

Uso: python scripts/alinhar_fala.py <wav> <roteiro.txt> <saida.json>
"""
import json
import re
import sys
import unicodedata
import wave

import numpy as np

FPS_ANALISE = 100  # janelas de 10 ms


def ler_wav(caminho):
    with wave.open(caminho) as w:
        sr, canais = w.getframerate(), w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), "<i2").reshape(-1, canais).mean(axis=1) / 32768
    return x, sr


def envelope_vogais(x, sr):
    passo = sr // FPS_ANALISE
    janela = passo * 3
    n = (len(x) - janela) // passo
    quadros = np.lib.stride_tricks.sliding_window_view(x, janela)[::passo][:n] * np.hanning(janela)
    espectro = np.abs(np.fft.rfft(quadros, axis=1)) ** 2
    freqs = np.fft.rfftfreq(janela, 1 / sr)
    faixa = (freqs >= 250) & (freqs <= 1500)
    e = 10 * np.log10(espectro[:, faixa].sum(axis=1) + 1e-10)
    nucleo = np.ones(5) / 5
    return np.convolve(e, nucleo, "same")


def picos(e, distancia=7, proeminencia=4.0):
    """Máximos locais com proeminência mínima (em dB)."""
    candidatos = [i for i in range(1, len(e) - 1) if e[i] >= e[i - 1] and e[i] > e[i + 1]]
    piso = np.percentile(e, 20)
    bons = []
    for i in candidatos:
        if e[i] < piso + 6:
            continue
        esq = e[max(0, i - 15):i + 1].min()
        dir_ = e[i:i + 16].min()
        if e[i] - max(esq, dir_) >= proeminencia:
            if bons and i - bons[-1] < distancia:
                if e[i] > e[bons[-1]]:
                    bons[-1] = i
                continue
            bons.append(i)
    return np.array(bons)


def sem_acento(t):
    return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")


def silabas(palavra):
    w = sem_acento(palavra)
    if re.fullmatch(r"\d+", w):
        return {"1": 2}.get(w, 2)  # "uma"
    if w in ("ia",):
        return 2  # "i-a"
    if w == "mcp":
        return 3  # "eme-cê-pê", dito rápido
    grupos = re.findall(r"[aeiouy]+", w)
    n = 0
    for g in grupos:
        # hiatos comuns contam duas; ditongos, uma
        n += 1 + len(re.findall(r"(?<=[aeo])(?=[aeo])|(?<=i)(?=[ao])(?!$)|(?<=u)(?=[ao])", g)) if len(g) > 1 else 1
    return max(1, n)


def alinhar(fronteiras, total_sil, tempos, gaps, janela=1.4):
    """Sílaba -> índice de pico (fracionário), linear por trechos entre âncoras.

    Começa proporcional (fração de sílabas = fração de picos) e prende cada
    fim de frase do roteiro ao respiro do áudio mais próximo, em ordem.
    """
    P = len(tempos)
    ancoras = [(0.0, 0.0), (float(total_sil), float(P - 1))]
    grandes = [i for i in range(1, P) if gaps[i] > 0.22]

    def mapa(s):
        xs, ys = zip(*sorted(ancoras))
        return float(np.interp(s, xs, ys))

    usados = set()
    for s, forca in sorted(fronteiras, key=lambda f: -f[1]):
        pi = mapa(s)
        tp = np.interp(pi, np.arange(P), tempos)
        menor = sorted(ancoras)
        antes = max((y for x, y in menor if x < s), default=0)
        depois = min((y for x, y in menor if x > s), default=P - 1)
        cand = [i for i in grandes if antes < i < depois and i not in usados
                and abs(tempos[i] - tp) < janela * forca]
        if not cand:
            continue
        melhor = min(cand, key=lambda i: abs(tempos[i] - tp) / (0.5 + gaps[i]))
        usados.add(melhor)
        ancoras.append((float(s), float(melhor)))
    return mapa, sorted(ancoras)


def main():
    wav, roteiro, saida = sys.argv[1:4]
    x, sr = ler_wav(wav)
    e = envelope_vogais(x, sr)
    pk = picos(e)
    tempos = pk / FPS_ANALISE
    gaps = np.diff(np.concatenate([[0.0], tempos]))
    respiro = np.clip((gaps - 0.12) / 0.3, 0, 1)

    texto = open(roteiro, encoding="utf-8").read().split()
    sil_palavra = [silabas(re.sub(r"[^\wÀ-ÿ-]", "", w) or "a") for w in texto]
    inicio_sil = np.concatenate([[0], np.cumsum(sil_palavra)])
    fronteiras = []
    for i in range(1, len(texto)):
        if re.search(r"[.?!:]$", texto[i - 1]):
            fronteiras.append((int(inicio_sil[i]), 1.0))
        elif re.search(r"[,;]$", texto[i - 1]):
            fronteiras.append((int(inicio_sil[i]), 0.5))
    mapa, ancoras = alinhar(fronteiras, int(inicio_sil[-1]), tempos, gaps)

    def tempo(s):
        return float(np.interp(mapa(s), np.arange(len(tempos)), tempos))

    duracao = len(x) / sr
    inicio_palavra = {i: tempo(inicio_sil[i]) for i in range(len(texto))}
    fim_palavra = {i: tempo(inicio_sil[i + 1] - 0.5) for i in range(len(texto))}
    seq = range(int(inicio_sil[-1]))
    legendas = []
    for i, w in enumerate(texto):
        ini = max(0.0, inicio_palavra[i] - 0.06)
        prox = inicio_palavra.get(i + 1, duracao + 0.06) - 0.06
        fim = min(prox, fim_palavra[i] + 0.18)
        fim = max(fim, ini + 0.08)
        legendas.append({
            "text": (" " if i else "") + w,
            "startMs": round(ini * 1000),
            "endMs": round(fim * 1000),
            "timestampMs": round(inicio_palavra[i] * 1000),
            "confidence": None,
        })
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(legendas, f, ensure_ascii=False, indent=1)
    print(f"{len(pk)} picos no áudio, {len(seq)} sílabas no texto, {len(texto)} palavras, {len(ancoras) - 2} âncoras, {duracao:.1f} s")


if __name__ == "__main__":
    main()
