# Passagem de trabalho — 09/10/2026

## Estado atual da main

Os PRs recentes de memória e diálogo estão mesclados:

| PR | Foco | Resultado principal | Estado |
|----|------|---------------------|--------|
| #113 | Síntese limitada + correção de memória pessoal | Síntese 3/10 → 10/10; correção 2/6 → 6/6 | Mesclado |
| #114 | Conservar intenção, referências e escopos | 47/72 → **72/72** turnos; 1/18 → **18/18** conversas | Mesclado |
| #115 | Memória de trabalho + raciocínio verificável | 24/24 contratos de transferência | Mesclado |
| #116 | Preservar hipóteses confirmadas | 12/32 → **32/32** contratos | Mesclado |

**Aberto agora:**

- **PR #117** — Memória explícita de pessoas, objetos e correções  
  Branch: `codex/memoria-sessao-20261009`  
  Resultado: 1/20 → **20/20** sessões (motor e API web)  
  Estado: aberto, `mergeable_state: unstable` (aguardar CI verde)  
  Limite declarado: o gerador neural ainda **não lê** esse estado.

## Restrição permanente

Somente arquitetura, tokenizadores e pesos próprios do Crivo.  
Não baixar, executar ou integrar modelos externos (incluindo locais).  
Registrado em `AGENTS.md`.

Pesos experimentais de geração, raciocínio modular e linguagem profunda  
permanecem **desativados** e com aprovação falsa. Não promover ao chat.

## O que mudou de verdade nesta semana

O foco saiu de “tentar ser generativo” e entrou em  
**“fazer a conversa não esquecer quem é quem”**.

Camadas de estado que existem agora na main (após #114–#116):
- intenção e escopos
- memória de trabalho
- hipóteses confirmáveis
- (em #117) pessoas, objetos e correções explícitas

Risco conhecido: várias camadas de memória estruturada podem se sobrepor.  
Evitar abrir novas frentes de memória até o gerador passar a ler o estado.

## Próximo passo técnico (depois do #117)

1. Estabilizar e mesclar o PR #117 (CI verde + teste manual rápido).
2. Fazer o **realizador / gerador de linguagem** ler e respeitar a memória explícita de sessão.
3. Só então voltar a qualquer experimentação de geração mais livre.

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
