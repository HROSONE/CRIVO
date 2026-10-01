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
| 2026-10-01 | Astronomia 5, 6, 7, 8 e 9 | [Lentes gravitacionais, buracos negros e distâncias](astronomia/2026-10-01-lentes-buracos-negros-e-distancias.md) | Pesquisa redigida e fontes institucionais consultadas; revisão e integração pendentes |

## Histórico e lacunas

As quatro rodadas narrativas anteriores foram apresentadas na conversa, porém **não** foram despejadas automaticamente nesta branch: qualquer passagem para o acervo exige nova verificação das fontes, datas e direitos, especialmente para alegações de pesquisas de 2026.

**Backlog científico prioritário, sem garantia de ineditismo ou de aprovação:** migração planetária e aquecimento de marés; ressonâncias de luas; nucleossíntese e evolução de estrelas; formação das primeiras galáxias; distâncias, erros sistemáticos e covariâncias; dinâmica e distribuição de matéria escura; expansão cósmica e interpretações de dados. Conferir o inventário atual antes de produzir outra ficha.

## Como ampliar o acervo sem conflitos

1. Consultar `main`, a skill atual e este índice; usar a mesma branch documental.
2. Escolher um tema específico ainda não aprofundado no acervo.
3. Publicar um **novo arquivo** com nome único sob `docs/pesquisa_conhecimento/<area>/` contendo data, escopo, fatos, relações causais, evidências, limites, URLs específicas, autoria, direitos quando verificados e lacunas.
4. Recarregar o SHA deste índice antes de atualizá-lo; nunca reverter contribuições simultâneas.
5. Informar o link efetivo do arquivo ao outro agente; não supor que esteja na `main`.

**Separação de eixos:** cobertura editorial de produção = não alterada; pesquisa documental = registrada; consulta simbólica = não testada; competência neural = não testada; certificação = não alterada.
