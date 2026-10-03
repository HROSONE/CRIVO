# Segunda rodada de programação

O treino Colab de 2.000 passos (pesos `60a27ab9c9aee0c09c5b12341c8516e63b745f4df9a66947bf97405828840395`) reduziu a perplexidade de diálogo de 308,41 para 48,93. Compilaram 5/8 respostas JS e 0/8 TS; nenhuma foi executada. Algumas respostas JS eram `return n` com variável inexistente. Não comprova correção nem nível sênior.

## Novo currículo

`dados/programacao/curriculo.json` contém 3.600 exemplos autorais em 30 famílias, em JS e TS, com quatro casos por exemplo. São variantes de constantes, prompts e formas de implementação, não 3.600 problemas independentes. Há 24 famílias de treino e seis de validação. Inclui operações numéricas, transformações e consultas de listas, ordenação sem mutação e processamento de texto ASCII. As 16 tarefas de teste anteriores permanecem reservadas e não entram no corpus de treino. Este benchmark já foi observado durante desenvolvimento; não é uma avaliação independente.

O conjunto completo passa a conter 3.868 exemplos de treino (2.896 de código e 972 conceituais), 816 de validação e 156 de teste. Oráculos, casos e respostas são metadata do currículo; os prompts de geração não recebem as respostas ou os oráculos reservados. Nenhum resultado novo do modelo foi medido ainda.

Validação autoral: 1.800 referências JavaScript e 1.800 TypeScript compilam e passam em 7.200 casos por linguagem. Essa execução no host é exclusiva das referências autorais revisáveis, nunca de código gerado pelo modelo.

## Avaliação no Colab

A avaliação continua compilando JS com Node e TS com `tsc --strict`. Bubblewrap usa `/proc` vazio em vez de montar procfs. Se o ambiente bloquear namespaces, há fallback QuickJS 1.19.4: VM em subprocesso, sem APIs de arquivos, rede ou bindings Python, com limites de memória, pilha, CPU e tempo. O relatório registra o runtime de cada execução. QuickJS não avalia APIs Node, módulos, navegador ou projetos completos; resultados nesse runtime exigem confirmação em Node antes de qualquer promoção.

O novo notebook faz um preflight funcional de JS/TS antes do treino. Falhas de compilação TS ganham um orçamento separado (20 s de CPU / 30 s de parede), para reduzir encerramentos sem diagnóstico por limite curto. A execução do candidato mantém os limites menores.

## Rodar

Abra `notebooks/treinar_programacao_colab_v2.ipynb` pelo Colab. Ative GPU, conecte o Drive e execute as células. Use perfil `atual`, 6.000 passos e uma execução nova (EXECUCAO_ID vazio). Nunca reutilize a pasta de execução antiga para o corpus novo.

Opcional: preencha `MODELO_INICIAL` com o caminho completo da pasta `candidato` anterior no Drive. Sem esse caminho, inicia dos pesos gerais próprios versionados. A inicialização verifica arquitetura/tokenizer; os hashes dos arquivos de origem ficam associados à nova execução. Não altera o candidato anterior e não retoma o Adam de um corpus diferente. Checkpoints desta nova rodada podem ser retomados com o seu próprio EXECUCAO_ID.

Ao final, confira `avaliacao.json` e `candidato/relatorio.json`. O candidato continua experimental. Aumento de capacidade e novas etapas dependem das medidas de correção; esta rodada mantém 2.612.352 parâmetros.
