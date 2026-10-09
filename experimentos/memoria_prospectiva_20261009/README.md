# Memória: avaliação prospectiva de novas formulações

O PR 117 preservou os referentes nas vinte sessões de desenvolvimento. Esta
rodada mede novas formulações na versão `467f644`, antes de qualquer ajuste
para elas. O conjunto foi congelado no commit `07a3b0c`.

São vinte sessões de quatro a oito mensagens do usuário. Misturam consultas
indiretas, ordem invertida, localização, objetivos, restrições, tempo com
qualificadores, correções, duas declarações na mesma mensagem e retomadas de
assunto. Há controles de pronomes únicos e ambíguos, hipótese, citação, fala
atribuída, retração e reinício. Uma sessão passa somente se todas as consultas
marcadas preservarem os referentes e valores e excluírem os concorrentes.

A meta mínima permanece em 12/20. Os critérios são externos ao motor e não
são enviados à memória ou usados como dados de treino. O SHA-256 congelado
é `5998a9d490eb3095927e433eddce9764f38145d95ae85f929e3c6a6e4c5d5081`.
Os identificadores completos de pessoas, objetos, preferências e objetivos
foram criados após os treinos e auditados em 632 arquivos textuais locais,
sem colisões. Não certificamos ausência no corpus bruto de treino completo,
que não está disponível; palavras e partes dos identificadores podem ser
conhecidas.

Esta avaliação é prospectiva e autoral, com conhecimento da implementação;
não é um teste cego externo. Após examinar suas falhas, passa a ser mais um
conjunto congelado de desenvolvimento. Não mede conversa livre geral, não
introduz modelos externos e não autoriza promover pesos neurais.

O par motor usa a configuração do protocolo anterior para comparação.
A avaliação adicional da API web usa os padrões normais de produção e
reconstitui somente as mensagens do usuário. Cada saída registra o commit,
os hashes das fontes, as respostas reais e todos os erros encontrados.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/memoria_prospectiva_20261009/avaliar.py --saida /tmp/memoria-prospectiva-motor.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/memoria_prospectiva_20261009/avaliar.py --modo web --saida /tmp/memoria-prospectiva-web.json
```

Os resultados iniciais serão preservados antes de alterar a memória. As
falhas comprovadas determinarão as correções. A versão do PR 117 continua
isolada durante seus checks; esta rodada não a modifica.
