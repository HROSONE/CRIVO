# Estado assíncrono: impedir respostas antigas e combinações ilegais

## Estados e dados
Idle, loading com request ID, success com data e error com mensagem são alternativas. Um megaobjeto com loading/error/data opcionais permite estados contraditórios. União discriminada melhora API estática e switch exaustivo expõe variante nova sem tratamento.

A implementação transition em [engenharia.mjs](exemplos/engenharia.mjs) é exemplo runtime simples. Ela presume eventos produzidos por aplicação confiável; não valida schema de payload/mensagem externo. A fronteira deve fazer parsing antes de dispatch.

## Geração da operação
start estabelece ID inteiro não negativo. Uma resposta só altera estado se houver operação loading com aquele ID. Resposta antiga é ignorada por identidade do estado. reset encerra estado lógico; response tardia não deve ressuscitar operação.

IDs precisam ser únicos/monotônicos no escopo que usa a máquina. A implementação aceita inteiro válido, mas não impede chamador reutilizar ID, o que pode fazer resposta antiga parecer atual. Camada proprietária deve gerar IDs e testar wrap/reset. ID não é credencial nem proteção de acesso.

## Cancelar ou ignorar
Abort reduz consumo de rede/CPU quando API suporta. Generation check impede commit stale mesmo quando abort chega tarde ou transporte não pode cancelar. São controles complementares. Loading finalizado por finally de request antiga também deve passar pelo mesmo gate de geração.

## UI e experiência
Render deriva de estado, sem efeito de rede dentro do render. Efeito de integração inicia trabalho e faz cleanup. Erros por campo precisam nome/associação acessíveis; mensagem de status não deve roubar foco ao chegar. Empty é resultado válido diferente de falha; lista vazia não equivale a ausência de response.

Mudança otimista exige relação com operação/entity/version. Rollback por snapshot antigo pode remover mudança posterior. Essa máquina simples não é protocolo de colaboração, cache global ou solução de rollback.

## Tipos e runtime
Fixture TS deve verificar: success exige data; loading exige id; evento desconhecido é erro; exhaustiveness falha ao adicionar variante. No runtime, entrada JSON é unknown e deve ser parseada. Cast de objeto recebido para State não constitui validação.

## Evidência e extensão
Testes emitem start 1/start 2/success 1/success 2 e exigem resultado novo; rejeitam evento desconhecido/ID inválido e verificam reset/erro atual. Extensões: stale-while-revalidate, multiple entities por chave, estados offline/retry, persistência e reducer tipado. Cada extensão precisa de novos estados legais, não apenas mais flags opcionais.

**Relações:** ts_state-events, frontend_react-races, frontend_react-reducer, ts_unioes, frontend_focus-races.

