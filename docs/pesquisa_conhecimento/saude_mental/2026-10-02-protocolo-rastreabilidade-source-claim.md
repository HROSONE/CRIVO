# Protocolo de rastreabilidade e auditoria source→claim

**Data:** 2026-10-02. Este protocolo governa a conversão do corpus de saúde mental em base científica auditável.

## 1. Unidade mínima
A unidade não é arquivo nem parágrafo: é CLAIM. Cada claim factual relevante recebe ID estável. Claims compostos devem ser quebrados quando partes exigem fontes/níveis de evidência diferentes.

## 2. Tipos
DEF definição operacional; OBS observação; ASSOC associação; PRED predição; CAUS causal; MECH mecanismo; DX diagnóstico/accuracy; TX tratamento; HARM dano; EPI epidemiologia; REG regulatório; GL guideline; MODEL modelo; CONT controvérsia.

## 3. Campos
claim_id; text; type; domain; population; exposure/intervention; comparator; outcome; horizon; source_id; source_type; year; N/studies; effect; uncertainty; risk_of_bias; causal_grade; external_validity; version/jurisdiction; contradiction_id; status; checked_date.

## 4. Status
VERIFIED = fonte diretamente sustenta claim. PARTIAL = sustenta parte/magnitude/contexto incompleto. CONCEPTUAL = regra/modelo sem claim empírico específico. CONTESTED = evidência séria conflitante. SUPERSEDED = versão/regulação substituída. UNVERIFIED = sem fonte adequada localizada. RETRACTED/CORRECTED = preservar histórico, não usar como suporte sem nota.

## 5. Hierarquia não mecânica
Guideline não substitui systematic review para effect size; RCT não substitui cohort para evento raro/long-term harm; cohort não substitui RCT automaticamente para efficacy; regulator é primário para authorization/warning; diagnostic manual é primário para classificação; primary mechanistic experiment pode ser necessário onde review dilui protocolo. Escolher fonte pela pergunta.

## 6. Claim strength <= evidence strength
Texto final nunca pode ser mais forte que desenho. 'Associated with' não vira 'causes'. 'May mediate' não vira 'mechanism is'. 'Statistically significant' não vira 'clinically important'. 'No significant difference' não vira equivalence. 'Noninferior' exige margem/design. 'No evidence of harm' não vira safe.

## 7. Quantitativos
Número sem denominador/contexto é inválido. Guardar measure, estimate, CI/CrI, units, time horizon e population. Para prevalence: case definition + window. Para diagnostic accuracy: reference standard + threshold + base rate. Para treatment: comparator + outcome. Para biomarker: sample handling + validation set + discrimination/calibration quando aplicável.

## 8. Replicabilidade
Registrar preregistration/protocol quando disponível; multiplicity; sample size; missing data; analytic flexibility; external replication; prospective validation. Discovery e validation no mesmo dataset não contam como external validation.

## 9. Contradições
Não apagar estudo conflitante. Criar contradiction set: claims A/B, diferenças de population/design/measure/version, evidence quality, possível explicação, unresolved status. Meta-analysis não encerra controvérsia automaticamente se inputs são biased/heterogeneous.

## 10. Atualidade
Classificação, guideline, label, authorization e warning recebem expiry/recheck priority. Molecular mechanism básico envelhece de modo diferente de regra regulatória. Annual/versioned sources devem carregar release.

## 11. Citation drift
Auditar se review realmente cita primary source para claim; se primary mede o construct alegado; se números foram copiados corretamente; se secondary source fortaleceu linguagem indevidamente. Evitar cadeia review->review->narrative sem retorno ao estudo quando claim é crítico.

## 12. COI e sponsorship
Funding/author COI são modifiers de interpretação, não prova automática de invalidade. Registrar sponsorship em drug/device trials e allegiance em psychotherapy quando disponível.

## 13. Generalização
Perguntar quem foi excluído: idosos, pregnancy, suicidality, substance use, multimorbidity, intellectual disability, non-English speakers, institutionalized, low-income settings. Efficacy em amostra seletiva não é effectiveness universal.

## 14. Red flags
Claim absoluto; linguagem causal em cross-sectional; biomarker sem external validation; subgroup sem interaction; post-hoc outcome; surrogate tratado como patient benefit; percent sem denominator; guideline sem versão; medication claim sem dose; diagnosis claim sem system/version; harm claim sem ascertainment; prevalence somada entre categorias sobrepostas.

## 15. Quality gate
Antes de considerar domínio 'forte': >=90% dos claims quantitativos críticos VERIFIED/PARTIAL com contexto; 100% dos claims regulatórios/guidelines versionados; claims causais com desenho explícito; contradictions catalogadas; nenhuma retraction conhecida usada silenciosamente; gaps declarados.

## 16. Aplicação ao CRIVO
Fase atual é documentação/pesquisa. Este protocolo NÃO é treinamento nem integração. Ele define como futura ingestão deve preservar provenance e uncertainty para impedir que o sistema transforme associação em fato causal.

**Integração:** nenhuma. **Treinamento:** nenhum.
