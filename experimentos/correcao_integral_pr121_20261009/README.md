# Correção de todas as causas dos checks com falha do #121

A auditoria dos sete jobs vermelhos encontrou duas causas, repetidas entre
Python 3.8, 3.11, 3.13 e a integração do interpretador. As seis falhas de catálogo
e continuação social foram corrigidas no #124. Faltava corrigir a definição
de “diferença de potencial”: após uma pergunta anterior, o roteador tratava a
palavra “diferença” no alias como pedido de comparação. Isso permanece reproduzível
na main `b2f718ad` anterior a esta alteração.

`auditoria_checks.json` registra os sete jobs, links e mensagens dos logs,
incluindo todos os nomes de testes que falharam. Os quatro jobs de composição
falharam na mesma pergunta; os três de regressões-b falharam nos mesmos seis
testes de autoconversa. Nenhuma outra falha apareceu nesses logs concluídos.

O roteador agora deixa uma pergunta definicional com alias completo reconhecido
no executor factual original, antes de usar fatos anteriores para comparação.
Não há regra específica para potencial elétrico. Uma comparação explícita
continua usando as duas fichas da sessão. Os dois contratos adicionais exercitam
o caso com geração própria ativa e a comparação legítima.

## Validação obrigatória desta correção

Reexecutar as baterias completas que falharam, com as expectativas existentes,
sem desligar a geração própria e sem retirar casos:

- `composicao`: os mesmos 18 testes, incluindo todos os conceitos, aliases e pares.
- `regressoes-b`: descoberta integral do grupo que tinha 645 testes no #121.
- Versões de Python: 3.8, 3.11 e 3.13.
- Checks usuais de configuração, roteamento de 35 casos, chat e diálogo.

O workflow `testes.yml` mantém a descoberta, os testes bíblicos e os testes
originais. A opção manual `grupos=composicao-regressoes-b` seleciona apenas
esses dois grupos nas três versões, sem acionar os jobs de matemática/treino.
A execução manual padrão e a semanal continuam com todos os quatro grupos;
os PRs e a verificação curta da main mantêm seus gatilhos anteriores.

```sh
gh workflow run testes.yml --repo HROSONE/CRIVO \
  --ref codex/correcao-121-completa-20261009 \
  -f grupos=composicao-regressoes-b -f benchmark=nenhum
```

Esta auditoria não declara os checks históricos do #121 verdes: eles executaram
o código anterior e continuam sendo o registro da falha. A correção precisa
ter resultados verdes no seu próprio commit antes de ser mesclada.
