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

## Resultados e correções

A primeira medição, sem editar a memória para este conjunto, deu 9/20 no
motor e 9/20 na API web. `baseline_motor.json` e `baseline_web.json` preservam
os erros e as respostas reais da versão congelada `07a3b0c`, cujo código da
memória corresponde ao PR 117. São novas formulações além do conjunto que
já atingira 20/20; não tratamos aquele resultado como garantia de transferência.

A leitura dos erros identificou consultas indiretas e invertidas sem rota,
objetivo/restrição perguntados como ação, tempo com “só”, preferência como
escolha explícita, o prefixo “Correção:”, duas declarações na mesma mensagem
e propriedade declarada pelo dono. A correção acrescenta essas construções
à gramática existente; não copia nomes, identificadores ou respostas do teste
para o motor. Consultas continuam ligadas aos sujeitos e às fontes da sessão.

Preferências compostas exigem todas as referências resolvidas antes de
atualizar os fatos. A continuação “agora prefere” reutiliza o sujeito explícito
da cláusula anterior, dentro da mesma mensagem. Uma cláusula sem interpretação
segura deixa a declaração inteira fora dessa coleta. Hipóteses e citações
continuam bloqueadas; perguntas não viram fonte. Cada atualização conserva
a fala original completa, e uma retração explícita mantém seu status mesmo
após a entrada do valor seguinte. Os testes detectaram e corrigiram problemas
na ordem dessa continuação e na preservação do status da retração.

O candidato `63b5ad0` atingiu 20/20 no motor e 20/20 na API web. A bateria anterior também foi
repetida nessa versão e conservou 20/20. Os 17 contratos puros (11 anteriores
e 6 novos) passaram em Python 3.8 com `-S`. A avaliação web está em `candidato_web.json`. Os 59 testes relacionados
de compreensão de intenção, memória, prioridade e raciocínio ativo também
passaram nessa versão; seus logs estão em `logs/`. `verificacao.json` registra
versões, hashes dos resultados e pesos próprios preservados.

O CI de diálogo inclui a meta de 12/20 deste conjunto no motor e na API web,
além dos contratos e das avaliações anteriores. Nenhum teste anterior foi
removido. O check atual do PR 117 durou 159 segundos; a nova avaliação é
acrescentada ao limite existente de quinze minutos.

O conjunto permanece inalterado. Depois de examinar suas falhas ele passa
a ser desenvolvimento congelado, e o 20/20 corrigido não é uma pontuação cega.
Ainda há limites de gramática, homônimos, referências indiretas e relações
não declaradas. O consumidor é a política estruturada; o gerador neural
continua sem ler este estado e seus pesos permanecem iguais.

O PR 117 foi mesclado em `b0fac387` após 34 checks aprovados, sem falhas;
o treino opcional foi ignorado conforme a configuração. Esta melhoria foi
transportada para `codex/memoria-transferencia-20261009`, a partir desse main.
As fontes avaliadas continuam idênticas, verificadas por seus hashes. A branch
experimental e os commits citados nas medições permanecem preservados.
A próxima revisão contém somente a melhoria de transferência e suas evidências;
sua aprovação remota ainda depende dos próprios checks.
