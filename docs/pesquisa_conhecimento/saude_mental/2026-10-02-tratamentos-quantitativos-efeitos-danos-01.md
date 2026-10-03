# Tratamentos quantitativos — efeitos, comparadores, NNT/NNH e danos, lote 1

**Data:** 2026-10-02. Objetivo: transformar claims de eficácia em objetos quantitativos auditáveis. Números abaixo pertencem à população, outcome, horizonte e comparador citados; não são probabilidades individuais universais.

## 1. Estrutura obrigatória
Cada tratamento deve guardar: population | diagnosis/version | intervention/dose | comparator | outcome definition | time horizon | N randomized/analyzed | effect measure | estimate | CI/CrI | absolute risk quando disponível | dropout | adverse events | funding/COI | certainty/risk of bias | source.
NNT = 1/absolute risk difference somente quando riscos e horizonte são compatíveis. NNH segue a mesma lógica para dano. Converter OR/RR/SMD em NNT sem baseline risk e assumptions explícitas é proibido.

## 2. Antidepressivos — acute MDD
Cipriani et al. 2018 network meta-analysis: 522 double-blind RCTs, 116.477 participantes, 21 antidepressivos. Todos os antidepressivos estudados tiveram odds de response maiores que placebo; ORs aproximadamente 1,37 a 2,13. Acceptability, definida como all-cause discontinuation, não acompanhou simplesmente efficacy. Head-to-head efficacy/acceptability variou entre moléculas.
Limites: acute adult MDD, trial populations, publication bias/sponsorship e transitivity de NMA; OR não é risk ratio e não deve virar NNT sem baseline. Ranking probability não é ranking universal para paciente.
Fonte: Lancet 2018;391:1357-1366. PMID 29477251. DOI 10.1016/S0140-6736(17)32802-7.

## 3. Psicoterapia para depressão
Meta-análises de psychotherapies encontram benefício médio versus control, mas magnitude depende fortemente do comparador: waitlist tende a produzir contraste maior que care-as-usual ou active control. Blinding de participante/terapeuta geralmente impossível; allegiance, publication bias, therapist clustering e outcome assessor importam.
Regra: armazenar CBT/IPT/BA/psychodynamic etc por população e comparator; não converter equivalência média entre classes em equivalência para todo indivíduo.

## 4. Antipsicóticos — manutenção em schizophrenia
Cochrane/meta-analytic evidence mostra que manutenção antipsicótica reduz relapse versus withdrawal/placebo em média, mas aumenta alguns adverse effects. Relapse prevention deve ser registrada com horizonte, definição de relapse e desenho de discontinuation; abrupt withdrawal pode inflar early relapse e não responde sozinho ao efeito de manutenção de longo prazo.
Comparar também functioning, quality of life, hospitalization, mortality, EPS, tardive dyskinesia, metabolic effects, prolactin, sedation e dropout. Symptom efficacy não resume net benefit.

## 5. Clozapina
Em treatment-resistant schizophrenia, guidelines como NICE recomendam clozapina após resposta inadequada a trials adequados de pelo menos dois antipsicóticos. A evidência de eficácia deve coexistir com ANC/neutropenia, myocarditis/cardiomyopathy, seizures, GI hypomotility, metabolic burden e interactions.
FDA removeu Clozapine REMS em 2025, mas remoção administrativa não remove risco biológico nem necessidade de monitoramento clínico conforme labeling.

## 6. Bipolar maintenance e lithium
Lithium possui evidência de relapse prevention/maintenance. Literatura sobre suicide/self-harm inclui RCTs e estudos observacionais com resultados e precisão diferentes; não armazenar 'anti-suicide' como magnitude causal única. Comparator, enrichment, adherence e discontinuation são cruciais.
Em mania/mixed presentations, antidepressant monotherapy pode ser inadequada; isso é regra de segurança/guideline, não demonstra etiologia monoaminérgica.

## 7. PTSD psychotherapy
Trauma-focused psychotherapies, incluindo exposure-based approaches e cognitive processing variants, têm suporte de guidelines e meta-analyses. Comparador e dropout são essenciais: treatment completion, symptom change e loss of diagnosis são outcomes distintos. Exposure pode elevar distress temporariamente sem significar dano persistente; adverse-event monitoring continua necessário.

## 8. OCD/ERP
ERP é intervenção central para OCD. Cadeia mecanística proposta: exposure + prevention of ritual/avoidance -> violation/updating of threat/action predictions e aprendizagem alternativa -> redução de compulsions/impairment. Habituation pode ocorrer, mas não é requisito mecanístico suficiente. Component/dismantling evidence deve separar ritual prevention do rótulo CBT amplo.

## 9. CBT-I
Evidência recente em routine care: revisão/meta-análise 2025 incluiu 32 estudos e 5.231 participantes; grandes mudanças within-group e remission agrupada em torno de 45% foram reportadas, mas risco de viés foi considerável e within-group effect não é causal effect contra controle. Sleep-hygiene education isolada é inferior a CBT-I/partial CBT-I em síntese de 42 RCTs/4.245 adultos.
Fontes: PMID 41342528; PMID 40449065.

## 10. OUD — agonist treatment
Methadone e buprenorphine têm evidência robusta para retention/redução de illicit opioid use em contextos estudados; grandes cohorts/meta-analyses associam tratamento agonista a menor mortality durante tratamento. Mortalidade pode aumentar após saída, tornando retention/continuity um outcome de segurança.
Não comparar 'medication versus abstinence' sem considerar selection, treatment exposure e immortal-time/time-varying bias em observacionais. Naloxone reverte overdose aguda, mas não substitui tratamento longitudinal de OUD.

## 11. Stimulant use disorders
Contingency management possui uma das bases mais consistentes para reduzir stimulant use em trials/reviews. Efeito é comportamento/outcome-específico e depende de reinforcement schedule, magnitude, duração e implementation. Benefício não implica que reward circuitry seja etiologia única.

## 12. Eating disorders
Adolescent anorexia: family-based/family therapy approaches têm papel importante em guidelines, mas weight restoration, eating psychopathology, medical stability, relapse e family burden são outcomes distintos. Bulimia/BED e adultos requerem evidência específica; não generalizar uma modalidade entre diagnoses/ages.

## 13. ECT
Para severe depression/catatonia e indicações selecionadas, ECT possui alta acute efficacy, mas outcome depende de técnica, electrode placement, pulse width, dose relativa ao seizure threshold e fase. Registrar response/remission, cognitive adverse effects, anesthesia risk, relapse e maintenance strategy. Acute response não é manutenção.

## 14. TMS
TMS é família de protocolos. Coil/target/frequency/pattern/intensity/session number alteram intervenção. iTBS pode reduzir session time em protocolos estudados, mas equivalência não transfere para qualquer theta-burst. Sham quality e blinding integrity importam.

## 15. Psicoterapia: danos e deterioração
Trials devem medir deterioration, serious adverse events, symptom exacerbation, dependency/boundary harms, induced memories/suggestion, dropout e functional deterioration. 'Não relatado' não equivale a 'zero'. Waitlist não controla attention/expectancy/relationship.

## 16. Effect heterogeneity
Average treatment effect ATE = E[Y(1)-Y(0)]. Individual treatment effect não é observável simultaneamente. Subgroup interaction exige teste formal; responder em um subgroup e não em outro não prova interaction. Prediction models precisam external validation/calibration e decision-curve/utility quando usados clinicamente.

## 17. Network meta-analysis
Exige transitivity, consistency e comparabilidade de effect modifiers. SUCRA/P-score/rank probability não mede magnitude clínica, certeza ou dano total. Nunca transformar ranking probabilístico em 'melhor tratamento' sem outcome/population/context.

## 18. Ledger
| ID | Claim | Evidência | Limite |
|---|---|---|---|
| TQ-001 | 21 antidepressivos superaram placebo em response na NMA 2018 | S4 | acute adult MDD; OR |
| TQ-002 | acceptability é outcome distinto de efficacy | S4 | all-cause dropout é proxy imperfeito |
| TQ-003 | maintenance antipsychotic reduz relapse em média | S4 | withdrawal design/horizon importam |
| TQ-004 | clozapina tem papel em treatment-resistant schizophrenia | S4 guideline | safety/monitoring central |
| TQ-005 | lithium maintenance tem eficácia; suicide magnitude não é única | S4 | design heterogeneity |
| TQ-006 | CBT-I routine-care melhora insomnia; within-group não prova causalidade | S4 | risk of bias |
| TQ-007 | sleep hygiene isolada não equivale a CBT-I | S4 | intervention heterogeneity |
| TQ-008 | agonist OUD treatment associa-se a menor mortality durante exposure | S4 | observational causal caveats |
| TQ-009 | contingency management é eficaz para stimulant outcomes | S4 | implementation/dose matter |
| TQ-010 | ECT acute efficacy não implica maintenance | S4 | technique/horizon |
| TQ-011 | TMS protocol é multidimensional | S4 | authorization/indication specific |
| TQ-012 | NNT/NNH depende de absolute baseline risk e horizon | S4 methods | não derivar de OR cru |

## 19. Próximo lote quantitativo
Extrair absolute response/remission/relapse e adverse-event rates com CI para MDD, schizophrenia, bipolar, OCD, PTSD, insomnia, SUD e eating disorders; adicionar NNT/NNH somente quando diretamente reportado ou derivável de riscos compatíveis. Priorizar primary/meta-analysis + guideline/regulatory triangulation.

**Integração:** nenhuma. **Treinamento:** nenhum.
