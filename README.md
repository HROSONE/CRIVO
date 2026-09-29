# Crivo v0.4 (em desenvolvimento)

Assistente de conversa em português, primeiro teste.
Assuntos: plantas, animais, clima, tempo, estações do ano, sistema solar, coisas de casa e programação.

## Interpretar o pedido antes de consultar o conhecimento

`interpretacao_pedidos.py` separa **intenção, alvo, condições e modo de
apresentação**. O quadro é interpretado antes dos motores de assunto.
Em `quais galáxias você conhece?`, `você conhece` expressa um pedido de
informação sobre a base, não uma propriedade que as galáxias precisam ter.
A categoria é resolvida no grafo ativo; o parser não contém nomes de
galáxias, planetas, aves ou objetos dos testes.

A mesma operação atende `quais aves você conhece?`, `quais planetas existem?`,
`me dê exemplos de ...` e categorias de um grafo personalizado. Todos os
qualificadores e filtros precisam ser interpretados; não se elimina um
critério desconhecido para listar só a parte reconhecida. A lista mostra
os exemplos disponíveis na instalação, sem afirmar que cobre o mundo.

Pedidos de **exemplos** excluem classes intermediárias da taxonomia
(destinos de `tipo_de`). Pedidos de **tipos** mostram essas classes.
`Galáxia espiral` é uma classe; Andrômeda e Via Láctea são exemplos.
O retorno preserva as provas e os IDs exibidos para filtros com `desses`.
`Fale sobre a primeira` usa somente a lista do turno anterior; não resolve
por uma lista antiga nem por itens ocultos pela paginação.

`O que você sabe sobre DNA?` e `você conhece Andrômeda?` usam o alvo inteiro
nos motores de informação. Um objeto conhecido apenas pelo grafo pode ser
explicado por suas relações diretas, sem inventar um verbete ou inverter
órbitas/composição. A ausência de uma categoria no grafo também não apaga
uma resposta já disponível em outro catálogo ativo. O histórico interno
registra o quadro em `pedido` para auditar a interpretação.

Interjeições completas como `meu Deus`, `nossa` e `eita` são reações sociais;
não abrem uma busca factual. Uma reação seguida de pergunta mantém o pedido.
Mensagens não interpretadas pedem assunto/intenção, sem despejar o catálogo.

O avanço é uma camada semântica limitada e reutilizável; não envolve treino
nas perguntas da captura ou treinamento de um novo modelo neural. Os testes
geram entidades e hierarquias fora do currículo, com pertencimentos/filtros
calculados pelo gerador como oráculo independente. Também verificam casos
negativos, API, escopo da base, classes/exemplos e contexto limitado.

```bash
python -m unittest testes_interpretacao_pedidos -v
```

## Conversa informal e feedback

O CRIVO distingue atos sociais completos de consultas de conhecimento.
`Eae, beleza?`, `Oi, tudo bem?` e `Como cê tá?` iniciam contato;
`tô bem` ou `sim` respondem ao contato imediatamente anterior. Um `sim`
em uma escolha de esclarecimento continua sendo tratado pelo motor de opções.

Críticas dirigidas ao assistente e avaliações como `essa resposta está errada`,
`não foi isso que eu pedi` e `isso não faz sentido` recebem uma resposta de
feedback. O motor consulta o pedido do turno imediatamente anterior para
pedir o trecho a conferir. Não muda um fato para concordar com uma reclamação.
Falhas e críticas sucessivas recebem tratamentos diferentes; uma saudação
ou outro pedido substitui o contexto anterior. A API reconstrói esse estado
pelo histórico de perguntas, sem compartilhar contexto entre usuários.

Saudações, feedback e pedidos também podem aparecer juntos:

```text
Eae, beleza?
Tô bem, e você?
Oi, tudo bem? O que é DNA?
Essa resposta está errada
Não foi isso que eu pedi. Você pode explicar o que é RNA?
Não, quero saber o que é Andrômeda
```

As regras reconhecem combinações de sujeito, predicado, intensificador,
vocativo e abertura. `Um burro é um mamífero?` e comandos que mencionem
`tudo bem` seguem para os motores factuais/de programação. Negação do pedido,
código e qualificadores são conservados ao separar uma abertura social.

O avanço é de interpretação de intenções e continuidade curta, com gramática
limitada. Não é um novo treino neural nem compreensão irrestrita de texto.
Os testes incluem a captura, variantes, falas compostas, proteção de consultas,
esclarecimento, feedback e isolamento da API:

```bash
python -m unittest testes_conversa_informal -v
```

## Conversa sobre o próprio CRIVO e capacidades da instalação

Perguntas como `Você pensa?`, `Você sente?` e `Você é consciente?` usam
uma intenção de autoconversa, sem procurar um assunto por semelhança
lexical. Antes dessa correção, `pensa` podia recuperar a resposta sobre
lâmpadas e `sente` a resposta sobre meses. Agora o CRIVO descreve seu
processamento e seus limites; ele não declara consciência ou emoções.
A rede classificadora só é mencionada quando realmente está carregada.

`O que você sabe fazer?`, `ajuda` e `assuntos` listam as funções e o
conhecimento disponíveis **na instalação ativa**. O catálogo usa os
verbetes carregados, as áreas declaradas no currículo ampliado e os módulos
presentes; bases personalizadas não anunciam o conhecimento da base padrão.
`Só isso?` ou `Como assim?` podem detalhar a autoconversa anterior. Essa
continuidade expira após outro assunto ou saudação, e a API a reconstrói
pelo histórico de perguntas.

```text
O que você sabe fazer?
Só isso?
Você pensa?
Como assim?
Você pode explicar o que é DNA?
Você acha que a Terra é um planeta?
```

Pedidos completos mantêm o conteúdo factual: `Você pensa que o Sol é uma
estrela?` consulta o motor existente. Qualificadores desconhecidos e
condicionais não são apagados para fabricar uma certeza. Perguntas pessoais
não reconhecidas, como `Você dorme?`, pedem reformulação antes do ranking;
perguntas factuais reais sobre lâmpadas continuam funcionando.

Este é um discriminador de intenções com gramática limitada, não compreensão
universal de conversa. Os testes reproduzem as capturas, variam formas
informais, conferem bases fictícias, expiração, pedidos informativos e API.

```bash
python -m unittest testes_autoconversa -v
```

## Conhecimento com fontes, composição e conversa

O currículo `conhecimento_expandido.json` acrescenta **25 conceitos e 97
unidades factuais**, com referências de NASA, NHGRI, MDN, Google e IBM.
Inclui Andrômeda, galáxias, buracos negros, DNA, RNA, genes, internet,
APIs, aprendizado de máquina e redes neurais. As definições e os detalhes
são dados revisados; a conversa não modifica esses arquivos.

O módulo `composicao_textual.py` planeja textos sobre até três conceitos,
seleciona fatos e os organiza em parágrafos, resumos, tópicos ou roteiros
curtos. Funciona também com verbetes editoriais e bases fictícias: não
existe uma resposta pronta para cada combinação. Cada sentença factual
mantém o vínculo com sua unidade de origem. Termos desconhecidos ou
modificadores não atendidos não são descartados para simular uma resposta.

```text
O que é Andrômeda?
Qual a distância dela?
Escreva um texto sobre DNA e RNA
Mais curto
Em tópicos
Continue
Qual é a fonte?
Faça um roteiro curto sobre fotossíntese
Escreva um texto sobre HTML, CSS e JavaScript
```

`Mais curto` e `Em tópicos` usam somente o conteúdo apresentado;
`Continue` e `Explique melhor` acrescentam fatos ainda não usados e avisam
quando eles acabam. `Não entendi` reduz a quantidade de informação.
`E o RNA?` troca o assunto mantendo o formato de composição.
Pronomes como `ela` exigem um único assunto no turno anterior; perguntas
relacionais passam pelo mecanismo de prova existente. Saudações, dúvidas
e assuntos desconhecidos expiram o contexto. A API reconstrói esse estado
pelo histórico de perguntas, sem compartilhar conversas entre instâncias.

A referência ao braço citado na resposta sobre Via Láctea agora tem um
vínculo editorial explícito com o **Braço de Órion**, incluindo localização.
O grafo recebeu **8 entidades e 18 fatos**, incluindo os três planetas
que faltavam nas consultas por órbita. Todos os oito planetas do Sistema
Solar podem aparecer nessas consultas.

A preferência de `galáxia` pelo conceito geral, e de `API` pela definição
ampliada, é declarada em `aliases_preferidos`, sem desempate por ordem.
A API preserva o identificador público anterior `prog_http` mediante
`id_resposta`. Outros apelidos ambíguos continuam sem escolha automática.
As fontes são exibidas apenas para os fatos usados, inclusive referências
editoriais já cadastradas. Entradas sem referência informam essa ausência.

**Limite:** isto é composição factual controlada, com gramática limitada,
sem geração irrestrita de histórias, opiniões, instruções arbitrárias ou
novos fatos. Não usa modelos externos; o treinamento da rede é separado
da composição. Conhecimento novo entra pelo currículo revisado no código.

**Validação de desenvolvimento:** a sonda do currículo ampliado passou
de 0/32 para 32/32. Há testes de combinações de conceitos, bases fictícias,
referências, fontes, limites de frases, recusas e API.

## Ciência e psicologia pelo índice 1991–2026

`conhecimento_mundo.json` acrescenta um primeiro currículo de **44 conceitos,
119 fatos, 10 relações direcionais e 6 comparações**. Os temas foram escolhidos
no [Índice das Publicações 1991–2026](https://wol.jw.org/pt/wol/library/r5/lp-t/todas-as-publica%C3%A7%C3%B5es/%C3%ADndice/%C3%ADndice-de-publica%C3%A7%C3%B5es/%C3%ADndice-1991-2026).
Há referências a **22 artigos** e **11 fontes primárias complementares**
(NIMH, NHLBI, NASA e Convenção sobre Diversidade Biológica). São resumos próprios
de conteúdos selecionados, revisados em **29/09/2026**. O índice inteiro ainda
não foi incorporado.

O currículo inclui cérebro, neurônios, sinapses, memória, neuroplasticidade,
sono, ansiedade, estresse, depressão, apoio emocional, luto, procrastinação,
células, proteínas, fotossíntese, ciclo da água, efeito estufa, biodiversidade,
biomimética, ecolocalização, constelações, universo e energia solar.
Cada conceito tem nomes alternativos e unidades de definição, funcionamento,
função, exemplo ou limite quando há evidência cadastrada.

Cada fato declara fonte e natureza: `cientifico`, `psicologico`, `orientacao`
ou `religioso`. Interpretações religiosas aparecem atribuídas à publicação,
com a expressão **“Segundo a interpretação religiosa da publicação”**.
Informações científicas antigas são conferidas quando necessário: o currículo
usa os três estágios não REM da classificação atual, e registra que o artigo
de 2003 empregava uma classificação de quatro. Fontes sem ano de publicação
confirmado exibem **“consulta 2026”**, sem inventar uma data de publicação.

```text
O que é um neurônio?
Como funciona a ecolocalização?
Qual é a função da membrana celular?
Por que o sono ajuda a memória?
Qual a diferença entre estresse e ansiedade?
Escreva um texto sobre memória e biodiversidade
Qual é a fonte?
Qual é a interpretação religiosa sobre biomimética?
```

Funções, causas e comparações usam fatos explícitos. Uma relação não autoriza
sua inversa, a retirada de uma negação ou a inclusão de um qualificador novo.
O currículo não fornece diagnósticos individuais, escolha de medicamentos
ou doses. Fatos do grafo anterior continuam válidos: adicionar o conceito
de universo não impede provar relações entre Sol, Via Láctea e Universo.
Os IDs públicos anteriores de fotossíntese e efeito estufa são preservados.

`curriculo_mundo.py` valida os dados e gera **297 exemplos genéricos de
conceitos**, a partir dos nomes e aliases. `Crivo`, `treinar_base` e o avaliador
da rede carregam a mesma população: **168 intenções e 764 exemplos** no total.
As consultas de `avaliar_mundo.py` ficam fora desses exemplos. O aprendizado
continua em Python padrão, offline, com a rede original do projeto.
`ensinar` mantém a base editorial separada dos exemplos derivados, evitando
duplicação ao salvar e recarregar.

O checkpoint `rede_crivo.json` foi treinado com 60 épocas, 512 dimensões,
48 neurônios ocultos, modo `portugues` e semente 42. Ele carrega automaticamente
quando rótulos e assinaturas são compatíveis. O fluxo `treinar-rede.yml` também
treina novamente quando o currículo ou seu carregador mudam.
`vercel.json` inclui o currículo, seus módulos e o checkpoint no pacote da API.

**Limites medidos:** a sonda do chatbot híbrido passou **51/51 consultas**
de definição, função, relação, comparação, composição, fontes e recusa.
Na verificação adicional `Defina <nome>` dos 44 conceitos, o classificador
isolado acertou o ID exato em **32/44**; ainda há confusões, inclusive com IDs
editoriais de conceitos sobrepostos. Esses números são verificações de
desenvolvimento, sem avaliação cega. A rede classifica assuntos; os 119 fatos
ficam no currículo e são selecionados pelo compositor. Esse treino não
transforma o modelo em uma LLM nem garante compreensão de qualquer pergunta.

```bash
python avaliar_mundo.py
python -m unittest testes_conhecimento_mundo -v
python rede_neural.py --base conhecimento.json --saida rede_crivo.json --epocas 60 --ocultos 48 --dimensao 512 --modo portugues --semente 42
```

A sonda foi usada no desenvolvimento; **não é teste cego nem uma medida
universal de inteligência**. O comparativo está em `avaliacao_escrita.json`.
As auditorias históricas preservam seus critérios e avaliam a população
editorial anterior em bases temporárias, sem o currículo adicional;
os testes novos exercitam o currículo ativo junto com os demais módulos.

```bash
python -m unittest testes_composicao_textual -v
python avaliar_escrita.py
python -m unittest discover -p 'testes*.py'
python avaliar_definicoes.py
```

## Consultar relações e combinar condições

O módulo `consultas_relacionais.py` monta um plano de consulta sobre o
grafo ativo. Ele procura os itens que satisfazem **todas** as condições,
preserva a direção das relações e mostra a prova de cada resultado.
Os nomes vêm dos dados; não há uma resposta programada para cada pergunta.

```text
Quais animais têm penas?
Quais astros orbitam o Sol e fazem parte da Via Láctea?
Quais planetas a Lua orbita?
De que a Terra faz parte?
A Terra é um planeta e faz parte da Via Láctea?
```

Após uma lista, `Desses, quais...` ou `E quais...` filtra somente os itens
exibidos no turno anterior. A API reconstrói esse contexto a partir do
histórico; uma saudação, outro assunto, dúvida ou resposta vazia o expira.
A saída é limitada a 20 itens, com aviso quando há outros resultados.

As respostas distinguem comprovação, contraprova e desconhecimento.
`Quais animais não são insetos?` exige uma incompatibilidade explícita:
ausência de classificação não basta. Já `Quais animais são aves e não
são aves?` identifica condições impossíveis. Negação de propriedades,
alternativas com `ou`, ações desconhecidas e modificadores não reconhecidos
pedem esclarecimento, sem descartar parte da pergunta.

**Validação:** a sonda de 36 casos foi executada antes da implementação
(2/36) e depois (36/36). Inclui perguntas, conversas e recusas esperadas;
foi usada no desenvolvimento e **não é teste cego**. Os testes adicionais
usam grafos fictícios com nomes novos, condições em ordens diferentes,
órbitas não transitivas, isolamento de bases e integração da API.
O comparativo reproduzível está em `avaliacao_consultas.json`.

Listas editoriais podem declarar, em `listas_relacionais`, exatamente
quais classes cobrem. Quando a consulta pede só essas classes, o CRIVO
preserva o texto editorial mais completo (como os oito planetas). Uma
condição extra exige a consulta estruturada; semelhança lexical não
substitui essa verificação. A correção mantém as 192 coincidências de IDs
na coorte histórica de 278 perguntas. Não é alegação de precisão geral
maior. Nenhum fato novo ou modelo externo foi acrescentado nesta etapa.

```bash
python -m unittest testes_consultas_relacionais -v
python avaliar_consultas.py
python -m unittest discover -p 'testes*.py'
python crivo.py --teste
python avaliar_regras_mistas.py
```

O ganho é **consultar e combinar melhor os fatos existentes**. O motor
continua com uma gramática limitada, sem compreensão livre, geração
aberta, aprendizagem espontânea ou conhecimento de assuntos ausentes.

## Categoria botânica de frutas: dados combináveis

O arquivo `frutas.json` tem **63 entradas curadas**, com nome, apelidos,
classificação botânica, descrição, informações sobre sementes e diferença
entre fruto botânico e fruta na culinária. O motor `frutas.py` usa **um
único algoritmo para todas as entradas**: não são 63 respostas ligadas
somente a 63 perguntas exatas. O programa identifica o nome da fruta,
a intenção do usuário e combina as propriedades cadastradas.

Exemplos para experimentar no chat (também funcionam pela API):

```text
O que é uma maçã?
O que são bananas?
Banana tem sementes?
O morango tem sementes do lado de fora?
Tomate é fruta ou legume?
Qual é o tipo botânico da maçã?
Qual é o tipo botânico do abacaxi?
Qual a diferença entre maçã e pera?
Me dê exemplos de frutas de caroço
Liste frutas cítricas
Qual a diferença entre fruto e fruta?
Como se formam os frutos?
```

A conversa curta permite `Qual o tipo botânico da maçã?` seguido de
`E a banana?`, com a intenção anterior mantida **apenas no próximo
turno**. No navegador, as mensagens anteriores são reenviadas ao
backend para reconstruir esse estado, sem gravar conversas no servidor.

**Controles de integridade:** uma banana não recebe automaticamente as
propriedades de uma maçã por pertencer à mesma categoria. A estrutura
`sementes` pode variar entre espécies e cultivares; a resposta
explica essas diferenças registradas. As classes botânicas são diferentes
de categorias culinárias; tomate é um fruto botânico, mas é usado
como hortaliça. Maçã/pera são pomos, banana é baga, morango é
agregado/acessório e abacaxi é múltiplo. A distinção está descrita em:

- https://open.lib.umn.edu/horticulture/chapter/8-1-fruit-morphology/
- https://pressbooks.lib.vt.edu/emgtraining/chapter/1/
- https://content.ces.ncsu.edu/extension-gardener-handbook/3-botany

Essa curadoria **não é um treino neuronal** e não implica compreensão
livre de qualquer frase. O programa sabe combinar somente campos e
relações que foram programados. Preços de mercado, sazonalidade local,
uso medicinal, alergias, toxicidade e dados inexistentes não podem ser
inferidos de fatos gerais da fruta; o motor prefere admitir que faltam
evidências. Ainda existem milhares de espécies não cadastradas; a
palavra "fruta" também tem usos regionais diferentes.

Para ampliar a categoria, adicione entradas válidas à matriz `itens`
de `frutas.json`, **sem modificar o parser**. A suíte `testes_frutas.py`
reexecuta consultas de definição, tipo botânico e sementes de **todas**
as entradas cadastradas, além de contrastes e negativas. Para reproduzir:

```bash
python -m unittest testes_frutas -v
python -m unittest discover -p 'testes*.py'
python avaliar_definicoes.py
```

Os testes e o benchmark continuam sendo **desenvolvimento**, não
validação independente de acerto em perguntas reais inéditas.

## Comparar conhecimentos: relações entre frutos (PR #17)

A partir dos **mesmos 63 registros** do catálogo botânico, o CRIVO
agora interpreta questões sobre duas espécies e **compõe uma resposta
com as características previamente curadas**, em vez de exigir que
cada par de frutas tenha uma resposta cadastrada manualmente.

Perguntas de demonstração:

```text
O que banana e uva têm em comum?
Qual a diferença entre milho e uva?
Maçã e pera são do mesmo tipo botânico?
Por que banana e uva são de tipos diferentes?
Por que tomate e pepino são frutos, mas usados como hortaliças?
O que feijão e arroz têm em comum?
Qual a diferença entre manga e mangaba?
```

Os passos de comparação são explícitos. O motor verifica o **tipo
botânico** de cada item, detecta igualdade/diferença de grupo,
apresenta os dois registros e contesta perguntas com uma premissa
incorreta (por exemplo, banana e uva *não* são de classes botânicas
diferentes segundo o catálogo; ambas são bagas). Comparar dois itens
não implica que compartilhem teor nutricional, reações alérgicas,
segurança alimentar, preço ou sementes idênticas. Solicitações sobre
propriedades não cadastradas continuam fora do escopo.

A curadoria distingue os produtos vegetais **que comemos** dos frutos
botânicos: os grãos comestíveis de feijão e amendoim são sementes
(provenientes de vagens); a parte suculenta do caju é um pedúnculo
floral, e seu fruto verdadeiro é a castanha. O comparador não afirma
que todas essas partes consumidas sejam frutos completos. Tampouco
conclui que todo alimento que não é considerado fruta de sobremesa
seja uma hortaliça.

**Correção científica:** a cariopse *não contém um grão separado*:
o **próprio grão de milho** é um fruto seco do tipo cariopse, em que
o pericarpo (parede do fruto) adere à semente. O registro de
`cariopse` e a descrição de `milho` foram corrigidos conforme:
- https://open.lib.umn.edu/horticulture/chapter/8-1-fruit-morphology/
- https://lod.nal.usda.gov/nalt/en/page/186294

**Reprodutibilidade:** `testes_relacoes_frutas.py` foi registrado
antes de implementar o mecanismo e inclui testes por pares, premissas
falsas, perguntas que exigem abstenção, preservação de perguntas
de programação e a API do chat. O teste combinatório enumera os
**1.953 pares** distintos de 63 registros
(`63 × 62 ÷ 2`), sem regras específicas para nomes como "uva"
ou "milho". Isso demonstra **reutilização da lógica formal**, não
compreensão universal da língua. Todos os resultados são testes
de desenvolvimento; não constituem um benchmark cego de inteligência.

```bash
python -m unittest testes_relacoes_frutas -v
python -m unittest discover -p 'testes*.py'
```

## Síntese comparativa curta (PR #18)

Em perguntas de comparação sobre frutas, o CRIVO agora **seleciona**
informações do cadastro, em vez de colar duas descrições inteiras
com cada grupo e as sementes. O algoritmo produz:

- A **semelhança verificável**, sem supor que as partes comestíveis
  sejam sempre o fruto completo.
- A **classificação de cada fruto**, sem repetir a definição longa
  de cada grupo botânico.
- Quando há diferença ou comparação aberta, **até um detalhe específico
  de cada item**, escolhido entre os fatos curados.
- Quando a comparação é sobre pertencer ao mesmo tipo, diz explicitamente
  se a premissa procede ou não; não afirma que dois itens têm as
  mesmas sementes, nutrientes ou propriedades medicinais.

Exemplo resumido de como apresentar a diferença entre banana e coco:

```text
Banana e coco são frutos botânicos. Suas classificações são diferentes:
banana é baga; coco é drupa. A banana tem polpa carnosa e suas variedades
cultivadas geralmente não desenvolvem sementes. O coco tem camada
fibrosa, parte interna endurecida e uma semente grande.
```

O campo **opcional** `destaque_comparativo` de `frutas.json` identifica um
detalhe factual curto, que o sistema não cria sozinho. Há destaques
curados para 18 itens, incluindo banana, coco, feijão, amendoim e caju.
Para os demais, o código utiliza **somente a primeira frase existente**
da descrição; assim, qualquer uma das 63 espécies pode participar de
uma comparação, sem escrever uma resposta para cada par.

Os testes incluem o relato real do usuário, integridade de assuntos
alheios, limites das conclusões e **todos os 1.953 pares** possíveis
do catálogo atual. Esse ganho é de **seleção e apresentação dos dados
cadastrados**, não geração livre de texto por rede neural.
A sintaxe reconhecida continua sendo restrita e todos os testes são
de desenvolvimento.

## Referências ao turno anterior e falsas despedidas (PR #22)

Se a resposta do CRIVO menciona um objeto, a pergunta seguinte
pode fazer referência ao mesmo objeto com palavras como `esse`,
`desse`, `essa` ou `daquele`. O sistema confere o **texto da última
resposta realmente mostrada**, aceita singular/plural simples e
reconhece o referente com a mesma lógica para assuntos diferentes.

Exemplo de teste real na versão do PR #22:

```text
Você: O que é Via Láctea?
CRIVO: ... o Sistema Solar fica num dos braços em espiral.
Você: Qual o nome desse braço que você falou?
CRIVO: Você está se referindo ao braço mencionado na minha resposta anterior.
       Reconheci o assunto, mas não tenho informação cadastrada
       suficiente para responder a esse detalhe com segurança.
```

Na versão do PR #22, o nome do braço e a definição de Andrômeda não
estavam cadastrados. A atualização de conhecimento descrita acima
acrescentou esses dados com fontes e vínculo editorial explícito.
Uma regra de linguagem, sozinha, continua sem autorizar a criação de fatos.

A implementação é reutilizável e também foi testada com respostas
sobre gás e estrelas e com uma base fictícia sobre um anel, sem regras
específicas para esses objetos. Referências não identificadas pedem
esclarecimento. O contexto **expira em um turno**, inclusive após
saudações ou declarações de desconhecimento, e a API web o reconstrói
reproduzindo somente as perguntas recentes do navegador.

A origem de `Até logo!` na pergunta do usuário era concreta: o
detector de despedida procurava `falou` como substring dentro de
qualquer frase. Agora exige uma despedida **completa**: `falou`
sozinho continua funcionando, mas `qual ... que você falou?` não é
uma despedida.

Este módulo **não aprende fatos novos**, não resolve qualquer pronome,
não acessa internet nem transforma relações sem evidência em certeza.
Seu papel é **localizar um referente reconhecível e admitir quando
não conhece o detalhe pedido**.

Testes de desenvolvimento:

```bash
python -m unittest testes_referencias_dialogo -v
python -m unittest discover -p 'testes*.py'
python avaliar_definicoes.py
```

## Cumprimentos, vocativos e perguntas ambíguas (PR #23)

O CRIVO separa **a saudação** do **pedido informativo** sem eliminar
a pergunta. Reconhece formas informais como `Eae`, `E aí`, `Oi`,
`Salve` e vocativos (`Crivo`) antes do pedido, conservando os acentos
e a grafia do restante da mensagem. A regra vale para definições,
composições de vários verbetes, provas relacionais e demais domínios
que o núcleo já conhece.

```text
Bom dia
  → Bom dia! Sou o Crivo. Sobre o que quer conversar?

Eae, Crivo. O que é HTML?
  → definição cadastrada de HTML

Salve, Crivo. A Terra é orbitada pela Lua?
  → evidência do grafo, se disponível
```

**O horário local do navegador não é conhecido pelo servidor.** Para
cumprimentos explícitos, o CRIVO responde com a mesma saudação do
usuário. Ele deixa de transformar `Bom dia` em `Boa noite` por depender
do horário de execução da função na hospedagem.

Quando uma frase pode pedir **duas definições** ou uma
**classificação**, o sistema pede esclarecimento, sem pressupor
dados ausentes:

```text
Eae, Crivo. O que é andromeda e uma estrela?
  → Você quer saber o que são andromeda e uma estrela separadamente
    ou quer perguntar se andromeda é uma estrela?
```

O mecanismo usa somente informações sobre Andrômeda que existam na
base ativa; o currículo novo já inclui sua definição. Comandos distintos continuam separados: `O que é
HTML e CSS?` usa os dois verbetes conhecidos; `O que é rotação e
translação?` preserva o conceito editorial único existente.

Perguntas sobre o que o CRIVO **disse no último turno** (por exemplo
`Você falou do Sol?`) consultam somente o texto da última resposta.
O sistema não pode trocar essa pergunta por uma definição de Sol
encontrada por semelhança de palavras.

Os testes de desenvolvimento variam horários, formas informais,
assuntos e um catálogo fictício, além de executar a regressão geral
e auditar o benchmark anterior. **Não é compreensão universal
do português** e não envolve API ou modelo de IA de terceiros.

## Interface web para testar no celular

A pasta `public/` contém o chat responsivo do CRIVO, com exemplos
clicáveis, uma esfera neural, histórico temporário, botão para limpar a
conversa, renderização **segura** de código e indicação de provas lógicas.
O endpoint `api/chat.py` executa **o `Crivo` original em Python**,
sem consultar outra IA, com até dez perguntas anteriores reenviadas pelo
navegador para reconstruir o contexto curto. Não há banco de conversas,
login nem API externa de inteligência artificial.

### Testar no computador ou no celular pela mesma rede Wi-Fi

No computador que tem o repositório:

```bash
python3 web_local.py
```

No Windows, use `py -3 web_local.py` ou `python web_local.py`.
O servidor requer Python 3.8 ou superior e usa somente a biblioteca padrão;
não precisa instalar pacotes Python.

Se preferir iniciar pelo NPM, na raiz do repositório execute:

```bash
npm run dev
```

`npm start` também funciona. Esses comandos localizam o Python instalado
e iniciam o mesmo servidor, sem dependências NPM e sem etapa de compilação.
Não é necessário executar `npm install`. Atualize a cópia do repositório
com `git pull` caso apareça `ENOENT ... package.json`.
Para escolher outra porta: `npm run dev -- --port 3000`.

Abra `http://127.0.0.1:8765` no **próprio computador**. Para usar no
**celular**, execute no computador:

```bash
python3 web_local.py --host 0.0.0.0
```

Pelo NPM: `npm run dev -- --host 0.0.0.0`.

Depois, conecte o celular à **mesma rede local** e abra
`http://IP_DO_COMPUTADOR:8765` (exemplo:
`http://192.168.1.10:8765`; substitua pelo IP real). Libere a porta
8765 **apenas na rede local** se o firewall bloquear. Não encaminhe
essa porta para a internet: o servidor de testes não tem autenticação.

### Abrir pela internet com Vercel

O repositório contém `vercel.json` e a função Python `api/chat.py`
para uma hospedagem Vercel sem dependências extras. Para disponibilizar
a URL pública:

1. Entre em [Vercel → New Project](https://vercel.com/new).
2. Importe o repositório público `HROSONE/CRIVO` do GitHub.
3. Escolha **Other** como Framework Preset e a **raiz do repositório**
   como Root Directory. Não precisa de Build Command. O `package.json`
   fornece apenas atalhos para o servidor local; não adiciona dependências.
4. Confirme o deploy. Abra a URL criada pela Vercel no celular.
5. Para verificar o backend, a URL `/api/chat` deve apresentar JSON
   com `"status": "ok"` e `"external_ai": false`.

A página estática é servida de `public/`; o chat faz POST JSON para
a mesma origem em `/api/chat`. O arquivo `vercel.json` inclui os
arquivos de Python e `conhecimento.json`/`relacoes.json` no pacote
da função. Para usar a **rede neural classificadora opcional** também
no servidor, inclua o checkpoint compatível `rede_crivo.json` na
implantação; sem ele, o recuperador e o grafo simbólico funcionam,
mas `neural_active` será `false`. A interface indica
o mecanismo da resposta, sem inventar uma classificação de confiança.

Se a conta Vercel ainda não estiver conectada ou o projeto não tiver
sido implantado, **o código no GitHub por si só não é uma URL pública
de chat**. A conexão com uma hospedagem é etapa distinta.

### Segurança e limites da interface

* Exige POST com `Content-Type: application/json` e tamanho de corpo
  limitado a 16 KiB; cada pergunta tem no máximo 1200 caracteres.
* O contexto de até dez perguntas fica na memória da aba e não é
  gravado pelo aplicativo em armazenamento permanente. Uma nova
  conversa apaga o contexto local. A infraestrutura de hospedagem
  pode ter logs operacionais próprios.
* Respostas e blocos de código são renderizados por `textContent`,
  não como HTML fornecido pelo usuário. O servidor não executa
  código enviado nas perguntas.
* Por padrão, `web_local.py` escuta somente `127.0.0.1`.
  Hospedagem pública sem login pode consumir recursos; proteja o
  projeto na Vercel se desejar acesso privado.
* Não é PWA offline: o navegador precisa alcançar o backend Python.
* Testes de API, histórico e servidor: `python -m unittest
  testes_web -v`; suíte geral: `python -m unittest discover
  -p 'testes*.py'`.

## Análise estruturada de português: intenção, sujeito e objeto (PR #21)

O módulo `analisador_portugues.py` acrescenta uma **gramática superficial
de português** ao núcleo do CRIVO. Em vez de encontrar uma resposta
porque sua pergunta compartilha palavras com um parágrafo, ele pode
montar um quadro como este:

```text
Pergunta: "O Sistema Solar contém a Terra?"
Intenção: verificar
Sujeito lógico: Terra
Predicado: parte_de
Objeto lógico: Sistema Solar
Evidência: Terra → Sistema Solar (fato cadastrado)
```

**A posição dos elementos na frase não determina sozinha a direção
do fato.** Em `A Terra é orbitada pela Lua?`, o sujeito da frase é
Terra, mas o sujeito do predicado lógico `orbita` é Lua. As
construções passivas e verbos de inclusão são interpretadas com
essa diferença preservada.

O analisador usa o **catálogo ativo de entidades e apelidos do
grafo**, com nomes completos e validação exata — os nomes Sol, Lua,
pinguim etc. não estão codificados na gramática. Reconhece formatos
variados de classificação, composição, órbita, propriedades, comparação
e pedidos de definição. Para cada quadro reconhecido, consulta
**exclusivamente o provador já existente** ou o verbete editorial
autorizado da base. Não grava relações nem deduz fatos por analogia.

Exemplos para o chat:

```text
Quero saber se o pinguim pertence ao grupo das aves
O Sistema Solar contém a Terra?
A Terra é orbitada pela Lua?
Qual característica o pinguim apresenta?
Existe alguma ligação entre Terra e Via Láctea?
Você poderia me explicar o que é HTML?
E o CSS?
```

Frases com negação ou hipóteses são protegidas: `O pinguim não é
uma ave?` e `Se a Lua fosse um planeta...` não viram afirmações
positivas por eliminação de palavras. Quando o grafo não permite
uma prova, o CRIVO afirma que **não possui evidência**, sem concluir
que a proposição é falsa.

### Avaliação e limite deste avanço

`testes_analisador_portugues.py` pré-registrou casos de astronomia,
animais, programação, contextos customizados e grafos de entidades
sintéticas. Há ainda uma matriz que produz **duas formulações
por aresta para todas as relações afirmativas cadastradas**,
de modo que não seja necessário criar um teste manual por nome.
A suíte geral e o benchmark anterior devem continuar aprovados.

Isso é **análise simbólica superficial**, não um parser linguístico
irrestrito nem uma rede neural treinada em todo o português. A lista
de verbos e construções reconhecidas ainda é limitada. Pronomes
complexos, metáforas, ambiguidades e conceitos fora do grafo ainda
podem exigir esclarecimento ou ficar sem resposta; a camada
conservadora foi inserida **depois** das rotas já existentes,
para não desestabilizar a recuperação anterior. Nenhum modelo
pretreinado ou API de IA participa.

Para testar:

```bash
python -m unittest testes_analisador_portugues -v
python -m unittest discover -p 'testes*.py'
python avaliar_definicoes.py
```

## Perguntas com vários conceitos e relações sem superclasse (PR #20)

O CRIVO agora reconhece uma **lista explícita de duas ou três definições**
na mesma pergunta, respeitando a base de conhecimento do ambiente:

```text
O que é HTML e CSS?
  → HTML: estrutura e semântica do conteúdo.
  → CSS: regras de apresentação e estilo.

O que é Git e SQL?
  → Define Git e SQL separadamente, com os verbetes cadastrados.

O que é HTML e Rust?
  → Não tenho uma definição cadastrada para Rust.
```

O mecanismo **não usa a resposta do assunto mais parecido** quando
identifica que um dos termos não tem definição editorial. Só apresenta
a **primeira frase curada** de cada verbete, evitando código e exemplos
irrelevantes; nunca usa a rede neural como fonte factual. Se nenhum
dos termos possui definição individual registrada, a consulta retorna
ao interpretador anterior para preservar temas estabelecidos como
`rotação e translação`, que podem constituir **um único conceito
composto**. Isso não permite deduzir qualquer definição a partir de
palavras compartilhadas.

Perguntas sobre **semelhança** primeiro verificam se os dois objetos
compartilham uma classe por `tipo_de`. Se não houver classe comum,
o interpretador procura ainda uma prova de composição por `parte_de`.
Por exemplo, a Terra não precisa ser do mesmo tipo que a Via Láctea
para que exista uma relação factual entre as duas:

```text
Terra → Sistema Solar → Via Láctea
```

O CRIVO explica que isso é uma relação de **parte e todo**, não
igualdade de categorias. Se não houver relação provada, **não declara
que a ligação é impossível**. O selo da interface `Prova lógica`
passa a ser mostrado apenas para resultados com um caminho de
prova ou dedução explícita, não para mensagens de abstenção.

Essa é uma composição **determinística, segura e restrita a formatos
de perguntas reconhecidos**, e não compreensão irrestrita do português.
A avaliação inclui perguntas dos prints do usuário, variações por
domínio, fatos totalmente sintéticos e os benchmarks históricos.
Todos os testes usados durante o ajuste são testes de
**desenvolvimento**, não avaliação cega.

## Interpretação transversal (PR #19)

O módulo `interpretacao_geral.py` interpreta **formatos de pergunta
reutilizáveis entre assuntos**, sem inserir um novo conjunto de frases
de animais, astronomia ou programação no cadastro.

### Perguntas de relação e semelhança

Com o **mesmo grafo** `relacoes.json` usado para inferência, é possível
consultar duas entidades conhecidas e ver os caminhos que as conectam:

```text
O que pinguim e tucano têm em comum?
  → ave; provas: pinguim → ave; tucano → ave.

O que a Terra e Marte têm em comum?
  → planeta; provas: Terra → planeta; Marte → planeta.

Qual é a relação entre a Terra e a Via Láctea?
  → Terra → Sistema Solar → Via Láctea.

Como o Sol se relaciona com o Universo?
  → Sol → Sistema Solar → Via Láctea → Universo.
```

O mecanismo busca a categoria ancestral comum de **menor distância**
e procura caminhos existentes para `tipo_de`, `parte_de`,
`orbita` (direta) e `tem_caracteristica` (herança validada).
Não faz analogias livres nem inventa arestas; quando conhece as duas
entidades, mas não encontra ligação, responde explicitamente que
**ausência de prova não significa inexistência da relação**. Nomes
desconhecidos não ganham entidades por similaridade lexical.

### Continuação definicional segura

Quando o CRIVO **acabou de responder uma definição editorial**, a
pergunta curta `E a Lua?` pode reutilizar a **intenção** da pergunta
anterior `O que é o Sol?`, mas deve buscar a nova definição na base:

```text
O que é HTML?
E CSS?
  → definição cadastrada de CSS, não repetição do texto de HTML.

O que é o Sol?
E a Lua?
  → definição cadastrada da Lua.

O que é o Sol?
E uma árvore binária?
  → "Não tenho uma definição cadastrada desse conceito."
```

O contexto só dura **um turno**, não persiste após uma saudação,
pergunta sem relação ou tema fora da base; a mesma lógica funciona no
chat web porque `web_core.py` reconstrói o histórico enviado.
Não inclui reconhecimento de pronomes arbitrários, tradução de
frases livres nem resolução de contradições sem fonte.

### Regressões

```bash
python -m unittest testes_interpretacao_geral -v
python -m unittest discover -p 'testes*.py'
python crivo.py --teste
python avaliar_definicoes.py
```

Os testes incluem grafos **sintéticos com nomes que não estão no
catálogo**, uso da API web e exemplos em quatro tópicos, além do
conjunto histórico de recuperação. É uma capacidade de **composição
simbólica rastreável**, não geração de linguagem por LLM nem treino
automático da rede própria. Todos os testes orientaram o
desenvolvimento; não equivalem a uma avaliação cega.

## Como usar

    python crivo.py                  # conversa no terminal
    python crivo.py "por que chove?" # uma pergunta só
    python crivo.py --teste          # bateria de testes (testes.json)

Só precisa de Python 3.8+, sem instalar nada.

## Definições com intenção explícita (PR #14)

Uma pergunta **“O que é uma árvore?”** exigia uma definição, mas a
v0.4 originalmente selecionava a resposta de `folhas_outono` — que
explica por que certas árvores perdem folhas. A versão corrigida
introduz a entrada **`arvore`**, com uma definição botânica escrita
na base de conhecimento, e um caminho restrito para pedidos como
`o que é X`, `defina X` e `o que significa X`.

A intenção de definição é comparada primeiro com **conceitos
efetivamente cadastrados**, em vez de supor que toda menção a
`árvore` responde qualquer pergunta sobre árvores. A entrada
`plantas_toxicas` utiliza os campos opcionais `definicoes`
(conceitos curados) e `resposta_definicao` (texto específico),
separados das perguntas sobre animais domésticos, para não
distorcer a recuperação de cuidados veterinários.

Para uma paráfrase sem correspondência definicional exata, o
recuperador só considera a resposta anterior se houver evidência
específica do conceito: nome exato do assunto, enunciado que descreve
o conceito ou qualificador documentado. Assim, perguntas por
`árvore binária`, `árvore genealógica`, `nuvem` e `folha`
**não devem disparar respostas sobre árvores botânicas, raios ou
folhas amarelas** se não há uma definição correspondente.

Exemplos esperados:

```text
você > O que é uma árvore?
Crivo > Uma árvore é uma planta geralmente de porte alto, com caule
        lenhoso (tronco) que sustenta ramos e folhas. (...)

você > O que é uma árvore binária?
Crivo > Ainda não tenho uma definição cadastrada para esse conceito. (...)

você > Por que as árvores perdem as folhas?
Crivo > Com dias mais curtos e frios, as árvores caducifólias (...)

você > O que é uma planta tóxica?
Crivo > Uma planta tóxica contém substâncias que podem causar
        intoxicação. (...)
```

**Avaliações (desenvolvimento, não testes cegos):** o arquivo
`coorte_geral_v04.json` congela os IDs e 278 perguntas gerais
anteriores à mudança. Com a nova intenção e com o grafo carregado,
a coorte mantém **192/278 acertos**, enquanto os erros passaram
de **44 para 42** e as abstenções de **42 para 44**. Na base geral
ampliada (282 perguntas), o resultado do benchmark de rotação é
**196 acertos, 43 erros e 43 abstenções**. Os novos conjuntos não
são comparáveis numericamente como se fossem a mesma população:
a base cresceu. Execute `python avaliar_definicoes.py` e
`python -m unittest testes_intencao_definicao -v`.

Este mecanismo **não é um gerador de definições nem entende qualquer
conceito**. Ele escolhe explicações revisadas e prefere se abster
quando não há evidência suficiente. A base de perguntas foi alterada,
então pesos neurais anteriores são incompatíveis e um novo
treinamento precisa gerar um checkpoint correspondente.

## Como funciona (honestamente)

A resposta padrao do Crivo v0.4 utiliza um mecanismo de recuperacao, nao uma rede geradora de texto:
1. `conhecimento.json` guarda 123 assuntos escritos à mão, com 463 formas de perguntar; 45 assuntos novos são de programação.
2. Ao iniciar, ele indexa tudo com TF-IDF (o "treino" é esse índice).
3. A pergunta é normalizada (sem acento, plural, diminutivo, sinônimos) e comparada com a base.
4. Se a confiança é baixa, ele diz que não sabe em vez de inventar.
5. Hora, data, mês, ano e estação atual vêm do relógio do computador.
6. Programação usa um índice por domínio e respeita a linguagem pedida. Exemplos cadastrados são exibidos junto das explicações, sem executar código do usuário.

Comandos na conversa: `assuntos`, `exemplos`, `mais` (próxima resposta parecida), `sair`.

## Próximos passos

- Ampliar `conhecimento.json` (cada pergunta nova que falhar vira uma entrada).
- Ampliar e avaliar a rede própria, inicializada do zero; sem modelos pré-treinados.

## Programação ensinada no código

O currículo contém **45 assuntos, 181 perguntas de treino e 31 exemplos** adicionados diretamente a `conhecimento.json`:

| Área | Conteúdo |
|---|---|
| Fundamentos | Programação, algoritmos, variáveis, tipos e investigação de bugs |
| Python | Entrada/saída, condições, laços, funções, listas, dicionários, comparação, exceções, arquivos, JSON, classes, módulos, ambiente virtual e testes |
| Web | HTML, CSS, API e HTTP |
| JavaScript | Variáveis, funções, arrays, DOM, promessas e async/await |
| SQL | Tabelas, SELECT/WHERE, JOIN e parâmetros com sqlite3 |
| Git | Controle de versão, commit, branch e revisão de diferenças |

Experimente:

```bash
python crivo.py "Definir uma função que soma em Python"
python crivo.py "Faça um exemplo de função de soma em JavaScript"
python crivo.py "Como resolver ValueError no Python?"
python crivo.py "Me mostra uma página básica em HTML"
```

O campo `resposta` guarda a explicação; `exemplo` guarda linguagem e código fixo. `area`/`linguagens` orientam a seleção, `identificadores` reconhece nomes de erro e `fontes` registra documentação consultada. O programa funciona offline: esses links não são consultados durante a conversa. Exemplos e explicações são autorais, conferidos nas documentações de [Python](https://docs.python.org/3/), [MDN](https://developer.mozilla.org/en-US/docs/Web/), [PostgreSQL](https://www.postgresql.org/docs/current/tutorial-sql.html) e [Git](https://git-scm.com/docs).

O índice calcula relevância separadamente para assuntos gerais e programação. A correspondência exata preserva operadores como `=`, `==` e `!=`, além de nomes como `C++` e `C#`; preservar nomes não significa ter conteúdo sobre essas linguagens. O classificador neural continua usando sua representação experimental anterior.

**Validação de desenvolvimento:** 45 perguntas novas de programação e um controle sobre plantas passaram; as frases não são cópias literais do treino, mas foram usadas durante o ajuste, portanto não são teste cego. As 181 perguntas cadastradas retornam os assuntos esperados. Exemplos Python são executados em pastas temporárias; exemplos JavaScript têm a sintaxe verificada e, quando independentes do navegador, a saída testada; SQL usa um banco SQLite em memória. HTML/CSS e comandos de Git/venv são exemplos didáticos, sem teste de navegador ou execução de comandos Git nesses testes.

Na avaliação que retira a pergunta de sua rodada de busca: **119/181 acertos em programação**, com 26 respostas erradas e 36 abstenções. Os **278 casos antigos mantiveram exatamente 192 acertos, 44 erros e 42 abstenções**, incluindo os mesmos erros. Os 65 testes originais e os 24 diálogos anteriores continuam passando. Resultados completos e limites estão em `avaliacao_programacao.json`.

**Limite:** isto ensina conceitos e exemplos recuperáveis. O Crivo não gera programas arbitrários, não executa trechos recebidos nem corrige automaticamente projetos. Treinar a rede com todos os assuntos amplia seus rótulos; não demonstra que ela aprendeu a escrever código livremente.

```bash
python -m unittest testes_programacao -v
```

O Crivo requer apenas Python; verificar os exemplos JavaScript também requer Node.js. O CI instala Node.js e testa Python 3.8, 3.11 e 3.13. As regressões executam em cada PR/push. Comparações neurais extensas ficam em **Actions → Testes Crivo → Run workflow → benchmark** (`portugues` ou `historico`), para não repetir toda a pesquisa a cada alteração. O treino dos pesos continua automático quando a base muda na `main`.

## Evolução experimental (PR #1)

- `Crivo.ensinar(id, topico, perguntas, resposta)` permite acrescentar entradas revisadas pelo desenvolvedor e persistir no JSON; não é aprendizagem autônoma.
- `historico` guarda as últimas 20 perguntas respondidas; `ultimo_assunto` oferece retomada limitada de referências.
- Perguntas negativas sobre ações recebem resposta de incerteza em vez de afirmação potencialmente perigosa.
- `python -m unittest discover -p 'testes*.py' -v` executa os testes adicionais; `python crivo.py --teste` executa os 65 testes existentes.
- Workflow GitHub Actions testa três versões de Python; conferir resultados antes de integrar.

**Limites:** a rede neural experimental classifica intenções; não aprende autonomamente a partir de texto livre, não possui raciocínio lógico geral nem geração aberta de linguagem. Recuperar respostas e lembrar referências não equivale a compreender português. Para evoluir em direção a um modelo próprio, é necessário criar um conjunto de dados de treino, uma arquitetura treinável, um procedimento de otimização e avaliações independentes. Não marcar funcionalidades como aprovadas sem testes executados.


## Assertividade v0.3

- Recuperação usa similaridade ponderada por raridade das palavras e média/melhor exemplo; duplicar perguntas idênticas não aumenta a pontuação.
- Vocabulário revisado no código reconhece mais flexões e sinônimos. Correção de grafia só atua em termos desconhecidos de pelo menos cinco letras com um único candidato próximo no índice.
- Perguntas exatamente cadastradas têm prioridade; empates entre intenções diferentes pedem esclarecimento antes de qualquer reforço neural.
- Saudações junto de perguntas não encerram a análise. Hora e data locais não interceptam perguntas sobre outros lugares ou acontecimentos históricos.
- Negações não cadastradas pedem reformulação, com tratamento limitado de perguntas de prevenção. Isso não equivale a compreender qualquer negação.
- Histórico também registra respostas exatas; `mais` não reaproveita resultados após uma pergunta sem resposta.

### Medição reproduzível

    python crivo.py --teste
    python -m unittest discover -p 'testes*.py' -v
    python avaliar_recuperador.py

Comparação com `ec8fd2a1698e82663eb146adf2d0ad55608d2295`, mesma base de conhecimento:

| Medida em 278 perguntas | Antes | v0.3 |
|---|---:|---:|
| Respostas corretas | 181 | 192 |
| Respostas erradas | 51 | 44 |
| Abstenções/pedidos de esclarecimento | 46 | 42 |
| Acerto sobre todas as perguntas | 65,1% | 69,1% |
| Precisão entre respostas dadas | 78,0% | 81,4% |

Os 65 testes originais continuam passando. Os 19 casos novos de conversa são regressões de desenvolvimento, não evidência de generalização independente. Resultados e erros restantes estão em `avaliacao_assertividade.json`.

**Protocolo e limite:** a avaliação retira cada pergunta do índice na sua rodada, mas mantém as respostas e outras perguntas da mesma intenção. Foi usada durante o desenvolvimento e não é um teste cego. Seus números não são diretamente comparáveis aos da rede neural treinada apenas com perguntas. A pontuação de similaridade não é probabilidade de verdade. A melhora é no mecanismo de escolha de respostas, não uma alegação de inteligência geral.

## Diálogo com esclarecimento

O Crivo agora guarda as opções que acabou de oferecer e entende a sua escolha:

```text
você > planta
Crivo > Encontrei duas possibilidades próximas. Qual delas você quer?
1. o que é fotossíntese
2. quantas vezes devo regar as plantas
você > a segunda
Crivo > [resposta cadastrada sobre regar]
```

- Aceita `1`, `2`, `a primeira`, `a segunda`, `opção 2` e nomes que identifiquem uma única opção, como `a de regar`.
- `Sim` confirma quando há apenas uma sugestão. Com duas opções, pede uma escolha explícita.
- `Não` ou `nenhuma das duas` cancela a escolha; uma pergunta nova descarta a pendência anterior.
- Registra no histórico a escolha e a pergunta que gerou as opções. `Mais` também atualiza o assunto para a resposta que foi efetivamente mostrada.
- A pendência pertence à instância de `Crivo`, não é salva no conhecimento e é descartada quando `ensinar()` muda a base.

Em 24 sequências de desenvolvimento fixadas antes da implementação, o resultado passou de **3/24 para 24/24**. A avaliação de perguntas isoladas permaneceu idêntica: **192 acertos, 44 erros e 42 abstenções em 278 perguntas**; os 65 testes originais continuam passando. O ganho medido é na continuidade da conversa. Não mede generalização para qualquer diálogo, aumento de conhecimento ou melhora da rede neural.

Os casos e o avaliador estão em `testes_dialogo.py`; o comparativo está em `avaliacao_dialogo.json`. Para verificar:

```bash
python -m unittest testes_dialogo -v
python avaliar_recuperador.py
```

## Experimentos de recuperação de programação (PR #8)

A sonda `experimento_programacao_adversarial.py` mede o **recuperador de
respostas fixas**, não geração de código nem inteligência geral. Identificou
quatro limitações reais da v0.4: negação descritiva em `const`, paráfrases
para entrada de dados em Python, JavaScript atuando sobre HTML e distinção de
`git diff` versus `git commit`. A quinta falha original era um erro
no próprio teste: `sistema_solar` é uma categoria, não um ID de resposta;
o esclarecimento foi aceito como resultado correto para a pergunta ampla.

As alterações do experimento são pontuais:
- Algumas equivalências de consulta são usadas **somente em contexto
  técnico explícito**, sem alterar a base de exemplos.
- HTML/CSS podem ser contexto de uma consulta JavaScript, sem exigir que
  cada entrada tenha todas essas linguagens como áreas próprias.
- Em uma consulta Git que pede comparar alterações de arquivos, `diff`
  entra como pista adicional; pedidos explícitos sobre `commit` e `push`
  não recebem essa pista.
- A negação descritiva sobre uma variável JavaScript que "não muda" é
  diferenciada de negações gerais que continuam pedindo esclarecimento.

**Medições reproduzíveis, sem rede neural:**
- Na sonda de desenvolvimento de 27 casos, o resultado final é **27/27**.
  Essa sonda orientou os ajustes; **não é teste cego** e inclui a correção
  de um resultado esperado inválido.
- Em 12 controles adicionais escritos depois dos ajustes, **11/12**. A
  pergunta "Como obter informações de quem usa o programa Python?"
  ainda foi associada a `prog_variavel` em vez de `py_input`. O
  recuperador continua limitado diante de algumas paráfrases.
- Nos 278 casos gerais anteriores, sem programação, o resultado permanece
  **192 acertos, 44 erros e 42 abstenções**; o experimento encerra com erro
  se os acertos gerais caírem abaixo de 192 ou as respostas erradas subirem
  acima de 44.

Rode `python experimento_programacao_adversarial.py` para gerar o relatório
JSON completo; `python -m unittest discover -p 'testes*.py'` inclui os
testes de regressão semântica. **Os resultados não atestam que o CRIVO
escreva programas sob demanda**: ele continua recuperando explicações e
exemplos previamente cadastrados, sem modelos externos.

## Interpretação de entrada do usuário (PR #9)

O recuperador usa um conjunto **restrito de pistas linguísticas** para reconhecer
quando uma consulta Python descreve pedir/receber informação da pessoa que
digita no terminal, ainda que não mencione literalmente `input`. Termos
como "pessoa", "usuário", "digitação" e verbos de solicitação precisam
formar uma combinação reconhecível. Isso não treina uma nova rede, nem
gera funções inéditas: o Crivo continua selecionando o exemplo `py_input`
previamente escrito.

A regra não é aplicada a pedidos sobre formulários web, câmera, APIs,
WhatsApp e outras interfaces não ensinadas; nesses casos deve admitir que
não sabe, em vez de exibir o exemplo de entrada pelo terminal. Outra
correção impede que "informe seu nome" dentro de uma pergunta de
programação acione a apresentação social do assistente. Perguntas que
descrevem interações JavaScript com campos HTML recebem pistas de DOM.
"Funciona" foi tratado como verbo genérico apenas na consulta,
evitando bloquear um assunto claramente reconhecido por uma palavra
não cadastrada.

**Métricas de desenvolvimento, não teste cego:**
- Bateria pré-registrada de 29 perguntas: **19/29 antes**, **29/29 após**.
- Controles adicionais elaborados depois das primeiras alterações:
  **23/23** após o ajuste. Esses controles detectaram inicialmente dois
  falsos positivos (`input` para câmera e formulário web), posteriormente
  corrigidos.
- Benchmark histórico de perguntas gerais com pergunta removida do índice:
  **192/278 corretas, 44 erradas, 42 abstenções**, sem alteração.
- O relatório detalhado e os testes estão em
  `experimento_entrada_usuario.py` e `testes_entrada_usuario.py`.

Os resultados foram utilizados para guiar o desenvolvimento e **não
significam compreensão geral, precisão de 100% fora dessas baterias nem
capacidade de programar arbitrariamente**. Melhorias posteriores exigem
casos novos e aferição independente.

## Raciocínio relacional multissalto (PR #10, experimental)

O CRIVO ganhou um segundo caminho de resposta, separado do recuperador e
da rede neural: `raciocinio.py` lê os **fatos explícitos** do arquivo
`relacoes.json` e busca cadeias transitivas em um grafo. O arquivo inicial
traz **42 entidades e 46 relações revisáveis**, nos tipos `tipo_de`
(classificação) e `parte_de` (composição). O motor verifica relações por
busca em largura e devolve a cadeia de evidências mais curta disponível.

Exemplos que **não precisam ser perguntas cadastradas**:

```text
você > Por que um pinguim é um ser vivo?
Crivo > Sim. Consigo concluir isso pelas relações cadastradas:
        pinguim → ave → vertebrado → animal → ser vivo.

você > A Terra faz parte da Via Láctea?
Crivo > Sim. Consigo concluir isso pelas relações cadastradas:
        Terra → Sistema Solar → Via Láctea.

você > Um gato é um peixe?
Crivo > Não tenho uma relação afirmativa cadastrada que permita
        concluir isso. Isso não significa que a afirmação seja falsa.
```

**Também aceita um silogismo com premissas hipotéticas no mesmo turno**.
Use duas afirmações e uma pergunta, separadas por vírgulas ou ponto e
vírgula. Os termos podem ser completamente inéditos:

```text
você > Se todo flumbo é blim, todo blim é taro, então flumbo é taro?
Crivo > Sim, somente se assumirmos as premissas informadas:
        flumbo → blim → taro. Isso não comprova que as premissas sejam reais.
```

A hipótese **não altera a base de conhecimento**: vale apenas para aquela
dedução. Conclusões invertidas não são assumidas. O CRIVO não mistura
automaticamente `tipo_de` com `parte_de`, não deduz falsidade a partir
da falta de um caminho, não processa negações hipotéticas e não recebe
qualquer frase arbitrária como fato. As relações são **curadoria manual**,
não verdades verificadas automaticamente; erros no cadastro podem produzir
conclusões erradas. Grafos com ciclos ou apelidos ambíguos são recusados.
Perguntas fora dos padrões reconhecidos continuam no recuperador anterior.

Para ampliar, acrescente entidades e fatos em `relacoes.json`. O
motor só utiliza o arquivo na **mesma pasta da base selecionada**:
bases personalizadas sem esse arquivo não herdam fatos. Testes executam
cadeias sintéticas inéditas, recusas, isolamento e regressões:

```bash
python -m unittest testes_raciocinio -v
python -m unittest discover -p 'testes*.py'
python crivo.py --teste
```

**Limite fundamental:** inferir relações declaradas, inclusive entre
premissas novas, é um avanço de composição simbólica; **não comprova
compreensão livre de linguagem, descoberta factual, raciocínio geral ou
capacidade de escrever programas completos**. A rede neural de classificação
não recebe essas relações automaticamente como treino.

## Inferência mista de fatos (PR #11)

O grafo experimental passou a ter **49 entidades e 59 fatos**, com
quatro tipos de relação e condições explícitas para combiná-los:

- `tipo_de` e `parte_de` são transitivas **somente dentro do mesmo tipo**.
- `tem_caracteristica` não é transitiva. O sistema pode herdar uma
  propriedade de uma classe por **zero ou mais** etapas `tipo_de` seguidas
  de **exatamente uma** etapa `tem_caracteristica`. Exemplo:
  `pinguim --tipo_de--> ave --tem_caracteristica--> penas`.
- `orbita` comprova apenas uma aresta **diretamente cadastrada**:
  `Lua --orbita--> Terra`. Não mistura `orbita` com `parte_de`,
  nem infere uma órbita direta a partir de várias órbitas sucessivas.
- Uma prova ausente resulta em **desconhecido**, nunca em "não é verdade".
  O sistema não deduz automaticamente a relação inversa.
  Um nó do tipo `caracteristica` só pode ser destino de
  `tem_caracteristica` e não pode ser uma classe, componente ou órbita.

As respostas exibem o caminho de relações que sustenta a conclusão.
O CRIVO não aprende regras ou fatos automaticamente lendo texto:
as arestas continuam cadastradas explicitamente e precisam de revisão
humana. Consultas fora dos padrões reconhecidos continuam no recuperador.

**Teste:** os casos de `testes_regras_mistas.py` foram registrados antes
de alterar o motor. Incluem demonstrações sintéticas com nomes que não
existem nos fatos cadastrados, contraexemplos e limites de inferência.
A suíte principal roda em Python 3.8, 3.11 e 3.13.

`python avaliar_regras_mistas.py` faz uma avaliação pareada de 278
perguntas gerais, removendo cada pergunta testada do índice. O
recuperador **sem grafo** apresenta **192 acertos**, enquanto
tanto o **grafo anterior** do PR #10 como **o grafo novo** apresentam
**189 acertos**. O novo motor não trouxe regressão adicional. As três
diferenças frente ao recuperador não assistido já existiam com o
PR #10 e envolvem perguntas sobre aranhas, sapos e o Sol.
Uma mudança no identificador da resposta lógica não é necessariamente
erro factual, mas requer uma comparação semântica separada.

```bash
python -m unittest testes_raciocinio testes_regras_mistas -v
python avaliar_regras_mistas.py
```

**Limite:** encadear relações explicitamente curadas não demonstra
compreensão livre de português, raciocínio causal, capacidade geral
de programação ou aprendizado autônomo. A rede neural classificadora
não passa automaticamente a utilizar os novos fatos como treino.

## Provas negativas e referências editoriais (PR #12)

O motor relacional agora distingue **três situações** para perguntas binárias
sobre `tipo_de`:

- **Prova positiva:** existe uma cadeia de categorias que demonstra a relação.
- **Prova negativa explícita:** foi cadastrada uma incompatibilidade
  `disjunto_de` entre duas classes (ou seus ancestrais via `tipo_de`).
  O CRIVO mostra qual caminho leva à incompatibilidade.
- **Sem prova:** ele informa que **não sabe concluir**, sem transformar
  a ausência de evidências numa resposta negativa.

As incompatibilidades iniciais são `aracnideo ↔ inseto` e
`anfibio ↔ reptil`; são relações cadastradas manualmente,
**não descobertas pela rede neural**. A incompatibilidade é simétrica,
mas somente `tipo_de` pode levar a uma classe incompatível. Não se
misturam `parte_de`, `orbita` ou `tem_caracteristica` nesse cálculo.
Um cadastro que coloque uma entidade em duas classes explicitamente
incompatíveis é rejeitado.

Alguns fatos trazem o campo opcional `fonte_id`, apontando para o
identificador de uma **explicação editorial já cadastrada** em
`conhecimento.json`. Quando o fato é comprovado e o identificador
existe na base ativa, o CRIVO apresenta a explicação **junto com a
prova**, preservando histórico e o comando `mais`. Exemplos:

```text
você > Por que a aranha é um inseto?
Crivo > [Explicação cadastrada de insetos]
        Relações verificadas: Não. aranha → aracnídeo;
        aracnídeo é disjunto de inseto.

você > Como sabemos que o Sol é uma estrela?
Crivo > [Explicação cadastrada do Sol]
        Relações verificadas: Sim. Sol → estrela.

você > O gato é um peixe?
Crivo > Não tenho uma relação afirmativa cadastrada que permita
        concluir isso. Isso não significa que a afirmação seja falsa.
```

Perguntas **exatas já cadastradas** continuam usando a explicação
original antes do raciocinador. O sistema só usa a referência quando
a prova aplicável tem um `fonte_id` existente; referência inexistente
não se converte em evidência e não causa falha. A veracidade e
a pertinência semântica desses ponteiros precisam de **curadoria
humana**: existir um ID não significa que a fonte confirme qualquer
afirmação feita sobre ele.

**Comparação de desenvolvimento:** em 278 perguntas gerais com a
pergunta-alvo retirada do índice, o antigo grafo produziu
**189 identificadores corretos, 47 erros e 42 abstenções**; a nova
integração produziu **192 corretos, 44 erros e 42 abstenções**,
preservando o resultado do recuperador sem grafo. Três casos voltaram
a usar as explicações anteriores: aranha/inseto, sapo/réptil e
Sol/estrela. **Isso mede a escolha de IDs e não constitui medição
cega de raciocínio geral ou prova de aprendizagem espontânea.**

Para reproduzir: `python avaliar_regras_mistas.py` e
`python -m unittest testes_integracao_evidencias -v`. Os
testes incluem grafos sintéticos com nomes inéditos, referências
inexistentes, contradições, consultas de outras relações e preservação
das hipóteses temporárias.

## Treinamento da rede neural propria (experimental)

A rede `RedeCrivo` e uma MLP original em Python puro, inicializada sem pesos pre-treinados. **Classifica intenções, não gera respostas abertas.** O recuperador do chatbot continua responsavel pelas respostas. O classificador neural, mesmo carregado, so e usado quando concorda com o recuperador e supera os limiares atuais; portanto, um benchmark neural melhor **nao garante** melhora no chatbot final.

### No GitHub (sem instalar nada no celular)

No GitHub, abra **Actions → Treinar cerebro original do Crivo → Run workflow**. O workflow tambem dispara quando o codigo neural ou a base de conhecimento mudar na `main`. Ele:

1. Executa a suite de regressao.
2. Treina do zero com todas as perguntas de `conhecimento.json`, 60 epocas, 48 neuronios ocultos e 512 dimensoes, representacao `portugues`.
3. Recarrega e valida os pesos no Crivo.
4. Disponibiliza o arquivo `rede_crivo.json` como artefato para download (retencao de 14 dias).

Para usar localmente, extraia `rede_crivo.json` para a **mesma pasta** do `conhecimento.json`, junto do `crivo.py`. O carregamento e automatico quando assinaturas e rotulos correspondem. Se as perguntas ou as regras linguisticas forem alteradas, um novo checkpoint criado por esse fluxo e rejeitado como desatualizado, sem impedir as respostas do recuperador; `Crivo.erro_rede` informa o motivo. Checkpoints antigos sem essas assinaturas continuam aceitos por compatibilidade.

### Treinamento manual parametrizado

```bash
python rede_neural.py --base conhecimento.json --saida rede_crivo.json --epocas 60 --ocultos 48 --dimensao 512 --modo portugues --semente 42
```

A medicao de **138/278 (49,64%)** para a rede com essas configuracoes foi obtida em uma validacao cruzada de desenvolvimento em que cada pergunta foi deixada de fora do treino da respectiva dobra. Esse numero **nao** mede o checkpoint treinado sobre todos os dados em perguntas inteiramente externas, nem demonstra compreensao geral ou efeito nas respostas reais. As regras de sinonimos foram desenvolvidas usando a mesma base e isso limita o grau de independencia da avaliacao.
