# Fichas avançadas: frontend

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## frontend_react-render — Renderização React

**Definição:** Componente calcula UI a partir de props/estado; render deve permanecer puro.

**Mecanismo:** Reconciliação usa tipo/posição/key; fase de commit aplica mudanças. Strict Mode pode repetir etapas em desenvolvimento para expor problemas.

**Falhas comuns:** Efeito de rede em render duplica trabalho; key por índice associa estado ao item errado ao reordenar.

**Escolha:** Manter render puro e keys estáveis relacionadas à identidade.

**Verificação proposta:** Testar reorder, montagem repetida e ausência de efeito externo durante render.

**Referências recomendadas:** [React documentation](https://react.dev/learn)

## frontend_react-state — Estado, snapshots e batching

**Definição:** Cada render observa snapshot do estado; updates enfileirados serão processados conforme React.

**Mecanismo:** Updater funcional calcula próximo valor a partir do estado anterior da fila; mutação não fornece nova identidade adequada.

**Falhas comuns:** Três setCount(count+1) no mesmo snapshot não equivalem a três incrementos funcionais.

**Escolha:** Usar updater para transições dependentes e reduzir estado duplicado/derivável.

**Verificação proposta:** Testar múltiplos updates, evento rápido e props mudando.

**Referências recomendadas:** [React documentation](https://react.dev/learn)

## frontend_react-effects — Efeitos e sincronização

**Definição:** Efeito sincroniza componente com sistema externo após commit; cleanup encerra sincronização anterior.

**Mecanismo:** Dependências devem representar valores reativos usados; subscribe/unsubscribe e abort precisam de cleanup.

**Falhas comuns:** Usar efeito para cálculo derivável duplica estado; omitir dependência cria closure desatualizada.

**Escolha:** Calcular dados durante render quando puro; efeito apenas para integração externa.

**Verificação proposta:** Testar troca de parâmetro, unmount e ciclo setup-cleanup adicional em desenvolvimento.

**Referências recomendadas:** [React documentation](https://react.dev/learn)

## frontend_react-races — Corridas de respostas na UI

**Definição:** Requisições concorrentes podem terminar fora de ordem e atualizar estado com resultado antigo.

**Mecanismo:** Abort reduz trabalho quando suportado; request id ou flag de geração impede commit de resposta obsoleta.

**Falhas comuns:** Só limpar loading em finally antigo pode ocultar request novo; abort pode chegar após resposta.

**Escolha:** Associar estado da requisição à chave e permitir update apenas da geração ativa.

**Verificação proposta:** Responder busca A depois de B e confirmar que B permanece na tela.

**Relações:** js_cancelamento, frontend_react-effects, frontend_react-state

**Referências recomendadas:** [React documentation](https://react.dev/learn)

## frontend_react-reducer — Reducers e máquinas de estado

**Definição:** Reducer puro representa transições a partir de estado e evento; união discriminada pode proibir estados inválidos.

**Mecanismo:** Estado pending/success/error com payload apropriado reduz combinações impossíveis; eventos precisam ser correlacionados à operação.

**Falhas comuns:** Estado separado loading/error/data pode permitir estados contraditórios; reducer não remove efeitos externos.

**Escolha:** Modelar transições e executar efeitos fora do reducer.

**Verificação proposta:** Testar evento inesperado, resposta antiga e reset durante operação.

**Referências recomendadas:** [React documentation](https://react.dev/learn)

## frontend_react-context — Context e distribuição de estado

**Definição:** Context transmite valor aos consumidores; update pode rerenderizar consumidores segundo identidade do valor.

**Mecanismo:** Separar contexts por frequência/responsabilidade e selecionar store externa quando acesso seletivo importa.

**Falhas comuns:** Provider gigante com objeto novo em cada render pode aumentar trabalho; memoização não corrige arquitetura de estado.

**Escolha:** Medir commits e colocar estado no menor owner que atende consumidores.

**Verificação proposta:** Perfil de atualização isolada e verificação de comportamento sem memo.

**Referências recomendadas:** [React documentation](https://react.dev/learn)

## frontend_react-memo — Memoização e otimização React

**Definição:** useMemo/useCallback/memo podem evitar cálculos ou renders sob condições de identidade e dependências.

**Mecanismo:** Benefício depende do custo evitado e frequência; caches não devem ser necessários à correção do programa.

**Falhas comuns:** Memo em todo componente aumenta complexidade; comparador que ignora prop funcional mantém callback antigo.

**Escolha:** Otimizar gargalo medido e manter semântica correta sem cache.

**Verificação proposta:** Usar profiler e comparar commits, CPU e interação em produção.

**Referências recomendadas:** [React documentation](https://react.dev/learn)

## frontend_hydration — SSR e hidratação

**Definição:** SSR produz HTML; hidratação conecta lógica cliente a markup compatível.

**Mecanismo:** Primeira renderização cliente precisa corresponder ao servidor; timezone, random, data atual e APIs de navegador podem divergir.

**Falhas comuns:** Suprimir warning não corrige conteúdo incompatível; segredo não deve entrar em props serializadas.

**Escolha:** Separar dados determinísticos e código exclusivo de cliente; definir boundary de serialização.

**Verificação proposta:** Testar reload direto, locale diferente e HTML sem JS.

**Referências recomendadas:** [React documentation](https://react.dev/learn)

## frontend_rsc — Server e Client Components

**Definição:** Server Components podem executar no servidor e enviar representação para árvore; Client Components participam da interatividade.

**Mecanismo:** Boundary define o que é enviado ao cliente; props serializáveis e regras de import dependem do framework.

**Falhas comuns:** use client não significa código nunca é pré-renderizado no servidor; segredo em bundle continua vazamento.

**Escolha:** Minimizar boundary cliente e validar autorização dentro de operações de servidor.

**Verificação proposta:** Inspecionar bundle, serialização e request direta ao endpoint de ação.

**Referências recomendadas:** [Next.js documentation](https://nextjs.org/docs)

## frontend_routing — Roteamento e estado da URL

**Definição:** URL identifica estado navegável e pode carregar filtros/paginação compartilháveis.

**Mecanismo:** Parse e validação de search params precisam de defaults; mudanças geram história e potencial refetch.

**Falhas comuns:** Duplicar estado local e URL sem fonte de verdade causa loops; autorização não pertence só à guarda cliente.

**Escolha:** Escolher canonical URL e sincronização unidirecional quando possível.

**Verificação proposta:** Testar back/forward, deep link, query inválida e refresh.

**Referências recomendadas:** [Next.js documentation](https://nextjs.org/docs)

## frontend_web-performance — Performance percebida

**Definição:** Latência de interação, estabilidade visual e carregamento são métricas distintas.

**Mecanismo:** Code splitting, dimensões de mídia, prioridade e redução de main-thread work ajudam conforme gargalo.

**Falhas comuns:** Pontuação lab isolada não descreve todos dispositivos; lazy load do elemento principal pode piorar LCP.

**Escolha:** Medir campo e laboratório com dispositivo/rede representativos.

**Verificação proposta:** Verificar waterfalls, tarefas longas, shift de layout e percentis por população.

**Referências recomendadas:** [Google Site Reliability Engineering](https://sre.google/books/)

## frontend_virtualization — Virtualização de listas

**Definição:** Renderizar janela visível reduz nós e trabalho de listas grandes.

**Mecanismo:** Overscan, medição de altura e identidade mantêm scroll estável; acessibilidade e busca precisam tratamento.

**Falhas comuns:** Virtualizar poucos itens pode custar mais; altura errada causa saltos e foco perdido.

**Escolha:** Usar quando perfil indica custo de DOM e planejar teclado/leitor de tela.

**Verificação proposta:** Testar 100 mil itens, alturas variáveis, foco e scroll para item selecionado.

**Referências recomendadas:** [React documentation](https://react.dev/learn)

## frontend_optimistic-ui — Atualização otimista

**Definição:** UI aplica mudança antes da confirmação para reduzir espera percebida.

**Mecanismo:** Operação deve ter identidade, estado pendente e reconciliação; falha pode exigir compensar apenas efeito daquela operação.

**Falhas comuns:** Rollback por snapshot antigo pode apagar updates posteriores; double retry duplica efeito sem idempotência.

**Escolha:** Usar quando erro recuperável e operação bem definida; reconciliar por entidade/versão.

**Verificação proposta:** Testar falha fora de ordem, conflito servidor e duas edições rápidas.

**Referências recomendadas:** [React documentation](https://react.dev/learn)


