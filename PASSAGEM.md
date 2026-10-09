# Passagem de trabalho — 09/10/2026

## Estado atual da main

Os PRs recentes de memória e diálogo estão mesclados:

| PR | Foco | Resultado principal | Estado |
|----|------|---------------------|--------|
| #113 | Síntese limitada + correção de memória pessoal | Síntese 3/10 → 10/10; correção 2/6 → 6/6 | Mesclado |
| #114 | Conservar intenção, referências e escopos | 47/72 → **72/72** turnos; 1/18 → **18/18** conversas | Mesclado |
| #115 | Memória de trabalho + raciocínio verificável | 24/24 contratos de transferência | Mesclado |
| #116 | Preservar hipóteses confirmadas | 12/32 → **32/32** contratos | Mesclado |
| #117 | Memória explícita de pessoas, objetos e correções | 1/20 → **20/20** sessões no motor e na API web | Mesclado |
| #118 | Novas perguntas e correções compostas | 9/20 → **20/20** novas sessões no motor e na API web | Mesclado |

O PR #117 foi mesclado em `b0fac387` após 34 checks aprovados, sem falhas.
O único check ignorado foi o treino opcional, conforme a configuração.

O PR #118 foi mesclado em `995df436` em 09/10 às 15:46 UTC, depois de
**19 checks aprovados**, sem falhas. As branches e os commits foram preservados.

Após o merge, uma conversa manual de **oito mensagens** pelo endpoint HTTP
do main manteve Saelina, Ondravel e suas preferências. As **três consultas
passaram**, incluindo a correção da preferência de Saelina sem modificar a
de Ondravel. Todas as chamadas retornaram HTTP 200. Os nomes e expressões
completas tinham zero ocorrências em 1.023 arquivos textuais locais auditados;
isso não certifica o corpus bruto indisponível. O trace dessa versão confirma
que as respostas ainda vieram da política estruturada, sem realização neural.

**Próxima revisão: o realizador lendo esse estado.**

- Branch de integração: `codex/realizador-sessao-20261009`.
- O Transformer próprio já existente recebe cada fato ativo selecionado,
  com sujeito, relação, valor e fonte do usuário. A memória permanece igual.
- Desenvolvimento congelado: **20/20** sessões no motor e na API web;
  em cada modo, **16/20** consultas com resposta neural aceita e **4/20**
  conservadas pela resposta estrutural após rejeição da guarda.
- A bateria anterior mantém 20/20. Passaram dez contratos do consumidor,
  25 contratos puros em Python 3.8 e as 92 regressões relacionadas; o caso
  HTTP bloqueado pelo sandbox passou na reexecução com socket permitido.
- Nenhum peso alterado ou promovido. Seleção estruturada, prefixo da fonte
  e guarda literal continuam limitando a geração; não é conversa livre.
- No replay HTTP das três consultas manuais, o candidato usou a rede em
  **3/3**, preservando texto e fontes do baseline, inclusive a correção.
- Evidências: `experimentos/realizacao_memoria_20261009/README.md`.
  A revisão do realizador depende dos próprios checks antes de mesclar.

## Restrição permanente

Somente arquitetura, tokenizadores e pesos próprios do Crivo.  
Não baixar, executar ou integrar modelos externos (incluindo locais).  
Registrado em `AGENTS.md`.

Pesos experimentais de geração, raciocínio modular e linguagem profunda  
permanecem **desativados** e com aprovação falsa. Não promover ao chat.

## O que mudou de verdade nesta semana

O foco saiu de “tentar ser generativo” e entrou em  
**“fazer a conversa não esquecer quem é quem”**.

Camadas de estado que existem agora na main (após #114–#118):
- intenção e escopos
- memória de trabalho
- hipóteses confirmáveis
- pessoas, objetos e correções explícitas

Risco conhecido: várias camadas de memória estruturada podem se sobrepor.  
Evitar abrir novas frentes de memória até o gerador passar a ler o estado.

## Próximo passo técnico

1. Integrar o consumidor neural já validado, após os checks da própria revisão.
2. Medir uso real da memória pelo gerador, distinguindo leitura do prompt,
   geração aceita e recuo. Conservação estrutural não é acerto neural.
3. Investigar as rejeições do realizador e registrar os limites da conversa.
   Não abrir outra frente de memória estruturada. Treinos de geração livre,
   ampliação do acervo, voz e microcircuitos continuam adiados nesta etapa.

## Regras de administração a partir de agora

- Máximo 1 PR grande de capacidade por vez.
- Todo PR de memória/conversa deve ter:
  - conjunto congelado **antes** da mudança
  - número claro (X/Y)
  - declaração explícita do que ainda **não** resolve
- Atualizar este `PASSAGEM.md` no mesmo PR ou imediatamente depois do merge.
- Manter o `ROADMAP.md` com no máximo 3 prioridades ativas.

## Histórico antigo

Notas anteriores a 08/10/2026 (PRs #103–#111, geração ancorada,  
experimentos de raciocínio, etc.) foram movidas para o histórico do  
repositório. Não use este arquivo como fonte daquelas etapas.
