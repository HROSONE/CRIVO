# Passagem de trabalho — 10/10/2026

O objetivo vigente é diálogo utilizável em português, com arquitetura,
tokenizadores e pesos próprios. O plano do dono de 09/10 substitui a
prioridade anterior de adiar treino de diálogo. Não criar outra memória,
ampliar acervo, aumentar parâmetros ou abrir outra frente nesta etapa.

## Estado mais recente — generalização medida, candidato reprovado

#130 mesclado em `431191b34e767a672921b0d0b79070ff8dd8293e` e validado
publicamente: 79/79, orientação prática autoral limitada, checkpoint de
diálogo `0873ad29…` ativo. Esse é o estado do chat; não confundir com os
ensaios abaixo nem com conversa livre geral.

Novo [experimento de generalização](experimentos/generalizacao_dialogo_20261010/README.md):
dez sondas autorais inéditas, 104 turnos no motor e site, congeladas antes
da mudança. 35 pedidos de escrita observados ampliam o conjunto sem
alterar os 79 anteriores. Baseline **80/114**; piloto final **96/114**,
novos **1/35 → 17/35**, antigos 79/79 preservados. Ainda há **16 casos
com referentes ausentes** e cinco desvios proibidos. Zero troca de domínio
detectada nesses 114, não nos 104 turnos completos.

Treino próprio realmente executado: 4.928 exemplos autorais combinados,
4.096 treino e 832 validação. GRU existente, **85.581 → 85.453 parâmetros**,
109,29 segundos CPU e repetição byte a byte. Nas 64 sequências controladas
com oito etapas compartilhadas: antigo 0/512, candidato 512/512;
retirando trecho anterior do candidato, 0/512. Isso mede uso do contexto
nos padrões treinados, não raciocínio/generalização. Dez sessões novas
completas: revisão pelo agente **0/10 → 1/10**, não participantes humanos.

**Não ativado.** O checkpoint e seu patch de piloto ficam apenas no
experimento. Runtime e checkpoint de produção iguais à base; 35 arquivos
anteriores de pesos/metadados e diálogo ativo intactos. Sem HTTP longo
aprovado: contrato atual reconstrói até dez mensagens anteriores.
Isolamento e medição são verificáveis; o CI não declara a integração verde.

Próximo passo único: corrigir interpretação/realização de acontecimentos
e restrições enquanto a escrita está ativa, medindo nos mesmos 35 pedidos.
Finais com evento, narrativa cotidiana e tom ainda falham. Utilidade nova
(bicicleta, horta, reformulação de frações, troca de tarefa) permanece
documentada nas sondas; sem alegar que esse treino a resolveu.

## Fase 0 concluída

O #125 está mesclado em `9ed051bf2b74668073e0ac480b43c652314b88e7`.
Antes do merge, `composicao` e `regressoes-b` passaram em 3.8/3.11/3.13,
sem falhas. Os seis smokes no HTTP público preservaram domínio e
referentes. O site nessa base fez **35/37** no novo conjunto congelado:
continua sem entregar as duas histórias, embora preserve a personagem
no esclarecimento. O CI após o merge usa smokes, sem repetir matriz longa.

## Fase 1: corpus e checkpoints de diálogo próprios

Experimento isolado: [relatório](experimentos/dialogo_20261010/README.md).

- **37 casos reais congelados**, incluindo os 35 anteriores sem alterar
  campos e duas consultas realmente observadas no site.
- **480 diálogos autorais / 5.760 turnos / 2.880 respostas alvo**;
  2.304 exemplos de treino e 576 de validação, por diálogo. Compartilham
  seis tipos e padrões de resposta; não representam diversidade humana.
- Seq2seq: treino realmente executado, **0/10 → 3/10** de conteúdo
  mínimo, mas leitura revela linguagem incoerente. Ensaio reprovado.
- GRU própria existente: **0/10 → 7/10** nos mesmos pedidos reais;
  **2/2 histórias** entregues com a capivara astronauta. Reduz para 88.969
  parâmetros. Repetição do treino produziu pesos idênticos byte a byte.
- Esses números comparam geradores isolados, **não o site antes/depois**.
  O site existente já acerta oito desses dez pedidos com respostas
  estruturadas. Substituir tudo pela GRU seria regressão.
- Ambos os checkpoints permanecem **aprovado=false, ativo_no_chat=false**.
  Nenhum dos 35 arquivos de pesos ativos mudou. Nenhum modelo externo
  foi baixado, executado ou chamado; nenhum workflow alterado.
- Sete contratos de isolamento, proveniência, partições e carregamento
  passaram. Dados, hashes, hiperparâmetros, falhas e reprodução estão
  em `experimentos/dialogo_20261010/`.

## Fase 2 — integração seletiva validada antes do merge

Relatório: [integração do diálogo](experimentos/integracao_dialogo_20261010/README.md).

- Mesmo conjunto congelado: **35/37 → 37/37**, no motor e HTTP real;
  zero troca de domínio e zero referente ausente, **2/2 narrativas**.
- Dez novas sessões congeladas antes da implementação, 62 mensagens:
  revisão pelo agente **4/10 → 7/10** mantendo o fio nos dois caminhos.
  Não são conversas com dez participantes humanos nem sete sessões
  inteiramente neurais; incluem os executores estruturados existentes.
- GRU do #126 aprovada **somente para história, continuação e final**
  no escopo demonstrado. A cópia de produção está em
  `rede_dialogo_conversa.json.gz`; os pesos são iguais ao experimento.
  Checkpoint experimental original e 35 pesos anteriores intactos.
- Guardas distintas: conversa permite composição; dados da sessão só
  entram por argumentos fornecidos. Fatos, cálculo e fonte continuam rígidos.
- Capacidades, funcionamento e autoria conservam o executor atual.
  Trace HTTP informa peça, uso da rede/estado, argumentos e recuos.
- CI por escopo: contratos da integração e 37 casos no HTTP entram no
  job de roteamento existente; matriz completa permanece manual/semanal.
- Merge requer os checks relevantes verdes e validação pública do
  commit após publicar; os resultados locais não substituem essa etapa.

## Limites atuais

Os geradores isolados da Fase 1 ainda falham em explicar funcionamento e autoria; não entregam
as perguntas enumeradas pedidas. Histórias são genéricas e capacidades
repetitivas. A GRU precisa receber ato/argumentos corretos; não interpreta
livremente o histórico. Métricas lexicais não certificam coerência humana.

## Fase 3 — segundo treino e falhas públicas

#127 mesclado e validado no site: 37/37 e 7/10 sessões, commit
`044ed446afd1c9b66c3b1ddd11b087c5c5a23658`. Seis turnos das três sessões
reprovadas foram congelados antes da mudança: **37/43 → 43/43** no motor/HTTP,
zero troca de domínio e referente ausente. Dez sessões intactas:
**7/10 → 10/10**, revisão pelo agente, não dez participantes humanos.
Orientação prática ainda genérica; não certifica conversa livre geral.

Segundo treino próprio: oito arcos, **4 → 52 padrões de ficção**, 384 diálogos
novos, 8.064 turnos com o corpus anterior. Treino focalizado: 1.216 respostas
e validação em 256, entidades separadas e arcos compartilhados.
**88.969 → 85.581 parâmetros**, reprodução byte a byte. Experimentos anteriores,
factual e 35 pesos intactos. Final isolado desativado; cópia de produção
aprovada somente após os gates. Dados/pesos preliminares preservados.

Retomada e esclarecimento nominal usam os estados existentes. Restrição de
nome preserva escrita; cinco frases conservam personagem, cenário e amigo.
Trace registra neutralização do texto residual quando interfere no ato.
34 contratos e sonda anotada de 48 contextos passaram; CI HTTP verifica 43 casos.
Limites: oito arcos, conselhos genéricos, contagens/estilos arbitrários e
continuação após final podem exigir esclarecimento. Publicação requer
checks verdes e replay público do commit integrado.

Evidências: [segundo treino](experimentos/dialogo_v2_20261010/README.md).

## Continuidade após #128 — falhas novas medidas

#128 mesclado e validado no site em `3e8eed593288af6be17c83d11aeae5d14d1e598e`:
43/43 e dez sessões anteriores preservadas. Em seguida foram executadas
seis novas sondas autorais de seis turnos no site e motor. Não são participantes
humanos. As três conversas de orientação prática continuam reprovadas.

18 turnos novos de escrita foram congelados, conservando os 43 anteriores:
**47/61 → 61/61** no motor/HTTP, zero troca de domínio e referente ausente.
O roteador agora atende aventura, mude o final, continuação após final,
mais uma vez e essa personagem. Companhia e cenário têm papéis separados.
A nova cena avança; reescrita preserva a cena anterior e os participantes.

Treino próprio executado e reproduzido byte a byte: 384 exemplos novos,
16 padrões, 1.536 treino/320 validação, 181 tokens e **85.581 parâmetros**,
sem aumento. Dez sessões anteriores mantêm os mesmos critérios restritos;
isto não transforma orientação genérica em ajuda prática aprovada.

A rede lê ato, cena e argumentos selecionados; texto residual neutralizado
após revisão detectar mistura/repetição. Oito arcos e seleção estrutural da
cena, sem planejamento neural geral. Checkpoint experimental isolado falso;
aprovação da cópia de produção exige resultados completos, revisão e gates.
Merge só com checks relevantes verdes; confirmar publicação e repetir no site.

Evidências: [continuidade](experimentos/dialogo_continuidade_20261010/README.md).

## Orientação prática após #129

#129 mesclado e validado publicamente em
`d62d19a694154b49fdb05a67bb299544cce89b39`: 61/61 casos e três novas sessões
de escrita resolvidas. As três sessões práticas ainda falhavam.

Os 18 turnos práticos realmente observados no site foram congelados, sem
alterar os 61 anteriores: **66/79 → 79/79** no motor e HTTP real, zero troca
de domínio e zero referente ausente. Nos novos casos: **5/18 → 18/18**;
os cinco acertos anteriores eram reconhecimento de objetivo/restrição/memória,
não ajuda concreta. Revisão das três sessões no motor: **0/3 → 3/3** para
ajuda ou esclarecimento específico. Não são participantes humanos.

O executor autoral usa histórico/tarefa já existentes. Desenho propõe traço e
ajuste da cauda, respeita material/tempo e condiciona o próximo passo à forma
relatada. Estudo pergunta o tópico ou propõe frações com cálculo exato,
reformulação e conferência do resultado anterior. Horta começa por observação
da luz e perguntas de condições, sem inventar cultivo. Hipótese não vira fato.
Cancelamento e tarefas posteriores suspendem o objetivo anterior.

**Não houve treino nem mudança de pesos.** Os 35 pesos anteriores e a GRU
de produção do #129 continuam intactos, com 85.581 parâmetros. Trace registra
`orientacao`, ato, fontes do usuário, cálculo e `gerador_neural_usado=false`.
Guardas de fatos/fontes continuam rígidas. Nove contratos adicionais cobrem
variações inéditas, correções, origem, HTTP e tentativa de adulteração.

Limites: três tarefas explícitas, histórico de vinte mensagens, instruções
de desenho em grande parte voltadas a peixe, operações restritas de frações
e esclarecimento inicial de horta. Há repetição; não é planejamento geral
nem compreensão neural livre. As dez sessões anteriores mantêm critérios
restritos; lembrar não certifica utilidade em outras tarefas.

O job de roteamento existente verifica os 79 casos por HTTP e os nove
contratos adicionais. Matriz completa manual/semanal. Publicação requer
checks relevantes verdes e replay público do commit integrado.

Evidências: [orientação prática](experimentos/orientacao_pratica_20261010/README.md).

## Próximo passo único

Medir novas conversas sem seguir estes três roteiros, conservando a bateria
congelada. Registrar onde o CRIVO ainda repete orientação ou perde a tarefa,
e usar essas falhas reais na próxima iteração do diálogo próprio. Não tomar
79/79 nesta bateria como aprovação de conversa livre geral.

## Histórico

As métricas estruturadas de #113–#124 não demonstram conversa livre.
O [documento anterior](https://github.com/HROSONE/CRIVO/blob/9ed051bf2b74668073e0ac480b43c652314b88e7/PASSAGEM.md)
permanece no histórico Git, assim como branches e checkpoints anteriores.
