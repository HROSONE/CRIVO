# Ledger de proveniência — psicofarmacologia, lote 1

**Data da checagem:** 2026-10-02
**Objetivo:** elevar claims farmacológicos de S1 para S3/S4.
**Regra:** números e status regulatório são versionados; fonte regulatória não prova etiologia.

| ID | Afirmação | Tipo | Fonte | Suporte | Volatilidade | Limites |
|---|---|---|---|---|---|---|
| PF-001 | CPIC 2023 fornece recomendações acionáveis para pares selecionados CYP2D6/CYP2C19/CYP2B6–antidepressivos | guideline/PGx | CPIC 2023 serotonin reuptake inhibitors | S4 | V2 | guideline interpreta genótipo já disponível; não decide universalmente quem testar |
| PF-002 | Evidência de SLC6A4/HTR2A não sustenta recomendações clínicas de prescrição antidepressiva comparáveis às CYP selecionadas | guideline/PGx | CPIC 2023 | S4 | V2 | não significa ausência de associação biológica |
| PF-003 | Clozapine REMS foi removido pela FDA com efeito em 13 Jun 2025 | regulatório | FDA Drug Safety Communication 27 Aug 2025 | S4 | V4 | status EUA; não generalizar para outros países |
| PF-004 | Remoção do REMS não remove risco de neutropenia grave nem recomendação de ANC monitoring | segurança/regulatório | FDA 2025 | S4 | V4 | frequência segue prescribing information vigente |
| PF-005 | FDA reavaliou REMS usando literatura, FAERS e estudos com Sentinel/VA/BWH | regulatório/evidência | FDA 2025 | S4 | V3 | decisão regulatória integra múltiplos dados; não é RCT |
| PF-006 | Aripiprazole oral é metabolizado principalmente por CYP2D6/CYP3A4 e dehydro-aripiprazole é metabólito ativo | PK | FDA label | S3 | V2 | formulação importa |
| PF-007 | Label oral reporta t1/2 média ~75 h para aripiprazole e ~94 h para dehydro-aripiprazole; CYP2D6 PM ~146 h para aripiprazole | PK quantitativa | FDA label | S3 | V2 | médias populacionais; label recuperado pode não ser versão mais nova |
| PF-008 | LAI aripiprazole possui PK muito diferente da formulação oral | PK/formulação | FDA label Abilify Maintena | S3 | V2 | não transferir half-life entre formulações |
| PF-009 | Smoking está associado a clearance de olanzapine ~40% maior em label FDA | PK/interação | FDA olanzapine label | S3 | V2 | smoking status é proxy de exposição à fumaça; efeito individual varia |
| PF-010 | Fluvoxamine reduz clearance/aumenta exposição de olanzapine por inibição CYP1A2 | DDI/PK | FDA olanzapine-containing label | S3 | V2 | magnitude varia por população/formulação |
| PF-011 | Target/receptor affinity de aripiprazole não equivale a mecanismo etiológico de schizophrenia/bipolar disorder | inferência | FDA label declara mecanismo clínico desconhecido apesar de farmacologia receptor | S3 | V1 | mecanismo terapêutico pode envolver receptores sem explicar etiologia |

## Extrações verificadas

### PF-001/PF-002 — CPIC 2023
O guideline revisa CYP2D6, CYP2C19, CYP2B6, SLC6A4 e HTR2A para serotonin reuptake inhibitor antidepressants. A função do documento é converter resultados genéticos existentes em recomendações de dose/seleção quando evidência permite; escolha de quem testar/custo-efetividade fica fora do escopo.

**Inferência permitida:** algumas relações gene–fármaco possuem utilidade prescritiva suficiente para recomendação.
**Inferência proibida:** “teste genético escolhe o antidepressivo perfeito”.

### PF-003–005 — clozapina
FDA removeu formalmente o Clozapine REMS em 2025. A agência manteve severe neutropenia no labeling/boxed warning e recomenda ANC monitoring conforme prescribing information.

**Inferência permitida:** obrigação administrativa REMS e necessidade clínica de monitorização são coisas diferentes.
**Inferência proibida:** “REMS acabou, então ANC não importa”.

### PF-006–008 — aripiprazol
Labels FDA sustentam metabolismo CYP2D6/CYP3A4 e metabólito ativo dehydro-aripiprazole. Formulações depot possuem absorção prolongada e meia-vida aparente diferente da oral.

**Inferência permitida:** genotype/inhibitors/formulation podem alterar exposição.
**Inferência proibida:** meia-vida de uma formulação vale para todas.

### PF-009/PF-010 — olanzapina
Label FDA reporta clearance maior em smokers e aumento de exposição com fluvoxamine.

**Inferência permitida:** exposição pode mudar quando smoking status ou CYP1A2 inhibition muda.
**Inferência proibida:** usar um percentual médio como ajuste automático individual sem contexto clínico.

## Correções de linguagem impostas ao acervo
1. Todo valor PK deve identificar **molécula + formulação + população/fonte**.
2. “Metabolizado por CYP” não significa que genotype necessariamente requer dose adjustment.
3. Receptor affinity/occupancy não prova etiologia.
4. Status FDA deve conter data e jurisdição.
5. Safety monitoring não deve ser inferido apenas da existência/remoção de REMS.
6. “Smoking interaction” deve distinguir fumaça de tabaco de nicotina quando mecanismo é CYP1A2 induction.

## Pendências do lote 2
- fluoxetine/norfluoxetine;
- paroxetine/CYP2D6/discontinuation;
- sertraline/CYP2C19;
- citalopram/escitalopram/QT;
- venlafaxine/desvenlafaxine;
- bupropion/hydroxybupropion/CYP2B6;
- clozapine PK além de REMS;
- risperidone/paliperidone;
- quetiapine/CYP3A4;
- lithium/renal/monitoring;
- valproate reproductive safety.

**Integração:** nenhuma. **Treinamento:** nenhum.
