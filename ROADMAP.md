# Prioridades ativas do CRIVO — 10/10/2026

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

## Integração medida — conclusão do plano de diálogo limitado

[Rodada causal](experimentos/continuidade_causal_20261010/README.md):
**0/10 → 10/10** conversas de oito turnos no motor/HTTP; **0/2 → 2/2**
esclarecimentos, zero troca de domínio e referente ausente nesse recorte.
Mesma GRU/85.130 parâmetros, 1.280 supervisões autorais adicionais;
original isolado false/false e reprodução idêntica. Estado e objeto
selecionados na escrita existente, sem nova memória/acervo/arquitetura.

As Fases 0–2 já têm integrações/medições relatadas abaixo e em PASSAGEM.
A Fase 3 pede expandir corpus com falhas novas, novo treino próprio,
melhorar esclarecimento e revisar a guarda: implementados e medidos nesta rodada. Todos os gates motor/HTTP passaram;
a saída operacional exige CI relevante verde e verificação do commit no site.
Motor: 110/114, 40/40 práticos, 8/8 diversidade e 2/2 sondas de 18 turnos.
Não abrir outra frente enquanto essa integração não estiver publicada.

O plano tem uma definição mensurável de diálogo limitado, não de IA humana
plena. Classes e quatro passos continuam autorais; problemas gramaticais,
padrões repetidos e ausência de generalização a novos assuntos permanecem.


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


O avanço anterior de utilidade prática (#133) continua preservado. Não
abrir memória/acervo, ampliar parâmetros ou iniciar outro PR de capacidade
enquanto esta integração não estiver verde e confirmada no site.
