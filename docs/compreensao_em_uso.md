# Compreensão de funções no chat em uso

Antes desta alteração, o chat público recusava a pergunta “Qual é o papel da
mitocôndria dentro de uma célula?”, apesar de possuir o fato sobre respiração
celular e produção de ATP. O compositor tentava resolver o trecho inteiro
“mitocôndria dentro de uma célula” como nome de um conceito.

O motor agora separa o pedido de função, o sujeito e o contexto. Reconhece
“papel”, “função”, “utilidade”, “para que serve” e “o que faz”. Tanto o sujeito
quanto o contexto precisam corresponder a nomes completos do catálogo; os
termos do contexto precisam aparecer na evidência selecionada. Uma definição
que descreve uma função pode responder ao pedido mesmo sem a etiqueta `funcao`.
Isso é seleção de evidência textual, não prova formal de uma relação nova.

Quando não existe uma comparação explícita, duas fichas conhecidas podem ser
apresentadas lado a lado, usando funções de ambas ou definições de ambas.
Uma explicação específica já cadastrada para o par tem prioridade. Pronomes
nas unidades de função conservam o antecedente da definição e suas fontes.
O turno “E o ribossomo?” conserva o pedido de função e troca o sujeito; a API
reconstrói esse contexto a partir do histórico e preserva as fontes utilizadas.

Não foram adicionadas respostas por pergunta, alterados os fatos do acervo,
treinados pesos ou habilitados candidatos experimentais. O Transformer mantém
sua configuração anterior. Esta entrega melhora a interpretação factual no
motor de produção; não demonstra conversa neural irrestrita.

## Verificação reproduzível

```bash
python -m unittest testes_funcoes_contextuais testes_busca_factual testes_web -v
python -m unittest testes_composicao_textual -v
python crivo.py --teste
```

Os testes novos incluem conceitos fictícios ausentes do currículo real,
contextos sem evidência, negação, qualificadores desconhecidos, comparação,
referentes e proveniência no contrato HTTP. A comparação pública em
`avaliacoes/compreensao_em_uso/antes_depois.json` registra 16 casos conhecidos;
é uma regressão de comportamento, não uma avaliação neural reservada.

O job `compreensao-chat` verifica o fluxo sem instalar bibliotecas de treino.
Após publicar, conferir `GET /api/chat` para o commit e `POST /api/chat` para
a pergunta original e seus turnos seguintes.
