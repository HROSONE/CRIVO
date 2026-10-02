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

## Modelo no repositório

`artefatos/analisador_pt` traz o modelo **biafim treinado no Google Colab**
(GPU T4, 40 épocas, semente 20261002, notebook deste repositório). Teste
oficial do Bosque (1.167 frases, 27.604 palavras, pontuação incluída),
reavaliado fora do Colab com a execução em NumPy:

| modelo | classe | lema | UAS (ligação certa) | LAS (ligação e tipo) | tempo/frase |
|---|---|---|---|---|---|
| CPU: janela + transições | 96,3% | 97,9% | 84,3% | 80,3% | 1–3 ms |
| **Colab: BiLSTM + biafim** | **97,0%** | **98,0%** | **88,9%** | **85,3%** | ~16 ms |

O biafim erra 29% menos ligações. Ainda erra casos pontuais (em "A menina
abriu o guarda-chuva porque começou a chover", liga "porque" a "chover" em
vez de "começou").

## Dados e licença

UD Portuguese-Bosque, commit fixado e SHA-256 conferido
(`dados/origem_ud_bosque.json`), licença **CC BY-SA 4.0**. Crédito:
Universal Dependencies, UD_Portuguese-Bosque (Rademaker et al., 2017),
conversão do Bosque, Floresta Sintá(c)tica, Linguateca. Os arquivos do
treebank não ficam no repositório; os pesos derivados seguem a mesma licença.

Limites: o Bosque é texto jornalístico; fala informal ("tô", "pra") é
normalizada antes, mas frases muito coloquiais devem ter mais erros.

## Passo 2: sentido e memória do que a pessoa conta (`sentido_frases.py`)

Cada oração vira um evento: ação (lema), agente, objeto, tempo, lugar,
negação e relações com outras orações pelos conectivos — porque/pois → causa,
quando → tempo, se → condição, para → finalidade, embora → concessão.

O Crivo guarda os eventos dos relatos (frases afirmativas) e responde
perguntas sobre eles **como relato** ("Você me contou que…"), nunca como fato
do conhecimento:

```
VOCÊ: meu cachorro latiu a noite toda porque viu um gato
VOCÊ: por que ele latiu?        → Você me contou que foi porque viu um gato.
VOCÊ: quem latiu?               → Pelo que você me contou, foi seu cachorro.
VOCÊ: o ônibus atrasou hoje
VOCÊ: por que o ônibus atrasou? → Você me contou que o ônibus atrasou hoje, mas não disse por quê.
```

Pergunta que não casa com nada contado (outro verbo, outro sujeito) segue o
caminho normal; conhecimento com fonte continua respondendo.

Bateria `avaliacoes/memoria_relatos_v1` (escrita antes da implementação):

| | antes | depois |
|---|---|---|
| dev (12 diálogos) | 2 | 12 |
| retido (8 diálogos) | 2 | 8 |

Limites: o retido tem só 8 diálogos e segue a mesma forma do dev; um erro do
analisador vira erro de memória (por isso o conectivo também é procurado na
oração encaixada); verbos em primeira pessoa são citados entre aspas em vez
de reconjugados.
