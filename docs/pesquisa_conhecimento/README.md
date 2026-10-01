# Acervo de pesquisa do CRIVO — branch isolada

**Branch de trabalho documental:** `pesquisa/acervo-conhecimento-crivo`  
**Estado:** somente pesquisa científica para revisão; **NÃO integrada, NÃO treinada, NÃO certificada**.

## Propósito e regras de coordenação entre agentes

O agente pesquisador pode consultar a `main` e as skills, consultar referências externas, redigir novos dossiês e atualizar **somente** os arquivos sob `docs/pesquisa_conhecimento/` nesta branch. Não altera nenhuma fonte, base, peso, teste, workflow ou skill de produção. Não faz merge nem abre PR automaticamente.

O agente integrador pode consultar este acervo quando conveniente e selecionar fatos para a base efetiva somente depois de: (1) verificar referências científicas, licenças e limitações; (2) comparar com o catálogo canônico para evitar conceitos duplicados; (3) produzir testes novos e avaliações independentes; (4) rodar CI e confirmar ausência de regressão. O agente integrador mantém autonomia sobre a integração.

**Importante:** pesquisa publicada aqui **não** significa que o CRIVO aprendeu ou demonstrou compreensão. A porcentagem de certificação não é modificada por este acervo.

## Dossiês disponíveis

| Data | Área/módulos | Documento | Estado |
| --- | --- | --- | --- |
| 2026-10-01 | **Auditoria 1 de 2 — NÃO aprovada** | [Matriz de rastreabilidade de 279 fatos](astronomia/2026-10-01-auditoria-1-matriz-rastreabilidade-279-fatos.md) | 72 conceitos + quatro luas; 25 associações com fonte insuficiente, 2 referências de Lagrange já parcialmente sustentadas e 232 enunciados com semântica ainda não conferida; exige correções |
| 2026-10-01 | **Auditoria 2 de 2 — NÃO aprovada** | [Consistência dos 20 dossiês, matemática e DART 2026](astronomia/2026-10-01-auditoria-2-consistencia-modelos-matematica-e-novidades.md) | 24 links internos, 15 checagens aritméticas, nova evidência 2026 e limites de fontes/direitos; bloqueios científicos permanecem |
| 2026-10-01 | Astronomia: auditoria científica focalizada | [Checagem de 279 fatos nominais, fontes, causalidade e fórmulas](astronomia/2026-10-01-auditoria-cientifica-fatos-fontes-e-formulas.md) | Triagem referencial de 72 fichas + quatro luas, correções reais lunar/DART, seis citações genéricas sinalizadas ao integrador e oito contas; NÃO é auditoria final aprovada |
| 2026-10-01 | Astronomia: auditoria parcial de referências e integração | [Conferência pontual de fontes, URLs e estado da branch](astronomia/2026-10-01-auditoria-parcial-fontes-e-integracao.md) | Auditoria amostral: validações externas e correção da tabela do índice; NÃO é uma auditoria final nem aprova módulos |
| 2026-10-01 | Astronomia 1–10: curadoria e parada | [Protocolo independente de revisão, provas e encerramento](astronomia/2026-10-01-protocolo-curadoria-revisao-independente-e-porta-saida.md) | Critérios de seleção, prova cega e duas auditorias documentais; NÃO executa treino nem certifica a skill |
| 2026-10-01 | Astronomia 1, 2, 3, 7, 8, 9 | [Corpos menores, cometas, Kuiper/Oort e DART](astronomia/2026-10-01-corpos-menores-cometas-cinturoes-defesa-planetaria.md) | Ontologia e mecanismos de famílias de corpos, observações diretas vs reservatórios inferidos, defesa planetária; revisão pendente |
| 2026-10-01 | Astronomia 2, 3, 7, 8, 9, 10 | [Exoplanetas: trânsito, Doppler, lentes, imagens e atmosferas](astronomia/2026-10-01-exoplanetas-metodos-deteccao-vieses-atmosferas.md) | Seleção, falsos positivos, raio/massa, atmosferas e catálogos PS NASA; revisão pendente |
| 2026-10-01 | Astronomia 5, 6, 7, 8, 9 | [Funções de massa galáctica e relação com halos](astronomia/2026-10-01-funcoes-massa-galaxias-halos-abundance-matching.md) | Luminosidade, seleção, abundância de halos, HOD e limitações; revisão pendente |
| 2026-10-01 | Astronomia 4, 7, 8, 9 | [Baixa massa, binárias e cristalização estelar](astronomia/2026-10-01-fisica-estelar-baixa-massa-binarias-cristalizacao.md) | Tempo de vida de anãs M, transferência de massa e Gaia das anãs brancas; revisão pendente |
| 2026-10-01 | Astronomia 2, 3, 4, 6, 7, 8, 9 | [Matemática orbital, radiação, cosmologia e covariância](astronomia/2026-10-01-matematica-orbital-observacional-inversoes-limites.md) | Kepler e vis-viva, escape, Hill, Roche, paralaxe e propagação; validação pendente |
| 2026-10-01 | Astronomia 2, 4, 6, 7, 8 | [Checagens dimensionais com valores publicados](astronomia/2026-10-01-checagens-numericas-dados-publicados-dimensoes.md) | Mercúrio, DART, Planck, Gaia, CMB, com hipóteses declaradas; sem reprocessar dados |
| 2026-10-01 | Astronomia 1–10: matriz de navegação | [Ontologia das 72 fichas + quatro luas e 20 relações](astronomia/2026-10-01-ontologia-72-fichas-matriz-de-evidencias.md) | Todos os nomes da main reconciliados com caminhos de curadoria; NÃO é revisão individual dos fatos |
| 2026-10-01 | Astronomia 5, 6, 7, 8, 9 | [Ciclo bariônico, feedback e evolução ambiental](astronomia/2026-10-01-ciclo-barionico-galaxias-feedback-ambiente.md) | Gás ISM/CGM/ICM, PHANGS, SFR, stripping, modelo de reserva, REBELS-25 2026; revisão científica e integração pendentes |
| 2026-10-01 | Astronomia 5, 6, 7, 8, 9 | [Matéria escura: observações, lentes e crescimento](astronomia/2026-10-01-materia-escura-crescimento-estrutura-lentes.md) | SPARC, Bullet Cluster, COSMOS-Web 2026, Planck e DES Y6; limites instrumentais e de modelos; revisão/integracão pendentes |
| 2026-10-01 | Astronomia 7, 8, 9, 10 | [Astrometria, espectros e incertezas com matemática](astronomia/2026-10-01-metodos-quantitativos-astrometria-espectros-incertezas.md) | Gaia DR3, distâncias probabilísticas, redshifts, CO, SNR e covariâncias; exercícios DIDÁTICOS, sem dados reais processados; integração pendente |
| 2026-10-01 | Astronomia 5, 6, 7, 8, 9 | [Dinâmica galáctica, arqueologia da Via Láctea e montagem hierárquica](astronomia/2026-10-01-dinamica-galactica-via-lactea-montagem-hierarquica.md) | Cinemática, warp, meio interestelar 3D, fusões antigas e limites de inferência; revisão/integração pendentes |
| 2026-10-01 | Astronomia 4, 5, 6, 7, 8, 9 | [Cosmologia primordial: nucleossíntese, recombinação e CMB](astronomia/2026-10-01-cosmologia-primitiva-nucleossintese-recombinacao-cmb.md) | Mecanismos térmicos, núcleos leves, espectro COBE, anisotropias Planck, acústica e reionização; revisão/integração pendentes |
| 2026-10-01 | Astronomia 6, 7, 8, 9, 10 | [BAO, distâncias, Hubble, DESI 2026 e energia escura](astronomia/2026-10-01-baos-hubble-desi-energia-escura-inferencias.md) | Medições DESI DR2, régua acústica, inferência da expansão, tensão de Hubble, distâncias e covariâncias; revisão/integração pendentes |
| 2026-10-01 | Astronomia 1, 4, 7, 8, 9 | [Estrutura estelar, fusão nuclear, neutrinos e observação](astronomia/2026-10-01-estrutura-estelar-fusao-neutrinos-e-observacao.md) | Pesquisa de equilíbrio, sequência principal, cadeia pp/CNO, Borexino, oscilações e observações Gaia; revisão/integração pendentes |
| 2026-10-01 | Astronomia 4, 5, 6, 7, 8, 9 | [Supernovas, remanescentes e nucleossíntese](astronomia/2026-10-01-remanescentes-supernovas-nucleossintese-evidencias.md) | Pesquisa de evolução tardia, tipos Ia/colapso, processos s/r, GW170817, SN 1987A e química do meio interestelar; revisão/integração pendentes |
| 2026-10-01 | Astronomia 1, 2, 3, 7, 8, 9 | [Interiores, diferenciação e comparação dos oito planetas](astronomia/2026-10-01-interiores-planetas-comparacao-diferenciacao.md) | Matriz comparativa, geodínamos, campos induzidos, clima e evidências de interior, com hipóteses e limites; revisão/integração pendentes |
| 2026-10-01 | Astronomia 2, 3, 7, 8, 9, 10 | [Cronologia isotópica, meteoritos, crateras e proveniência](astronomia/2026-10-01-cronologia-meteoritos-crateras-e-proveniencia.md) | Relógios isotópicos, diferenciação dos planetesimais, Bennu/Vesta/Ceres, idade relativa vs. modelada; revisão/integração pendentes |
| 2026-10-01 | Astronomia 2, 3, 7, 8, 9 | [Formação planetária, migração e evidências](astronomia/2026-10-01-formacao-planetaria-dinamica-evidencias.md) | Dossiê científico de mecanismos, fluxos de gás/sólidos, acreção, migração, disco PDS 70 e limitações; revisão/integração pendentes |
| 2026-10-01 | Astronomia 1, 2, 3, 7, 8, 9 | [Luas, marés, ressonâncias e oceanos](astronomia/2026-10-01-luas-ressonancias-mares-oceanos.md) | Origem de luas, Io/Europa/Ganimedes, Encélado, Titã, Tritão, Roche e Hill; revisão/integração pendentes |
| 2026-10-01 | Astronomia: auditoria dos 10 módulos | [Lacunas, critérios de qualidade e parada](astronomia/2026-10-01-auditoria-de-lacunas-e-criterio-de-parada.md) | Escopo do acervo e condições para encerrar a PESQUISA e passar à próxima área; não é certificação do CRIVO |
| 2026-10-01 | Astronomia 5, 6, 7, 8 e 9 | [Lentes gravitacionais, buracos negros e distâncias](astronomia/2026-10-01-lentes-buracos-negros-e-distancias.md) | Pesquisa redigida e fontes institucionais consultadas; revisão e integração pendentes |

## Critério de transição entre áreas

Antes de aprofundar indefinidamente uma área, aplicar a [auditoria de lacunas e critério de parada de Astronomia](astronomia/2026-10-01-auditoria-de-lacunas-e-criterio-de-parada.md): cada módulo exige inventário, explicação causal, evidências, limites, comparação, fontes verificadas e revisão cruzada. Após os 10 módulos documentais e duas revisões sem lacuna central ou erro bloqueante, encerrar a pesquisa dessa área, registrar o parecer e escolher outra disciplina. Isso NÃO altera a porcentagem de certificação, os pesos neurais ou a base ativa. Para novas áreas, criar protocolo análogo.

## Histórico e lacunas

As rodadas narrativas anteriores da conversa ainda NÃO foram integralmente transpostas: algumas lacunas dos módulos 2 e 3 foram agora pesquisadas e REDIGIDAS novamente, com referências verificadas, nos dossiês de formação planetária e de luas. Os demais conteúdos continuam exigindo curadoria antes de publicação. Material de pesquisa não equivale a conhecimento integrado.

**Backlog científico prioritário, sem garantia de ineditismo ou de aprovação:** a branch já contém dossiês sobre migração planetária, marés e ressonâncias lunares, comparação dos interiores dos oito planetas e cronologia de meteoritos/crateras. Permanecem: revisão científica humana, mapeamento completo dos corpos menores e histórico de impactos, matemática observacional com incertezas reais; física estelar e nucleossíntese agora possuem dois dossiês substanciais, mas faltam síntese quantitativa de canais estelares, revisão científica independente e avaliação da documentação essencial; novos documentos cobrem aspectos de CMB, expansão cósmica, distâncias/covariâncias e DESI DR2, mas ainda faltam evolução quantitativa das galáxias/estrutura, matéria escura, exercícios com dados reais, inventário de cosmologia revisado externamente e aprofundamento nas disciplinas anteriores. Conferir o inventário atual antes de produzir outra ficha.

## Estado documental após a pesquisa de 01/10/2026

**Dossiês temáticos registrados e consultáveis na branch: 9**, além do protocolo de lacunas: formação planetária, luas, interiores comparados dos planetas, cronologia isotópica/meteoritos/crateras, lentes/buracos negros/distâncias, estrutura estelar e neutrinos, supernovas/nucleossíntese, cosmologia primordial/CMB e BAO/Hubble/DESI. Os dois documentos de cosmologia desta rodada listam **28 entradas bibliográficas (14 + 14)**, com fontes institucionais e artigos relacionados entre si; isso NÃO representa 28 estudos independentes nem 28 fatos certificados. A discussão da energia escura distingue a sugestão DESI 2025 da revisão DESI julho/2026, que se aproximou das predições ΛCDM neste teste. Nenhum dos dez módulos documentais foi declarado pronto e nenhuma certificação foi alterada. Todo material carece de auditoria científica antes de integração.

## Como ampliar o acervo sem conflitos

1. Consultar `main`, a skill atual e este índice; usar a mesma branch documental.
2. Escolher um tema específico ainda não aprofundado no acervo.
3. Publicar um **novo arquivo** com nome único sob `docs/pesquisa_conhecimento/<area>/` contendo data, escopo, fatos, relações causais, evidências, limites, URLs específicas, autoria, direitos quando verificados e lacunas.
4. Recarregar o SHA deste índice antes de atualizá-lo; nunca reverter contribuições simultâneas.
5. Informar o link efetivo do arquivo ao outro agente; não supor que esteja na `main`.

**Separação de eixos:** cobertura editorial de produção = não alterada; pesquisa documental = registrada; consulta simbólica = não testada; competência neural = não testada; certificação = não alterada.

## Atualização complementar — ciclo bariônico, massa escura e métodos quantitativos (01/10/2026)

**Inventário a partir das entradas deste índice:** 13 dossiês temáticos com link da branch, além do protocolo de auditoria. Alguns foram registrados pelo outro agente durante a pesquisa, e não foram reescritos aqui para evitar conflito. Nesta etapa foram acrescentados os três dossiês acima, enfocando mecanismos de gás e feedback, evidências gravitacionais e calibração quantitativa; cada um separa observação, modelo e hipótese. A contagem mede arquivos indexados, não porcentagem de domínio, fontes independentes, certificação neural ou estudo humano revisado. A seção histórica anterior com contagem de nove dossiês permanece como fotografia da época anterior.

**Pendências priorizadas:** completar parte observacional de corpos menores/exoplanetas, dinâmica de halo–galáxia e funções de massa, revisar cientificamente os dez módulos por conceito, reunir exercícios com dados abertos reais e suas covariâncias e preparar matriz editorial completa de provas para o agente integrador. **Nenhum módulo desta skill está certificado ou concluído pela pesquisa nesta etapa.**

## Atualização do inventário — complementos estruturais (01/10/2026)

**Situação conferida na edição atual:** 20 dossiês temáticos com links rastreáveis na branch, mais a auditoria principal de lacunas. Foram adicionados os sete documentos acima: pequenos corpos, exoplanetas, ligação galáxia–halo, baixa massa e binárias, matemática aplicada, checagens com números publicados e mapa de todas as **72 fichas nominais** do catálogo astronômico da main mais quatro luas de arquivo próprio. O índice de conceitos é uma ferramenta de navegação, **não** revisão individual das 279 afirmações registradas anteriormente na main nem confirmação de capacidade cognitiva da IA.

**Nota sobre versões:** o bloco histórico de nove e treze dossiês abaixo descreve etapas anteriores e não o total atual. O número atual é o da tabela de dossiês no início deste README; novas publicações concorrentes precisam recarregar o arquivo antes de atualizar essas contagens.

**Lacunas que continuam abertas apesar da amplitude:** revisão científica individual e independente das afirmações (inclusive URLs e evidência primária), reprodução de análises com dados observacionais brutos/erros e documentação definitiva da rubrica da skill, testes cegos e integração pelo outro agente. Esses bloqueios NÃO podem ser resolvidos apenas escrevendo mais dossiês. Astronomia **não** foi declarada formalmente encerrada porque a auditoria ainda não encontrou duas revisões finais sem lacunas centrais.

## Controle atual de volume e limites — entrega de complementação (01/10/2026)

**Indexados agora: 20 dossiês científicos temáticos + 1 protocolo de curadoria**, mais a auditoria de lacunas. Os documentos científicos adicionais cobrem corpos menores, exoplanetas, binárias e cristalização estelar, funções de massa galáctica, matemática orbital, checagens com números publicados, ontologia canônica e procedimento de avaliação independente. **Esse número representa arquivos publicados, não módulos aprovados ou desempenho da IA.** Dada a ampla cobertura temática, a próxima etapa de rotina deve priorizar correção de evidências, qualidade e auditorias antes de criar novas curiosidades sobre Astronomia.

**Bloqueio verdadeiro para encerrar a pesquisa:** revisão cruzada por evidência e pelo escopo dos dez módulos; auditoria externa quando houver revisor; execução independente de dados quantitativos, quando autorizada; duas auditorias documentais consecutivas sem lacuna crítica para o encerramento editorial. O protocolo foi registrado, mas nenhuma dessas auditorias finais foi considerada aprovada por pressuposição. Certificação do CRIVO na main: não modificada por esta branch.

## Estado de duas auditorias de 01/10/2026 — veredito científico

Duas passagens distintas foram EXECUTADAS e registradas na branch, **AMBAS COM BLOQUEIOS E NÃO APROVADAS**. O primeiro relatório apresenta matriz de 279 afirmações, com errata: 25 insuficientes, 2 passíveis de aprofundamento e 232 ainda não cotejadas individualmente. O segundo confronta os 20 dossiês, refaz 15 cálculos e incorpora na documentação a medição publicada em março/2026 da mudança heliocêntrica de ~0,15 s no sistema Didymos, diferente da redução de ~32–33 min no período binário. As duas passagens foram conduzidas pelo mesmo agente, logo não equivalem a revisão metodologicamente independente de dois especialistas. Não marcar pesquisa_documental_pronta, não declarar Astronomia concluída e **não alterar certificação na main**. Próxima ação: sanar fontes fracas na produção por integração revisada, examinar conteúdo integral das 279 afirmações e obter revisão independente antes de refazer as auditorias finais.
