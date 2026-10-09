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

O PR #117 foi mesclado em `b0fac387` após 34 checks aprovados, sem falhas.
O único check ignorado foi o treino opcional, conforme a configuração.

**Próxima revisão preparada:**

- Memória em novas formulações e preferências compostas.
  Branch: `codex/memoria-transferencia-20261009`.
  Resultado: **9/20 → 20/20** nas vinte novas sessões, no motor e na API web.
  A bateria anterior conserva 20/20; 59 regressões relacionadas passaram,
  assim como 17 contratos puros em Python 3.8 sem dependências opcionais.
  Os resultados, fontes e limites estão em
  `experimentos/memoria_prospectiva_20261009/README.md`.
  Estado: a integração depende dos checks desta revisão.
  Limite: gramática explícita; o gerador neural ainda não lê o estado.

## Restrição permanente

Somente arquitetura, tokenizadores e pesos próprios do Crivo.  
Não baixar, executar ou integrar modelos externos (incluindo locais).  
Registrado em `AGENTS.md`.

Pesos experimentais de geração, raciocínio modular e linguagem profunda  
permanecem **desativados** e com aprovação falsa. Não promover ao chat.

## O que mudou de verdade nesta semana

O foco saiu de “tentar ser generativo” e entrou em  
**“fazer a conversa não esquecer quem é quem”**.

Camadas de estado que existem agora na main (após #114–#117):
- intenção e escopos
- memória de trabalho
- hipóteses confirmáveis
- pessoas, objetos e correções explícitas

Risco conhecido: várias camadas de memória estruturada podem se sobrepor.  
Evitar abrir novas frentes de memória até o gerador passar a ler o estado.

## Próximo passo técnico

1. Validar e mesclar a melhoria de transferência com os próprios checks verdes.
2. Continuar medindo conservação de pessoas, objetos, restrições e correções
   em formulações novas, com critérios congelados antes de ajustar o motor.
3. Registrar as falhas e limites da conversa real. O foco autorizado continua
   na memória de sessão; treinos de geração livre e novas frentes generativas
   permanecem adiados durante essa etapa.

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
