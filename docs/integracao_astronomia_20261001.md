# Integração do acervo avançado de astronomia

O material de `pesquisa/acervo-conhecimento-crivo`, congelado no commit
`5f5e8d037c0fa381735670575618e02b5f7e68cb`, passou a alimentar respostas do
motor padrão. A branch de pesquisa permanece independente para receber novos
trabalhos; esta integração não sobrescreve seu conteúdo.

Foram incorporadas **121 unidades factuais autorais**: 56 ampliam conceitos
existentes e 65 descrevem **19 conceitos novos**. A seleção aborda formação
planetária, instabilidade de fluxo, acreção de seixos, diferenciação e sismologia
planetária, cadeia próton-próton, ciclo CNO, degenerescência, kilonovas, processo s,
gás circumgaláctico, feedback, remoção de gás, abundâncias galáxia–halo, lentes,
BAO, tensão de Hubble, distâncias, covariância e impacto cinético.

As fichas existentes também recebem limites e evidências sobre neutrinos,
cristalização, exoplanetas, Roche, marés, CMB, matéria escura, imagens EHT,
oceanos de luas e DART. As medidas binária e heliocêntrica do DART são distintas.
A atualização DESI de julho de 2026 é descrita no contexto de seu teste Lyα,
sem apresentar a natureza da energia escura como questão encerrada.

## Respostas e rastreabilidade

Além de definições e funcionamento, o compositor consulta fatos marcados como
evidência ou limite. A resolução utiliza o assunto completo, preservando
qualificadores desconhecidos; não converte uma pergunta sobre uma alegação
inventada numa resposta sobre o termo mais próximo.

Exemplos no CLI ou laboratório web:

```text
O que é migração planetária?
Como funciona ciclo CNO?
Quais são as evidências de matéria escura?
Qual é a fonte?
Quais são os limites disso?
O que é sismologia planetária?
Quais são os limites de kilonova?
```

`Qual é a fonte?` recupera as referências das unidades efetivamente exibidas,
incluindo referências complementares. Esses comandos também funcionam com
outros catálogos; não dependem de respostas prontas para cada pergunta astronômica.

O [manifesto](../dados/integracao_astronomia_20261001.json) registra posição,
conceito, fonte, origem documental e hashes dos arquivos anteriores. A
[verificação bibliográfica](../avaliacoes/fontes_astronomia_20261001.json)
preserva URLs e hashes de **54 fontes consultadas**, incluindo o texto integral
de dois manuscritos de autores, sem distribuir páginas ou PDFs remotos.

O diagnóstico novo registrou **17/17 consultas** corretas, incluindo uma sequência
de evidência, fonte e limite. A [comparação na prova congelada](../avaliacoes/astronomia_comparacao_congelada_20261001.json)
preservou **31/58** antes e depois, com **14/14 controles** e nenhuma regressão
nessa rubrica. Essa prova continua abaixo do critério de certificação.

## Correções e pendências

Das 27 alterações propostas no acervo, **26 foram aplicadas**. A afirmação
sobre comensurabilidade e ressonância passou a citar o manuscrito de Choksi e
Chiang: a nota inicial distingue razão entre períodos de libração de um argumento
ressonante. Fontes complementares continuam associadas ao escape e à resistência
material no limite de Roche.

Permanece pendente a substituição da referência da afirmação sobre estabilidade
dentro da esfera de Hill (`mundo_esfera_hill`, fato 2). O periódico bloqueou o
acesso ao conteúdo de Domingos et al. (2006); conferir somente o título e DOI
não é suficiente para promover a proposta. A referência anterior permanece,
e a pendência está explícita no manifesto.

O restante das afirmações do acervo não recebe aprovação automática por esta
seleção. As auditorias documentais originais são preservadas como registros de
pesquisa, com suas limitações. Não houve certificação científica independente
nem alteração da porcentagem de certificação do Crivo.

## Compatibilidade e verificação

Os 20 novos conceitos pertencem ao catálogo do compositor. Os 241 rótulos e
as perguntas do classificador neural permanecem iguais, e sua assinatura
continua compatível com os pesos já treinados. Nenhum peso foi alterado e o
workflow de linguagem profunda permanece intacto. O treinamento em andamento
continua sobre seu próprio commit congelado.

Os testes verificam consultas reais, aliases, funcionamento, fontes específicas,
retomada contextual, recusa de qualificadores inventados, limites científicos,
proveniência e compatibilidade neural. Um conceito fictício fora da astronomia
verifica que a nova consulta de evidência se generaliza ao esquema do catálogo.
Os casos desta integração são diagnósticos de desenvolvimento, não prova cega
de domínio científico irrestrito.

```bash
python -m unittest testes_astronomia_avancada -v
python -m unittest discover -p 'testes*.py'
```

As fontes novas usam `somente_referencia` e `reproducao_autorizada: false`.
Isso registra bibliografia de sínteses originais, sem presumir autorização de
cópia integral, imagens, tabelas, dados ou endosso dos autores e instituições.
Não há download ou serviço externo durante a conversa.

## Compreensão da própria base (02/10/2026)

Uma sondagem com perguntas comuns mostrou que o Crivo tinha os fatos, mas não
os alcançava: "Como as estrelas nascem?" e "Como Júpiter se formou?" (ordem de
palavras), "Europa tem oceano?" e "Mercúrio tem luas?" (propriedade),
"Quantos metros tem uma unidade astronômica?" (quantidade), "Qual a idade do
Sistema Solar?" (tempo) e "O que foi a missão DART?" (nome citado só dentro
de fatos). Pior: "Quantas luas tem Júpiter?" respondia sobre a Lua da Terra
e "Encélado tem vida?" sobre a vida de cães e gatos.

`CompositorTextual.buscar_fatos` localiza o fato que contém **todas** as
pistas da pergunta dentro do conceito citado (ou, sem ficha própria, um nome
raro presente em até três fatos, avisando isso). Perguntas de quantidade e
tempo preferem fatos com valor numérico; sem valor, a resposta diz
"Não tenho esse valor numérico cadastrado". Não responde perguntas causais
("por que"), negações, hipóteses, qualificadores ausentes ou relações entre
dois conceitos, cuja direção pertence ao raciocinador. A fonte e os limites
continuam retomáveis com "Qual é a fonte?" e "Quais são os limites disso?".

No `crivo.py`, uma resposta aproximada da base anterior só vence a busca
factual quando é candidata clara e menciona o assunto; uma recusa do
compositor não oculta mais uma resposta cadastrada que cobre todas as
palavras ("Por que Plutão não é mais planeta?"; "não é mais X" é tratado
como "deixou de ser X"). Na prova congelada, 31/58 passou a 32/58, com
14/14 controles e nenhum fato fora de escopo.

Lacunas de conteúdo (recusadas corretamente, sem ficha cadastrada): Big Bang,
idade do universo, temperatura do Sol, telescópio James Webb e número de luas
de Júpiter. Preenchê-las exige novas fichas com fontes verificadas.
Testes: `python -m unittest testes_busca_factual -v`.

## Causa, mecanismo e conversa cotidiana (02/10/2026)

A parte útil da proposta de consolidação (PR #47) foi incorporada à busca
factual, sem o módulo novo que, na comparação, respondia "Como se define
evolução estelar?" com a definição de API. Perguntas de causa e mecanismo
em paráfrase ("O que deixa Marte com aparência vermelha?", "De que maneira
o eixo inclinado de Urano afeta suas estações?") agora recuperam o fato do
assunto citado. Uma pergunta causal exige linguagem causal no próprio fato
("produz", "por causa", "ajudam a explicar"); comparação exige um fato que
cite os dois termos; um único elo para a definição de outro conceito citado
só é acrescentado quando há conteúdo em comum. "Descreva X …" e "Explique
a origem de X" também foram atendidos. Na prova congelada: 32/58 → 34/58,
14/14 controles, nenhum fato fora de escopo.

`conversa_cotidiana.py` trata o bate-papo curto com o turno anterior:
respostas ao "como você está?", reações ("legal", "haha", "sério?"),
"sim/não" após uma oferta, "me fala mais", "pode repetir?", "qual é o meu
nome?", curiosidades (fatos com fonte) e preferências pessoais sobre assuntos
cadastrados. "Sim/não" que respondem a um esclarecimento pendente continuam
no fluxo anterior. Relatos neutros ("eu moro no Brasil") não recebem mais
perguntas de plano de ação. Testes: `testes_conversa_cotidiana.py`.
