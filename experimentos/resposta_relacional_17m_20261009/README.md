# Triagem nos pesos maiores próprios

O gerador ancorado de 17.428.224 parâmetros já está disponível e usa a mesma
arquitetura causal, com configuração e tokenizer próprios diferentes. A sonda
direta mostrou redação mais clara, mas execução insuficiente do pedido. Esta
triagem testa adaptar essa base existente, sem novo pré-treino ou peso externo.

Usa o mesmo currículo revisado e treinador do piloto menor, via referência
relativa, e os mesmos 12 diálogos de desenvolvimento congelados. Os dados
continuam procedurais, com formas compartilhadas; não avaliação independente.
O tokenizer maior é usado para recodificar integralmente os pares e verificar
se cabem em 256 tokens. Replay: os mesmos 27 pares humanos antigos.

Há dois braços, controle antigo e currículo relacional, partindo exatamente
dos mesmos pesos maiores. Orçamento menor: 30.000 tokens-alvo por braço,
900 segundos no máximo. Checkpoint: passo zero ou fim, por perda de validação
relacional. A coleta de sessões não participa do treino nem da escolha.
Não comparar diretamente contagens de tokens entre tokenizadores/modelos
para atribuir efeito causal ao número de parâmetros.

A base Torch local foi convertida dos tensores NumPy próprios, com igualdade
verificada após recarga e paridade dos dois executores de tokenização em 53
textos. `diagnostico_pareado_20261009/conversao_ancorado.json` documenta origem,
hashes e limites. A conversão não é treino e não altera a geração protegida do
chat. Os pesos candidatos ficam locais e continuam experimentais.

Esta é uma extensão curta da investigação, motivada pela função e qualidade
de redação dos pesos já disponíveis. Integração exige comportamento adequado,
retenção e ausência de erros críticos de fonte/correção; menor perda não aprova.
O teto de 90 minutos de computação ativa da investigação continua valendo.
