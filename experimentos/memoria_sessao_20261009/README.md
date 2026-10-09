# Memória explícita da sessão — 9 de outubro de 2026

Quando duas pessoas têm objetos do mesmo tipo, a conversa precisa conservar
quem possui cada objeto, seus atributos e as correções posteriores. Esta
mudança acrescenta uma memória estruturada por instância de `Crivo` e usa seus
dados para responder consultas explícitas. Não houve treino de geração,
ampliação do acervo, mudança de pesos ou integração de modelos externos.

## Medição

As vinte sessões, com quatro a seis entradas do usuário cada, foram congeladas
no commit `aa34fcc23f2f2061969a771313e2581b1bceaa34`, antes de editar o motor.
A base foi o `main` após o PR 116, `93b3f0a`. O SHA-256 do conjunto permanece
`a94354a97fba30d4a09fd2012ee197839cdf545ada3af3fcda2e30b76295b8df`.

| Configuração | Sessões adequadas |
| --- | ---: |
| Motor anterior, mesma configuração do protocolo | 1/20 |
| Motor com memória explícita | 20/20 |
| API web com as configurações normais e replay do histórico | 20/20 |
| Meta mínima proposta | 12/20 |

`baseline.json`, `candidato.json` e `web.json` contêm as respostas reais.
As duas avaliações finais apontam para o código `d7c1f8c`; seus hashes de
fontes estão registrados. O par motor anterior/candidato desliga os
classificadores opcionais de linguagem e interpretação de perguntas, para
isolar a mudança. A avaliação web adicional usa os padrões de produção.

Uma sessão só passa quando **todas as consultas marcadas** conservam os
referentes e valores e não devolvem valores de outra pessoa ou valores
retraídos. Os critérios ficam no avaliador; não entram no motor, em prompts,
na memória nem no treino. A avaliação automática usa fragmentos obrigatórios
e proibidos, com esclarecimento obrigatório em casos desconhecidos ou
ambíguos. As respostas finais das consultas também foram inspecionadas.
As confirmações intermediárias sem critérios não são pontuadas.

As famílias incluem propriedade, cor, localização, tempo pessoal versus
tempo alheio, preferências, objetivos, restrições, substituição de um atributo,
retração sem alternativa, fala atribuída, hipótese, pronome único ou ambíguo,
mudança de assunto, resumo focado e reinício.

## Identificadores novos e limites da novidade

Nomes, objetos rotulados e preferências receberam sufixos aleatórios de 48
bits criados nesta rodada, após os treinos. `auditoria_novidade.json` registra
zero colisões em 622 arquivos textuais de dados, currículos e experimentos
disponíveis localmente. O corpus bruto completo de pré-treino não está
disponível; não certificamos ausência em todos os arquivos antigos. Palavras
e partes dos identificadores podem ter aparecido antes. A novidade verificada
é a das strings completas das entidades e preferências, não a de cada token.

O conjunto é autoral e sintético. Ele ficou congelado antes da implementação,
mas, após examinar suas falhas, é uma **avaliação de desenvolvimento congelada**.
Não é um conjunto cego independente. O resultado anterior de 0/12 avaliava
geradores e outra bateria; os pesos desses geradores continuam iguais.

## Estado e uso no diálogo

`memoria_sessao.py` conserva:

- Entidades: pessoas e objetos, com identificadores por nome e proprietário.
- Afirmações: sujeito, relação, valor literal, escopo, status e fala de origem.
- Correções: vínculo entre o registro substituído/retirado e sua atualização.
- Temas: declarações de mudança de assunto, sem apagar as pessoas anteriores.

As relações implementadas são vínculo declarado, preferência, preferência
atribuída a outra pessoa, objetivo, tempo, autorização/restrição de uma ação,
proprietário, cor e localização. Consultas usam somente registros ativos.
Uma correção de cor não apaga a localização; uma negação sem novo valor deixa
a propriedade desconhecida. Pronomes exigem um único antecedente compatível.
Respostas do assistente nunca viram evidência. Hipóteses, perguntas, citações
e escopo ficcional não atualizam os fatos reais dessa memória.

O motor lê a grafia original antes da resolução e correção de texto das rotas
anteriores. As respostas são compostas dos valores registrados. Consultas
de objetos exigem um proprietário presente na sessão, evitando interceptar
perguntas factuais sobre o núcleo do átomo ou o solo de Marte. A agenda
continua com o calculador existente. O reinício nativo também limpa a memória
nova. A API reconstrói o estado pelo histórico de mensagens do usuário; a
proveniência retorna em `session_memory` e não é uma prova de fato global.

Exemplo também exercitado no chat normal: Lia possui uma mochila azul, Maria
uma verde; o usuário tem vinte minutos e Maria sessenta. A consulta à mochila
de Lia retorna azul; a consulta ao tempo do usuário retorna vinte minutos.

## Verificação e correções durante o desenvolvimento

Os 155 testes de regressão de sessão, hipóteses, argumentos, memória, crise,
ecossistema e contrato web passaram em `7a984b4`, incluindo HTTP real local.
A proteção adicional de consultas a proprietários desconhecidos, `d7c1f8c`,
passou nos nove contratos sem dependências e nas vinte sessões motor/web.
Os nove contratos também passaram em Python 3.8 com `-S`.
Os logs e `verificacao.json` registram essas versões separadamente.

A primeira implementação acertou 19/20: uma consulta de fala atribuída caiu
na gramática da preferência geral. A ordem das consultas foi corrigida.
A regressão identificou a agenda entrando na rota de permissões; restringimos
permissões a ações no infinitivo e preservamos frases de agenda. O primeiro
teste HTTP esbarrou na restrição de sockets do ambiente; a reexecução com
sockets locais passou. A varredura ampliada de todos os conceitos científicos
foi interrompida por sua duração, sem falhas anteriores; a suíte completa
continua no CI. Nenhum teste foi removido do CI.

Os hashes dos dois arquivos de pesos ativos foram conferidos e permanecem
iguais. Não houve promoção de pesos nem aprovação neural nova.

## Reprodução

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest testes_memoria_sessao -v
python -S -m unittest testes_memoria_sessao.TestesMemoriaSessao -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/memoria_sessao_20261009/avaliar.py --exigir-meta --saida /tmp/memoria-motor.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/memoria_sessao_20261009/avaliar.py --modo web --exigir-meta --saida /tmp/memoria-web.json
```

## Capacidade demonstrada

A meta de preservação foi atendida nestas frases curtas e relações explícitas.
A gramática ainda é limitada: não resolve paráfrases arbitrárias, múltiplas
pessoas homônimas, vários objetos com o mesmo nome e proprietário, ou causas
não declaradas. Preferências e objetivos usam o valor vigente de cada slot.
Não há persistência em Drive ou memória de longo prazo nova.

O consumidor atual do estado é a política estruturada. O gerador neural ainda
não lê esse estado nem foi ensinado a reproduzi-lo. O próximo trabalho deve
permanecer na validação da memória com formulações independentes; conversa
livre geral e treino neural exigem suas próprias medidas de capacidade.
