# Fichas avançadas: web

Exportação determinística de `catalogo-avancado.json`. Síntese autoral; referências remotas precisam de conferência editorial. Acervo não integrado ao runtime.

## web_dom — DOM e ownership

**Definição:** DOM é árvore de nós com APIs e eventos; leitura/escrita pode acionar estilo e layout.

**Mecanismo:** Separar construção, lookup e atualização; bibliotecas UI mantêm ownership da região renderizada.

**Falhas comuns:** Mutar nó controlado por framework cria divergência; innerHTML não confiável produz XSS.

**Escolha:** Escolher dono da árvore e usar APIs seguras de texto/dados.

**Verificação proposta:** Testar montagem/desmontagem, eventos e alteração externa inesperada.

**Referências recomendadas:** [HTML Living Standard](https://html.spec.whatwg.org/)

## web_events — Propagação de eventos

**Definição:** Eventos podem percorrer captura, alvo e bubbling; composed path importa em Shadow DOM.

**Mecanismo:** preventDefault cancela default quando permitido; stopPropagation limita propagação, não a ação default. passive pode impedir cancelamento.

**Falhas comuns:** Confundir target/currentTarget quebra delegação; listener anônimo sem referência complica remoção.

**Escolha:** Usar delegação onde fizer sentido e limpar listeners no lifetime do componente.

**Verificação proposta:** Testar filho clicado, evento não bubbling, listener passive e shadow boundary.

**Referências recomendadas:** [HTML Living Standard](https://html.spec.whatwg.org/)

## web_render-pipeline — Layout, paint e compositing

**Definição:** Navegador calcula estilos, layout e pintura conforme mudanças e dependências.

**Mecanismo:** Alternar escrita e leitura geométrica pode forçar layout síncrono; transforms/compositor ajudam em casos específicos, sem garantia universal.

**Falhas comuns:** will-change em tudo aumenta recursos; requestAnimationFrame não autoriza trabalho ilimitado.

**Escolha:** Agrupar leituras/escritas e medir frame time no dispositivo alvo.

**Verificação proposta:** Usar performance trace para localizar forced layout e frames acima do budget.

**Referências recomendadas:** [HTML Living Standard](https://html.spec.whatwg.org/)

## web_css-layout — Flexbox, grid e sizing

**Definição:** CSS resolve layout segundo formatting context, intrinsic sizing e constraints.

**Mecanismo:** Flex organiza eixo principal e secundário; grid define tracks. min-width:auto pode impedir shrink; overflow/containing blocks alteram resultado.

**Falhas comuns:** Somar percentuais com gap pode transbordar; altura percentual depende de containing block definido.

**Escolha:** Escolher grid para estrutura bidimensional e flex para sequência, respeitando contexto.

**Verificação proposta:** Testar conteúdo longo, min-content, zoom, RTL e viewport estreito.

**Referências recomendadas:** [CSS specifications](https://www.w3.org/Style/CSS/specs.en.html)

## web_css-cascade — Cascade e especificidade

**Definição:** Cascade escolhe declarações por origem, importância, layers, especificidade e ordem conforme regras.

**Mecanismo:** Custom properties herdam normalmente e são resolvidas no contexto; layers permitem organizar precedência.

**Falhas comuns:** !important generalizado torna manutenção difícil; selector mais longo não substitui entendimento da cascade.

**Escolha:** Definir tokens/layers e componentes com especificidade controlada.

**Verificação proposta:** Testar temas, fallback de var, herança e overrides acessíveis.

**Referências recomendadas:** [CSS specifications](https://www.w3.org/Style/CSS/specs.en.html)

## web_a11y — Acessibilidade semântica

**Definição:** Interface deve ser operável e compreensível por teclado e tecnologias assistivas.

**Mecanismo:** HTML nativo fornece roles/comportamentos; labels, foco, nome acessível e mensagens de erro conectam UI ao usuário.

**Falhas comuns:** Div clicável sem teclado/role não equivale a botão; ARIA não implementa comportamento.

**Escolha:** Começar por elementos nativos; verificar navegação, leitores de tela e contraste.

**Verificação proposta:** Testar Tab/Shift+Tab/Enter/Escape, foco visível e labels com automação e revisão humana.

**Referências recomendadas:** [WCAG 2.2](https://www.w3.org/TR/WCAG22/)

## web_dialogs — Diálogos e gerenciamento de foco

**Definição:** Modal exige interação/foco coerentes, nome acessível e retorno ao contexto após fechar.

**Mecanismo:** Componente deve lidar com foco inicial, fechamento e conteúdo de fundo conforme padrão/elemento escolhido.

**Falhas comuns:** Trap mal implementado bloqueia usuário; autofocus fora do modal e restoration inexistente desorientam.

**Escolha:** Usar primitive revisada ou dialog nativo com comportamento verificado.

**Verificação proposta:** Testar abertura pelo teclado, Escape, foco após remoção e múltiplos diálogos.

**Referências recomendadas:** [WCAG 2.2](https://www.w3.org/TR/WCAG22/)

## web_forms — Formulários e submissão

**Definição:** Formulário associa controles, labels e ação; estado pendente/erro faz parte do contrato.

**Mecanismo:** Validação cliente melhora UX, mas servidor permanece autoridade. Abort/retry pode não desfazer envio já aceito.

**Falhas comuns:** Desabilitar botão não impede requests concorrentes por outros clientes; placeholder não substitui label.

**Escolha:** Mostrar erros vinculados ao campo e manter dados válidos após falha.

**Verificação proposta:** Testar double submit, navegação por teclado, servidor rejeitando e conexão perdida.

**Referências recomendadas:** [HTML Living Standard](https://html.spec.whatwg.org/)

## web_browser-storage — Storage e offline

**Definição:** localStorage é síncrono e guarda strings; IndexedDB fornece armazenamento transacional local com APIs assíncronas.

**Mecanismo:** Quota, eviction e disponibilidade variam; service worker pode interceptar rede e cachear recursos.

**Falhas comuns:** Persistência local não é garantida backup; cache de dado sensível compartilha risco do dispositivo/origem.

**Escolha:** Definir versão de dados, migração, limites e estratégia de reconciliação offline.

**Verificação proposta:** Testar quota, storage indisponível, atualização do schema e duas abas concorrentes.

**Referências recomendadas:** [HTML Living Standard](https://html.spec.whatwg.org/)

## web_service-worker — Service workers e cache de aplicação

**Definição:** Service worker tem lifecycle próprio e pode servir respostas offline conforme estratégia.

**Mecanismo:** Install/activate e clientes controlados influenciam atualização; cache names e asset hashing evitam mistura de versões.

**Falhas comuns:** Cache eterno pode prender usuário em aplicação velha; SW não possui lifetime infinito nem DOM.

**Escolha:** Escolher network/cache strategy por recurso e política de upgrade.

**Verificação proposta:** Testar versão antiga aberta, atualização, offline e remoção de caches obsoletos.

**Referências recomendadas:** [MDN JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)

## web_semantic-tokens — Design tokens e semântica visual

**Definição:** Tokens de cor/spacing/tipografia precisam refletir função e tema, com contraste observado.

**Mecanismo:** Tokens como texto/surface/focus permitem temas consistentes; CSS variables fornecem mecanismo.

**Falhas comuns:** Trocar cor sem verificar contraste/estados torna UI inacessível; token raw não diz função.

**Escolha:** Separar palette de tokens semânticos e testar temas/estados reais.

**Verificação proposta:** Medir contraste normal/hover/disabled/focus e preferências de alto contraste.

**Relações:** web_a11y

**Referências recomendadas:** [WCAG 2.2](https://www.w3.org/TR/WCAG22/)

