# Gerador de frases com verificador de fidelidade (2026-10-02)

## O que muda

Antes, a reação a um relato tinha sempre a mesma forma:
"Reação, eco. Noção. Pergunta." Agora o conteúdo continua decidido do
mesmo jeito (o **plano**), mas a forma sai de três peças:

1. **Candidatas** (`gerador_frases.candidatos`): o mesmo plano dito de
   várias formas: reação + eco ("Poxa, você perdeu o ônibus."), eco como
   pergunta ("Você passou na prova? Parabéns!"), "É, …" antes da noção e
   "E …" antes da pergunta.
2. **Verificador de fidelidade** (`gerador_frases.verificar`): descarta a
   candidata que
   - acrescenta palavra de conteúdo que não veio da fala, do plano nem do
     vocabulário de conversa (a fala passada para "você" conta: "fiz" →
     "fez");
   - perde parte do plano (eco, causa ou noção);
   - acrescenta negação;
   - repete reação ("Que legal… Que bom saber disso.").
3. **Pontuador neural** (`pontuador_frases`): o transformer causal do
   projeto (`artefatos/linguagem_profunda`, 2,6 M parâmetros, treinado do
   zero) agora roda em NumPy (`pesos_numpy.npz`, float16) e com BPE em
   Python puro, sem PyTorch nem tokenizers. Ele escolhe, entre as
   candidatas válidas que não repetem a estrutura da resposta anterior, a
   mais natural como resposta à fala. Leva cerca de 6 ms por candidata.

Também: a pergunta da noção só é usada quando o tempo verbal combina com o
relato ("vou comemorar com uma pizza" não recebe "Qual sabor você pediu?").

## Medição

| | antes | depois |
|---|---|---|
| presença dev: turnos ok / estrutura seguida igual / palavras inventadas | 35/35, 2, 0 | 35/35, 1, 0 |
| presença retido / retido2 (agregado) | 15/19, 0, 0 · 27/29, 1, 0 | 15/19, 0, 0 · 27/29, 0, 0 |
| conversa cotidiana dev / retido / retido2 | 36/36 · 23/24 · 12/15 | igual |
| memória de relatos dev / retido / retido2 | 12/12 · 8/8 · 10/10 | igual |

Pontuador na bateria `fluencia_v1` (par natural × estranha, escrita antes
de qualquer ajuste): **dev 19/25, retido 17/25**. É um modelo pequeno
(perplexidade ~86): acerta ordem de palavras, redundância e repetição, mas
erra metade dos erros de conjugação e concordância. Por isso ele só
escolhe a forma; quem garante que nada é inventado é o verificador, e o
gerador não monta frases com esses erros.

Catracas novas: `avaliacoes/presenca_v1/limiares.json`
(`mesma_estrutura_max`, `fatos_novos_max`) e
`avaliacoes/fluencia_v1/limiares.json`.

## Próximo passo possível

Um pontuador melhor vem de um modelo treinado por mais tempo. O workflow
`treinar-linguagem-profunda.yml` já faz isso (12 000 + 3 000 passos); um
checkpoint novo só entra se passar na `fluencia_v1` (dev e retido) acima
da linha de base. Depois do treino, rodar `python
scripts/exportar_pontuador.py`.
