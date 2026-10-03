# ICD-11 — matriz por código, release e mudanças entre versões

**Checagem:** 2026-10-03. **Escopo:** fecha a pendência declarada em `2026-10-02-icd11-arquitetura-diagnostica-fronteiras-02.md` ("ainda falta matriz code/release-level e auditoria anual de mudanças"). Não repete a síntese clínica (CDDR) das partes 1–2 nem os dados de confiabilidade do field study (já em `epidemiologia-diagnostico-triagem-quantitativa` e no ledger transversal).

## Status das fontes deste bloco

- **icd.who.int/browse estava bloqueado** nesta sessão (proxy 403). Os códigos foram conferidos em **espelhos secundários do MMS** (findacode.com, autoicdapi.com, worldoftaxonomy.com, codingahead.com) e em artigos de revisão (PMC6983973; BMC Psychiatry 2023 10.1186/s12888-023-05186-w; Gaebel 2020 DCNS; PMC9881116; PMC12638403; PMC12008857).
- Rótulos:
  - **VERIFIED-SEC**: código e título conferidos em ≥1 espelho do MMS e coerentes com uma revisão. Não foi conferido no navegador oficial.
  - **PARTIAL**: só uma fonte, ou a fonte é imprecisa.
  - **UNVERIFIED**: escrito de memória e marcado como pendente.
- **O que este bloco não permite concluir:**
  - os espelhos não indicam em qual release cada código entrou nem se mudou. Por isso a coluna "estável 2022→2026" é **inferência**, não verificação;
  - a mudança release-a-release só pode ser confirmada com as notas de versão oficiais do WHO (pendência RL-P1).

## 1. Releases do MMS

| ID | Afirmação | Fonte | Status | O que **não** permite concluir |
| --- | --- | --- | --- | --- |
| REL-001 | Releases do MMS: 2018 (pré-implementação), 2019-04 (adotada pela 72ª WHA, maio 2019), 2020-09, 2021-05, 2022-02, 2023-01, 2024-01, 2025-01, 2026-01. | Wikipedia "ICD-11"; ICD-API "Supported Classification Versions" (título indexado) | PARTIAL | Não diz o que mudou no capítulo 06 em cada release. |
| REL-002 | ICD-11 entrou em vigor para registro em 1º jan 2022. | WHO "International Classification of Diseases"; Pezzella 2022 *World Psychiatry* (10.1002/wps.20982) | VERIFIED-SEC | "Em vigor" ≠ "em uso": vigorar não implica que um país codifique em ICD-11 (ver REL-004). |
| REL-003 | O manual clínico CDDR do capítulo 06 foi publicado pela WHO em 8 mar 2024. Ele é distinto do MMS (estatístico). | WHO news 08-03-2024 | VERIFIED-SEC | O CDDR 2024 não está atrelado a uma release anual do MMS. Um código do MMS pode mudar sem que o CDDR seja reeditado, e vice-versa. |
| REL-004 | Adoção heterogênea. Mai/2024: 132 Estados-membros em alguma fase, 14 coletando/reportando dados em ICD-11. EUA: ICD-10-CM segue obrigatório para cobrança; morbidade em ICD-11 projetada não antes de 2027–2029. Brasil: implantação faseada com conclusão prevista para 2027. | WHO FAQ "ICD-11 implementation"; ICD10monitor 2025; Rev Panam Salud Publica 2025 "Implementation of the ICD-11 in Brazil" | PARTIAL (números de fontes secundárias; FAQ WHO não lida integralmente) | Não permite assumir que dados epidemiológicos brasileiros ou americanos recentes usem categorias ICD-11. A maior parte da literatura de prevalência ainda usa ICD-10/DSM. |

**Regra para a base:** todo código ICD-11 citado em dossiê deve trazer a release (`MMS 2026-01` por padrão) e o status de conferência. Um código sem release é tratado como `V2` (volatilidade moderada).

## 2. Matriz do capítulo 06 (blocos e códigos principais)

Faixa do capítulo: **6A00–6E8Z** (VERIFIED-SEC, autoicdapi chapter 6). Os equivalentes ICD-10 são **aproximações conceituais** e não a tabela oficial de mapeamento WHO 10→11, que não foi conferida (pendência RL-P2).

### 2.1 Neurodesenvolvimento (6A00–6A0Z)

| ID | Código | Entidade | ICD-10 aprox. | Mudança relevante | Status |
| --- | --- | --- | --- | --- | --- |
| COD-001 | 6A00 (.0 leve, .1 moderado, .2 grave, .3 profundo, .4 provisório) | Transtornos do desenvolvimento intelectual | F70–F79 ("retardo mental") | Renomeado. Gravidade definida em **desvios-padrão/percentis** de funcionamento intelectual **e** adaptativo, com indicadores comportamentais quando não há teste padronizado. Grave vs profundo distingue-se **só** pelo comportamento adaptativo (testes não discriminam abaixo do percentil 0,003). | VERIFIED-SEC (findacode 6A00.3; worldoftaxonomy) |
| COD-002 | 6A02 (.0–.5 por DI × linguagem funcional) | Transtorno do espectro do autismo | F84.0/F84.1/F84.5 | Categoria única. Qualificadores cruzam presença de DI com nível de linguagem funcional. | VERIFIED-SEC |
| COD-003 | 6A05 (.0 desatento, .1 hiperativo-impulsivo, .2 combinado) | TDAH | F90 | Movido do bloco infantil para o neurodesenvolvimento. Apresentações em vez de subtipos. | VERIFIED-SEC |
| COD-004 | 6A01, 6A03, 6A04, 6A06 | Fala/linguagem; aprendizagem; coordenação motora; movimentos estereotipados | F80–F82, F98.4 | Agrupados no neurodesenvolvimento. | VERIFIED-SEC (Springer *Nervenarzt* 2025) |

**Correção registrada (C-ICD-1):**
- A revisão alemã indexada (Springer 2025, s00115-025-01876-w, resumo de busca) descreve a DI com **três** níveis e faixas de QI (55–69/40–54/<40).
- O MMS lista **quatro** níveis mais provisório, definidos por DP/percentil com componente adaptativo obrigatório.
- A descrição por QI é uma simplificação e não deve ser usada como regra ICD-11. Status: CONTESTED quanto à fonte secundária; o MMS prevalece.

### 2.2 Psicose e catatonia (6A20–6A4Z)

| ID | Código | Entidade | ICD-10 aprox. | Mudança relevante | Status |
| --- | --- | --- | --- | --- | --- |
| COD-005 | 6A20 | Esquizofrenia | F20 | **Subtipos removidos** (paranoide, hebefrênica, catatônica etc.) por instabilidade longitudinal e baixa validade prognóstica. Em seu lugar: qualificadores de curso (primeiro episódio, múltiplos episódios, contínuo) e de sintoma (6A25). | VERIFIED-SEC (PMC12638403; Springer s00115-025-01861-3) |
| COD-006 | 6A21 | Transtorno esquizoafetivo | F25 | Definido por episódio, não por curso vitalício. | VERIFIED-SEC (código); PARTIAL (mudança conceitual, das revisões gerais) |
| COD-007 | 6A22, 6A23, 6A24 | Esquizotípico; psicótico agudo e transitório; delirante | F21, F23, F22 | O esquizotípico permanece no bloco psicótico (no DSM-5 é transtorno de personalidade). | PARTIAL (códigos citados em revisões; espelho não aberto para cada um) |
| COD-008 | 6A25 | Manifestações sintomáticas de transtornos psicóticos primários | — (novo) | Dimensões positiva, negativa, depressiva, maníaca, psicomotora e cognitiva, graduadas. | PARTIAL (citado em revisões; espelho não conferido) |
| COD-009 | 6A40 / 6A41 | Catatonia associada a outro transtorno mental / induzida por substâncias ou medicamentos | F20.2, F06.1 | **Catatonia passa a entidade independente**, aplicável a humor, autismo etc., e não só à esquizofrenia. Catatonia por condição médica fica fora do bloco (secundária, 6E69, UNVERIFIED). | VERIFIED-SEC (6A40/6A41; PMC12008857) |

### 2.3 Humor (6A60–6A8Z)

| ID | Código | Entidade | ICD-10 aprox. | Mudança relevante | Status |
| --- | --- | --- | --- | --- | --- |
| COD-010 | 6A60 (18 subcódigos) | Bipolar tipo I | F31 | Episódio atual codificado na subcategoria. | VERIFIED-SEC |
| COD-011 | 6A61 | Bipolar tipo II | F31.8 ("outros") | **Código próprio** (no ICD-10 não havia). | VERIFIED-SEC |
| COD-012 | 6A62 | Ciclotimia | F34.0 | Movida para o bloco bipolar. | UNVERIFIED (código de memória) |
| COD-013 | 6A70 (.0 leve; .1 moderado sem psicose; .2 moderado com psicose; .3 grave sem psicose; .4 grave com psicose; demais: gravidade não especificada / remissão) | Transtorno depressivo de episódio único | F32 | Existe "moderado **com** sintomas psicóticos" (6A70.2). No ICD-10, psicose implicava episódio grave (F32.3). | VERIFIED-SEC (findacode 6A70.2) |
| COD-014 | 6A71 | Transtorno depressivo recorrente | F33 | ≥2 episódios separados por remissão. | VERIFIED-SEC |
| COD-015 | 6A72 | Distimia | F34.1 | — | VERIFIED-SEC (citado como diferencial em 6A71) |
| COD-016 | 6A73 | Transtorno misto depressivo e ansioso | F41.2 | **Mantido** no ICD-11 (ausente no DSM-5). Fronteira de baixa confiabilidade histórica. | UNVERIFIED (código de memória) |
| COD-017 | GA34.41 | Transtorno disfórico pré-menstrual | N94.3 (não específico) | Classificado no capítulo genitourinário, listado também no humor. | UNVERIFIED |

**Contradição C-ICD-2 (crítica):**
- Parker 2025 (*Aust N Z J Psychiatry*, 10.1177/00048674251356403) publica crítica dos critérios ICD-11 para transtornos de humor.
- Aqui só o título e a existência foram verificados, não os argumentos.
- **Não** permite concluir que os critérios sejam inválidos. Registra que a validade da subdivisão por gravidade e psicose é discutida.

### 2.4 Ansiedade, obsessivo-compulsivo, estresse e dissociação (6B00–6B6Z)

| ID | Código | Entidade | ICD-10 aprox. | Mudança relevante | Status |
| --- | --- | --- | --- | --- | --- |
| COD-018 | 6B00–6B06 | TAG; pânico; agorafobia; fobia específica; ansiedade social; ansiedade de separação; mutismo seletivo | F41.1, F41.0, F40.0, F40.2, F40.1, F93.0, F94.0 | Ansiedade de separação e mutismo seletivo saem do bloco infantil. **Pânico deixa de ser subordinado à agorafobia.** | VERIFIED-SEC |
| COD-019 | 6B20 (.0 insight bom/razoável; .1 insight pobre/ausente; .Z) | TOC | F42 | Qualificador de insight em vez de subtipos (predominantemente obsessivo, compulsivo etc.). | VERIFIED-SEC |
| COD-020 | 6B21–6B25 | Dismórfico corporal; referência olfativa; hipocondria; acumulação; transtornos de comportamento repetitivo focado no corpo | F45.2 (dismorfia/hipocondria), F63.3 (tricotilomania) | **Hipocondria sai dos somatoformes** e entra no espectro obsessivo-compulsivo. Acumulação e referência olfativa são novas. | PARTIAL (bloco citado em revisões; códigos individuais não abertos no espelho) |
| COD-021 | 6B40 | TEPT | F43.1 | Requisitos mais estreitos, centrados em revivência no presente, evitação e senso de ameaça. | VERIFIED-SEC |
| COD-022 | 6B41 | TEPT complexo | — (novo; próximo de F62.0) | TEPT + perturbações de auto-organização. | VERIFIED-SEC |
| COD-023 | 6B42 | Transtorno de luto prolongado | — (novo) | Duração mínima de referência de 6 meses após a perda, com variação cultural (ver CDDR, parte 1). | VERIFIED-SEC (código) |
| COD-024 | 6B60 | Transtorno dissociativo de sintomas neurológicos (FND) | F44.4–F44.7 | Unifica conversões motoras, sensoriais e convulsivas sob qualificadores de sintoma. | UNVERIFIED (código não confirmado no espelho) |

### 2.5 Alimentação, eliminação, sofrimento corporal (6B80–6C2Z)

| ID | Código | Entidade | ICD-10 aprox. | Mudança relevante | Status |
| --- | --- | --- | --- | --- | --- |
| COD-025 | 6B80–6B85 | Anorexia; bulimia; compulsão alimentar; ARFID; pica; ruminação-regurgitação | F50.0, F50.2, (F50.8/F50.9), F98.2, F98.3, F98.2 | **Compulsão alimentar e ARFID** passam a categorias próprias. Feeding (infantil) e eating unificados. | VERIFIED-SEC (findacode bloco 6B8) |
| COD-026 | 6C00 (.0 noturna, .1 diurna, .2 ambas, .Z) | Enurese | F98.0 | Idade de desenvolvimento de referência: 5 anos. | VERIFIED-SEC |
| COD-027 | 6C20 | Transtorno de sofrimento corporal (bodily distress) | F45.x (maioria), F48.0 (neurastenia) | **Somatoformes e neurastenia retirados**, substituídos por categoria única com gravidade. A controvérsia sobre sobreposição com síndromes funcionais e EM/SFC está na parte 2 da arquitetura. | PARTIAL (código das revisões; transição F48.0→6C20 vista em fonte de advocacy, dxrevisionwatch) |

### 2.6 Substâncias e comportamentos aditivos (6C40–6C5Z)

| ID | Código | Entidade | ICD-10 aprox. | Mudança relevante | Status |
| --- | --- | --- | --- | --- | --- |
| COD-028 | 6C40 (.1 padrão nocivo; .2 dependência com .20 uso contínuo, .21 episódico, .22 remissão completa precoce, .23 remissão parcial sustentada, …) | Transtornos por uso de álcool | F10 | Remissão codificada na subcategoria. "Padrão nocivo" exige ≥12 meses (uso episódico) ou ≥1 mês (contínuo). | VERIFIED-SEC |
| COD-029 | 6C41–6C4H | Demais substâncias (canabis, opioides, sedativos, cocaína, estimulantes etc.) | F11–F19 | Estrutura repetida por substância. **Os códigos individuais não foram conferidos.** | UNVERIFIED (por substância) |
| COD-030 | QE10 | Uso perigoso (hazardous) de álcool | — | Fica no capítulo 24 (fatores que influenciam a saúde), **não** no 06. É fator de risco, não transtorno. | UNVERIFIED |
| COD-031 | 6C50 / 6C51 | Transtorno do jogo de azar / transtorno de jogo (gaming) | F63.0 / — | Jogo de azar passa de "hábitos e impulsos" para comportamentos aditivos. **Gaming disorder é novo** e foi controverso na comunidade científica. | VERIFIED-SEC (6C51); PARTIAL (6C50) |

### 2.7 Impulsos, disruptivos, personalidade, parafilias, neurocognitivos (6C7x–6D8x)

| ID | Código | Entidade | ICD-10 aprox. | Mudança relevante | Status |
| --- | --- | --- | --- | --- | --- |
| COD-032 | 6C72 | Comportamento sexual compulsivo | F52.7 (impulso sexual excessivo) | **Classificado em controle de impulsos, não em adições.** | VERIFIED-SEC |
| COD-033 | 6C73 | Explosivo intermitente | F63.8 | Categoria própria. | UNVERIFIED |
| COD-034 | 6D10 (.0 leve, .1 moderado, .2 grave) | Transtorno de personalidade | F60.0–F60.9 | **Tipos categóricos removidos.** Diagnóstico por gravidade; "dificuldade de personalidade" (QE50.7) fica fora do capítulo 06. | VERIFIED-SEC (6D10.0); UNVERIFIED (QE50.7) |
| COD-035 | 6D11 (.0 afetividade negativa, .1 distanciamento, .2 dissocialidade, .3 desinibição, .4 anancastia, .5 padrão borderline) | Traços ou padrões proeminentes | F60.x | Cinco domínios de traço mais **padrão borderline**, mantido como concessão à utilidade clínica e à base de tratamento (DBT, MBT). | VERIFIED-SEC (PMC9881116; findacode 6D11) |
| COD-036 | 6D70 (.0 por doença classificada noutro lugar; .1 por substância/medicamento; …) | Delirium | F05 | — | VERIFIED-SEC |
| COD-037 | 6D71 | Transtorno neurocognitivo leve | — (próximo de F06.7) | Novo como categoria específica. | VERIFIED-SEC |
| COD-038 | 6D80–6D8Z (6D80 demência por doença de Alzheimer) | Demências | F00–F03 | Ver C-ICD-3. | VERIFIED-SEC (6D80 no capítulo 06) |

**Contradição C-ICD-3 (onde fica a demência):**
- Uma revisão de busca e várias fontes secundárias afirmam que a demência "foi movida para o capítulo de doenças neurológicas".
- Os espelhos do MMS mostram **6D80 (demência por Alzheimer) dentro do capítulo 06**.
- Interpretação mais provável, a confirmar no navegador oficial (RL-P3):
  - a **síndrome demencial** é codificada em 6D8x (capítulo 06);
  - a **doença** subjacente (por exemplo, Alzheimer) é codificada no capítulo 08 (neurológico);
  - as duas se ligam por pós-coordenação ou dupla filiação (*multiple parenting*).
- A frase "demência saiu do capítulo mental" é **imprecisa** e não deve ser repetida na base sem qualificação.

### 2.8 Fora do capítulo 06 (relevantes para saúde mental)

| ID | Código | Entidade | Local | Mudança | Status |
| --- | --- | --- | --- | --- | --- |
| COD-039 | HA60 / HA61 / HA6Z | Incongruência de gênero (adolescência/adulto; infância; não especificada) | Cap. 17 (condições relacionadas à saúde sexual) | **Deixou de ser transtorno mental.** No ICD-10 eram F64.x. | VERIFIED-SEC |
| COD-040 | HA00–HA0Z (disfunções sexuais) | Disfunções sexuais | Cap. 17 | Saíram do capítulo mental (F52). Modelo integrado, não dicotomia orgânico/não orgânico. | PARTIAL (faixa do capítulo 17 confirmada; códigos individuais não) |
| COD-041 | 7A00–7B2Z (7A00 insônia crônica) | Transtornos de sono-vigília | Cap. 07 (novo) | Saíram do capítulo mental (F51) e unificaram com G47. | PARTIAL (mudança VERIFIED-SEC; código 7A00 UNVERIFIED) |
| COD-042 | MB26.A | Ideação suicida | Cap. 21 (sintomas e sinais) | Código de sintoma, não de diagnóstico. | VERIFIED-SEC |
| COD-043 | MB23.R | Tentativa de suicídio | Cap. 21 | Episódio de autolesão com intenção consciente de morrer. | VERIFIED-SEC |
| COD-044 | MB23.E | Autolesão não suicida | Cap. 21 | Código próprio. **Não é transtorno** no ICD-11; no DSM-5 é "condição para estudo adicional". | VERIFIED-SEC |
| COD-045 | Capítulo 23 (causas externas, autolesão intencional) | Mecanismo e intenção para mortalidade | Cap. 23 | Equivale a ICD-10 X60–X84. Faixa de códigos não conferida. | UNVERIFIED |

**O que COD-042 a COD-045 não permitem concluir:**
- código de sintoma (MB26.A) ≠ avaliação de risco. A presença do código em prontuário não estima probabilidade de suicídio;
- em séries de mortalidade, a mudança ICD-10→ICD-11 pode criar **quebras artificiais** se a codificação de intenção mudar. Não há estudo de bridge-coding conferido aqui (RL-P4).

## 3. Mudanças estruturais ICD-10 → ICD-11 (síntese verificável)

| ID | Mudança | Fonte | Status | Leitura correta / limite |
| --- | --- | --- | --- | --- |
| CHG-001 | Bloco "transtornos com início na infância e adolescência" (F90–F98) **eliminado**. Entidades redistribuídas por continuidade ao longo da vida. | PMC6983973; BMC Psychiatry 2023 | VERIFIED-SEC | Organização de capítulo não é evidência de continuidade biológica; é escolha nosológica. |
| CHG-002 | Ordem do capítulo segue perspectiva do desenvolvimento (neurodesenvolvimento → neurocognitivos). | PMC6983973 | VERIFIED-SEC | Idem. |
| CHG-003 | Evitar pontos de corte arbitrários (número exato de sintomas e durações) em favor de características essenciais. | PMC6983973 | VERIFIED-SEC (já registrado na parte 1) | Aumenta flexibilidade; pode reduzir confiabilidade em pesquisa. Ver dados de kappa já na base. |
| CHG-004 | Novas categorias: TEPT complexo, luto prolongado, gaming, comportamento sexual compulsivo, compulsão alimentar, ARFID, bipolar II (código próprio), acumulação, referência olfativa, catatonia independente, neurocognitivo leve. | WHO news 2024; revisões | VERIFIED-SEC (a maioria) | Nova categoria ≠ nova doença descoberta: reflete consenso de utilidade clínica. |
| CHG-005 | Retiradas e fusões: subtipos de esquizofrenia; tipos de transtorno de personalidade; somatoformes e neurastenia (→ 6C20); hipocondria movida para o espectro TOC. | PMC12638403; PMC9881116; dxrevisionwatch | VERIFIED-SEC / PARTIAL (neurastenia) | — |
| CHG-006 | Saíram do capítulo mental: incongruência de gênero e disfunções sexuais (cap. 17), sono-vigília (cap. 07). | PMC7801846 (tabela); autoicdapi | VERIFIED-SEC | Mudança de capítulo não muda tratamento nem a necessidade de atenção em saúde mental. |
| CHG-007 | Pós-coordenação: códigos-tronco combináveis com extensões e qualificadores (gravidade, curso, insight, remissão). | ICD-11 Reference Guide (título indexado) | PARTIAL | Não verifiquei regras específicas de cluster coding. |

## 4. Implicações para a base e o protocolo

1. **Volatilidade:** códigos-tronco do capítulo 06 → `V1` (estáveis desde 2019 até onde os espelhos mostram); subcódigos de gravidade/especificadores → `V2`; códigos fora do capítulo 06 citados como "relacionados" → `V2`.
2. **Sem regra executável baseada só em código.** Um código não substitui avaliação clínica (já é regra da parte 1).
3. **Comparabilidade:** prevalências em ICD-10, DSM-IV/5 e ICD-11 não são intercambiáveis. Exemplos de divergência estrutural:
   - TEPT: o ICD-11 é mais estreito;
   - TEPT complexo: não existe no DSM-5-TR;
   - transtornos de personalidade: dimensionais no ICD-11.

   Toda comparação epidemiológica deve declarar o sistema.
4. **Distinção obrigatória:** existir uma categoria no ICD-11 é decisão de classificação (utilidade clínica e consenso). **Não** demonstra entidade biológica discreta, mecanismo, nem biomarcador.

## 5. Pendências explícitas (não preenchidas de memória)

- **RL-P1:** notas de versão oficiais WHO 2023-01 → 2026-01 para o capítulo 06 (códigos adicionados, renomeados, desativados). Exige acesso a icd.who.int.
- **RL-P2:** tabela oficial de mapeamento ICD-10→ICD-11 (WHO mapping tables) para validar as colunas "ICD-10 aprox.".
- **RL-P3:** confirmar no navegador oficial a dupla filiação demência 6D8x ↔ capítulo 08 (C-ICD-3).
- **RL-P4:** estudos de bridge-coding em mortalidade por suicídio na transição ICD-10→ICD-11.
- **RL-P5:** códigos UNVERIFIED desta matriz:
  - 6A62, 6A73, GA34.41;
  - 6B21–6B25 individualmente, 6B60;
  - 6C41–6C4H, QE10, 6C73, QE50.7;
  - 7A00, faixa do capítulo 23.
- **RL-P6:** ICD-11 para Atenção Primária (ICD-11-PHC) e versão em português do Brasil (tradução oficial e termos).

## 6. Tabela-resumo

| Classe | Total | VERIFIED-SEC | PARTIAL | UNVERIFIED |
| --- | --- | --- | --- | --- |
| Releases e adoção (REL) | 4 | 2 | 2 | 0 |
| Códigos (COD) | 45 | 28 | 9 | 8 |
| Mudanças (CHG) | 7 | 5 | 2 | 0 |
| Contradições/correções | C-ICD-1, C-ICD-2, C-ICD-3 | — | — | — |

A contagem por status é aproximada: linhas com status misto contam pelo status mais favorável da parte principal.

**Integração:** nenhuma. **Treinamento:** nenhum.
