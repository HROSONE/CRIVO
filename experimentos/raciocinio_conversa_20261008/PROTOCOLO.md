# Raciocínio em conversa — experimento próprio

Base: PR114, commit cb3b256. Desenvolver em branch separada, preservar todos os checkpoints e o teste de conversa livre anterior como diagnóstico reutilizado, sem chamá-lo de validação inédita.

Primeiro comparar três checkpoints compatíveis com seus tokenizadores próprios: linguagem 2,6M; base do leitor 17,4M; piloto modular 17,4M. O leitor é usado aqui apenas em sua projeção causal de linguagem como experimento; isso não transforma sua aprovação para leitura em aprovação para diálogo. Geração crua, greedy, 64 tokens, histórico com respostas reais do próprio candidato. Avaliar semanticamente as 24 respostas e registrar repetições/término como diagnósticos auxiliares, não como capacidade de raciocínio.

Depois desenvolver interpretação de intenção, fatos e correções, memória de trabalho por sessão e execução verificável de cálculo, interseção de restrições e condições/posse. As conclusões dependem de relatos do usuário, sem certificá-los como fatos do mundo. Preserve consultas factuais, código, crise, fontes e protocolos já existentes. Usar supervisão rastreável e pesos próprios somente.

O controle final autoral será fixado antes da implementação e dos treinos. Famílias/paráfrases, números e entidades diferentes do treino, com casos incompletos, negativos, atualizações e mudanças de assunto. Os dados de teste não são usados pelo treino, pela seleção dos checkpoints ou para ampliar padrões. Não alterar oráculos após olhar os resultados. Ao diagnosticar erros do controle, sua avaliação futura deve ser identificada como reprodução, e outro controle deve ser fixado para novas decisões.

Comparar interpretação, operação selecionada, conclusão verificável e resposta textual separadamente. Verificar também o caminho real do chat por replay e ausência de vazamento entre instâncias. Se o gerador ajustado não preservar as conclusões ou não generalizar, rejeitá-lo; publicar esse resultado sem substituí-lo por aprovação falsa. Um ganho híbrido de interpretação + motores explícitos não será anunciado como prova de raciocínio neural geral.

Controle e treino são autorais, sem avaliação humana independente. Não medir apenas palavras esperadas nem crescimento de parâmetros. A entrega deve incluir respostas completas, métricas por tarefa, regressões, limites e código reproduzível.
