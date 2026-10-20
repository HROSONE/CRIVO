# Fase 2 — pré-treino continuado do 17M: resultado (12/10/2026)

**Reprovada nas metas que eu mesmo fixei, com melhora real em tudo o que foi medido.** A base
exportada serve de ponto de partida para a fase 3, mas não vai para o chat
(`ativo_no_chat=false`, `promovido=false`).

- Mesmo 17M (17.428.224 parâmetros), mesmos dados próprios (Wikipédia pt, OASST2, acervo),
  passos 14.433 → 54.433 (+40.000, ~655M tokens), 5% de janelas com trecho repetido.
- Rodou em 4 sessões de T4 grátis em três contas. Os checkpoints numerados permitiram retomar
  depois de duas quedas sem perder mais de ~70 passos.
- Base: `MyDrive/CRIVO/transformer-17m-continuo/base`, pesos sha256
  `57e809f42e2848bc4765faf3ada83998d6cad25d27954183d25a5f25a9573384`.

## Metas e resultado

| Medida (sonda do próprio notebook) | Início (passo 14.433) | Fim (54.433) | Melhor | Meta | Passou? |
|---|---|---|---|---|---|
| Cópia top-1 de trecho repetido | 11,0% | 50,9% | 52,6% (51.933) | ≥ 80% | não |
| Perda do nome inventado na 2ª menção | 2,54 nats | 2,14 nats | 1,71 (26.933) | ≤ 1,0 | não |
| Perda de validação | 3,2252 | 2,9462 | 2,9462 | não piorar | sim |

Histórico completo das 17 sondas em `resultado_fase2.json`.

## Leitura

- A cópia em contexto quase quintuplicou, mas estabilizou em ~51% nos últimos 10 mil passos,
  com a taxa de aprendizado já baixa. Mais passos do mesmo jeito dificilmente chegam a 80%.
- A cópia de nomes inventados oscila muito entre sondas (1,71 a 2,49) e terminou só um pouco
  melhor que o início. É o ponto fraco que mais importa para a fase 3, que pede o nome exato.
- A validação melhorou o tempo todo: o modelo não perdeu português ao aprender a copiar.

**Correção de um número que eu vinha usando.** Durante o treino comparei com "26,7% de cópia e
1,71 nats" como ponto de partida. O 26,7% é a sonda avulsa (`scripts/sonda_copia_17m.py`) nos
pesos do leitor, outro modelo (`sonda_copia_leitor_17m.json`), e 1,71 é a sonda do passo 26.933,
não do início. O ponto de partida comparável, medido pelo mesmo notebook, é 11,0% e 2,54 nats.
Com ele, a cópia de nomes melhorou um pouco em vez de piorar, como eu tinha dito.

## Limites

- A sonda usa 50 tokens aleatórios repetidos e um nome inventado; mede cópia em contexto,
  não conversa.
- Uma única corrida, sem repetição com outra semente.
- A tabela foi lida do print da célula 4; os checkpoints e o histórico original ficam no Drive.

## Próximo passo

A fase 3 (`experimentos/fase3_realizador_20261012/`) parte desta base, com o critério dela:
nome exato e fatos fiéis no teste cego. Se reprovar nesses dois pontos, o próximo passo é
reforçar a cópia de nomes em frases reais nos dados, não baixar as metas.
