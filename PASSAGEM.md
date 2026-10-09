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
| #119 | Transformer próprio lendo fatos ativos da sessão | **20/20** sessões; 16 realizações neurais e quatro recuos | Mesclado |

O PR #119 foi mesclado em `ef2fafdb` em 09/10 às 17:11 UTC, com 34 checks
aprovados e um treino opcional ignorado. As branches foram preservadas.

**Revisão atual: pedidos abertos sobre o estado que já existe.**

- Branch: `codex/conversa-livre-20261009`; base `ef2fafdb`.
- Novo desenvolvimento congelado antes da implementação: **0/12 → 11/12
  sessões**, **2/25 → 23/25 solicitações**, no motor e na API padrão.
- O consumidor reconhece operações limitadas e usa os fatos ativos para
  sugerir, justificar uma escolha, resumir e perguntar o que falta. Não
  acrescenta outro coletor, gramática de declaração ou camada de memória.
- Em cada modo: 16 realizações neurais da sessão aceitas, um recuo pela
  guarda e quatro esclarecimentos sem evidência. A resposta factual de DNA
  também usa a rede, mas não é realização da memória pessoal.
- Replay HTTP adicional: oito mensagens, três consultas corretas e três
  realizações neurais; correção preservada sem trocar as pessoas.
- O novo roteador autoral de 56.406 parâmetros foi treinado, reprovou na
  validação e permanece **desativado, aprovado=false**. Não reduza seu
  limiar nem o promova com base nos acertos de treino.
- Memória e checkpoints ativos permanecem iguais à base. Seleção e
  complementos conversacionais são estruturais; somente os fatos têm
  realização pelo Transformer ancorado. Ainda não é geração livre.
- Falha restante explícita: conversa causal sobre lápis, desenho e calma.
  Não alterar o conjunto para fazê-la desaparecer.
- Evidências e limites: `experimentos/conversa_livre_20261009/README.md`.
  A revisão ainda depende dos próprios checks antes de mesclar.

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

**Histórico da integração do realizador (#119, já mesclado).**

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
  A revisão do realizador foi mesclada após seus próprios checks aprovados.

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

1. Mesclar a revisão de pedidos abertos somente após seus próprios checks.
2. Investigar a falha causal demonstrada e a generalização do roteamento,
   preservando o conjunto e medindo cobertura e erro das aceitações.
3. Distinguir operações estruturais, leitura e realização neural, mantendo
   os recuos e os limites documentados.
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
