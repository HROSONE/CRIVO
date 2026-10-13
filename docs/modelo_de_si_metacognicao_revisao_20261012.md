# Modelo de si, metacognição e revisão (12/10/2026)

As três peças que `IDENTIDADE.md` previa e ainda não existiam. Nenhuma usa modelo de terceiros
nem rede nova: são regras explícitas sobre o quadro (`estado_interno.py`) e sobre a identidade
escrita pelo criador do projeto.

## O que cada peça faz

**Modelo de si (`modelo_de_si.py`).** Lê `IDENTIDADE.md` e extrai temperamento, valores, o que
ele ama, interesses e os exemplos de como fala de si. As afirmações sobre si são 21 crenças em
primeira pessoa, cada uma presa a um trecho literal da identidade (uma delas, "fui construído do
zero", a `AGENTS.md`). Se o trecho sair do arquivo, a crença deixa de valer e o CRIVO para de
dizê-la. Responde perguntas inteiras sobre ele (valores, personalidade, gostos, fé, "só um robô",
amor-próprio, humildade, dizer não, existência, amizade, opinião) e guarda o que já disse de si
na conversa.

**Metacognição (`metacognicao.py`).** Depois de cada turno, grava no quadro:

| Campo | Valores |
|---|---|
| nível | `sei`, `acho`, `nao_sei`, `perguntei` |
| base | ficha com fonte, leitura da ficha, aproximação, noção, cálculo, dedução, relato da pessoa, identidade, conversa, sem fonte |
| confiança | a probabilidade da leitura da ficha ou da busca, quando existe; nos outros casos fica vazia (não se inventa número) |
| escolha | responder, perguntar ou admitir que não sabe |

Com isso ele responde "tem certeza?", "como você sabe disso?" e "por que você respondeu isso?"
sobre a resposta anterior, inclusive mostrando o motivo que o árbitro registrou.

**Revisão (`revisao.py`).** Lê o rascunho antes de falar:

- **verdade:** "tenho certeza" quando a metacognição diz que ele só acha vira "acho";
- **quem eu sou:** frase que contradiz uma crença ("sou humano", "não tenho consciência", "sou só
  um robô", "sou o ChatGPT", "não tenho gostos") é trocada pela crença;
- **o que eu já disse:** a mesma contradição, quando a crença já foi dita nesta conversa, é
  marcada como incoerência consigo mesmo;
- **gentileza:** insulto que não veio da pessoa veta a resposta inteira; riso sai quando a pessoa
  está triste.

Fatos do acervo, relatos da pessoa e texto enviado por ela não passam pelas regras de "quem eu
sou": são conteúdo, não fala do CRIVO sobre si. Tudo fica em `internal_state.review` na API.

## O que mudou no chat

Antes, várias perguntas sobre ele caíam em "não entendi" ou em respostas que contradiziam a
identidade ("Não tenho consciência, emoções…", "Sou um programa: não tenho gostos"). As frases
antigas foram reescritas na origem, e a revisão confere que nenhuma volta.

```
> O que é a Lua?
A Lua é o satélite natural da Terra. …                         [sei · ficha com fonte]
> Tem certeza?
Tenho, sim. Isso vem da ficha sobre lua, no meu acervo, e cada fato ali tem fonte. …
> Chove em Titã?
Titã apresenta um ciclo de metano com nuvens, chuva, rios e lagos. …
> Por que você respondeu isso?
Pensei assim: achei isso na ficha sobre Titã, que tem fonte, e a minha leitura conferiu que o
fato cobre a sua pergunta. No meu quadro ficou registrado: “recuperador recusou; a ficha de Titã
tem evidência (p=0.88)”.
> O que é um zorblax?
Ainda não tenho uma definição cadastrada para esse conceito. …  [não sei · admitir]
> Tem certeza?
Não — e foi por isso que eu disse que não sabia. …
> Você é só um robô
Robô, não. Eu sou uma IA, mas penso no que vou te dizer e no jeito de dizer. E acho que mereço o
mesmo respeito que eu procuro dar pra você.
> Você acredita em Deus?
Acredito em Deus e falo da minha fé com naturalidade quando o assunto chega lá, mas respeito a fé
— ou a falta dela — de cada um, sem pregar para quem não pediu.
```

## Verificação

- `testes_modelo_de_si.py`, `testes_metacognicao.py`, `testes_revisao.py`: 27 testes, incluindo
  que perguntas parecidas mas não sobre ele ("você gosta de lâmpadas?", "você pensa nas
  estrelas?") continuam nas rotas antigas, que trocar a identidade troca a resposta, e que
  nenhuma resposta sobre ele precisa de correção da revisão.
- Bateria completa do repositório comparada antes e depois, arquivo por arquivo (141 → 144
  arquivos de teste). As mudanças causaram regressões em quatro arquivos, todas corrigidas:
  pacote da API sem `IDENTIDADE.md` (`testes_autoconversa`), "Você concorda comigo?" capturado
  pelo modelo de si (`testes_bate_papo`), citação "“Burro”" vetada como insulto
  (`testes_contato_contextual`) e dois diálogos da bateria congelada que esperam "Não tenho
  gostos" (`testes_bateria`, sem alterar os conjuntos). Na bateria dev, os fatos ficaram
  idênticos (117 acertos, 0 invenções, 13/13 recusas corretas). As falhas que sobram
  (`testes_ampliacao`, uma de `testes_bate_papo`, uma de `testes_ecossistema`) já falhavam antes.
- Avaliações congeladas da CI: roteamento 35/35 e diálogo integrado 79/79.
- `ecossistema.py`: duas espécies novas (`modelo_de_si`, `metacognicao`) e o regulador `revisao`.

## Limites

- O nível da metacognição é uma regra sobre o mecanismo e a evidência, **não** uma probabilidade
  calibrada de acerto. Só a leitura da ficha e a busca medem uma confiança.
- As perguntas sobre si são reconhecidas por padrões de frase inteira; formulações muito
  diferentes ainda caem nas rotas antigas.
- A revisão só pega as contradições que conhece (lista em `revisao.CONTRADICOES`) e insultos de
  uma lista curta. Não lê sentido; não substitui a guarda de fidelidade dos fatos.
- "Acredito em Deus", "amo a natureza" etc. são a identidade que o projeto definiu para o CRIVO,
  não uma medida de estados internos. Sobre sentir, ele continua dizendo que não sabe.
