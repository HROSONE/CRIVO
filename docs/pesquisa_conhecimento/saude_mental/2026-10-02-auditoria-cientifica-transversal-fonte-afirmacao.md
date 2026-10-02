# Auditoria científica transversal — fase 1: rastreabilidade e risco de afirmação

**Data:** 2026-10-02
**Status:** REPROVADA PARA CONCLUSÃO — cobertura ampla, rastreabilidade ainda insuficiente.

## Objetivo
A coleção já possui grande cobertura conceitual. O gargalo agora é provar, para cada afirmação material, **qual evidência a sustenta, quão direta ela é, quão atual precisa ser e qual inferência foi feita**.

# 1. Classes de afirmação

## A — definição/estrutura relativamente estável
Ex.: definição matemática de sensibilidade, receptor ionotrópico, princípio de reinforcement.
Exige fonte canônica, mas baixa volatilidade.

## B — associação empírica
Ex.: grupo X apresenta diferença média Y.
Exige população, desenho, efeito/incerteza, replicação e alternativas.

## C — causal/mecanística
Ex.: intervenção em alvo X produz mudança clínica via mecanismo M.
Exige perturbação, temporalidade, mediação/target engagement ou triangulação forte. Alto risco de overclaim.

## D — eficácia comparativa
Exige população, intervenção, comparador, outcome, follow-up, effect size e risco de viés.

## E — segurança
Eventos adversos, contraindicações, withdrawal e monitorização. Alta prioridade e atualização.

## F — regulatória/guideline
FDA/NICE/APA/WHO. Deve carregar organização, documento, data/versão, população/jurisdição.

## G — epidemiologia
Prevalência/incidência/burden. Precisa ano, população, método e geografia.

## H — controvérsia
Precisa representar evidência pró/contra assimetricamente conforme força, sem false balance.

# 2. Níveis de suporte fonte→afirmação

**S0** nenhuma fonte identificável ligada.
**S1** fonte estrutural listada no fim do dossiê, sem mapeamento da afirmação.
**S2** fonte específica plausível, mas sem localização/extração do resultado.
**S3** fonte específica com claim, população/design e resultado correspondente.
**S4** triangulação: primário + síntese/guideline quando apropriado, incluindo limitações/replicação.

Para declarar coleção auditada, afirmações C–G materiais devem chegar pelo menos a S3; afirmações centrais/controversas idealmente S4.

# 3. Diagnóstico atual

Grande parte dos dossiês está em **S1**: referências estruturais existem, porém ainda não há associação sentença→fonte. Portanto quantidade e qualidade conceitual **não autorizam** declarar nível doutoral concluído.

# 4. Prioridade crítica

### Farmacologia
Alto risco: meia-vida, CYP, metabólitos, receptor, QT, retirada, REMS, monitoring.
Ação: labels FDA/EMA quando pertinente + CPIC + meta-análises.

### Psicoterapia
Alto risco: “funciona”, superioridade, mecanismos/mediadores e harms.
Ação: guideline + systematic review/meta-analysis + mecanismo trial.

### Neurociência
Alto risco: função regional, causalidade de circuitos, neurotransmissores, biomarkers.
Ação: revisão + perturbação/lesão quando houver + replicação.

### Diagnóstico
Alto risco: critérios, diferenciais e mudança de classificação.
Ação: ICD-11/WHO e guideline atual.

### Epidemiologia
Alto risco: números globais e tendências.
Ação: WHO/GBD/original dataset com ano.

# 5. Afirmações que devem ser protegidas contra overclaim
- “dopamina causa X”;
- “serotonina baixa causa depressão”;
- “amígdala é centro do medo”;
- “PFC é cérebro racional”;
- “cortical thinning prova pruning”;
- “brain mature at 25”;
- “biomarker positivo = doença clínica”;
- “gene causa transtorno complexo”;
- “resposta a medicamento confirma diagnóstico”;
- “mediação estatística prova mecanismo”;
- “fMRI activation identifica processo mental”;
- “therapy efficacy prova teoria da terapia”;
- “não significativo = tratamentos equivalentes”;
- “withdrawal = addiction”;
- “trauma = BPD”;
- “BMI = gravidade de eating disorder”.

# 6. Esquema de proveniência
Cada unidade final deverá permitir:
`claim_id | claim | type | source_id | source_type | year | population | design | N | effect | uncertainty | directness | causal_status | replication | limitations | volatility | checked_date`.

# 7. Volatilidade

**V0:** matemática/anatomia fundamental — revisar raramente.
**V1:** modelos teóricos estáveis — revisar em ciclos longos.
**V2:** sínteses clínicas — revisão periódica.
**V3:** guidelines/fármacos/regulação — revisão frequente.
**V4:** dados emergentes/approvals/safety alerts — monitorização ativa.

# 8. Auditoria de atualidade
Uma fonte antiga não é inválida automaticamente. Perguntar:
- é descoberta histórica ainda válida?
- há revisão posterior?
- guideline foi substituída?
- status regulatório mudou?
- diagnóstico mudou de DSM/ICD?
- tecnologia de biomarcador evoluiu?

# 9. Auditoria de replicabilidade
Para claim empírico importante:
- preregistration?
- sample size/power?
- independent replication?
- multisite?
- meta-analysis?
- heterogeneity?
- publication bias?
- external validity?

# 10. Auditoria causal
Classificar:
0 descrição;
1 associação;
2 temporalidade;
3 adjustment/quasi-experimental;
4 randomized perturbation;
5 mechanistic mediation/triangulation.

Escala é heurística documental, não “nota universal de causalidade”.

# 11. Auditoria de tratamento
Separar:
`efficacy | effectiveness | acceptability | dropout | adverse events | functioning | QoL | relapse | mortality`.

Resposta sintomática não representa automaticamente todos os outcomes.

# 12. Auditoria de diagnóstico
Separar:
`criterion validity | reliability | differential | course | impairment | biomarkers | rule-outs`.
Ausência de biomarcador não invalida síndrome clínica; presença de associação biológica não transforma diagnóstico em teste laboratorial.

# 13. Auditoria de população
Marcar idade, sexo/gênero quando relevante, ancestralidade, país, setting, gravidade e comorbidades. Não extrapolar RCT altamente selecionado para toda população.

# 14. Auditoria de linguagem
Palavras de alto risco:
“causa”, “prova”, “sempre”, “nunca”, “cura”, “melhor”, “biomarcador”, “específico”, “prediz”.
Toda ocorrência deve ser revisada por força de evidência.

# 15. Auditoria matemática
Toda fórmula precisa definir símbolos, pressupostos e domínio. Fórmula pedagógica não deve ser apresentada como modelo completo do cérebro.

# 16. Resultado desta fase
**Cobertura temática:** ampla.
**Profundidade conceitual:** alta em múltiplos eixos.
**Rastreabilidade sentença→fonte:** insuficiente.
**Quantificação de efeito:** insuficiente.
**Auditoria de atualidade:** parcial.
**Replicabilidade explícita:** parcial.
**Conclusão doutoral:** NÃO.

# 17. Próxima fase obrigatória
Criar ledger fonte-afirmação começando por claims de maior risco:
1. psicofarmacologia;
2. tratamentos;
3. biomarcadores/neurociência causal;
4. epidemiologia;
5. classificação/diagnóstico.

Não adicionar volume indiscriminadamente enquanto esses claims não ganharem proveniência.

**Integração:** nenhuma. **Treinamento:** nenhum.
