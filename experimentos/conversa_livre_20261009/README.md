# Pedidos abertos sobre a sessão — 09/10/2026

O main ef2fafd (PR #119 mesclado) lembrava os dados, mas não os usava para
uma sugestão ou explicação aberta. Esta revisão liga cinco atos limitados
ao estado existente: sugerir, explicar escolhas, resumir, consultar e
perguntar o que falta. Nenhuma gramática de declaração foi adicionada.

## Medição congelada

As 12 sessões, 57 mensagens e 25 solicitações foram congeladas no commit
adb6017 antes da implementação. O SHA256 de `sessoes.json` é
`b2f0d427b3a5387a10a6755b56f9ad4f3f74ebc4d193347d9d400c6d0a593501`.
Critérios nunca entram no pedido do modelo e permaneceram iguais. O
avaliador final também verifica que o código não muda durante a execução.

| Medida | Main anterior | Candidato — motor | Candidato — API |
|---|---:|---:|---:|
| Sessões com todos os critérios preservados | 0/12 | 11/12 | 11/12 |
| Solicitações corretas | 2/25 | 23/25 | 23/25 |
| Realizações neurais aceitas dos fatos da sessão | 0 | 16 | 16 |

Os dois acertos anteriores eram recusas genéricas que satisfaziam critérios
fracos de desconhecimento. A leitura das 25 respostas novas confirmou
esclarecimentos pertinentes nos casos desconhecidos e ambíguos.
Nas 21 solicitações encaminhadas ao consumidor pessoal: 16 realizações
neurais, um recuo pela guarda literal e quatro esclarecimentos sem fatos.
A rede leu a memória em 17 solicitações; ler não equivale a gerar com êxito.
O campo `respostas_neurais=17` dos relatórios inclui também a resposta
factual sobre DNA; não significa 17 realizações da memória pessoal.

A sessão 9 permanece reprovada nos dois modos: o relato sobre lápis,
desenho e calma não vira uma comparação causal coerente. Não mudamos o
teste para esconder essa falha. A meta anterior à implementação era 8/12.

## O que está ativo

A seleção dos sujeitos, fatos atuais e operações é **estrutural**. O
Transformer autoral existente recebe os fatos completos e conserva os
mesmos controles do PR #119: contexto limitado, prefixo da fonte e guarda
literal. Os complementos da sugestão e do próximo passo são estruturais;
não são planejamento aprendido pela rede. Sem geração ou após uma
rejeição, conserva-se a resposta estrutural. As respostas do bot nunca
viram declarações de memória. Uma proibição exige esclarecimento antes de
recomendar a opção preferida. Fatos substituídos ou retirados não entram
na seleção. A continuação usa apenas o trace do turno imediatamente
anterior, com referentes ainda existentes.

A troca explícita de tema com pergunta factual volta à ficha correspondente
e conserva sua fonte. Código, textos enviados e ficção mantêm suas rotas.
A crise continua prioritária. Isso é conversa contextual limitada; não é
geração livre nem raciocínio geral. Consultas não reconhecidas ainda podem
cair nas limitações dos roteadores antigos. Não há promessa de interpretar
qualquer paráfrase, categoria de presente ou problema causal.

`controle_codigo.json` confirma memória e três checkpoints ativos iguais
à base. Os nomes das 12 sessões têm zero ocorrências no texto rastreado da
base e no currículo novo; a auditoria não certifica corpus bruto ausente.

## Treino executado e rejeitado

Treinamos uma RedeSequencial autoral 1168×48×6, 56.406 parâmetros, durante
110 épocas, semente 119. Foram 2.544 exemplos de treino e 448 de validação,
com famílias, nomes e frases separados. Só o currículo autoral congelado
entrou no treino. A validação interna teve 240/448 classificações corretas,
168/297 aceitações corretas e **104/192 negativos aceitos**. Os limiares
continuaram 0,80 e margem 0,20. Apesar de acertar o treino, não generalizou.

O checkpoint está em `roteador_rejeitado/pesos.json`, com `aprovado=false`,
sem caminho de ativação no chat. O modelo e treinador estão confinados a
este experimento. O consumidor ativo usa operadores explícitos, em vez
de publicar esse roteador ou reduzir o limiar. `pesquisa.md` documenta
fontes primárias e a mudança de hipótese. A validação foi inspecionada:
não é reservada para certificação futura. Nenhum peso de geração mudou.

## Verificação

- 31 testes de memória, paráfrases e realizador passaram.
- 42 testes relacionados a diálogo passaram, com quatro pulos previstos.
- 17 contratos iniciais passaram; os dois contratos posteriores de
  preferência proibida e disponibilidade sem objetivo entraram na rodada
  final de Python 3.8: **27/27**, sem dependências opcionais (19 do consumidor
  e oito guardas do realizador).
- A bateria anterior de desenvolvimento conserva **20/20 mensagens**,
  em seis conversas. Este relatório não reivindica reexecução de todos os
  outros conjuntos antigos nem substitui a matriz completa do CI.
- Replay HTTP complementar: **8/8 HTTP 200, 3/3 consultas, 3/3 realizações
  neurais**, com Melorina, Renavo e correção de preferência. Os resultados
  completos estão em `manual_http.json`. É um teste autoral, não cego.

Reprodução:

```sh
OPENBLAS_NUM_THREADS=1 python experimentos/conversa_livre_20261009/avaliar.py --exigir-meta --saida /tmp/livre-motor.json
OPENBLAS_NUM_THREADS=1 python experimentos/conversa_livre_20261009/avaliar.py --modo web --exigir-meta --saida /tmp/livre-web.json
python -S -m unittest testes_conversa_sessao testes_realizacao_memoria.TestesFonteDoRealizador
OPENBLAS_NUM_THREADS=1 python experimentos/conversa_livre_20261009/manual_http.py
```

O replay HTTP requer socket local. A reprodução do treino requer NumPy,
é opcional e termina com falha proposital enquanto não atingir o gate:
`python experimentos/conversa_livre_20261009/treinar_roteador.py`.
Não inicia nenhum treino de geração livre. O CI descobre os 19 contratos
na matriz existente e roda também a sonda congelada de motor. A aprovação
da revisão depende dos próprios checks; não pressupõe os checks do #119.

## Regressões encontradas pelo CI e corrigidas

O candidato inicial a6aa22b falhou no CI completo. A reprodução do job de
compreensão encontrou três falhas em 52 testes: perguntas sobre Plutão,
Urano e Vênus entravam na rota pessoal porque a heurística tratava um nome
capitalizado como possível pessoa. A pergunta original sobre Marte tinha
esse mesmo desvio, reprovando a etapa comum à matriz de 12 jobs.

A correção exige um sujeito já registrado ou uma continuação imediata
ligada à resposta pessoal anterior. Apenas uma solicitação explicitamente
pessoal de preferência desconhecida pode pedir esclarecimento sem sujeito
registrado. Nomes de planetas e personagens bíblicos não criam referentes.
Nenhum critério, caso original, peso ou teste existente foi removido.

Passaram os 22 contratos direcionados (20 do consumidor e dois métodos
factualmente reprovados) e os 12 testes bíblicos. Os logs estão em
`correcao_ci/`. Isso não substitui a aprovação do CI completo do novo commit.
A correção de repetição pós-merge, já aplicada na main em 60fd187, foi
incorporada à branch: PR continua com matriz completa e main tem apenas
cinco contratos rápidos. O job pós-merge dessa correção passou em 20s;
seu sucesso não constitui aprovação do PR 120.
