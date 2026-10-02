# Analisador de frases (em andamento)

Objetivo: o Crivo entender **como as palavras de uma frase se ligam** — quem
faz a ação, sobre o quê, quando, e conectivos como "porque" (causa) — para
depois montar o sentido da frase e guardar o que a pessoa contou.

Para cada palavra, `analisador_frases.py` dá a classe gramatical (padrão
UPOS), o lema ("abriu" → "abrir") e a palavra de que ela depende, com o tipo
de ligação (padrão Universal Dependencies: sujeito, objeto, conectivo…).

```
python analisador_frases.py "A menina abriu o guarda-chuva porque começou a chover."
```

## Dois modelos, treinados do zero

| | onde treina | modelo | execução no Crivo |
|---|---|---|---|
| `scripts/treinar_analisador.py` | CPU (NumPy) | rede de janela + parser por transições (Chen & Manning, 2014) | NumPy |
| `scripts/treinar_analisador_biafim.py` | GPU (Colab) | BiLSTM 2×200 + biafim (Dozat & Manning, 2017) | NumPy (LSTM e árvore máxima de Chu-Liu-Edmonds), sem torch |

`notebooks/treinar_analisador_colab.ipynb` roda o treino biafim no Google
Colab com GPU e gera `modelo.npz` + `meta.json` para `artefatos/analisador_pt/`.
A execução em NumPy é conferida contra o torch antes da avaliação.

Os pesos só são usados se a avaliação no **teste oficial** (frases que o
treino não vê) passar do mínimo em `analisador_frases.MINIMO`; sem pesos
aprovados ou sem NumPy, o analisador fica desligado.

## Primeira versão no repositório (modelo de CPU)

`artefatos/analisador_pt` traz o modelo de CPU (8 épocas do etiquetador, 10
do parser, semente fixa). Teste oficial do Bosque, 1.167 frases, 27.604
palavras, pontuação incluída:

| classe (UPOS) | lema | UAS (ligação certa) | LAS (ligação e tipo certos) |
|---|---|---|---|
| 96,3% | 97,9% | 84,3% | 80,3% |

Cerca de 1–3 ms por frase. O modelo biafim do Colab deve substituí-lo se
tiver notas melhores no mesmo teste.

## Dados e licença

UD Portuguese-Bosque, commit fixado e SHA-256 conferido
(`dados/origem_ud_bosque.json`), licença **CC BY-SA 4.0**. Crédito:
Universal Dependencies, UD_Portuguese-Bosque (Rademaker et al., 2017),
conversão do Bosque, Floresta Sintá(c)tica, Linguateca. Os arquivos do
treebank não ficam no repositório; os pesos derivados seguem a mesma licença.

Limites: o Bosque é texto jornalístico; fala informal ("tô", "pra") é
normalizada antes, mas frases muito coloquiais devem ter mais erros.
