# Contexto do laboratório e próxima rodada no GitHub

O relato do laboratório expôs cinco falhas: resposta negativa curta após saudação, apresentação do nome, elogio, autoria em primeira/segunda pessoa e pergunta sobre capacidade. Os novos atos reconhecem frases completas antes das reflexões genéricas, preservam a grafia do nome e deixam fatos e perguntas de definição no fluxo factual. Nome é estado da conversa e pode ser reenviado pelo contrato HTTP já existente; não adiciona armazenamento no servidor. Autoria é registrada como declaração do usuário, sem conferir identidade ou conceder privilégios.

`testes_conversa_laboratorio.py` reproduz a sequência anexada em um único bot e por replay HTTP, verifica memória do nome, sessões independentes e controles para profissões, negações e perguntas factuais. A correção é no motor de conversa; o treino de programação não substitui esse motor.

## Programação

A rodada Colab de 6.000 passos compilou 7/8 JS e 6/8 TS e acertou zero das 16 tarefas. Ela iniciou dos pesos gerais (`345008...`), não do candidato Colab de 2.000 passos. O melhor valor de validação de diálogo ocorreu no passo 800, não no último.

Nesta rodada, `algoritmos.json` acrescenta 960 variantes de prompts em 30 famílias autorais, com respostas e casos: matrizes, estatística simples, índices, somas acumuladas, janelas, Euclides, Fibonacci, primalidade e texto. São 30 famílias, não 960 algoritmos independentes. O gerador `scripts/gerar_algoritmos_programacao.py` reproduz o arquivo. As famílias de teste do benchmark anterior continuam fora do treino. Como os resultados desse benchmark já foram observados no desenvolvimento, ele não é uma avaliação independente.

O preparador limita o currículo anterior a quatro exemplos por família/linguagem para diminuir a dominância das variantes simples. O corpus resultante tem 1.948 exemplos de treino (976 de código e 972 conceituais), 336 de validação e 156 de teste. Esse corpus pequeno não é suficiente para programação de fronteira.

## Seleção e execução

O treinador aceita `--selecionar-melhor` e `--paciencia-validacoes N`. Salva o menor valor de entropia cruzada na validação da fase atual em `candidato/melhor/`, com tokenizer, pesos, relatório e checkpoint. Preserva separadamente o último estado de Adam/RNG em `candidato/checkpoint.pt`. As opções de seleção fazem parte da assinatura de retomada. Seleção por perda de validação não garante correção funcional.

O workflow manual `programacao.yml` usa CPU, perfil atual de 2.612.352 parâmetros, até 2.000 passos, limite de 2.200 s para o ciclo e parada após quatro avaliações sem melhora. Compilação Node/TS e preflight funcional precedem o treino; QuickJS é usado quando bubblewrap não está disponível. Resultados QuickJS continuam sujeitos à confirmação em Node para promoção. O candidato permanece experimental.

Os pesos de 6.000 passos enviados pelo usuário não foram disponibilizados; esta execução começa dos pesos gerais próprios versionados. Não é retomada do Colab. O artefato `candidato-programacao-atual` contém corpus, seleção, pesos, checkpoints e `avaliacao.json`, disponível por 30 dias no run do GitHub.

Referências autorais: 2.280 implementações e 9.136 casos por linguagem aprovados. Isso mede as referências, não o modelo.
