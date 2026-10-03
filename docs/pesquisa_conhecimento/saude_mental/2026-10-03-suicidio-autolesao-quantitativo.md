# Suicídio e autolesão — epidemiologia, predição, intervenções e restrição de meios (quantitativo)

**Checagem:** 2026-10-03. **Origem:** déficit material AD-01 da auditoria adversarial 01.

**Escopo:** números com denominador, efeito, IC, desenho e limite. Complementa:
- as regras gerais já existentes: `epidemiologia-prevencao...` §14 e `etica...` §18–19;
- os códigos ICD-11 MB26.A, MB23.R e MB23.E (matriz ICD-11);
- os efeitos antissuicidas já registrados em TQ4: lítio, com a contradição de Katz 2022; esketamina; suicidalidade pediátrica (PED).

**Rótulos:** VERIFIED-ABS (resumo indexado conferido), PARTIAL, UNVERIFIED. Acesso direto a PubMed/WHO estava bloqueado; texto integral não lido.

**Regra de leitura:** suicídio é evento raro no nível individual. Por isso, **associação forte ≠ predição útil**, e redução relativa grande pode significar diferença absoluta pequena. Todo número abaixo deve ser lido junto com o risco basal.

## 1. Epidemiologia

| ID | Afirmação | Fonte | Status | O que **não** permite concluir |
| --- | --- | --- | --- | --- |
| SU-001 | 727.000 suicídios no mundo em 2021 (703.000 em 2019). Taxa padronizada global 8,9/100 mil (9,0 em 2019). Homens 12,3 vs mulheres 5,6/100 mil. 73% dos suicídios em países de baixa e média renda. 3ª causa de morte aos 15–29 anos (2ª em mulheres dessa faixa) | WHO, *Suicide worldwide in 2021: global health estimates* (2025, ISBN 9789240110069) | VERIFIED-ABS (via comunicados de WHO/IASP) | Estimativas modeladas: países sem registro vital de qualidade dependem de modelos. Subnotificação e classificação errada de intenção variam por país. A estabilidade da taxa padronizada esconde aumentos regionais (ver SU-002) |
| SU-002 | **Brasil:** 112.230 suicídios de 2010 a 2019; o número anual subiu 43% (9.454 → 13.523). Taxa de 6,6/100 mil em 2019. Crescimento médio de 1,4% ao ano em 2000–2018, acelerado para ~3,2% ao ano a partir de 2014. Suicídio é a 2ª causa de morte aos 15–19 anos | Ministério da Saúde, Boletim Epidemiológico vol. 55 nº 4 (2024), panorama 2010–2021; estudo de tendência citado no mesmo levantamento | VERIFIED-ABS (números do boletim via busca); a tendência 2014+ é PARTIAL (estudo secundário) | Parte do aumento pode refletir **melhora de registro** (menos óbitos de intenção indeterminada), e não só aumento real. A taxa brasileira está **abaixo** da média global padronizada; "epidemia" é termo impreciso |

## 2. Predição de risco — o limite central

| ID | Afirmação | Fonte | Status | O que **não** permite concluir |
| --- | --- | --- | --- | --- |
| SU-003 | Em 50 anos de pesquisa (365 estudos, 3.428 efeitos), fatores de risco preveem pensamentos e comportamentos suicidas **só um pouco melhor que o acaso**. A capacidade preditiva não melhorou ao longo do tempo | Franklin et al. 2017, *Psychol Bull* (PMID 27841450) | VERIFIED-ABS | Que fatores de risco sejam irrelevantes: são **associados** ao desfecho, mas não discriminam indivíduos. Modelos multivariados e de aprendizado de máquina posteriores melhoram a discriminação, mas o VPP continua baixo por causa da taxa-base (SU-004) |
| SU-004 | Pacientes psiquiátricos classificados como "alto risco": **5,5%** morreram por suicídio em ~63 meses vs 0,9% dos de "baixo risco". OR 4,84 (3,79–6,20; 53 amostras, 37 estudos). Categorização multifatorial não supera muito fatores isolados | Large et al. 2016, *PLoS One* (PMC4902221) | VERIFIED-ABS | **94,5% dos "alto risco" não morrem por suicídio** no período, e muitos suicídios ocorrem no grupo de "baixo risco" (que é muito mais numeroso). Classificação de risco **não** deve decidir sozinha o acesso a cuidado nem justificar coerção (regra já em `etica...` §18) |
| SU-005 | Taxa de suicídio após alta psiquiátrica: 484/100 mil pessoas-ano (422–555); **1.132/100 mil nos primeiros 3 meses**. 100 estudos, 17.857 suicídios, 4,7 milhões de pessoas-ano | Chung et al. 2017, *JAMA Psychiatry* (PMID 28564699) | VERIFIED-ABS | Taxa agregada de 1946 a 2016, com heterogeneidade grande. Não identifica **quem**. O que justifica é intensificar o seguimento após a alta, e não prever casos individuais |
| SU-006 | Item 9 do PHQ-9 ("pensamentos de morte ou autolesão"): em 84.000+ pacientes ambulatoriais, o risco cumulativo em 1 ano de **tentativa** sobe de 0,4% ("nunca") para 4% ("quase todos os dias"); o de **morte** sobe de 0,03% para 0,3%. Segue preditor após ajuste | Simon et al. 2013, *Psychiatr Serv* | VERIFIED-ABS | Mesmo no nível máximo, 96% não tentam e 99,7% não morrem em 1 ano. Item positivo exige **avaliação**, não alarme automático. Sistema de saúde integrado dos EUA; a transferência para o Brasil não foi estudada aqui |
| SU-007 | A C-SSRS mostrou validade convergente e divergente e consistência interna da subescala de intensidade de ideação em 3 estudos multicêntricos (adolescentes e adultos); associada a tentativa subsequente | Posner et al. 2011, *Am J Psychiatry* | VERIFIED-ABS (sem sensibilidade/especificidade conferidas) | Instrumento estrutura a avaliação, mas **não** resolve o problema de VPP (SU-003/004). Valores de sensibilidade/especificidade dependem do ponto de corte e da população: UNVERIFIED |

## 3. Intervenções com efeito sobre comportamento suicida

| ID | Intervenção | Fonte | Desenho | Número-chave | Status | O que **não** permite concluir |
| --- | --- | --- | --- | --- | --- | --- |
| SU-008 | Plano de segurança (SPI) + contato telefônico após emergência | Stanley et al. 2018, *JAMA Psychiatry* (9 emergências VA) | **Coorte comparativa** (não ECR): 1.186 SPI+ vs 454 cuidado usual | Comportamento suicida em 6 meses: 3,03% vs 5,29%; OR 0,56 (0,33–0,95); ~45% menos. Comparecimento ≥1 consulta: OR 2,06 | VERIFIED-ABS | Não randomizado, logo é possível confundimento por sítio e período. Diferença absoluta ~2,3 pontos. Veteranos dos EUA. Não demonstra redução de **mortes** |
| SU-009 | Intervenções de contato breve (telefonemas, cartões de crise, cartas/postais) | Milner et al. 2015, *Br J Psychiatry* (14 ECR, 12 meta-analisados) | Meta-análise de ECR | **Número de repetições** de autolesão por pessoa: IRR 0,66 (0,54–0,80) | VERIFIED-ABS | Redução de episódios repetidos ≠ redução de pessoas que repetem, nem de suicídio. Os mesmos autores não acharam efeito claro sobre suicídio (PARTIAL, não conferido) |
| SU-010 | "Cartas de cuidado" | Motto & Bostrom 2001, *Psychiatr Serv* (843 pacientes que **recusaram** seguimento após internação) | ECR | Suicídio em 2 anos: 1,80% (cartas) vs 3,52% (controle) | PARTIAL (valores de fonte secundária; diferença ao longo de 5 anos diminui) | Ensaio único, antigo, população específica. Replicações posteriores mostraram efeitos inconsistentes. Não é "intervenção comprovada" isolada |
| SU-011 | TCC para autolesão em adultos | Witt et al. 2021, Cochrane CD013668 | Meta-análise de ECR | Repetição de autolesão em 6 meses: OR 0,54 (0,34–0,85; 12 ECR, 1.317); em 12 meses: OR 0,80 (0,65–0,98; 10 ECR, 2.232) | VERIFIED-ABS | Certeza GRADE não conferida aqui. Efeito em 12 meses modesto. Não demonstra redução de suicídio |
| SU-012 | DBT para autolesão em adultos | Witt et al. 2021 (mesma revisão) | Meta-análise | **Proporção** que repete: OR 0,59 (0,16–2,15; 3 ECR) em 6 meses, **não significativa**. **Frequência** de autolesão: diferença média −18,82 (−36,68 a −0,95) | VERIFIED-ABS | Poucos ECR e IC muito largo. Contraste com B-03 (TPB, psicoterapias em geral, certeza baixa): DBT reduz frequência, mas não demonstra reduzir a proporção de pessoas que repetem. Ver C-SU-1 |
| SU-013 | Clozapina vs olanzapina na esquizofrenia de alto risco | Meltzer et al. 2003, *Arch Gen Psychiatry* (InterSePT, 980 pacientes, 2 anos) | ECR aberto com avaliação cega do desfecho | Comportamento suicida: HR 0,76 (0,58–0,97). Tentativas 34 vs 55; internações para prevenir suicídio 82 vs 107 | VERIFIED-ABS | Mortes por suicídio poucas e sem diferença demonstrada. Patrocínio do fabricante (ver IB-013). Contato clínico maior no braço clozapina (monitoramento hematológico) pode contribuir. Base da indicação regulatória nos EUA |
| SU-014 | Cetamina IV em dose única sobre **ideação** suicida | Wilkinson et al. 2018, *Am J Psychiatry* 175:150–158 (IPD de 10 estudos, 167 participantes com ideação) | Meta-análise de dados individuais vs salina/midazolam | Redução de ideação maior que controle já no dia 1, persistindo até o dia 7 | VERIFIED-ABS | **Ideação ≠ comportamento ≠ morte.** Amostra pequena. Cegamento imperfeito (efeitos dissociativos). Efeito de dose única de curta duração. Não demonstra prevenção de suicídio |
| SU-015 | Lítio | TQ4: Cipriani 2013 vs Katz 2022 | — | ver TQ4 | CONTESTED (magnitude) | — |

**Contradição C-SU-1 (DBT):**
- B-03: psicoterapias para TPB, entre elas a DBT, reduzem autolesão, SMD −0,32, com certeza baixa.
- SU-012: em adultos com autolesão, a DBT não reduz significativamente a **proporção** que repete, embora reduza a **frequência**.
- Os dois achados são compatíveis: são populações e desfechos diferentes.
- Leitura correta: "a DBT reduz a frequência de autolesão em alguns grupos, com certeza baixa a moderada". **Não** "a DBT previne suicídio".

## 4. Restrição de meios (intervenções populacionais)

| ID | Intervenção | Fonte | Desenho | Número-chave | Status | O que **não** permite concluir |
| --- | --- | --- | --- | --- | --- | --- |
| SU-016 | Banimento de pesticidas altamente tóxicos (Sri Lanka) | Gunnell et al. 2007, *Int J Epidemiol*; Knipe et al. 2017, *Lancet Glob Health* | Séries temporais nacionais | Taxa caiu do pico de 47/100 mil (1995) para ~metade em 2005. 19.769 suicídios a menos em 1996–2005 vs 1986–95. 1995–2015: redução >70%, ~93.000 vidas salvas, ~US$1,3 por DALY | VERIFIED-ABS | Série temporal sem contrafactual randomizado. Os autores testaram fatores concorrentes (desemprego, álcool, guerra) sem explicar a queda. Generalizável **onde o meio é dominante**; no Brasil, o perfil de métodos difere (enforcamento predominante, PARTIAL) |
| SU-017 | Redução do tamanho das embalagens de paracetamol (Reino Unido, set. 1998) | Hawton et al. 2013, *BMJ* (séries temporais interrompidas) | Quase-experimental | Mortes por paracetamol −43%; ~765 mortes a menos em 11 anos (comunicados citam "mais de 600"; PARTIAL quanto ao número exato) | VERIFIED-ABS (direção e 43%) | Não demonstra redução **total** de suicídios: a substituição de método foi avaliada como parcial e incerta |
| SU-018 | Acesso a arma de fogo no domicílio | Anglemyer et al. 2014, *Ann Intern Med* (16 estudos observacionais) | Meta-análise observacional | Suicídio: OR 3,24 (2,41–4,40). Vítima de homicídio: OR ~2 | VERIFIED-ABS | Associação; confundimento residual possível (por exemplo, características de quem tem arma). Dados majoritariamente dos EUA. Coerente com a letalidade do método, mas não é ECR |

**Regra derivada:** restrição de meios é das intervenções populacionais com evidência mais consistente. A lógica é **letalidade × impulsividade da crise**: crises agudas são frequentemente breves, e reduzir o acesso a métodos letais nesse intervalo salva vidas. Isso **não** significa que toda restrição seja eficaz em todo contexto. O efeito depende de o meio ser frequente e letal localmente.

## 5. Comunicação e mídia

| ID | Afirmação | Fonte | Status | O que **não** permite concluir |
| --- | --- | --- | --- | --- |
| SU-019 | Após reportagem de suicídio de celebridade, o risco de suicídio sobe 13% (RR 1,13; 1,08–1,18; 14 estudos; mediana de 28 dias). Quando o **método** é reportado, mortes pelo mesmo método sobem 30% (RR 1,30; 1,18–1,44) | Niederkrotenthaler et al. 2020, *BMJ* (31 estudos; 20 com risco moderado de viés na análise principal) | VERIFIED-ABS | Estudos observacionais de séries temporais; causalidade plausível (consistência, especificidade de método, temporalidade), não demonstrada experimentalmente |
| SU-020 | **Efeito Papageno:** narrativas de superação de crise suicida podem **reduzir** a ideação em parte do público | Niederkrotenthaler et al. (literatura 2010+, revisões) | PARTIAL (sem magnitude conferida) | Evidência majoritariamente de experimentos de curto prazo com desfecho de ideação, não de mortes |

**Implicação para qualquer sistema que converse sobre suicídio** (documental; integração **não** autorizada nesta fase):
- não descrever métodos;
- não romantizar;
- oferecer caminhos de ajuda;
- histórias de superação são preferíveis.

Essas regras são coerentes com SU-019/020 e com as diretrizes de mídia da WHO. A versão das diretrizes não foi conferida: UNVERIFIED.

## 6. Síntese doutoral

1. **Predição individual é fraca** (SU-003/004/006). O papel da avaliação é **estruturar o cuidado e a segurança**, não prever.
2. **Janelas de alto risco existem e são acionáveis:** pós-alta (SU-005) e após tentativa. A evidência mais consistente é para **seguimento ativo** (SU-008/009) e **restrição de meios** (SU-016–018).
3. **Ideação, comportamento e morte são desfechos diferentes.** A cetamina age na ideação (SU-014). A clozapina e a TCC reduzem comportamentos (SU-011/013). A demonstração de redução de **mortes** por ECR é rara em qualquer intervenção, porque o evento é raro e os ensaios não têm poder.
4. **Contexto brasileiro:** taxa crescente desde 2014 (SU-002). Os métodos e o acesso a serviços diferem dos países onde os estudos foram feitos. A transferência dos números exige cautela (o bloco Brasil trata disso).

## 7. Pendências

- **SU-P1:** WHO LIVE LIFE (2021) e diretrizes de mídia WHO/IASP (versão 2023): conferir versão e recomendações.
- **SU-P2:** métodos de suicídio no Brasil (proporção de enforcamento, envenenamento, armas): número oficial.
- **SU-P3:** meta-análises de aprendizado de máquina em predição de suicídio (AUC vs VPP).
- **SU-P4:** evidência sobre linhas de crise (988 nos EUA; CVV 188 no Brasil): efeito sobre desfechos, além da satisfação.
- **SU-P5:** autolesão em adolescentes (Cochrane 2021, Witt; DBT-A, McCauley 2018).

## 8. Tabela-resumo

| Classe | IDs | Status predominante |
| --- | --- | --- |
| Epidemiologia | SU-001, SU-002 | VERIFIED-ABS (tendência BR PARTIAL) |
| Predição/instrumentos | SU-003–SU-007 | VERIFIED-ABS |
| Intervenções clínicas | SU-008–SU-015 | VERIFIED-ABS (SU-010 PARTIAL; SU-015 CONTESTED) |
| Restrição de meios | SU-016–SU-018 | VERIFIED-ABS |
| Mídia | SU-019, SU-020 | VERIFIED-ABS / PARTIAL |
| Contradições | C-SU-1 | — |

**Integração:** nenhuma. **Treinamento:** nenhum.
