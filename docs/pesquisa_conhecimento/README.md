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
