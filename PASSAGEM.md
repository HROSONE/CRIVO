# Passagem de trabalho — 10/10/2026

O objetivo vigente é diálogo utilizável em português, com arquitetura,
tokenizadores e pesos próprios. O plano do dono de 09/10 substitui a
prioridade anterior de adiar treino de diálogo. Não criar outra memória,
ampliar acervo, aumentar parâmetros ou abrir outra frente nesta etapa.

## Fase 0 concluída

O #125 está mesclado em `9ed051bf2b74668073e0ac480b43c652314b88e7`.
Antes do merge, `composicao` e `regressoes-b` passaram em 3.8/3.11/3.13,
sem falhas. Os seis smokes no HTTP público preservaram domínio e
referentes. O site nessa base fez **35/37** no novo conjunto congelado:
continua sem entregar as duas histórias, embora preserve a personagem
no esclarecimento. O CI após o merge usa smokes, sem repetir matriz longa.

## Fase 1: corpus e checkpoints de diálogo próprios

Experimento isolado: [relatório](experimentos/dialogo_20261010/README.md).

- **37 casos reais congelados**, incluindo os 35 anteriores sem alterar
  campos e duas consultas realmente observadas no site.
- **480 diálogos autorais / 5.760 turnos / 2.880 respostas alvo**;
  2.304 exemplos de treino e 576 de validação, por diálogo. Compartilham
  seis tipos e padrões de resposta; não representam diversidade humana.
- Seq2seq: treino realmente executado, **0/10 → 3/10** de conteúdo
  mínimo, mas leitura revela linguagem incoerente. Ensaio reprovado.
- GRU própria existente: **0/10 → 7/10** nos mesmos pedidos reais;
  **2/2 histórias** entregues com a capivara astronauta. Reduz para 88.969
  parâmetros. Repetição do treino produziu pesos idênticos byte a byte.
- Esses números comparam geradores isolados, **não o site antes/depois**.
  O site existente já acerta oito desses dez pedidos com respostas
  estruturadas. Substituir tudo pela GRU seria regressão.
- Ambos os checkpoints permanecem **aprovado=false, ativo_no_chat=false**.
  Nenhum dos 35 arquivos de pesos ativos mudou. Nenhum modelo externo
  foi baixado, executado ou chamado; nenhum workflow alterado.
- Sete contratos de isolamento, proveniência, partições e carregamento
  passaram. Dados, hashes, hiperparâmetros, falhas e reprodução estão
  em `experimentos/dialogo_20261010/`.

## Limites atuais

O candidato ainda falha em explicar funcionamento e autoria; não entrega
as perguntas enumeradas pedidas. Histórias são genéricas e capacidades
repetitivas. A GRU precisa receber ato/argumentos corretos; não interpreta
livremente o histórico. Métricas lexicais não certificam coerência humana.

A Fase 2 não foi implementada: faltam guarda de conversa, integração,
trace e avaliação no motor/HTTP e em dez conversas reais de 6–8 turnos.
O chat público continua usando os pesos e as rotas da base.

## Próximo passo único

Integrar seletivamente a rota de conversa no PR de Fase 2, preservando
as respostas atuais nos atos em que o candidato falha. Antes do merge:
≥34/37 com peça certa, zero troca de domínio, 100% dos referentes
exigidos, pelo menos 6/10 conversas reais mantendo o fio, duas histórias
entregues, checks relevantes verdes e validação do commit no site.
Não promover nenhum checkpoint enquanto esses critérios não passarem.

## Histórico

As métricas estruturadas de #113–#124 não demonstram conversa livre.
O [documento anterior](https://github.com/HROSONE/CRIVO/blob/9ed051bf2b74668073e0ac480b43c652314b88e7/PASSAGEM.md)
permanece no histórico Git, assim como branches e checkpoints anteriores.
