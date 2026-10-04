# Recuperação do treino próprio e do armazenamento — 04/10/2026

O pré-treino de 30.000 passos foi concluído e continua aproveitável. O candidato
não demonstrou conversação confiável e não deve substituir o motor atual.
Nenhum peso externo pré-treinado foi usado nesta investigação.

## Resultados conferidos nos artefatos

Arquitetura: 15.953.664 parâmetros, 8 camadas, dimensão 384, contexto 512.
O pré-treino processou 184.320.000 tokens-alvo **com repetição do corpus**.
No SFT original, o melhor ponto foi o passo 200; a execução parou em 1.000 por
validação. Continuar até 6.000 não era sinal de que a qualidade melhoraria.

| Medida | Resultado |
|---|---:|
| CE humana de validação antes do SFT | 2,884557 |
| Melhor CE humana do SFT original (passo 200) | 2,842532 |
| CE humana no passo 1.000 | 3,05596 |
| CE humana do teste reservado, candidato original | 2,679556 |
| CE humana do teste reservado, baseline 2,6 M | 4,225228 |
| Contrato integrado original | 33/72, contra 42/72 do motor atual |
| Respostas de origem neural aprovadas no contrato | 6/36 |

Menor entropia cruzada mede previsão dos tokens com a resposta correta anterior
fornecida. Ela não comprova que o modelo consegue sustentar uma resposta livre.
Não usar os exemplos do teste reservado para montar treino ou escolher hiperparâmetros.

Os pesos do melhor SFT original foram recuperados e conferidos pelo SHA-256
`8882d3a1ff14372f17b10438fa7bb675dd23aea810eefd273413b5bff300e451`.
A base própria de pré-treino usada no piloto tem SHA-256
`470098b465de7f0f5d470849b69af19af0ab7ae138eadee8f2e694170c88ce5f`.
A geração com cache e a referência sem cache diferiram em no máximo 4,3e-6 nos
logits conferidos: o cache não explica as frases incoerentes.

## Correções

- Pausas operacionais deixam de contar como avaliações adicionais e de consumir
  a paciência da parada antecipada. Execução contínua e retomada fora de um
  intervalo de avaliação preservam seleção, pesos, Adam e RNG nos testes.
- O salvamento final não repete uma gravação já feita no mesmo passo.
- A opção experimental `--perda-por-resposta` dá peso igual à janela de resposta
  de cada par amostrado, em vez de deixar respostas longas dominarem a média
  do lote. A política faz parte da assinatura de retomada.
- Novo fluxo: treino em disco local; upload de arquivo ZIP novo entre blocos;
  verificação de tamanho e MD5 remoto; retenção dos dois snapshots mais recentes
  do mesmo experimento/etapa. Não sobrescreve continuamente um binário no Drive.
- A restauração verifica SHA-256 de cada arquivo, recusa arquivos inesperados,
  duplicados e caminhos externos, e não sobrescreve um destino existente.
- A limpeza histórica atua somente nos binários das pastas identificadas do
  experimento. Preserva a revisão atual, as duas mais novas e revisões fixadas.

Foram listadas 101 revisões de um checkpoint de cerca de 182 MiB. A soma dos
tamanhos históricos listados não é uma medição da quota faturada pelo Drive.
A limpeza real precisa da API de revisões autenticada no Colab: o conector desta
sessão permite listar revisões, mas não excluí-las. Não foi afirmado que o espaço
já foi liberado.

## Piloto pequeno realizado sem consumir GPU do usuário

Reaproveitou a base própria; lote 12, LR 0,00003, semente 20261004, replay de
linguagem 0,15, validação humana completa a cada 50 passos, perda por resposta.
Em CPU, o orçamento de 600 segundos encerrou no passo 51. O melhor ponto validado
foi o passo 50, com **CE humana 2,826618**, contra 2,842532 do melhor SFT anterior.

Nas sondas exploratórias de geração, o piloto ainda respondeu de forma incorreta
sobre geladeira, organização de tarefas, correção de data e JavaScript. A melhora
de validação não justifica promoção nem outra rodada longa de GPU. Os resultados
livres estão em `resultados/recuperacao_dialogo_20261004.json`.

O piloto de até 300 passos fica disponível, **desligado por padrão**, para uma
comparação controlada. A próxima mudança de qualidade deve revisar diversidade,
contexto completo e supervisão do diálogo, com critérios de respostas livres,
e não apenas aumentar o número de passos no mesmo conjunto pequeno.

## Usar sem repetir os 30.000 passos

Abra [Recuperar diálogo no Colab](https://colab.research.google.com/github/HROSONE/CRIVO/blob/codex/dialogos-colab-amplos/notebooks/recuperar_dialogo_colab.ipynb).
Com o treino antigo parado, execute as células na conta com acesso aos arquivos.
O padrão confere os relatórios e limpa versões antigas usando CPU. Deixe
`TREINAR_PILOTO = False` para não gastar GPU. O pré-treino e o melhor SFT original
permanecem preservados. A limpeza de versões é permanente; os arquivos atuais
não são excluídos.

O novo piloto usa pasta, ponteiro e revisão próprios. Não se tenta retomar Adam
antigo com código ou objetivo alterado: isso permanece recusado pela assinatura.
Depois que um piloto começa, sua revisão é fixada para retomar o mesmo experimento.
Os snapshots guardam checkpoint, pesos, tokenizer e relatório, atuais e melhores.
O corpus público é reproduzido por hashes; não é copiado ao Drive a cada bloco.

Uma desconexão pode perder até um bloco ainda não enviado (máximo 100 passos neste
piloto). Limites e disponibilidade de GPU do Colab continuam sendo do provedor.
Não rode duas sessões escrevendo no mesmo experimento ao mesmo tempo.
