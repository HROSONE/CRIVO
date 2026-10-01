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
