# Passagem de trabalho — 16/10/2026

## Estado atualizado — 16/10/2026: v6-r0 em avaliação, não promovido

A rodada de conversa v6-r0 (checkpoint informado: passo 1.890, cerca de 46,1M parâmetros) apresentou melhora nas métricas comparativas compartilhadas pelo criador, mas ainda tem falhas relevantes por categoria. Os arquivos originais do Drive e seus hashes ainda precisam ser conferidos. **Não presumir que o v6-r0 esteja ativo no chat:** o código abaixo ainda documenta o carregamento da fase 6b v4. Não alterar o modelo ativo até validar checkpoint, tokenizador, testes comparáveis e compatibilidade.

- [Relatório v6-r0, métricas e limitações](experimentos/fase6b_conversa_humana/RESULTADO_v6_r0.md)
- [Código de seleção/carregamento atual](conversa_v3d.py)
- Próximo passo: conferir os artefatos originais e reproduzir a comparação no mesmo protocolo; manter o modelo atual como fallback até aprovação explícita.

---

## Histórico anterior — 10/10/2026

## Prioridade atual — última rodada de sessões concluída, sem promoção

[Relatório atual](experimentos/gerador_historico_textual_20261010/RELATORIO_SESSOES.md).
No mesmo PR #137 foram entregues **36 sessões autorais de seis turnos / 424
respostas deslexicalizadas**, com **3.699 treino / 428 desenvolvimento**
(334 antigos intactos + 94 novos). Não são conversas humanas; nomes/cortesia
não contam como capacidades. Texto e papéis entram na rede sem slots prontos.

Mesma rede própria: **81.433 parâmetros / 720 entradas**. Realocou **151
entradas lexicais** para verbos novos, sem alterar tokenizador ou capacidade;
569 IDs/pesos lexicais e demais pesos preservados na inicialização. Dicionário,
mistura de corpus e treino mudaram juntos: não isola causalidade.
Dois treinos reais: 20 épocas/selecionada16, **317,81 s**, e refino de seis
épocas/selecionada2, **60,18 s**. Menor erro de desenvolvimento selecionou a
primeira passagem em `a4c8312`, antes do teste final. Nenhum treino depois.

**Resultado: 0/10 sessões coerentes antes e depois; regressão.** Triagem
11→8/60; violações de data corrigida, preferência, destinatário e estado da
história. Todas as saídas terminaram; fontes completas. Desenvolvimento antigo
107→47/334 alvos literais, novo1/94; refino50/334 +1/94, rejeitado pelo critério.
Sem histórico14/60 e invertido10/60 na triagem, ambos0/10. Não demonstrou
benefício de histórico ordenado nem conversa natural. Revisão autoral do
agente, não independente/cega; saídas e motivos publicados.

Checkpoints `5ea28636d815…` e `2d33641a4460…`: **false/false**, fora do chat.
Oito pesos de raiz auditados e oito arquivos críticos intactos nesta rodada;
ativo público `28d05179e4dd…` preservado. Integridade nova **5/5** passou;
isso não aprova capacidade. Sem merge, nova memória/acervo/regra ou mudança
lateral de CI. Dívida da sonda antiga documentada na rodada anterior; não
mesclar com check relevante vermelho. PR continua em rascunho.

Último trabalho de hoje concluído como experimento negativo. Próximo passo
único desta frente: separar no desenvolvimento o efeito da realocação lexical
e do replay antes de outro treino, preservando o corpus variado entregue.
Os 10 casos agora são regressão conhecida; não ajustar o gerador a eles.

## Histórico — rodada 3 e contrastes

No mesmo experimento/PR #137, foram concluídos dois treinos próprios com
histórico textual, sem slots ou intenção pronta. [Relatório da rodada 3](experimentos/gerador_historico_textual_20261010/RELATORIO_RODADA3.md).
Mesma capacidade: **81.433 parâmetros / 720 tokens**, pesos iniciais próprios
preservados e Adam novo; arquitetura, matemática e inferência intactas.
Treinador ganhou apenas continuação opcional com os IDs de vocabulário
preservados. Não baixou, executou ou integrou modelos externos.

Corpus: 100 → **400 formulações deslexicalizadas de pedido**, 6.731 exemplos
de treino, depois **7.202** com contrastes de correção/autoria/hipótese/ausência.
**334 exemplos de desenvolvimento anteriores preservados**. As 100 famílias
originais de resposta ainda são estreitas; novas formulações e nomes não
representam novas capacidades. Dados e revisão autorais do agente, não
conversas humanas observadas ou avaliação independente/cega.

Desenvolvimento: entropia **2,3756 → 0,6390 → 0,5271**; gerações iguais aos
alvos **26 → 75 → 107/334**. Sondas contrastivas: **4 → 9/32**. Treinos reais:
24 épocas/791,37 s e 12 épocas/408,61 s. Isso mede reprodução interna, não
compreensão geral. Seleção dos pesos em `910dc91`, antes de abrir o teste final.

Nova avaliação congelada antes dos dados, `a09c13e`: **12 sessões / 48 turnos**,
SHA `5ba9c48eebac…`. Resultado: **0/12 mantêm o fio antes e depois**; triagem
11 → 9/48. Mesmo checkpoint sem histórico: 12/48; invertido: 11/48; ambos
0/12. Sem fonte truncada; EOS em todas. Frases quebradas, referentes perdidos,
tarefas trocadas e pelo menos três violações confirmadas, apesar de zero
termos proibidos na triagem. Não demonstrou melhora de conversa natural.

Os checkpoints `3b81f5a47b59…` e `a18055611310…` continuam **false/false**,
fora do chat. O ativo #136 `28d05179e4dd…` e os oito pesos de raiz auditados
são idênticos à base. Não promover por perda menor ou por CI verde.
Regressão anterior e pergunta dinossauros/IA continuam reprovadas; são
casos conhecidos, não avaliação inédita desta rodada. Piloto e rodadas
anteriores preservados.

Verificações: Seq2Seq **21/21**, integridade **10/10**. Bateria por escopo:
78 testes, um falha em três subcasos da sonda antiga de escrita. Falhas e
respostas idênticas reproduzidas na base `b0bdb055…`; documentação/logs no
experimento. Sem enfraquecer teste, mudar workflow/matriz, incluir correção
lateral de CI ou mesclar com check relevante vermelho. PR permanece em
rascunho; falha lateral não impediu concluir os treinos isolados.

Próximo trabalho único: diversificar **respostas completas e sessões**, além
de reformular os mesmos padrões, com texto/histórico e outro teste congelado
antes do treino. Os 12 casos novos agora viram regressão conhecida. Sem
nova memória, acervo, orientação, guardas ou parâmetros ampliados.

## Histórico — objetos e correções na escrita

[Experimento de referências](experimentos/referentes_escrita_20261010/README.md),
base pública #135 (`ca31090f6ce0…`): **52 turnos / 11 sessões** congelados
antes da mudança. Site e motor: 0/6 referências/correções e 0/5 fronteiras;
depois, **6/6 e 5/5 no motor e HTTP**, zero violação de objeto/estado/domínio
nos critérios limitados. Sondas autorais do agente, não sessões do dono nem
avaliação humana/cega.

O objeto do acontecimento ativo chega ao gerador mesmo após pronome; uma
correção explícita substitui o objeto em vez de acumulá-lo como novo fato.
Ambiguidade, negação e história antiga depois de pergunta factual pedem
esclarecimento. A fonte da resolução aparece no trace. Usa a última escrita
existente, sem nova memória, acervo, arquitetura ou parâmetros.

Não houve treino nesta rodada. Checkpoint próprio aprovado `28d05179e4dd…`
permanece idêntico; todos os dados/juízes/checkpoints anteriores preservados.
Exigir regressões históricas e checks relevantes verdes antes do merge,
confirmar commit/checkpoint no site e repetir os 52 turnos antes de publicar.
A matriz completa segue manual/semanal; pós-merge somente verificação curta.

Limites: apenas objeto único com artigo explícito, poucos verbos de pronome e
correção do trecho inteiro. Não resolve qualquer pronome ou correção livre;
negação não é realizada como cena nova. Concordância, transições genéricas,
dez classes e quatro passos permanecem. Não alegar generalização geral.
Próximo passo único após publicação: melhorar a naturalidade da realização
com corpus próprio, preservando estes casos e os gates anteriores.

## Integração medida — ligação entre acontecimentos e continuação

[Experimento causal](experimentos/continuidade_causal_20261010/README.md),
base #134: 88 turnos novos congelados, **0/10 → 10/10** no motor e HTTP
local real; **0/2 → 2/2** esclarecimentos, zero troca de domínio,
referente exigido ausente ou inversão de estado nos critérios limitados.
Sondas autorais do agente, não participantes humanos/avaliação cega.
Objeto literal e estado da escrita entram na mesma GRU própria; não
recopia o relato inteiro. Seleção do estado/passo é estrutural.

Treino real, 20 épocas, mesma rede de **85.130 parâmetros / 321 tokens**;
9.024 exemplos anteriores intactos + 1.280 supervisões próprias. Treino e
validação compartilham padrões/vetores: não demonstra compreensão neural
geral. Repetição byte a byte. Original `adf0fa8c…` permanece false/false;
#134 arquivado. Cópia aprovada após todos os gates motor + HTTP; original continua isolado.

Motor já preservou **110/114**, 79 antigos, 52 histórias; **40/40** práticos,
**8/8** diversidade, **2/2** sondas prospectivas de 18 turnos. Todos esses gates passaram também no HTTP. Formas comuns de continuação:
0/3 → 3/3 nos dois modos, 24 turnos, regressão 114 repetida sem perda.
Cópia aprovada `28d05179e4dd…`; original false/false.
Publicação exige CI relevante verde e confirmação do commit/checkpoint no site.

Ainda dez classes/quatro passos, extração limitada, cabeçalhos genéricos,
artigos/concordância imperfeitos, episódios clássicos. Não fôlego infinito,
planejamento livre, generalização irrestrita ou diálogo humano geral.
A rodada atende corpus/segundo treino/esclarecimento/guarda da Fase 3
no recorte medido. Depois de CI verde, merge e validação pública, as
Fases 0–3 atendem o plano mínimo de diálogo limitado. O objetivo de
conversa humana geral continua não demonstrado. Não abrir outra frente
para substituir esse limite por uma alegação de capacidade não medida.


## Estado anterior — variedade da realização própria medida (#134)

[Experimento de diversidade](experimentos/diversidade_dialogo_20261010/README.md):
os mesmos 48 turnos em oito sessões autorais passaram de **0/8 → 8/8**
no motor e HTTP (base público, depois local real). Corpos distintos,
retirando cabeçalho e declarações copiadas: **8 → 32**. Zero problemas
nos critérios limitados de fidelidade; 48 respostas idênticas nos dois
modos. Não humanos nem avaliação cega; padrões de classes conhecidas.

GRU própria existente, mesmos **85.130 parâmetros**, 321 tokens e
atributos. Corpus 9.024 exemplos; 1.920 alvos ganham formulações autorais.
20 épocas, treino realmente executado e repetido **byte a byte**.
Original `4b871b30…` permanece false/false; somente a cópia
`ca908bff34dece5d6b3b3ea208dbdeca2d5c499cecf31f1edd63ade77b575ee2`
é aprovada após gates. #133 `4e5894e2…` arquivado, pesos/evidências
anteriores preservados. Sem modelo externo, nova arquitetura ou memória.

**110/114**, todos os **79 antigos**, **52 histórias**, zero domínio,
referentes ausentes ou desvios preservados no motor e HTTP. Utilidade
prática permanece **40/40**, textos do motor idênticos ao #133. Mesmas
dez sessões/104 turnos idênticos nos dois modos; seis critérios mínimos
de escrita mantidos. Não se afrouxaram os quatro casos não pontuados.

Ainda são quatro padrões por classe; escolha estrutural, declarações
recopiadas, finais e transições genéricos, personagens secundários pouco
ativos e episódios clássicos reutilizados. Não prova planejamento, novos
assuntos, conversa humana nem fôlego infinito.

CI por escopo acrescenta contratos de aprovação/diversidade e 48 HTTP;
não aciona a matriz completa nem repete escrita após merge. Confirmar
commit/checkpoint e repetir 48 turnos + smokes conhecidos no site antes
de declarar publicado; `validar_publicacao.py` exige os hashes esperados.

Próximo passo único: melhorar a ligação entre acontecimentos e
continuações, reduzindo relatos recopiados e transições genéricas com
corpus próprio e a mesma rede, preservando os gates atuais.

## Estado anterior — continuidade prática medida (#133)

[Experimento de contexto prático](experimentos/contexto_pratico_20261010/README.md):
mesmos 40 turnos das quatro falhas após #132, **15/40 → 40/40** no motor
 e HTTP real (antes público, depois local); sessões mínimas **0/4 → 4/4**,
zero desvio proibido no conjunto. Quatro sondas adicionais autorais,
29 turnos, **0/4 → 4/4** segundo leitura do agente; sem humanos/avaliação
cega. Referentes, restrições e tempo declarados entram na tarefa correta.
Fatos hipotéticos não substituem observações. Guarda rejeita troca de
minutos/vasos; não cria memória nem aprende modelos novos.

**110/114** anteriores preservados no motor/HTTP, 79/79 antigos,
52/52 histórias, zero domínio/referente ausente. Os quatro antigos não
pontuados continuam documentados. Checkpoint aprovado `4e5894e2…`,
35 pesos anteriores e experimento #132 intactos. Orientação prática é
estrutural/autoral, não geração neural ou planejamento geral; linguagem
repetitiva, regras limitadas e janela de vinte mensagens permanecem.

CI existente por escopo inclui contratos + 40 HTTP + 114, sem bateria
completa ou repetição depois do merge. Confirmar commit/checkpoint e
os mesmos 40 casos no site após publicar antes de declarar concluído.

Próximo passo único: diversificar a realização do contexto correto com
corpus próprio de diálogo e falhas novas medidas no site, mantendo
estes gates; sem nova memória/acervo/arquitetura/parâmetros externos.


O objetivo vigente é diálogo utilizável em português, com arquitetura,
tokenizadores e pesos próprios. O plano do dono de 09/10 substitui a
prioridade anterior de adiar treino de diálogo. Não criar outra memória,
ampliar acervo, aumentar parâmetros ou abrir outra frente nesta etapa.

## Estado anterior — escrita condicionada aprovada no #132

[Experimento de acontecimentos](experimentos/escrita_acontecimentos_20261010/README.md),
base #131 `ed2bf1a7…`: mesmos 114 casos, **80 → 110/114** no motor;
**110/114 HTTP local real**, 79/79 antigos preservados nos dois modos,
zero troca de domínio, referente ausente e desvio proibido nesses 114.
52/52 histórias entregues. Quatro casos de metadados/restrição usam
esclarecimento em vez da peça escrita esperada; critérios não alterados.

Mesmas dez sessões autorais, 104 turnos por modo: **0/10 → 6/10** atendem
critérios mínimos de escrita, segundo leitura do agente. Não participantes
humanos nem avaliação cega. As quatro práticas novas continuam falhando;
transições genéricas, episódios reutilizados e simplificação limitada.
Não declarar conversa livre geral ou raciocínio neural demonstrado.

GRU própria existente: **85.581 → 85.130 parâmetros**, 9.024 exemplos
combinados (6.144 treino / 2.880 validação), 32 épocas finais, repetição
byte a byte. 2.048/2.048 saídas controladas de acontecimentos em padrões
compartilhados; não prova generalização. Seleção de reação/transição é
estrutural; a rede realiza o contexto. Sem modelo externo.

Candidato original `a042a271…` continua false/false. Cópia de integração
`4e5894e2fe4a23bab63cb3a6b8a69da023a2b07b43829a7e706e6528bd1e780d`
aprovada e habilitada após gates. Checkpoint anterior `0873ad29…` arquivado,
35 pesos/metadados anteriores intactos. Fatos/cálculos/fontes continuam
rígidos. API e navegador: histórico de vinte mensagens, 24.000 caracteres;
doze turnos reais reconstruídos sem truncar abertura. Não memória infinita.

CI de escrita por escopo: contratos HTTP + conjunto congelado, sem push
após merge; matriz completa manual/semanal. Após merge, confirmar commit
atual e checkpoint acima no site e executar smoke com entidades inéditas.

Etapa seguinte do #132, atendida no experimento de contexto prático: corrigir as quatro falhas observadas
(frações/tempo, bicicleta/rodas, horta/condições, troca/retomada), congelando
antes e preservando os 114. Não abrir nova memória ou ampliar acervo/modelos.

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
