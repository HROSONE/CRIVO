# Rodada textual 3 e continuação contrastiva — 10/10/2026

**Não aprovada para o chat.** O desenvolvimento melhorou, mas as conversas
novas continuaram **0/12**. Não foi demonstrada melhora de conversa natural.
O PR #137 continua como experimento isolado, com pesos próprios preservados.

## Trabalho efetivamente executado

O corpus passou de 100 para **400 formulações deslexicalizadas de pedido**,
com **6.731 exemplos de treino**. Depois foram acrescentados contrastes
textuais de correção, autoria, hipótese e informação ausente: **7.202 exemplos
únicos de treino**. Os **334 exemplos de desenvolvimento anteriores foram
preservados**, sem incorporação ao treino. Não é um corpus de conversas
humanas: são supervisões autorais. As 100 famílias originais de resposta
continuam estreitas; quatro formulações não equivalem a quatro capacidades.
Os contrastes têm 19 categorias com nomes variados e 16 categorias de
informação ausente; não multiplicar esse número pelas expansões lexicais.

Foram feitos dois treinos reais com o mesmo vocabulário, IDs e arquitetura:
**81.433 parâmetros, 720 tokens, BiGRU/GRU própria com atenção e cópia**.
Recebe mensagem e histórico com papéis; nenhum slot, intenção pronta ou
resposta do juiz entra na rede. Não consulta o corpus durante a geração.
Nenhum modelo externo foi baixado, executado ou integrado.

- Rodada 3: continuação dos pesos próprios da rodada 2, 24 épocas,
  Adam novo 0,0009, dropout 0,15, amostragem 0,10; **791,37 segundos**.
- Contrastes: continuação da rodada 3, 12 épocas, Adam novo 0,0006,
  dropout 0,10, amostragem 0,10; **408,61 segundos**.
- Ambas: semente 173, lote 32, 24 unidades, embeddings 16, 128 buckets,
  fonte 192, resposta 64, dropout lexical 0,05, validação a cada duas épocas.
  NumPy 2.3.5, CPU e uma thread BLAS. Não é retomada exata do otimizador.

O treinador de raiz ganhou inicialização opcional por checkpoint próprio
compatível, preservando a associação entre índices e pesos. Matemática,
arquitetura, tokenizer, inferência e integração permaneceram intactos.
Os oito pesos de raiz auditados, incluindo o ativo `28d05179e4dd…`, são
idênticos à base #136. Nenhum checkpoint factual foi sobrescrito.

## Separação e escolha antes do teste final

Uma avaliação nova de **12 sessões × 4 turnos** foi congelada no commit
`a09c13e`, antes de preparar os dados desta rodada. SHA-256:
`5ba9c48eebac0b461fb115ca368ec6e9cfc6a4f8fc79c0847e20aedfd33f9f0b`.
Os nomes, situações e mensagens desses casos não entram no corpus.

Dados/protocolo do primeiro treino foram registrados em `16c3604`.
O treino da rodada 3 e a preparação dos contrastes estão em `f9d57b7`.
A seleção foi registrada em **`910dc91` antes de executar o teste final**:
usar contrastes se melhorassem as 32 sondas de desenvolvimento e não
piorassem a entropia nos 334 casos em mais de 10%. Escolheu contrastes.
Não houve adaptação posterior aos erros do holdout.

As sessões seguintes recebem as respostas realmente geradas, sem respostas
corretas inseridas no histórico. Decodificação gulosa fixa, 64 tokens.
O mesmo checkpoint é testado sem histórico e com a ordem invertida.
O agente escreveu corpus, sondas e revisão: **não é avaliação humana
independente ou cega**. Casos da rodada 2 e pergunta real do dono agora são
regressão conhecida; não entram no placar inédito.

## Números e resultado

| Desenvolvimento conhecido | Rodada 2 | Rodada 3 | Contrastes |
|---|---:|---:|---:|
| Entropia com resposta anterior correta | 2,3756 | 0,6390 | 0,5271 |
| Gerações iguais ao alvo / 334 | 26 | 75 | 107 |
| Sondas contrastivas iguais ao alvo / 32 | — | 4 | 9 |

Igualdade literal mede reprodução, não naturalidade. As reformulações de
desenvolvimento compartilham operações/respostas com o treino. O ganho
interno não prova generalização a diálogos ou acontecimentos novos.

| Avaliação nova | Sessões na triagem | Turnos na triagem |
|---|---:|---:|
| Antes: pesos próprios da rodada 2, com histórico | 0/12 | 11/48 |
| Depois: contrastes, com histórico real | **0/12** | **9/48** |
| Mesmo checkpoint, sem histórico | 0/12 | 12/48 |
| Mesmo checkpoint, histórico invertido | 0/12 | 11/48 |

Revisão das 48 respostas: **0/12 mantêm o fio**, antes e depois. Frases
quebradas, referentes ausentes, tarefas trocadas e histórias não entregues.
O resultado não mostra benefício do histórico no holdout. Todas chegaram
ao EOS, nenhuma fonte foi cortada: o fracasso não é truncamento.

Mesmo com zero termos proibidos na triagem depois, há **pelo menos três
violações confirmadas**: preferência por lugar não declarada; pé repetido
após mudança para chão; preferência por ter companhia inventada. A lista
não é exaustiva. Triagem lexical aceitou nove frases, algumas sem sentido.
Ver `revisao_final_qualitativa.json` e saídas integrais dos três controles.

A pergunta conhecida do dono sobre dinossauros/IA continua reprovada:
“Comece pela rever a escolha. Vale pensar no que mudou e decidir se a
escolha.” Não responde o dilema ou a comparação; não foi treinada uma
resposta específica para ela. Regressão anterior: 0/12 e 5/36 na triagem.

## Pesos, hashes e verificação

- Rodada 3: `3b81f5a47b59f394402551d166994027ff4e224c4e8730631f58cd9f81c46473`.
- Contrastes selecionados: `a180556113106ca125f0420cc80227a6703908678babe7725cda40fafb62ffaa`.
- Corpus rodada 3: `6cd6f3d2e81af55b9917b11131261b2bb68db5a522a87257f770b6913dc73f88`.
- Corpus contrastes: `a3170c2259b3608af3ce9d60bb88f79817e5b552ef361f83c43a14946e0b0881`.

Ambos `aprovado: false` e `ativo_no_chat: false`. Protocolos/manifestos
registram origem, hashes dos scripts/dados, hiperparâmetros e ambiente.
Reprodução byte a byte não foi executada nem alegada.

**21 testes Seq2Seq e 10 de integridade passaram.** A bateria por escopo
executou 78 testes: um teste falha em três subcasos da sonda antiga de
escrita. Reproduzido no commit base `b0bdb055…`, com falhas e respostas
idênticas. Ver `divida_ci_rodada3.json` e os dois logs versionados. Não foi
alterada a sonda, relaxado critério ou desobrigado check. Nenhuma matriz,
workflow ou correção lateral de CI entrou. Não mesclar com check relevante
vermelho; essa dívida não impede concluir o experimento isolado de treino.

Para reproduzir sem sobrescrever arquivos preservados: num checkout
isolado de `16c3604`, executar `rodada3.py treinar`; num checkout isolado de
`f9d57b7`, executar `contrastes.py treinar`. O primeiro contém pesos iniciais
da rodada 2; o segundo já contém a rodada 3 e o protocolo contrastivo,
mas ainda não contém o checkpoint de contrastes. Com NumPy instalado:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/gerador_historico_textual_20261010/rodada3.py treinar
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/gerador_historico_textual_20261010/contrastes.py treinar
```

## Próximo trabalho único

Diversificar **respostas completas e sessões**, além de reformular pedidos
das mesmas 100 famílias; treinar com histórico textual e reservar outro
teste antes desse treino. Estes 12 casos tornam-se regressão conhecida.
Não adicionar uma regra para cada falha, aumentar parâmetros ou aprovar
pelo erro interno menor. O portão de conversa natural continua fechado.
