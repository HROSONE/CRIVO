# Próximo nível: medição, fichas, quadro único e vetores (02/10/2026)

## 1. Bateria de medição

`avaliacoes/bateria_v1/` tem 232 perguntas de astronomia (com resposta na base
ou que devem ser recusadas) e 25 diálogos curtos, em dois conjuntos:

- **dev**: guia o desenvolvimento;
- **retido**: só medição; não se ajusta código olhando suas falhas.

`scripts/avaliar_bateria.py` classifica cada resposta como acerto, parcial,
recusa indevida, **assunto errado** (o erro grave: responder sobre outro tema)
ou invenção. `testes_bateria.py` é uma catraca: o CI falha se os números
registrados em `limiares.json` piorarem.

| | antes de #48 | #48 | #49 | agora |
|---|---|---|---|---|
| fatos dev | 72/119 | 85/119 | 88/119 | 98/124 |
| fatos retido | 25/78 | 40/78 | 41/78 | 46/81 |
| assunto errado (dev+retido) | 9 | 6 | 6 | 2 |
| invenções (dev+retido) | 4 | 4 | 4 | 0 |
| diálogos | 4/25 | 4/25 | 25/25 | 25/25 |

Os totais mudaram porque perguntas antes sem resposta (Big Bang, idade do
universo, temperatura do Sol, luas de Júpiter, Webb) ganharam fichas.

## 2. Fichas com fonte no lugar da base antiga

Fichas novas no catálogo expandido (sem alterar a assinatura da rede): Sol,
Big Bang, luas galileanas, Telescópio James Webb, planeta anão, Plutão,
eclipse, cometa e Via Láctea. Vênus (467 °C) e Lua (ciclo de 29,5 dias)
ganharam fatos migrados da base antiga, agora com fonte; a base antiga dizia
460 °C. Fontes: NASA, ESA, IAU e IPAC/Caltech.

As páginas foram conferidas por trechos em mecanismo de busca, pois o acesso
direto estava bloqueado na rede do ambiente; cada fonte registra isso no campo
`verificacao`. **Revisão humana recomendada.**

A ficha tem prioridade: uma resposta antiga por semelhança só vale se mencionar
o assunto e cobrir a pergunta; senão o Crivo admite o limite. Fichas cujo nome
coincide com entradas antigas (`somente_busca`) atendem apenas a perguntas de
propriedade, para não quebrar definições, elipses e referências existentes.

## 3. Quadro único de interpretação

`CompositorTextual.interpretar()` produz um `QuadroFactual` (intenção, assunto,
outros conceitos, pistas, motivo de recusa), consumido pelo planejador da busca e
pelas decisões do `crivo.py`, e registrado no histórico (`quadro_factual`). Os
demais motores da cascata continuam existindo; o quadro unifica o caminho
factual, que é onde estavam os erros de assunto.

## 4. Vetores de palavras treinados do zero

`scripts/treinar_vetores_palavras.py` treina skip-gram com amostragem negativa
em NumPy sobre artigos da Wikipédia em português (mesma fonte do pré-treino,
SHA verificado), no workflow `treinar-vetores.yml`, que grava os vetores na
branch. A busca aceita **uma** palavra aproximada por similaridade e a resposta
declara a aproximação ("Entendi “fortes” como próximo de “intensos”…").

Os vetores só são usados se o relatório do treino passar no controle de
qualidade: pares equivalentes conhecidos precisam ficar claramente mais próximos
que pares aleatórios. O primeiro treino (8 mil artigos, 2 minutos) não passou e
fica desligado. Os números da tabela acima são **sem** vetores.

## 5. Sinônimos e antônimos: experimento e decisão

O treino de 100 mil artigos passou no controle inicial (sinônimos 0,58 contra
pares aleatórios 0,00), mas aproximou **antônimos tanto quanto sinônimos**
(0,60 contra 0,58; "rápido"/"lento" 0,79). Usá-los poderia trocar *frio* por
*quente*. Dois experimentos, medidos em pares **reservados** do léxico
`dados/lexico_sinonimos_antonimos_pt.json` (palavras ausentes do ajuste):

| experimento | sinônimos reservados | antônimos reservados |
|---|---|---|
| vetores originais | 0,472 | 0,523 |
| counter-fitting (`scripts/ajustar_vetores_lexico.py`) | 0,472 | 0,524 |

O ajuste separa perfeitamente os pares que viu (0,985 contra 0,109), mas **não
generaliza**. Um classificador logístico sinônimo × antônimo sobre os vetores
também não generalizou (AUC 0,51 nos reservados). Conclusão: vetores de
contexto desse porte não distinguem sinônimo de antônimo, e aproximar por
similaridade não é seguro. Eles continuam desligados; o controle agora exige
equivalentes ao menos 0,15 acima dos antônimos.

A busca usa diretamente o **léxico curado** (180 pares autorais, com flexões):
um sinônimo listado pode substituir **uma** palavra da pergunta, com aviso
("Entendi “fortes” como próximo de “intensos”…"); um antônimo listado nunca é
aproximado. Ganho medido: dev 98 → 99/124, retido 46/81, sem aumento de
assunto errado ou invenção. Ampliar o léxico (ou usar um tesauro com licença
compatível) amplia a cobertura sem o risco dos vetores.
