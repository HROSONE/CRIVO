# Treino nativo JS/TS com código real

O candidato anterior falhou na compilação de todas as 16 tarefas. Esta rodada muda
os dados e o treinamento; não atribui capacidade sênior ao modelo.

## Dados e licenças

`dados/programacao/fontes_codigo.json` fixa revisão, arquivo SHA-256, diretório e
licença de Ramda, Remeda, Zod, Immer, TypeScript e Three.js. O preparador baixa
somente fontes (nenhum peso externo), preserva as licenças MIT e Apache-2.0 e
analisa a sintaxe com TypeScript e `node --check`. Não executa os módulos baixados.
Não instalar dependências nem executar testes/builds de terceiros para curar as fontes.

A preparação local desta revisão aprovou 1.360 arquivos reais, 14.528.636 bytes
(~13,9 MiB), excluindo testes, declarações `.d.ts`, duplicatas exatas e nomes de
implementações diretamente relacionados às famílias reservadas do benchmark.
Treino: 1.087 arquivos, 3.006.292 tokens incluindo as referências autorais de treino.
Validação: 143 arquivos e 248 instruções de código. Teste: 130 arquivos e 16 instruções.

Utilitários de mesmo nome em bibliotecas/linguagens diferentes ficam na mesma
partição. O tokenizer BPE de 4.096 tokens aprende somente na partição de treino.
Esta separação não prova independência semântica. O benchmark sintético de 16
problemas já foi observado e serve como diagnóstico; não é certificação externa.
A análise de sintaxe das fontes não verifica os tipos ou o funcionamento dos projetos.
As referências autorais de instruções têm testes funcionais próprios.

## Etapas

1. Transformer próprio `codigo6m`: 5.912.576 parâmetros, dimensão 256, 6 camadas,
   8 cabeças e contexto 512; inicialização do zero com o novo tokenizer de código.
2. Pré-treino autoregressivo em código, até 12.000 passos, lote 4; seleção pela
   entropia de validação de código. Horizonte máximo: 24.576.000 tokens de entrada.
3. Ajuste por instruções de código (976 exemplos de treino, sem misturar alvos de
   definições), até 8.000 passos, com 10% de repetição de linguagem de código.
4. A cada 1.000 passos do ajuste, gerar uma resposta por família/linguagem de
   validação, sem recuperação nem reparo. Escolher pelo total de soluções corretas,
   depois compilação, término e, apenas como desempate, perda de validação.
   Código gerado usa o verificador isolado; respostas esperadas não entram no prompt.
5. Avaliar o melhor candidato no teste, sem usar o teste para seleção. Preservar
   fontes, licenças, hashes, último checkpoint/Adam/RNG e melhor checkpoint.

A seleção funcional não substitui regressões, teste independente nem os critérios
mínimos de promoção. Código correto em poucas tarefas não comprova competência
em projetos. QuickJS não testa APIs Node/navegador e não basta para promoção.
Não há ativação automática no site.

## GitHub

Workflow `treino-codigo-real.yml`, runner CPU, orçamento de treino de 9.600 segundos
(~2h40), teto de job de 210 minutos com instalação/verificação/avaliação. Se o
orçamento vencer, pausa a etapa salvando checkpoint; a quantidade final de passos
fica nos relatórios. O tempo de GPU não foi usado. Artefatos ficam disponíveis
por 30 dias; baixar para preservação permanente.

```sh
python scripts/treinar_codigo_real.py --saida /tmp/ciclo-real \
  --cache /tmp/fontes-codigo --tsc /tmp/ts/node_modules/typescript/lib/tsc.js \
  --perfil codigo6m --pretreino-passos 12000 --sft-passos 8000 \
  --threads 2 --max-segundos 9600
```

Retomada de uma etapa: use `scripts/treinar_linguagem_profunda.py --retomar` com
mesma configuração, corpus, política de seleção e versão do código. Não usar
pesos do antigo candidato como se fossem compatíveis com este tokenizer/arquitetura.
