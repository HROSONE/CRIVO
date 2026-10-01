# Astronomia — auditoria de lacunas e protocolo para encerrar a PESQUISA

**Data da auditoria:** 2026-10-01  
**Branch:** `pesquisa/acervo-conhecimento-crivo`  
**Estado:** pesquisa para revisão; **NÃO integrada, NÃO treinada, NÃO certificada**.  
**Objetivo:** encontrar as lacunas que impedem que o *acervo documental* seja amplo e confiável e estabelecer quando o agente pesquisador deve **parar de pesquisar Astronomia e avançar para outra disciplina**.

## 1. Referências locais verificadas antes desta auditoria

- `main:docs/skill_especializacao_astronomia.md`: dez módulos e gate científico/neural/CI para certificação do CRIVO. A **conclusão documental aqui definida NÃO substitui** o gate de certificação.
- `main:conhecimento_mundo.json`: 72 itens explicitamente marcados como `area=astronomia`; nas fichas, 72 fatos classificados como `definicao`, 107 como `detalhe`, 73 como `limite`, 1 como `causa` e 2 como `exemplo`. Essas contagens são do arquivo `conhecimento_mundo.json`, não de todas as outras fontes agregadas.
- `main:conhecimento_astronomia_luas.json`: quatro fichas de luas (Lua da Terra, Europa, Titã e Encélado). O registro integrado da skill informa 76 fichas e 279 fatos no currículo astronômico.
- `main:avaliacoes/integracao_20261001.json`: registro histórico de avaliação diagnóstica, sem prova cega nem certificação; não usar métricas de desempenho como porcentagem de completude da pesquisa.
- `pesquisa/acervo-conhecimento-crivo:docs/pesquisa_conhecimento/README.md`: até esta auditoria, apenas um dossiê científico novo está listado e gravado nesta branch, sobre lentes gravitacionais, buracos negros, feedback galáctico, fontes compactas distantes e escala de distâncias.
- **Importante:** exposições feitas na conversa anterior sobre corpos menores, formação planetária, marés, física estelar e cosmologia ainda NÃO constituem documentos do acervo. Não presumir incorporação, nem importar afirmações sem rever a proveniência e as datas.

## 2. Matriz de lacunas por módulo do currículo

A classificação abaixo é um **diagnóstico de documentação disponível nesta branch**, não uma medida de compreensão do CRIVO. "Existente na main" não equivale a material científico revisado nesta branch.

| Módulo da skill | Já consta em algum lugar | Lacunas documentais bloqueantes | Prioridade da pesquisa |
| --- | --- | --- | --- |
| 1. Vocabulário e ontologia | Definições canônicas e limites em `conhecimento_mundo.json` | Inventário de entidades e aliases sem duplicidade; fronteiras entre estrela, planeta, lua, objeto transnetuniano e demais classes; definições operacionais, condições e contraexemplos | Alta |
| 2. Sistema Solar | Oito planetas, Lua, Europa, Titã, Encélado e alguns corpos menores na main | Comparação física entre mundos; ressonâncias, marés, evolução térmica, origem e limites de observação; amostras, composição e história de asteroides/cometas; luas adicionais sob critério de relevância | Máxima |
| 3. Formação planetária | Termos de disco, acreção e planetesimal no catálogo da main | Balanço de momento angular; colisão/fragmentação, instabilidade de concentração, acreção de seixos, linha de gelo, migração, dispersão de gás, evidência em discos reais e hipóteses concorrentes | Máxima |
| 4. Física estelar | Termos de protoestrela, fusão e remanescentes | Equilíbrio e transporte de energia; ciclo próton–próton/CNO; limites de massa; supernovas; anãs brancas/estrelas de nêutrons/buracos negros; processos s/r e fontes observacionais | Alta |
| 5. Galáxias | Dossiê sobre lentes, acreção e feedback; termos de tipos galácticos na main | Formação hierárquica, arqueologia galáctica, gás e formação estelar, dinâmica, relação matéria luminosa/massa inferida, modelos alternativos e incertezas | Média-alta |
| 6. Cosmologia | Dossiê parcial de distâncias; termos do Universo primordial na main | Nucleossíntese primordial, recombinação, CMB e espectros acústicos; expansão e diferentes distâncias cosmológicas; energia escura e limites da inferência; dados conflitantes | Alta |
| 7. Observação | Lentes e distâncias descritas no dossiê; técnicas listadas na main | Fundamentos de detectores, calibração, astrometria, espectroscopia, fotometria, seleção/amostragem, sinais vs. ruído, falsos positivos e cruzamento de métodos independentes | Alta |
| 8. Matemática aplicada | Fórmulas pontuais de deflexão e fluxo no dossiê | Gravitação, Kepler, energia e momento angular, órbitas, propagação de incertezas, ordem de grandeza, equações com hipóteses e exemplos numéricos reprodutíveis; relatividade aplicada | Máxima |
| 9. Explicação e raciocínio | Relações causais esparsas no primeiro dossiê | Banco transversal de comparações, objeções, premissas falsas, contraexemplos, relações condicionais e distinção dado→inferência→modelo→hipótese em vários módulos | Máxima |
| 10. Prova final | Gate de especialização existe na main | **Apenas no acervo:** preparar matriz de evidências, propostas de sondas inéditas e checklist de revisão científica; avaliação cega, testes e certificação cabem ao agente integrador, não à rotina pesquisadora | Alta |

## 3. Definição objetiva de "muito bom" para PESQUISA

Cada módulo só passa a **`pesquisa_documental_pronta`** quando TODAS as condições aplicáveis estiverem demonstradas no acervo:

1. **Cobertura delimitada:** existe inventário de conceitos essenciais, relações e casos-limite do módulo, confrontado com a skill atual e o catálogo real da main; não há tópico central obrigatório sem documentação. Não usar contagem arbitrária de fatos como substituto de profundidade.
2. **Profundidade:** cada conceito prioritário possui definição operacional; mecanismo/causa ou justificativa de por que não se aplica; propriedades, relações com pelo menos outros dois conceitos quando pertinentes; exemplo concreto; contraexemplo ou confusão comum; limitações e evidências observacionais/experimentais.
3. **Proveniência:** as afirmações centrais possuem fontes específicas verificadas, com instituição/autores, URL, data/contexto e restrições de reutilização registradas. Para afirmações recentes, surpreendentes ou disputadas, procurar pelo menos **duas fontes independentes** sempre que existirem; diferenciar comunicado de artigo primário, hipótese de consenso e notícia de estudo concluído. Indicar explicitamente quando só há uma fonte.
4. **Revisão cruzada:** conferir erros de unidades, conceitos duplicados, referências quebradas, hipóteses apresentadas como certezas, omissões de condições físicas e contradições entre documentos. Não inventar precisão ou comprovação indisponível.
5. **Amplitude:** o tema é explicado em múltiplos níveis (intuitivo, causal e quando aplicável matemático), com comparações envolvendo outras áreas e distinções de observação direta versus inferência.
6. **Entrega rastreável:** os documentos pertinentes estão publicados **somente** em `docs/pesquisa_conhecimento/<area>/` na branch documental; o README contém um índice não duplicado e o relatório de lacunas indica o que foi resolvido e o que continua aberto.

### Critério de PARADA da área

Quando os dez módulos estiverem marcados `pesquisa_documental_pronta`, realizar uma **revisão final de lacunas críticas**. Se **duas revisões consecutivas**, baseadas no inventário atual e nas fontes, não identificarem lacuna central substantiva nem erro científico bloqueante, marcar Astronomia como **`pesquisa_documental_suficiente_para_curadoria`**. Nesse momento:

- **PARE de adicionar documentos genéricos de Astronomia.** Novidades científicas futuras poderão entrar em revisões pontuais, mas não impedem a transição.
- **ESCOLHA OUTRA ÁREA** por dependências e lacunas (por exemplo Física fundamental/Matemática, depois Química/Biologia, conforme inventário), criando o mesmo processo de auditoria.
- **NÃO** equipare o fechamento documental a diploma, conhecimento absoluto, domínio da rede neural ou aprovação da skill. A certificação acadêmica interna do CRIVO exige integração, prova independente, critérios por módulo e CI pelo outro agente.
- **NÃO** mantenha a pesquisa eternamente aberta só porque o Universo é inesgotável: curiosidades e temas de fronteira não bloqueiam conclusão de um currículo delimitado; registre-os como extensão opcional.

Se a pesquisa não conseguir validar uma afirmação controversa, marcar `evidencia_insuficiente`, preservar a incerteza e prosseguir; não forçar uma afirmação sem base só para atingir o critério.

## 4. Etapas concretas e próximas entregas

**Fase A — base conceitual:** produzir dossiês exclusivos e auditados de módulos 1–3: taxonomia e definições, mapa físico do Sistema Solar, evolução orbital, migração, marés e formação planetária; evitar repetir texto que já está na main sem acrescentar mecanismo e evidência.

**Fase B — mecanismos:** módulos 4–6: energia nuclear e transferência de energia estelar, remanescentes e síntese de elementos, evolução galáctica e física cosmológica, com fontes primárias.

**Fase C — instrumentos e explicações:** módulos 7–9: inferência observacional, matemática com exemplos e incertezas, relações causais transversais e contraexemplos.

**Fase D — entrega ao agente integrador:** módulo 10 documental: índice completo, matriz evidência→módulo→fontes, lacunas residuais, materiais ainda controversos e recomendações de futuras avaliações. **Não executar** testes, treinar, abrir PR ou editar a skill de produção.

**Fase E — auditorias de encerramento:** duas verificações independentes do inventário, sem lacunas críticas. Publicar um parecer explícito de encerramento **da pesquisa**, depois mudar o foco para a área seguinte.

## 5. Estado nesta data

- **Pesquisa documental:** 1 dossiê temático publicado, profundidade pontual; inventário dos dez módulos **ainda incompleto**.
- **Módulos documentalmente prontos:** nenhum demonstrado nesta auditoria; não atribuir "10%" por existir uma ficha.
- **Treinamento/incorporação decorrente desta branch:** nenhum.
- **Consulta simbólica/neural:** não testadas nesta auditoria.
- **Certificação da skill:** **0/10 (0%)**, conforme registro na main; não altera métricas históricas.
- **Próximo bloqueio concreto:** começar a fase A, verificar e registrar fontes dos materiais sobre formação planetária e dinâmica de luas antes de transferir os relatos da conversa.

**Referências internas de navegação:** [skill de astronomia na main](https://github.com/HROSONE/CRIVO/blob/main/docs/skill_especializacao_astronomia.md), [catálogo científico](https://github.com/HROSONE/CRIVO/blob/main/conhecimento_mundo.json), [catálogo lunar](https://github.com/HROSONE/CRIVO/blob/main/conhecimento_astronomia_luas.json), [relatório de integração](https://github.com/HROSONE/CRIVO/blob/main/avaliacoes/integracao_20261001.json) e [acervo documental](https://github.com/HROSONE/CRIVO/tree/pesquisa/acervo-conhecimento-crivo/docs/pesquisa_conhecimento).


## 6. Acompanhamento da Fase A após a auditoria inicial — 01/10/2026

A auditoria acima preserva a fotografia feita ANTES dos dossiês novos. Posteriormente, foram publicados e relidos na mesma branch:

- [Formação planetária, transporte de momento angular e evidências](2026-10-01-formacao-planetaria-dinamica-evidencias.md): mecanismo de crescimento de sólidos, obstáculos à formação de planetesimais, instabilidade de fluxo, acreção de seixos, linha de gelo, migração, estrutura PDS 70 e inferências sobre discos, com 14 referências listadas.
- [Luas, ressonâncias, marés e oceanos](2026-10-01-luas-ressonancias-mares-oceanos.md): origens alternativas, Io/Europa/Ganimedes, campo magnético de Europa, plumas e fosfatos de Encélado, meteorologia de Titã, captura de Tritão e escalas gravitacionais, com 20 referências listadas.

**Inventário verificável agora:** três dossiês temáticos no acervo, incluindo o documento anterior de lentes/buracos negros/distâncias, mais este protocolo. Isso amplia a Fase A, mas não certifica módulos: não houve inventário exaustivo de todos os corpos e relações, revisão científica externa nem duas auditorias finais. A contagem de referências é bibliográfica, NÃO indica número de fatos assimilados ou fontes independentes.

**Lacunas residuais da Fase A:** diferenciação planetária, cronologia por isótopos, interior comparado dos oito planetas, órbitas de corpos menores, migração de grandes impactos, comparação sistemática entre famílias de luas, exercícios com unidades/erros. Necessário evitar aprofundar uma mesma notícia se ela não fecha uma dessas lacunas.

**Estado por módulos documentais:** 1 = incompleto; 2 = incompleto, agora com relações causais adicionais; 3 = incompleto, agora com mecanismos documentados; 4–9 = incompletos em níveis diferentes; 10 = pendente de consolidação. **Nenhum** marcado como pesquisa_documental_pronta nesta rodada. Certificação neural/simbólica, integração à main e treinamento permanecem fora do escopo deste acervo.


## 7. Acompanhamento da Fase A: interiores, oito planetas e cronologia — 01/10/2026

**Dossiês novos publicados e relidos na branch:**

- [Diferenciação interna e comparação física dos oito planetas](2026-10-01-interiores-planetas-comparacao-diferenciacao.md): compara Mercúrio, Vênus, Terra, Marte, Júpiter, Saturno, Urano e Netuno quanto a energia, composição, magnetismo, fontes de calor, ambiente superficial, instrumentos e modelos. Destaca revisões de modelos do núcleo de Marte a partir do InSight, núcleo diluído de Júpiter e sismologia indireta por anéis de Saturno; 24 entradas bibliográficas, inclusive referências repetidas.
- [Cronologia, meteoritos, crateras e proveniência](2026-10-01-cronologia-meteoritos-crateras-e-proveniencia.md): distingue idades de minerais, corpos e superfícies; discute datação Pb–Pb/Al–Mg, Vesta/Ceres, Bennu, superposição e calibração de crateras e interpretações da cronologia lunar; 20 entradas bibliográficas, inclusive repetidas.

**Novo inventário na branch:** 5 dossiês científicos temáticos + 1 protocolo de auditoria. Os textos são material para revisão e possível incorporação pelo outro agente; não foram executados testes ou treinamentos e nenhuma fonte de código foi modificada nesta rodada.

**Efeitos na matriz documental, SEM aprovação antecipada:**

| Módulo | Avanço documental comprovado nesta rodada | Pendência que ainda impede declarar pronto |
| --- | --- | --- |
| 1 | Distinções taxonômicas e limites das classificações dos oito planetas | Ontologia completa/aliases canônicos e revisão cruzada das fichas |
| 2 | Comparação causal de todos os oito planetas; pequenos corpos Vesta, Ceres, Bennu e crateras | Cobertura sistemática de cometas, famílias de asteroides, anéis e todas as dinâmicas do escopo |
| 3 | Mecanismos de segregação interna, calor radioativo e cronologia de formação | Cenários de impactos, evolução tectônica e formação em diversidade de ambientes |
| 4–6 | Não foram aprofundados centralmente por estes dois novos dossiês | Pesquisa estelar, galáctica e cosmológica continua pendente |
| 7 | Sismologia, gravimetria, magnetometria, análise de amostras e crateras | Instrumentos, calibração, seleção de observações e erros em cada método |
| 8 | Equações e distinções de relógios; fórmulas condicionais | Exercícios com dados e incertezas instrumentais reproduzidos por terceiros |
| 9 | Contraexemplos físicos e distinções observação/inferência/modelo | Matriz transversal e avaliação inédita não contaminada |
| 10 | Material para futura matriz de evidências e possíveis rubricas | Agente integrador e revisor independente decidirão provas e certificação |

**Nenhum módulo está classificado como pesquisa_documental_pronta.** Próximos dossiês prioritários: fundamentos de fusão estelar e nucleossíntese (módulo 4) e, depois, cosmologia física (módulo 6). Para os módulos 2 e 3, retomar apenas lacunas estruturais, não novas listas de curiosidades. Não alterar percentual certificado (continua 0/10 conforme skill da main), não alegar competência neural/simbólica não medida e não mudar base ativa.


## 8. Acompanhamento da Fase B: estrutura estelar, neutrinos, remanescentes e nucleossíntese — 01/10/2026

**Entregas publicadas, com referência e arquivo verificados nesta branch:**

- [Estrutura estelar, fusão nuclear, neutrinos e observação](2026-10-01-estrutura-estelar-fusao-neutrinos-e-observacao.md): equilíbrio hidrostático, energia gravitacional pré-fusão, cadeia pp/CNO, medição Borexino 2020, oscilação de neutrinos, transporte radiativo/convectivo, Gaia H–R e asterossismologia; doze entradas de referências, algumas relacionadas à mesma observação/instituição.
- [Supernovas, remanescentes e nucleossíntese](2026-10-01-remanescentes-supernovas-nucleossintese-evidencias.md): evolução de gigantes, anãs brancas/estrelas de nêutrons/buracos negros, canais termonuclear e colapso, s-processo, r-processo, GW170817, SN 1987A, GRB 230307A e limites de inferência; 22 entradas de referências, inclusive fontes duplicadas identificadas no próprio documento.

**Inventário atual:** sete dossiês temáticos + esta auditoria; *isso é contagem de documentos, NÃO percentual científico certificado*. Os relatos anteriores apresentados em conversa não devem ser confundidos com publicação em branch. Fontes bibliográficas podem se repetir entre documentos.

**Matriz de lacunas após a Fase B:**

| Módulo | Evidência documental nova | Lacuna de fechamento ainda aberta |
| --- | --- | --- |
| 4 — Física estelar | Cadeia causal colapso→fusões→fases evolutivas→remanescentes; casos observacionais Borexino, Gaia, SN 1987A, GW170817 e Webb | Matrizes quantitativas por massa e metalicidade; binárias, baixa massa, cristalização de anãs brancas; revisão externa de limites nucleares e observacionais |
| 5 — Galáxias | Enriquecimento químico por ventos, explosões e fusões; relação do espectro com metalicidade | Montagem hierárquica e dinâmica galáctica ainda não documentadas amplamente |
| 6 — Cosmologia | Distinção da nucleossíntese primordial vs. estelar e escala de observação de fontes distantes | Expansão, CMB, nucleossíntese primordial aprofundada, energia escura e interpretações de dados |
| 7 — Observação | Neutrinos, espectros, oscilação estelar, radiação multi-banda e ondas gravitacionais | Calibração, seleção instrumental, vieses, erros sistemáticos e redução de dados |
| 8 — Matemática | Equações de suporte hidrostático, energia e escala de luminosidade | Cálculos numéricos com unidades, propagação de incerteza e dados observados |
| 9 — Raciocínio | Dado versus inferência; exemplos sobre fusão, neutrinos e explosões de origens diversas | Provas independentes, comparações envolvendo outras disciplinas e raciocínio robusto para enunciados inéditos |
| 10 — Prova final | Referências e exemplos de perguntas para futura curadoria | Avaliação cega e certificação são responsabilidade do agente integrador, nunca desta branch |

**Decisão de qualidade:** módulo 4 recebeu cobertura relevante, mas ainda NÃO satisfaz todos os requisitos de `pesquisa_documental_pronta` (revisão científica independente, matriz de escopo completo e conferência de limites). Nenhum dos dez módulos foi certificado editorial/neuralmente. A conclusão documental continua pendente, sem prazo artificial.

**Próximo foco de pesquisa:** material substancial para módulo 6 — radiação cósmica de fundo, medidas de expansão, modelos cosmológicos e incertezas — priorizando fontes primárias; depois complementar dinâmicas/estrutura galáctica e a matemática observacional transversal. Módulo 4 poderá receber revisão focada para preencher lacunas que restam, não expansão indefinida de curiosidades.

**Integrado ao CRIVO nesta execução:** nada. **Peso neural/CI alterado:** não. **Consulta simbólica/neural avaliada:** não. **Certificação registrada na skill da main:** permanece 0/10.


## 9. Acompanhamento da Fase C: cosmologia primordial e expansão — 01/10/2026

**Documentos publicados e relidos nesta branch:**
- [Cosmologia primordial: nucleossíntese, recombinação e CMB](2026-10-01-cosmologia-primitiva-nucleossintese-recombinacao-cmb.md): física do Universo quente, separação entre núcleos/átomos/estrelas, formação de núcleos leves, observações FIRAS/DMR-COBE, parâmetros Planck publicados em 2020, anisotropias, polarização, inflação sob teste e reionização. Contém 14 entradas de fontes com dependências bibliográficas explícitas.
- [BAO, distâncias cosmológicas, Hubble, DESI 2026 e energia escura](2026-10-01-baos-hubble-desi-energia-escura-inferencias.md): standard ruler, redshift, distâncias D_L/D_A/D_M, H0 local versus inferido do CMB, escala acústica observada, correlação Lyα de DESI, histórico 2025 versus atualização de 30/07/2026, covariância e sistemáticos. Contém 14 entradas de fontes, incluindo materiais do mesmo levantamento e repetição institucional explícita.

**Inventário documental atual após esta entrega:** 9 dossiês temáticos + 1 auditoria. Isso NÃO significa 90% da especialização ou nove módulos concluídos; dossiês distribuem-se de maneira desigual entre os módulos e ainda carecem de curadoria independente.

| Módulo | Novo conhecimento documentado | Lacuna que ainda impede marcar módulo como pronto |
| --- | --- | --- |
| 6 — Cosmologia | Nucleossíntese primordial, recombinação e radiação de fundo, acústica CMB/BAO, formação de estruturas e reionização, histórico de aceleração e tensões de expansão; DESI 2026 contextualizado | Revisão científica cruzada e recente de fontes, integralização dos conceitos delimitados, dinâmica quantitativa da estrutura cósmica, natureza de matéria/energia escura, inferências em modelos concorrentes com condições |
| 7 — Observação | Distâncias cosmológicas e linhas de absorção Lyα; diferenças entre COBE/Planck/DESI/supernovas; ruído, contaminantes e calibração | Exercícios com reduções de dados e vieses quantitativos reais por técnica; avaliação por especialista |
| 8 — Matemática aplicada | Relações de redshift, H(z), D_H, D_L, D_A, parâmetro w, exemplos numéricos hipotéticos e dependência de hipóteses | Cálculos reproduzíveis com medições instrumentais, incerteza, covariância e dados abertos documentados |
| 9 — Raciocínio | Distinções dado→hipótese→modelo, exemplos de inferência e contraexemplos que relacionam várias épocas | Matriz transversal do escopo completo e avaliação independente não contaminada |
| 10 — Prova final | Matriz bibliográfica/epistêmica disponível para curadoria futura | Prova cega e verificação neural pertencem ao agente integrador; jamais executar nesta branch |

**Resultado do gate de pesquisa documental:** **NENHUM módulo foi certificado como pesquisa_documental_pronta**, pois as condições acordadas incluem revisão cruzada, cobertura integral delimitada e ausência de lacuna central. Não decretar conclusão geral da Astronomia nem mudança de disciplina.

**Próximas lacunas priorizadas:** (a) evolução quantitativa da estrutura cósmica, dinâmica galáctica e halos; (b) instrumentos, matemática aplicada e estudos com dados reproduzíveis; (c) corpos menores e comparação sistemática de asteroides/cometas; (d) revisão da matriz integral de 10 módulos, sem converter volumes de dossiês em certificação. Fontes emergentes de 2026 devem ser sempre comparadas a primários/observações e registrar datas corretamente.

**Integrado na main por esta rotina:** nada. **CI/treino/checkpoints:** inalterados. **Consulta simbólica e competência neural:** não avaliadas. **Certificação:** inalterada em 0/10, conforme última skill verificada na main.


## 10. Acompanhamento adicional: ciclo do gás, matéria escura e métodos quantitativos — 01/10/2026

**Arquivos novos confirmados por leitura nesta branch:**

- [Ciclo bariônico, feedback e evolução ambiental](2026-10-01-ciclo-barionico-galaxias-feedback-ambiente.md): contrasta ISM, CGM e ICM, formação estelar e traçadores PHANGS, eficiência, balanço de reservatório, jatos, ram-pressure e a estimativa CO de REBELS-25 divulgada pelo ALMA/VLA em 12/06/2026. Fonte listada não é prova de medição independente nem do treino do CRIVO.
- [Matéria escura, lentes e crescimento](2026-10-01-materia-escura-crescimento-estrutura-lentes.md): decomposição de curvas SPARC, colisão do Bullet Cluster, mapa de lentes fracas COSMOS-Web de janeiro de 2026, parâmetros Planck e DES Y6. Deixa explícito que mapa de massa é inferido e que a natureza microscópica não foi identificada.
- [Astrometria, espectros e incertezas](2026-10-01-metodos-quantitativos-astrometria-espectros-incertezas.md): Gaia DR3, paralaxe ruidosa, correções sistemáticas variáveis, Doppler/redshift, fotometria, SNR e propagação de covariância, com contas didáticas e protocolos de dados futuros **NÃO executados**.

**Inventário após os documentos:** 13 dossiês temáticos listados no README + uma auditoria de lacunas. O índice havia sido atualizado por outro agente com um dossiê de dinâmica galáctica, por isso a contagem de 13 resulta de trabalho intercalado, não apenas dos três novos documentos. A existência de arquivo não implica 13 módulos, 13% ou proficiência científica.

| Módulo | Lacuna parcialmente atacada | Bloqueio remanescente para encerramento DOCUMENTAL |
| --- | --- | --- |
| 5 — Galáxias | Ciclo do gás, feedback, stripping, matéria não luminosa, comparação de linhas independentes | Funções de luminosidade e massa; relação halo–galáxia e alterações por redshift; revisão crítica de teorias alternativas e seleção observacional |
| 6 — Cosmologia | Estrutura e lentes, Planck e DES Y6, conexão baryon feedback–potência de matéria | Confrontar modelos e dados entre sondas, diferenças CMB/lentes e generalização de amostras |
| 7 — Observação | Gaia DR3, espectroscopia, PHANGS, SNR e papel do detector | Trabalhar dados reais versionados e independentes, revisar amostragem de diversas técnicas e erros de calibração |
| 8 — Matemática aplicada | Equações de densidade, velocidade, massa dinâmica, distância, redshift e covariância, com unidades | Exercícios sobre o inventário completo de física orbital/estelar e repetição de contas com dados externos |
| 9 — Raciocínio | Condições, causa vs. correlação, exemplos que corrigem premissas falsas | Matriz geral de raciocínio por módulos, rubrica científica externa e avaliação inédita |
| 10 — Prova final | Bibliografia, limites, propostas para protocolos de teste futuros | Avaliações cegas, treinamento e CI pertencem ao agente integrador, NÃO são ação desta branch |

**Decisão de qualidade:** os documentos aprofundam lacunas centrais, mas ainda há tópicos obrigatórios não cobertos/revisados; **nenhum módulo foi classificado pesquisa_documental_pronta**, não encerrar Astronomia agora. **Próximos passos documentais prioritários:** completar lacunas de corpos menores e observação planetária; aprofundar funções e ambientes de galáxias apenas quando o inventário exigir; publicar mapa conceitual canônico, matriz integral de fontes/afirmações e auditorias de revisão. Evitar curiosidades repetidas.

**Não alterado:** main, pesos, testes, treino, modelos, skills de produção, CI ou PR. Esta pesquisa não certificou o CRIVO e não mede consulta neural/simbólica. Estado oficial prévio conforme main: 0/10.
