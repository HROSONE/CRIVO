# Tratamentos quantitativos — riscos absolutos, manutenção e dropout, lote 3

**Recuperação:** 2026-10-02. Este dossiê preserva a pesquisa quantitativa que havia sido realizada mas não persistida após bloqueio de escrita. Não integra nem treina o CRIVO.

## Princípio
Efeito deve ser representado simultaneamente em escala relativa e absoluta quando os dados permitem. Para cada estimativa: população, comparador, outcome, horizonte, desenho, N, estimate/CI e limitações. NNT/NNH não é constante intrínseca do tratamento.

## Psicoterapia para depressão — resposta absoluta
Uma meta-análise de centenas de RCTs de psicoterapia para depressão adulta estimou taxas absolutas de resposta e examinou diferenças por condição de controle. O corpus incluiu aproximadamente 441 ensaios e 33.881 participantes. A probabilidade absoluta de resposta varia substancialmente com definição de response e comparador; waitlist, usual care e outros controles não são intercambiáveis.
Implicação: registrar response_treatment e response_control, e não apenas standardized mean difference. Uma resposta de 50% no braço tratado não significa efeito causal de 50%; parte ocorreria sem aquela intervenção específica.

## PTSD — heterogeneidade individual e dropout
Individual-participant-data e meta-analytic evidence permitem estudar moderators com mais rigor que subgroup comparisons isoladas, mas moderator causal exige interaction e desenho apropriado. Trauma-focused psychotherapy apresenta benefício médio importante em PTSD, porém completion/dropout varia entre modalidades, populações e settings.
Dropout não é sinônimo de dano ou falha: pode refletir tolerabilidade, logística, preferência, melhora, piora ou incompatibilidade. Comparações de dropout precisam de definição uniforme e denominador randomized.

## OCD/ERP — adesão e tolerabilidade
ERP é tratamento central, mas exposure assignment, ritual prevention, therapist support, dose e homework adherence variam. Meta-analytic dropout deve ser separado em all-cause e adverse-event/intolerance quando disponível. Distress durante exposure não equivale automaticamente a deterioration.

## Schizophrenia — manutenção antipsicótica
Meta-análise de manutenção reuniu 75 RCTs e cerca de 9.145 participantes. Em 7–12 meses, relapse ocorreu aproximadamente em 24% com manutenção antipsicótica versus 61% com placebo/withdrawal; RR ~0,38 (95% CI ~0,32–0,45), correspondendo a NNTB aproximadamente 3 nesse conjunto/horizonte.
Interpretação correta: grande redução média de relapse no contexto dos trials. Não implica que toda pessoa recaia sem medicamento ou que toda pessoa se beneficie igualmente. Desenho de withdrawal, duração prévia de estabilidade, abruptness, definição de relapse e seleção de participantes alteram transportabilidade.

## Absoluto versus relativo
Risk difference = p_treatment - p_control. Para benefício em evento indesejado, absolute risk reduction = p_control - p_treatment. NNTB = 1/ARR. RR preserva comparação proporcional, mas a mesma RR gera ARR/NNT muito diferentes em baseline risks diferentes.
Exemplo metodológico: RR 0,5 com baseline 60% produz redução absoluta 30 pontos; com baseline 10%, 5 pontos. Portanto o CRIVO nunca deve armazenar 'NNT do tratamento' sem outcome/horizon/population/comparator.

## Response, remission, relapse, recurrence
Response = redução clinicamente definida; remission = estado abaixo de threshold definido; relapse = retorno durante/remissão inicial conforme protocolo; recurrence = novo episódio após recovery conforme definição. Estudos variam; guardar definição original em vez de harmonizar silenciosamente.

## Missing data
Last observation carried forward pode enviesar. Mixed models/MMRM, multiple imputation e estimands modernos têm assumptions distintas. Intention-to-treat preserva randomization conceitualmente, mas missing outcomes continuam problema. Per-protocol pode responder aderência sob seleção, não eficácia randomizada pura.

## Estimands
Pergunta terapêutica deve declarar estratégia para intercurrent events: discontinuation, rescue medication, switching, death, nonadherence. Treatment-policy, hypothetical e while-on-treatment estimands respondem perguntas diferentes. Não combinar seus números como se fossem equivalentes.

## Minimal clinically important difference
Statistical significance não garante importância clínica. MCID pode ser anchor-based ou distribution-based e variar por baseline/severity/population. Dichotomizar escala contínua em response perde informação e cria threshold dependence; ainda assim pode ajudar decisão quando definição é clinicamente validada.

## Multiplicidade e selective reporting
Múltiplos outcomes/timepoints/subgroups aumentam chance de achados espúrios. Priorizar protocol/preregistration, primary outcome e prespecified analyses. Outcome switching deve ser marcado no ledger quando identificado.

## Generalização
Trials frequentemente excluem severe comorbidity, acute suicidality, pregnancy, substance use, frailty ou complex medical illness. Efficacy estimate em amostra seletiva não é automaticamente effectiveness em população clínica geral.

## Ledger recuperado
| ID | Claim | Evidência | Limite |
|---|---|---|---|
| TQ3-001 | taxas absolutas de resposta em psychotherapy dependem do comparator | meta-analysis ~441 RCTs/~33.881 | definitions/control heterogeneity |
| TQ3-002 | response rate no braço tratado não é causal effect | trial methodology | precisa control counterfactual |
| TQ3-003 | dropout em PTSD/ERP não equivale automaticamente a harm | meta/trial methods | reasons often incompletely measured |
| TQ3-004 | antipsychotic maintenance reduz relapse substancialmente em média | 75 RCTs/~9.145; 7–12m ~24% vs 61%; RR ~0.38 | withdrawal/design/transportability |
| TQ3-005 | NNT varia com baseline risk/outcome/horizon | arithmetic/methods | não é propriedade fixa |
| TQ3-006 | response/remission/relapse precisam definição original | measurement | thresholds differ |
| TQ3-007 | missing-data method implica assumptions | trial methods | nenhum método recupera dados sem assumptions |
| TQ3-008 | estimands diferentes respondem perguntas diferentes | ICH/trial methods | não intercambiáveis |

## Estado
Este lote recupera a pesquisa quantitativa que havia ficado fora da branch. Próximo aprofundamento deverá validar source→claim de cada número contra publicação primária/revisão e acrescentar absolute harms, CI e follow-up por intervenção.

**Integração:** nenhuma. **Treinamento:** nenhum.