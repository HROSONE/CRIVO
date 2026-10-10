# Prioridades ativas do CRIVO — 10/10/2026

## Prioridade atual — generalização do gerador textual (experimento reprovado)

A etapa de diálogo limitado (#136) está publicada. No
[experimento textual](experimentos/gerador_historico_textual_20261010/README.md),
a rede Seq2Seq própria já existente recebeu somente texto/histórico com
papéis, sem slots ou intenção pronta. Pesos aleatórios novos, 81.433
parâmetros/720 tokens, 3.707 treino + 334 desenvolvimento, 100 padrões
em dez grupos. Treino efetivo: 20 épocas/330,13 s, melhor época 12.

Avaliação nova congelada antes dos dados: 12 sessões/36 turnos mais uma
pergunta real do dono. Resultado: **0/12 mantêm o fio**; controle sem
histórico também 0/12. Houve inversões de correção (domingo→quarta,
caleidoscópio→bússola) e respostas malformadas; não alegar zero invenção.
Pedido real dinossauros/IA também reprovado. Juiz lexical não aprova
naturalidade; revisão do agente, não avaliação humana independente/cega.

Nos 100 pedidos vistos no treino: 87 alvos literais com histórico, 32 sem;
4/4 nomes novos copiados com a mesma pergunta treinada. Mostra leitura
textual em padrões conhecidos, sem generalização da linguagem. Perda de
treino 0,1195 contra desenvolvimento 2,3756; não confundir memorização com
avanço em conversa natural. Famílias/saídas de desenvolvimento da rodada 2
compartilhadas; piloto com famílias separadas e alvos impossíveis preservado.

Checkpoint `1027f94344ca…` continua false/false; não entrou no chat.
Pesos, arquitetura, treinador e runtime da produção #136 permanecem
intactos. PR experimental #137 em rascunho, sem nova memória/acervo,
orientação, guardas, parâmetros ampliados ou CI lateral.

Próximo passo único: mais formulações de entrada por ato no corpus
próprio e outra avaliação congelada antes do próximo treino. Estes casos
são regressão conhecida; não chamá-los inéditos depois de usá-los para
preparar a próxima rodada. Não promover este checkpoint por CI verde.

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
