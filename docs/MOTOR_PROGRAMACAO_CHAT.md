# Motor próprio de programação no chat

A classe `Crivo`, a API `/api/chat` e a interface web agora usam o motor de
interpretação, diagnóstico e síntese limitada. A ativação é padrão e não exige
argumentos de laboratório. Não utiliza modelos externos nem GPU.

## Como experimentar

No menu **Programação**, use **Testar uma correção de código** ou **Rastrear uma
soma de array**. O primeiro botão envia este pedido real:

````text
Corrija este código JavaScript:
```javascript
return entrada - 2;
```
Exemplos: [{"entrada":0,"saida":2},{"entrada":3,"saida":5}]
````

O Crivo reproduz a saída incorreta, testa edições da AST e mostra a correção
`return entrada + 2;`. Informa quantos exemplos passaram, os fragmentos antes/depois
e o caráter de hipótese. Não certifica o programa para entradas que não recebeu.

Também pode enviar o código primeiro e os exemplos na mensagem seguinte. Para
executar sem pedir uma correção:

````text
Interprete este código JavaScript:
```javascript
let total = entrada + 2;
return total;
```
Entrada: 3
````

Para montar uma função simples, envie `Gere JavaScript com estes exemplos:` e uma
linha `Exemplos: [...]`. A função é construída pela busca limitada e conferida com
os exemplos. Não é geração textual livre. Também aceita um objeto JSON escrito
na mensagem com `acao` (`interpretar`, `diagnosticar` ou `gerar`), `codigo`,
`entrada`, `desenvolvimento` e `tipo` opcional para síntese. Não aceita referências
corretas ou casos reservados como campos do contrato.

## O que está ativo

- Parser e executor próprios do subconjunto JavaScript; estados e erros limitados
  por orçamento de execução. Código é tratado antes das reformulações linguísticas.
- Diagnóstico por exemplos de desenvolvimento e reparos locais de AST, sem ranking
  neural por padrão. A comparação anterior favoreceu a busca estrutural sem rede.
- Síntese a partir de exemplos na gramática já existente.
- Rede própria V3 de efeitos, **1.679 parâmetros**, com pesos reais do treino
  GitHub `37144385856`, semente padrão 7. Arquivo de pesos: **16.600 bytes**.
  A procedência e o SHA-256 ficam em `artefatos/efeitos_programacao/proveniencia.json`.

A rede prevê efeitos das operações que realmente ocorreram e compara suas
previsões com o executor exato. A API e a resposta informam concordâncias e limites.
Essa conferência auxiliar não torna a rede responsável pela geração de reparos
nem garante intenção correta do programa. O resultado e a aprovação de reparos
vêm do executor próprio exato. Efeitos fora do domínio não são previstos; não há
fallback silencioso apresentado como previsão neural.

A rede de ranking de 960 parâmetros continua no laboratório, e o Transformer de
programação permanece sujeito ao gate experimental existente. Esta ativação não
carrega nem promove esses candidatos. Não retreina nem altera os experimentos V1,
V2 e V3 congelados.

## Limites da integração

- Corpo de função de até 1.000 caracteres e 160 nós da AST; até seis exemplos,
  com no máximo 128 valores por entrada ou saída. O limite normal da mensagem
  continua 1.200 caracteres.
- Uma função completa pode ser enviada se tiver somente o parâmetro `entrada`.
  Aceita anotações simples na assinatura TypeScript; o corpo precisa pertencer
  ao subconjunto JavaScript, sem anotações internas, imports ou chamadas livres.
- Diagnóstico: até 256 edições, 128 verificações e 512 passos por execução.
  Síntese: até 1.000 candidatos. Arrays, objetos, strings e números continuam
  sujeitos aos limites do interpretador.
- O contrato exige que a entrada não seja modificada. Uma função que retorna o
  valor esperado mas modifica a entrada não é aprovada pelo diagnóstico/síntese.
- O histórico HTTP reconstrói o código e os exemplos sem repetir buscas antigas.
  O servidor não guarda conversas. Apenas pesos fixos do projeto ficam em cache.
- O histórico enviado à API continua sendo de mensagens do usuário. O replay não
  conserva automaticamente o código que foi criado na resposta do assistente;
  para analisar esse código, copie-o para a próxima mensagem.

## API e publicação

`GET /api/chat` informa `programming_active` e `programming_effects_model`.
`POST /api/chat` mantém o contrato existente `message`, `history` e `memory`;
respostas do motor acrescentam `code_analysis` com método, orçamento, resultado
ou hipótese e auditoria dos efeitos. A interface usa o selo **Análise de código**.

Os pesos têm integridade verificada antes de serem carregados. Sem NumPy ou pesos
compatíveis, o executor/diagnóstico/síntese continuam funcionando e o status da
rede informa `active: false`; nenhuma rede aleatória é criada para inferência.
A configuração da Vercel inclui os três arquivos pequenos do modelo, e o GitHub
executa testes de conversa, replay, HTTP, Unicode, regressões e uso efetivo dos
pesos antes da integração. A publicação em produção segue a integração Git já
existente no projeto. A confirmação de uso no site deve vir de seu `/api/chat`,
não apenas da conclusão do merge.
