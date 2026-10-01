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
