# Ledger de proveniência — psicofarmacologia, lote 2

**Data da checagem:** 2026-10-02
**Escopo:** antidepressivos e estabilizadores.
**Princípio:** dado PK/PD não é diagnóstico, e alvo farmacológico não é etiologia.

| ID | Claim auditado | Classe | Suporte | Volatilidade | Fonte primária/canônica |
|---|---|---|---|---|---|
| PF-012 | Fluoxetina e norfluoxetina têm eliminação lenta e persistem por semanas após uso crônico | PK | S3 | V2 | FDA fluoxetine label |
| PF-013 | Fluoxetina inibe CYP2D6 e pode tornar metabolizador normal funcionalmente semelhante a poor metabolizer para substratos | DDI/PK | S3 | V2 | FDA label |
| PF-014 | Longa persistência da fluoxetina reduz velocidade de queda de exposição, mas não significa ausência universal de withdrawal | PK/withdrawal | S3 | V2 | FDA + guideline withdrawal |
| PF-015 | Paroxetina é metabolizada por CYP2D6 e também inibe CYP2D6 | PK/DDI | S3 | V2 | FDA paroxetine label |
| PF-016 | Paroxetina apresenta cinética não linear em parte por saturação/inibição do CYP2D6 | PK | S3 | V2 | FDA label |
| PF-017 | Paroxetina requer atenção especial à descontinuação; retirada não deve ser chamada automaticamente de addiction | segurança | S4 | V2 | FDA + NICE |
| PF-018 | Sertralina possui metabolismo múltiplo; CPIC usa CYP2C19 e CYP2B6 para recomendações selecionadas | PGx | S4 | V2 | CPIC 2023 + label |
| PF-019 | Citalopram tem warning de prolongamento QT dose-dependente e restrições de dose em contextos de maior exposição | segurança/regulatório | S4 | V3 | FDA safety communication/label |
| PF-020 | Escitalopram é o S-enantiômero do citalopram; não assumir equivalência miligrama-a-miligrama | farmacologia | S3 | V2 | FDA labels |
| PF-021 | Venlafaxina é convertida a O-desmethylvenlafaxine principalmente por CYP2D6 | PK | S3 | V2 | FDA venlafaxine label |
| PF-022 | Desvenlafaxina é o principal metabólito ativo da venlafaxina e tem perfil de metabolismo distinto | PK | S3 | V2 | FDA desvenlafaxine label |
| PF-023 | Venlafaxina pode produzir síndrome de descontinuação; meia-vida/exposição são relevantes mas não explicam sozinhas gravidade individual | segurança | S3 | V2 | FDA + NICE |
| PF-024 | Bupropiona é metabolizada a hydroxybupropion principalmente por CYP2B6; metabólitos são farmacologicamente ativos | PK | S3 | V2 | FDA bupropion label |
| PF-025 | Bupropiona inibe CYP2D6 e pode elevar exposição de substratos CYP2D6 | DDI | S3 | V2 | FDA label |
| PF-026 | Bupropiona possui risco dose/contexto-dependente de convulsão; contraindicações e fatores predisponentes importam | segurança | S4 | V3 | FDA boxed/label |
| PF-027 | Lítio não é metabolizado e é eliminado predominantemente pelos rins | PK | S3 | V2 | FDA lithium label |
| PF-028 | Alterações de função renal, volume/sódio e interações podem alterar níveis de lítio | PK/segurança | S4 | V3 | FDA/NICE |
| PF-029 | Lítio possui janela terapêutica estreita e requer monitorização clínica/laboratorial | segurança | S4 | V3 | FDA/NICE |
| PF-030 | Valproato possui riscos fetais importantes e restrições/precauções reprodutivas fortes; regras exatas dependem da jurisdição/data | segurança/regulatório | S4 | V4 | FDA + MHRA/NICE |
| PF-031 | Segurança reprodutiva de valproato não pode ser resumida como “evitar na gravidez”; prevenção, indicação e alternativas precisam ser contextualizadas | inferência clínica | S4 | V4 | regulators/guidelines |

## Fluoxetina
A longa meia-vida do composto e do metabólito ativo norfluoxetina produz mudanças lentas de concentração e interações que podem persistir após interrupção.

**Não inferir:** “meia-vida longa = antidepressivo melhor”.
**Não inferir:** “fluoxetina nunca produz sintomas de retirada”.

## Paroxetina
CYP2D6 participa do metabolismo e a própria molécula inibe CYP2D6. A não linearidade significa que mudanças de dose/exposição não precisam ser proporcionais.

**Separar:** concentração, ocupação do transportador, benefício e withdrawal.

## Sertralina
CPIC 2023 integra CYP2C19 e CYP2B6 para recomendações farmacogenéticas selecionadas. A magnitude clínica depende do fenótipo metabolizador, alternativas e contexto.

**Não inferir:** genótipo sozinho determina resposta antidepressiva.

## Citalopram/escitalopram
O risco QT exige distinguir concentração, dose, fatores de risco, eletrólitos e co-medicações. QT prolongado é marcador eletrofisiológico de risco, não sinônimo de torsades em cada pessoa.

## Venlafaxina/desvenlafaxina
A conversão CYP2D6 ajuda explicar diferenças metabólicas entre pessoas. Metabólito ativo significa que “menos parent drug” não equivale automaticamente a “menos atividade farmacológica”.

## Bupropiona
Hydroxybupropion e outros metabólitos contribuem à exposição/atividade. CYP2B6 influencia formação; CYP2D6 inhibition importa para interações.

Risco de seizure deve ser descrito com dose/formulação/fatores predisponentes; não como propriedade binária.

## Lítio
Por não depender de metabolismo hepático clássico, interações relevantes frequentemente alteram perfusão/filtração/reabsorção renal e balanço de sódio/água.

A cadeia correta é:
`dose → absorção → distribuição → função renal/sódio/interações → concentração → efeito/toxicidade`.

**Não usar nível sérico sem horário relativo à dose e contexto.**

## Valproato
Teratogenicidade e neurodevelopmental risk tornam o tema regulatoriamente volátil. O ledger deve manter fonte por jurisdição/data e evitar copiar regra britânica/europeia como regra universal brasileira ou americana.

## Regras de inferência adicionadas
1. Metabólito ativo muda interpretação de parent concentration.
2. Inibição enzimática e ser substrato são relações diferentes.
3. Genotype→exposure não é igual a genotype→clinical response.
4. QT prolongation→risk não é igual a arrhythmia certa.
5. Withdrawal→neuroadaptação não é igual a addiction.
6. Renal elimination exige integrar kidney function, volume/sodium e interações.
7. Pregnancy safety é claim de alta volatilidade e jurisdição.
8. Dose máxima regulatória não é dose-alvo universal.

## Pendências lote 3
- clozapine PK/DDI/constipation/myocarditis;
- risperidone/paliperidone;
- quetiapine/norquetiapine;
- olanzapine metabolic outcomes;
- aripiprazole akathisia/impulse-control warning;
- lamotrigine/rash/titration;
- carbamazepine autoinduction/interactions;
- benzodiazepine comparative PK;
- stimulants/nonstimulants ADHD;
- ketamine/esketamine.

**Integração:** nenhuma. **Treinamento:** nenhum.
