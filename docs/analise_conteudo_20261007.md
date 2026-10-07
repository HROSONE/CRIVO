# Análise de conteúdo enviado — primeira etapa

O chat pode receber um texto novo e trabalhar sobre ele, sem buscar uma ficha parecida no acervo. O fluxo é extrativo e determinístico: não é um novo treino do Transformer nem análise semântica geral.

## Uso

```
Resuma este texto em 2 frases: <conteúdo>
Analise este conteúdo: <conteúdo>
Identifique os padrões nesta sequência de ideias: <conteúdo>
Liste as ideias centrais: <conteúdo>
```

Também é possível enviar `Texto: <conteúdo>` e depois pedir `Resuma isso`, `E os padrões?` ou `Qual a fonte?`. Dois-pontos ou uma quebra de linha separam o pedido do conteúdo; aspas duplas também são aceitas. A fonte é o conteúdo enviado, não uma referência do catálogo.

O limite é de 12.000 caracteres para a mensagem inteira com conteúdo explícito, incluindo o cabeçalho. Perguntas comuns continuam com limite de 1.200. São aceitas até 200 unidades (frases ou itens); entradas maiores pedem divisão, sem truncar silenciosamente. O histórico contém no máximo dez mensagens e 24.000 caracteres; a interface remove as mais antigas quando necessário. O corpo HTTP tem limite de 256 KiB, tanto em Content-Length quanto em chunked.

## O que o motor faz

- Divide o documento em frases/itens com citações e offsets. Os offsets são relativos ao campo `content_analysis.conteudo`, que remove apenas espaços externos ao conteúdo delimitado.
- Escolhe trechos por frequência de termos, tamanho e redução de redundância, conservando a ordem original. O resumo padrão seleciona até três trechos; pedidos explícitos de uma a oito frases ajustam a seleção. Frases repetidas não ocupam várias posições.
- Mantém os dois lados de uma oposição literal quando um deles é selecionado, mesmo que seja necessário exceder o número pedido. Isso é explicado na resposta.
- Aponta recorrências lexicais e marcadores explícitos de contraste, condição, ordem, causa e conclusão. A recorrência de uma palavra não prova identidade semântica, e um conector causal não comprova a causa no mundo.
- Sinaliza afirmações iguais com/sem “não” como hipótese de oposição, com ambos os trechos. Sujeitos e condições textuais diferentes não são fundidos. Não pretende encontrar todas as contradições.

Na API, `content_analysis` traz método, modo, documento, unidades selecionadas, padrões, estatuto de observação/hipótese e evidências. A resposta mostra referências `[1]`, `[2]` etc. A interface identifica a análise extrativa, sem atribuí-la à geração neural ou à prova lógica.

## Integração e memória

O motor entra antes da busca factual e da interpretação de comandos de programação, após o protocolo de crise existente. O conteúdo não é executado, não vira uma ficha e não é tratado como declaração pessoal. Contextos pendentes de outros motores são limpos ao responder sobre o documento.

O documento fica somente no estado da instância de conversa. O adaptador HTTP reconstrói esse estado pelo histórico; uma requisição isolada não recupera o texto de outra pessoa. Uma mudança de assunto encerra o contexto do documento. Consulta de fonte apresenta os trechos originais. Não há gravação do documento no acervo ou treino automático.

## Validação

A suíte conjunta de análise, compreensão textual, memória, ecossistema, API HTTP/chunked e geração factual teve 88 testes aprovados. A análise também passou sem NumPy. Foram testados citações e offsets, negações em resumos, oposição literal, condições diferentes, ausência de padrões, isolamento entre requisições, conteúdo longo e limites do histórico/HTTP.

No navegador, um conteúdo com 54 unidades e mais de 1.200 caracteres passou por análise → resumo → padrões → fonte. As citações retornadas corresponderam ao texto original e não houve erros de JavaScript. O workflow `analise-conteudo.yml` exige esses contratos, incluindo a execução sem NumPy.

## Limites

A escolha das ideias centrais é uma heurística lexical, não compreensão geral. O resumo copia trechos completos; não produz uma paráfrase aprendida nem verifica a verdade externa do documento. A segmentação pode dividir abreviações, e relações implícitas, ironia e equivalências entre palavras não são resolvidas. O próximo avanço precisa de avaliação independente de relevância e de modelos treinados para essas relações, mantendo as evidências desta etapa.
