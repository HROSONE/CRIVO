# Fichas avançadas: typescript

Exportação determinística de `catalogo-avancado.json`. Síntese autoral; referências remotas precisam de conferência editorial. Acervo não integrado ao runtime.

## ts_apagamento — Apagamento de tipos

**Definição:** TypeScript verifica código estaticamente e normalmente remove anotações na emissão; não valida dados no runtime.

**Mecanismo:** Tipos não alteram automaticamente representação de valores; interface/type desaparecem. Algumas construções como enums podem emitir JS.

**Falhas comuns:** JSON.parse tipado por as Usuario continua aceitando payload inválido; compilação bem-sucedida não garante ausência de erro.

**Escolha:** Tratar toda fronteira externa como unknown e validar antes de construir tipo de domínio.

**Verificação proposta:** Enviar payload faltando campo e verificar rejeição real; inspecionar JS emitido.

**Conferência pontual (ver conferencia-fontes-2.json):** ts-assertions

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_strict — Configuração estrita

**Definição:** strict ativa família de checagens, incluindo null e parâmetros implícitos; opções adicionais tratam índices e propriedades opcionais.

**Mecanismo:** noUncheckedIndexedAccess adiciona undefined ao acesso não provado; exactOptionalPropertyTypes distingue ausência de propriedade de valor undefined.

**Falhas comuns:** strict sozinho não elimina any, assertions, limites do sistema nem dados externos inválidos.

**Escolha:** Adotar strict e opções adicionais conforme baseline; migrar por módulo sem silenciar diagnósticos globalmente.

**Verificação proposta:** Compilar fixtures de null, índice fora de faixa, optional undefined e catch unknown.

**Conferência pontual (ver conferencia-fontes-2.json):** ts-optional

**Referências recomendadas:** [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_unknown-any — unknown, any e never

**Definição:** unknown exige narrowing antes de uso; any permite operações sem verificação; never representa conjunto sem valores.

**Mecanismo:** unknown preserva necessidade de prova local. any contamina inferência; never aparece em funções que não retornam e estados impossíveis.

**Falhas comuns:** Usar any como solução permanente mascara bugs; declarar nunca por assertion não prova impossibilidade.

**Escolha:** Preferir unknown em boundaries; any só em adaptação pequena com justificativa e teste.

**Verificação proposta:** Verificar que acesso em unknown falha no compilador e que switch exaustivo quebra ao adicionar variante.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_narrowing — Narrowing e fluxo de controle

**Definição:** Compilador refina tipos usando condições, retornos e assignments conforme análise de fluxo.

**Mecanismo:** typeof, instanceof, in, equality e discriminantes refinam uniões. Reatribuição e aliasing limitam provas.

**Falhas comuns:** Truthy check elimina 0 e string vazia; narrowing não impede mudança externa do objeto em tempo de execução.

**Escolha:** Validar condição semântica exata, como value !== undefined, e capturar snapshots quando necessário.

**Verificação proposta:** Testar 0, vazio, null, variante desconhecida e mutação entre checagem e uso.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_guards — Type guards e assertion functions

**Definição:** Predicado x is T e assinatura asserts x is T expressam contratos confiados ao autor.

**Mecanismo:** Compilador usa a assinatura, mas não prova que corpo valida todo T; retorno falso também precisa ter semântica correta quando aplicável.

**Falhas comuns:** Guard que só testa um campo pode afirmar shape inválido; assertion com condição frouxa cria segurança ilusória.

**Escolha:** Implementar guard junto ao schema e testar contra entradas hostis e incompletas.

**Verificação proposta:** Gerar objetos quase válidos, arrays no lugar de objetos e campos com tipos errados.

**Conferência pontual (ver conferencia-fontes-2.json):** ts-assertions

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_structural — Tipagem estrutural e excesso de propriedades

**Definição:** Compatibilidade considera estrutura de membros, não nome da declaração, com regras específicas.

**Mecanismo:** Excess property checks em literals detectam alguns erros, mas variável intermediária pode permitir campos adicionais.

**Falhas comuns:** Type não sela objeto runtime; interface com id não prova origem/autorização do id.

**Escolha:** Usar branding para distinções semânticas e validação allowlist para formato estrito externo.

**Verificação proposta:** Comparar literal e variável com campo extra; garantir schema rejeita campo proibido.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_unioes — Uniões discriminadas

**Definição:** União representa alternativas; campo literal comum permite selecionar variante com segurança.

**Mecanismo:** switch sobre tag reduz tipos; função assertNever pode transformar adição de caso em erro de compilação.

**Falhas comuns:** Campos opcionais em um megaobjeto permitem estados inválidos como sucesso sem valor e erro sem causa.

**Escolha:** Modelar estados exclusivos com variantes e transições explícitas.

**Verificação proposta:** Adicionar variante ao modelo e verificar erro em consumidores não atualizados.

**Invariantes:** Variante possui campos obrigatórios específicos; exhaustiveness considera todas tags.

**Pré-requisitos:** ts_narrowing; ts_unknown-any

**Exemplo local:** exemplos/contratos.ts#LoadState

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_intersecoes — Interseções e conflitos

**Definição:** A & B exige cumprir simultaneamente ambos tipos; não significa sobrescrever campos de A com B.

**Mecanismo:** Interseção de propriedades incompatíveis pode produzir never; composição de objetos runtime via spread tem outra semântica.

**Falhas comuns:** Usar intersection para simular override pode produzir tipo impossível ou enganoso.

**Escolha:** Para substituição usar Omit<A,keyof B> & B quando contrato realmente sobrescreve.

**Verificação proposta:** Compilar conflito de campo string/number e comparar tipo com objeto de spread.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_generics — Generics e preservação de relações

**Definição:** Parâmetros de tipo expressam relação entre entradas/saídas e restrições; não criam valores por si só.

**Mecanismo:** T extends Base permite usar membros de Base, mas não construir qualquer T só com Base. inferência depende de posições e contexto.

**Falhas comuns:** Generic usado só na saída pode fabricar certeza; casts escondem violação da relação.

**Escolha:** Introduzir generic quando ele conecta posições ou preserva informação; preferir tipo simples quando não há relação.

**Verificação proposta:** Testar subtipo com campo obrigatório extra e função que tenta devolver apenas Base.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_keyof — keyof, indexed access e chaves

**Definição:** keyof produz chaves de um tipo; T[K] relaciona valor à chave escolhida.

**Mecanismo:** Função get<T,K extends keyof T> retorna T[K]; index signatures ampliam espaço de chaves e índices desconhecidos exigem cautela.

**Falhas comuns:** Object.keys não pode ser afirmado universalmente como (keyof T)[] porque objetos runtime podem ter propriedades extras.

**Escolha:** Restringir origem do objeto, validar chaves ou aceitar string[] com checagem explícita.

**Verificação proposta:** Testar chave inexistente, símbolo, índice numérico e objeto com campos runtime extras.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_mapped — Mapped types e modificadores

**Definição:** Mapped types transformam propriedades e podem alterar readonly/optional e remapear chaves.

**Mecanismo:** Partial, Required, Pick e Omit são transformações estáticas, geralmente superficiais; key remapping usa as e tipos de template.

**Falhas comuns:** Partial<Config> não cria patch semanticamente válido nem valida undefined; DeepPartial requer política para arrays/funções.

**Escolha:** Projetar DTOs explícitos para escrita e contratos de patch; usar utilities quando transformação é de fato a desejada.

**Verificação proposta:** Testar patch vazio, campos nested, readonly e optional com configuração estrita.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_conditional — Conditional types e distribuição

**Definição:** T extends U ? X : Y computa tipo; parâmetro nu em posição checked distribui sobre união.

**Mecanismo:** [T] extends [U] inibe distribuição; never pode produzir resultados surpreendentes por ser união vazia.

**Falhas comuns:** Recursão/type-level programming excessivo torna compilador lento e mensagens ilegíveis.

**Escolha:** Preferir tipos simples e limitar recursão; medir tempo de check em bibliotecas sofisticadas.

**Verificação proposta:** Comparar distributivo/não distributivo e testar união com never.

**Pré-requisitos:** ts_generics; ts_unioes

**Relações:** ts_infer; ts_type-performance

**Conferência pontual (ver conferencia-fontes-2.json):** ts-distribution

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_infer — infer e extração de tipos

**Definição:** infer introduz variável dentro de padrão conditional para extrair parte de um tipo.

**Mecanismo:** Pode extrair elemento de array, retorno ou argumentos de função; overloads têm regras específicas de inferência.

**Falhas comuns:** Inferência em overloads não realiza resolução completa por chamada; extração pode perder relações de generic.

**Escolha:** Expor tipos auxiliares documentados e exemplos de consumo.

**Verificação proposta:** Testar função genérica, overload e Promise aninhada usando Awaited.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_templates — Template literal types

**Definição:** Tipos de template representam combinações de strings e permitem parse/transformações estáticas.

**Mecanismo:** Unions em slots formam produto de alternativas; número de combinações pode explodir e custar compilação.

**Falhas comuns:** Tipo de rota não valida URL externa; conjuntos enormes podem tornar editor inutilizável.

**Escolha:** Usar para vocabulário pequeno de chaves/rotas; validar runtime e evitar codificar gramáticas ilimitadas em tipos.

**Verificação proposta:** Medir check com união crescente e testar rota inesperada recebida por HTTP.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_tuplas — Tuplas e variadic tuples

**Definição:** Tuplas expressam posições e aridade; elementos opcionais/rest suportam argumentos e composição.

**Mecanismo:** readonly tuple restringe escrita através daquela referência; as const preserva literais e readonly superficial.

**Falhas comuns:** Indexar com número amplo perde precisão; readonly não impede mutação através de alias mutável existente.

**Escolha:** Usar tupla para posição semântica fixa e objeto quando nomes tornam contrato mais claro.

**Verificação proposta:** Testar aridade, optional/rest e alias mutável do mesmo array.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_satisfies — satisfies e literal inference

**Definição:** satisfies verifica compatibilidade com um tipo sem simplesmente substituir o tipo da expressão pelo alvo.

**Mecanismo:** Pode conservar informação útil de propriedades para consumidores; contextual typing ainda influencia inferência. as const preserva literais.

**Falhas comuns:** satisfies não valida valor externo nem congela objeto no runtime; assertion as não é verificação equivalente.

**Escolha:** Usar em catálogos/configurações autorais e conferir inferência com fixtures.

**Verificação proposta:** Adicionar campo inválido e verificar erro; comparar typeof com anotação explícita e assertion.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_brands — Branded types e unidades

**Definição:** Brand combina estrutura com marcador para distinguir valores semanticamente diferentes.

**Mecanismo:** Marca unique symbol evita colisões estáticas; factory valida valor antes da assertion localizada. Não cria garantia criptográfica de origem.

**Falhas comuns:** Cast direto pode forjar brand; UserId não equivale a permissão de acessar usuário.

**Escolha:** Usar brands para IDs, moeda/unidades e strings validadas; manter autorização separada.

**Verificação proposta:** Impedir troca de UserId/OrderId no typecheck e rejeitar valor malformado na factory.

**Relações:** ts_schemas; seguranca_authn-authz

**Exemplo local:** exemplos/contratos.ts#UserId

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_variance — Variância e substituição

**Definição:** Covariância preserva direção de subtipagem; contravariância inverte; invariância exige compatibilidade em ambas direções.

**Mecanismo:** Funções recebem e produzem valores; strictFunctionTypes trata certos parâmetros contravariantemente, com exceções como métodos.

**Falhas comuns:** Arrays mutáveis e exceções bivariantes podem permitir situações inseguras; TypeScript é deliberadamente não totalmente sound.

**Escolha:** Expor readonly para consumo, evitar callback excessivamente especializado e conhecer exceções.

**Verificação proposta:** Testar callback que exige subtipo em API que promete aceitar tipo base.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_overloads — Overloads e assinaturas

**Definição:** Overloads descrevem chamadas permitidas; assinatura de implementação precisa servir às alternativas.

**Mecanismo:** Assinatura de implementação não é chamada pública extra; união pode ser mais simples quando retorno não depende da forma de entrada.

**Falhas comuns:** Overloads demais duplicam lógica e podem impedir chamada com união de argumentos.

**Escolha:** Usar overload quando relação entrada/saída precisa dele; preferir generics/união quando clareza melhora.

**Verificação proposta:** Testar todas assinaturas, chamada union e casos negativos com expect-error.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_readonly — Readonly e aliasing

**Definição:** readonly restringe atribuição estática através de referência; não congela valor em runtime.

**Mecanismo:** Readonly<T> é superficial; readonly arrays não expõem mutadores naquela view. Aliases e código JS ainda podem mudar objeto.

**Falhas comuns:** Confiar em readonly para isolamento concorrente ou integridade contra dados externos é incorreto.

**Escolha:** Combinar disciplina de ownership, criação de cópias e freeze quando apropriado.

**Verificação proposta:** Criar alias mutável e observar mudança visível no consumidor readonly.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_null-option — Ausência, null e optional

**Definição:** Optional indica que propriedade pode estar ausente; null e undefined podem ter semânticas distintas.

**Mecanismo:** exactOptionalPropertyTypes diferencia ausência e atribuição explícita undefined; JSON omite undefined em propriedades.

**Falhas comuns:** Usar || como default substitui 0 e false; ?? só trata null/undefined.

**Escolha:** Definir política de ausência por API e persistência, incluindo patch versus remoção.

**Verificação proposta:** Testar missing, undefined, null, 0, false e string vazia.

**Conferência pontual (ver conferencia-fontes-2.json):** ts-optional

**Referências recomendadas:** [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_enum — Enums e literal unions

**Definição:** Enum pode gerar objeto runtime; string literal union descreve opções sem emissão própria.

**Mecanismo:** Numeric enums podem incluir reverse mapping; const enum tem implicações de publicação, inline e compilação isolada.

**Falhas comuns:** Publicar const enum pode causar incompatibilidades entre versões e ferramentas; Object.values de numeric enum inclui nomes/valores.

**Escolha:** Preferir catálogo as const mais union quando suficiente; decidir enum pelo contrato runtime.

**Verificação proposta:** Inspecionar output JS e consumir pacote com configuração de build diferente.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_declarations — Declarações .d.ts e pacotes

**Definição:** Declarações descrevem API JS ao consumidor e precisam corresponder ao artefato publicado.

**Mecanismo:** exports e types direcionam resolução; versões de TS/runtime e ESM/CJS influenciam interoperabilidade.

**Falhas comuns:** Tipos corretos para source podem apontar para arquivo inexistente no tarball ou divergir do runtime.

**Escolha:** Testar instalação do pacote empacotado em projetos consumidores ESM/CJS e typecheck independente.

**Verificação proposta:** Verificar exports, resolução, source maps e declaração de dependências de tipos.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_resolution — moduleResolution e emissão

**Definição:** Resolução modela host/bundler; modo escolhido precisa combinar com module e execução do artefato.

**Mecanismo:** NodeNext considera package type e extensões; bundler admite fluxos diferentes. paths resolve tipos mas não reescreve imports automaticamente.

**Falhas comuns:** Alias que funciona no editor pode falhar no Node compilado; target não fornece polyfills.

**Escolha:** Escolher config pelo ambiente real; documentar transpiler, bundler e runtime separadamente.

**Verificação proposta:** Executar build publicado sem dev server e testar imports/extensões/alias.

**Referências recomendadas:** [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_isolated — Compilação isolada e imports de tipo

**Definição:** Transpiladores por arquivo não têm todas informações de projeto para transformar construções dependentes de tipos.

**Mecanismo:** import type explicita apagamento; verbatimModuleSyntax preserva decisões de import/export conforme configuração.

**Falhas comuns:** Import só de tipo sem marca pode produzir dependência runtime indesejada; transpilar não significa checar tipos.

**Escolha:** Separar pipeline de typecheck e emissão; validar configurações compatíveis com tooling.

**Verificação proposta:** Rodar tsc --noEmit além do bundler e inspecionar imports no JS gerado.

**Referências recomendadas:** [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_dom-types — Tipos de DOM e host

**Definição:** lib seleciona declarações ambientas disponíveis, não instala APIs no ambiente.

**Mecanismo:** Document, window e tipos Node podem conviver e criar ambiguidade de timers/global. querySelector retorna potencialmente null.

**Falhas comuns:** Adicionar DOM a projeto Node pode fazer API ausente passar no compilador.

**Escolha:** Manter tsconfigs por host e tipar elemento depois de validar existência e espécie.

**Verificação proposta:** Testar projeto sem DOM, timer typing e seletor que não encontra elemento.

**Referências recomendadas:** [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_errors-result — Result e erros tipados

**Definição:** Result representa sucesso/falha por união discriminada quando falhas esperadas fazem parte do contrato.

**Mecanismo:** Exceções continuam para defeitos ou fronteiras escolhidas; Promise<T> não expressa tipo da rejeição.

**Falhas comuns:** Capturar tudo em Result sem categorias perde stack e contexto; exception não é tipada automaticamente.

**Escolha:** Diferenciar falha de negócio, transporte e bug; preservar cause e escolher estratégia consistente.

**Verificação proposta:** Testar todos códigos de falha e garantir consumidor trata variante nova.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_schemas — Schema runtime e fonte de verdade

**Definição:** Schema valida valores externos e pode produzir tipo estático por inferência, conforme biblioteca.

**Mecanismo:** Parse deve impor coercion, unknown keys, limites e refinamentos; transformações mudam tipo de entrada/saída.

**Falhas comuns:** Ter interface e schema manual independentes permite divergência; validação de formato não prova regra transacional.

**Escolha:** Derivar DTO do schema quando possível e checar invariantes de domínio após parsing.

**Verificação proposta:** Testar valor boundary, chave extra, tipo errado e transformação não reversível.

**Relações:** ts_apagamento; backend_validation

**Exemplo local:** exemplos/padroes.mjs#parseUser

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_type-tests — Testes de tipos

**Definição:** Fixtures de compilação verificam inferência, chamadas proibidas e API pública.

**Mecanismo:** @ts-expect-error falha quando diagnóstico esperado desaparece, mas não garante qual diagnóstico ocorreu sem ferramenta adicional.

**Falhas comuns:** Só testar runtime deixa regressão de API tipada passar; snapshot de tipo pode depender da versão.

**Escolha:** Separar testes positivos/negativos com linhas pequenas e versão TS registrada.

**Verificação proposta:** Executar tsc strict sobre consumidor externo e fixture inválida por razão única.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_type-performance — Performance do compilador

**Definição:** Tipos recursivos, intersections profundas e unions combinatórias aumentam tempo/memória de checking.

**Mecanismo:** extendedDiagnostics e traces ajudam localizar custo; fronteiras nomeadas e interfaces podem reduzir recomputação em casos específicos.

**Falhas comuns:** Tipo sofisticado pode inviabilizar editor sem melhorar contrato real; otimização depende da versão.

**Escolha:** Medir antes/depois e limitar complexidade exposta; não micro-otimizar sem evidência.

**Verificação proposta:** Comparar incremental e build limpo, tempo de check e memória com dados de escala.

**Referências recomendadas:** [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_boundary-dto — DTO de entrada, domínio e saída

**Definição:** DTO descreve contrato de transporte; entidade/value object representa invariantes internas; DTO de saída define informação autorizada.

**Mecanismo:** Transformação explícita permite omitir secrets e campos internos; tipo de entidade não deve ser serializado indiscriminadamente.

**Falhas comuns:** Retornar objeto inteiro inclui senha hash, flags internas ou tenant indevido; Partial<Entity> aceita mudanças proibidas.

**Escolha:** Schemas por operação e mapper de saída com allowlist; distinguir leitura/escrita.

**Verificação proposta:** Adicionar secret à entidade e garantir que response schema/body não muda.

**Relações:** seguranca_privacy

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_patch-model — Modelagem de PATCH

**Definição:** Patch precisa separar manter, substituir e remover conforme significado do campo.

**Mecanismo:** União de operações ou schema com política explícita evita confundir missing, undefined e null.

**Falhas comuns:** Partial permite combinações de negócio inválidas; merge genérico pode habilitar mass assignment.

**Escolha:** Definir patch por caso de uso e validar transição após aplicar.

**Verificação proposta:** Testar field ausente, remoção proibida, valor nulo permitido e chave desconhecida.

**Relações:** ts_null-option

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_opaque-constructor — Construtores de valores opacos

**Definição:** Factory valida e produz tipo de domínio; construtor público cru pode invalidar invariant.

**Mecanismo:** Brand é barreira estática leve; encapsulamento e métodos podem adicionar checagens runtime.

**Falhas comuns:** Exportar assertion genérica brand<T> permite criar qualquer valor sem prova.

**Escolha:** Exportar factories específicas, manter cast privado e preservar representação validada.

**Verificação proposta:** Testar entrada malformada e consumidor tentando montar valor sem factory.

**Relações:** ts_brands

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_async-result — Result em operações assíncronas

**Definição:** Promise<Result<T,E>> separa falha esperada de rejeição por defeito/infra conforme contrato escolhido.

**Mecanismo:** Consumidor trata ok/tag depois de await; mapper de erro conserva causa e categorias.

**Falhas comuns:** Marcar toda exceção como erro de negócio pode ocultar bug; Promise<Result> ainda pode rejeitar se implementação lança.

**Escolha:** Documentar se API nunca rejeita ou permite erro inesperado e testar ambos.

**Verificação proposta:** Simular validação, indisponibilidade e defeito de programação; verificar categoria correta.

**Relações:** ts_errors-result

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_contravariance — Contravariância de callback

**Definição:** Callback que API chama com Base precisa aceitar todo Base prometido, não apenas subtipo restrito.

**Mecanismo:** strictFunctionTypes ajuda para propriedades de função; métodos possuem concessões de bivariance.

**Falhas comuns:** Callback que exige Derived.foo quebra quando API entrega Base; método pode esconder a incompatibilidade.

**Escolha:** Preferir contratos de função explícitos e teste negativo de consumidores.

**Verificação proposta:** Compilar callback estreito em propriedade function e comparar com sintaxe de método.

**Relações:** ts_variance

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_function-this — Parâmetro this e bindings

**Definição:** TypeScript pode declarar tipo do this de função ordinária e checar uso em contexto.

**Mecanismo:** Parâmetro this é apagado; noImplicitThis detecta algumas ambiguidades. Arrow possui captura lexical.

**Falhas comuns:** Tipar this não faz bind no runtime; método extraído pode executar com undefined.

**Escolha:** Declarar this quando API depende de receptor e bind ao passar callback.

**Verificação proposta:** Compilar chamada sem receiver e executar extração em JS.

**Relações:** js_this

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_satisfies-palette — Config autoral sem perder precisão

**Definição:** satisfies verifica shape mantendo informação inferida útil, sujeito ao contexto da expressão.

**Mecanismo:** Catálogo pode conservar chaves e valores específicos; annotation explícita pode ampliar tipo observado.

**Falhas comuns:** Confundir satisfies com assertion de dado externo ignora que nenhuma validação runtime ocorre.

**Escolha:** Usar em registry interno e schema runtime para entradas; testar tipo resultante.

**Verificação proposta:** Verificar typo em chave e acesso a membro específico do valor inferido.

**Relações:** ts_satisfies

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_freshness — Freshness e index signatures

**Definição:** Excess-property checking é uma verificação contextual de certos literals, não uma regra de selamento estrutural.

**Mecanismo:** Objeto de variável com campos extras pode ser atribuído; index signature permite conjunto mais aberto.

**Falhas comuns:** Exact<T> artificial por utility pode criar mensagens ruins e não validar runtime.

**Escolha:** Definir política de unknown keys no parser e tipos claros para registros abertos.

**Verificação proposta:** Comparar literal/variável e payload JSON com campo admin inesperado.

**Relações:** ts_structural

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_recursive-schema — Schemas recursivos

**Definição:** Estrutura recursiva pode ser descrita por tipo, mas parser runtime precisa limites de profundidade/tamanho.

**Mecanismo:** Referência lazy resolve declaração de schema; parsing profundo ainda consome stack/tempo.

**Falhas comuns:** Tipo recursivo aceito não impede ciclo de objeto runtime nem nesting hostil.

**Escolha:** Impor budget e usar traversal iterativo quando necessário; distinguir JSON acíclico de objetos gerais.

**Verificação proposta:** Testar nesting grande, ciclo e total de nós máximo.

**Relações:** ts_schemas

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_exact-errors — Códigos de erro estáveis

**Definição:** Erro público deve ter código estável e payload permitido; mensagem humana não é protocolo confiável.

**Mecanismo:** União por code descreve campos específicos e permite handling exaustivo.

**Falhas comuns:** Cliente que depende de texto traduzido quebra; stack/cause não deve ser enviado automaticamente.

**Escolha:** Separar internal Error de public error DTO e mapping auditável.

**Verificação proposta:** Adicionar código novo e verificar consumidor obrigatório; validar redaction.

**Relações:** ts_unioes

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_state-events — Eventos ligados a estado

**Definição:** Tipos podem representar eventos/transições, mas objeto mutável complexo pode exigir máquina runtime.

**Mecanismo:** Reducer com discriminantes garante handling; guard runtime protege evento de origem externa.

**Falhas comuns:** Assinar evento com as ignora estado atual; tipar dispatch não garante sequência legal.

**Escolha:** Tabela de transições e invariantes com efeito fora do reducer.

**Verificação proposta:** Gerar sequências incluindo eventos inválidos e exigir estado válido sempre.

**Relações:** frontend_react-reducer

**Exemplo local:** exemplos/engenharia.mjs#transition

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_index-totality — Acesso indexado e totalidade

**Definição:** Array/record podem não conter chave solicitada; tipo de acesso deve refletir ausência.

**Mecanismo:** noUncheckedIndexedAccess amplia para undefined onde não há prova de presença; bounds check nem sempre estreita como esperado.

**Falhas comuns:** Non-null assertion depois de check errado transforma exceção em promessa de segurança.

**Escolha:** Retornar Option/Result ou testar valor local capturado; preferir APIs totalizadas.

**Verificação proposta:** Testar array vazio, buracos, chave inexistente e valor undefined presente.

**Relações:** ts_keyof

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_awaited — Awaited e inferência assíncrona

**Definição:** Awaited modela unwrap recursivo de awaitables segundo transformação estática definida.

**Mecanismo:** Retornos de combinadores inferem tuplas/uniões conforme tipos e versão; input unknown continua unknown.

**Falhas comuns:** Criar PromiseValue que só unwrap uma camada diverge de nested thenables e unions.

**Escolha:** Usar utility documentada e fixtures do caso real.

**Verificação proposta:** Compilar Promise aninhada, union com valor direto, never e unknown.

**Relações:** ts_infer

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_utility-depth — Utilities superficiais e profundas

**Definição:** Readonly/Partial/Required transformam camada de propriedades, não grafo inteiro.

**Mecanismo:** Deep utilities precisam política para Map/Set, funções, arrays, tuples e classes.

**Falhas comuns:** DeepReadonly ingênuo pode quebrar métodos de classe e não corresponder a freeze runtime.

**Escolha:** Definir domínio de aplicação da utility e limitar complexidade de tipos.

**Verificação proposta:** Testar tuple, callback, classe, optional e nested array.

**Relações:** ts_mapped

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_union-correlation — Correlação em uniões

**Definição:** Union de pares relacionados conserva vínculo; dois campos com unions independentes permitem combinações ilegais.

**Mecanismo:** Destructuring/narrowing preserva correlação em alguns padrões/versões, mas extrações genéricas podem perdê-la.

**Falhas comuns:** Evento com kind numérico e payload string pode ser aceito em megaobjeto de tipos independentes.

**Escolha:** Modelar cada variante completa e dispatch após narrowing claro.

**Verificação proposta:** Compilar pares incompatíveis e validar runtime em entrada externa.

**Relações:** ts_unioes

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_literal-widening — Widening e inferência de literais

**Definição:** Tipo literal pode ampliar para string/number conforme mutabilidade e contexto.

**Mecanismo:** const binding e as const afetam inferência de formas distintas; const type parameters dependem da versão TS.

**Falhas comuns:** Generic que deveria preservar rota pode inferir string amplo; as const não congela runtime.

**Escolha:** Controlar contextual typing com intenção e verificar API pública inferida.

**Verificação proposta:** Comparar const object, as const, satisfies e generic com fixture de inferência.

**Relações:** ts_satisfies

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_distributive-never — never e distribuição

**Definição:** never é união vazia; conditional distributivo sobre ele pode resultar em never sem avaliar branch intuitiva.

**Mecanismo:** Wrapper tuple muda teste para o conjunto inteiro; diferenças importam em utilities de detecção.

**Falhas comuns:** IsNever<T> escrito T extends never pode não retornar true para never.

**Escolha:** Testar utilities com never/any/unknown e unions, sem assumir álgebra ideal em any.

**Verificação proposta:** Compilar tabela de resultados e checar constraints do domínio aceito.

**Relações:** ts_conditional

**Conferência pontual (ver conferencia-fontes-2.json):** ts-distribution

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_types-serialization — Serialização e tipo de saída

**Definição:** Tipo TS não implica que valor é serializável para JSON ou boundary framework.

**Mecanismo:** Date vira string em JSON; BigInt pode lançar; funções/undefined podem ser omitidos; cycles falham.

**Falhas comuns:** Retornar T depois de JSON roundtrip afirma equivalência falsa.

**Escolha:** Definir DTO serializável e decoder de retorno; testar transformações com tipos reais.

**Verificação proposta:** Roundtrip de Date/BigInt/undefined/ciclo e comparação por contrato.

**Relações:** js_json

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_ambient-globals — Globals e declaração ambiente

**Definição:** declare informa checker de símbolo supostamente existente, sem emitir implementação.

**Mecanismo:** Global augmentation e múltiplos @types podem alterar projeto inteiro e produzir conflitos.

**Falhas comuns:** declare const window faz compilar em Node mas não cria window; ambient declaration incorreta esconde defeito.

**Escolha:** Isolar tipos por host e usar imports explícitos quando possível.

**Verificação proposta:** Executar artefato em host prometido e compilar sem tipos de outro ambiente.

**Relações:** ts_dom-types

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_declaration-merging — Declaration merging e augmentation

**Definição:** Certas declarações compatíveis se fundem; module augmentation amplia tipos de módulo existente.

**Mecanismo:** Ampliação precisa estar no programa e corresponder a código/runtime que realmente adiciona comportamento.

**Falhas comuns:** Adicionar método a interface sem implementar prototype/factory cria API inexistente.

**Escolha:** Usar augmentation pequena e empacotada com implementação comprovada.

**Verificação proposta:** Compilar consumidor e invocar membro no artefato publicado.

**Relações:** ts_declarations

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_compiler-api — Compiler API e transformações

**Definição:** TypeScript Compiler API oferece AST, checker e emissão para tooling.

**Mecanismo:** SyntaxKind e node factories têm contratos versionados; checker fornece símbolos/tipos para refactor.

**Falhas comuns:** Editar AST sem maps ou usar node/text offsets stale pode perder comments e alterar código errado.

**Escolha:** Fixar versão suportada e testar transform com golden fixtures e typecheck.

**Verificação proposta:** Testar aliases, overloads, comentários e transform idempotente.

**Relações:** fronteira_incremental-types

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_project-references — Project references e build

**Definição:** References organizam compilação de projetos dependentes com fronteiras e artefatos.

**Mecanismo:** composite/declaration e tsc -b suportam build incremental; configs devem refletir grafo verdadeiro.

**Falhas comuns:** Ciclo entre projetos ou source import fora da boundary impede modularidade; cache stale pode mascarar.

**Escolha:** Separar configs por pacote/host e testar clean build junto de incremental.

**Verificação proposta:** Remover outputs/cache e reconstruir; comparar artefatos e ordem.

**Relações:** ts_resolution

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_ts-runtime-tests — Separar typecheck e execução

**Definição:** Typecheck cobre certos usos de API; runtime testa semântica/efeitos de valores concretos.

**Mecanismo:** Transpilers rápidos podem não checar tipos; tsc --noEmit não executa programa.

**Falhas comuns:** Testes runtime verdes com types errados quebram consumidor; tipos verdes com parser falso permitem entrada inválida.

**Escolha:** Executar ambos e manter fixtures de consumidores externos.

**Verificação proposta:** Introduzir typo de tipo e bug runtime separadamente; cada check deve detectar seu eixo.

**Relações:** ts_type-tests

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_const-enum-publish — const enum e publicação

**Definição:** const enum pode ser inlined e não existir como objeto runtime; toolchains diferem.

**Mecanismo:** Consumidor pode inline versão antiga contra JS novo; isolatedModules e ambient const enums geram restrições.

**Falhas comuns:** Assumir tree shaking resolve todos riscos de const enum público ignora compatibilidade.

**Escolha:** Preferir union/catalog as const para biblioteca quando runtime identity não é necessária.

**Verificação proposta:** Consumir versões divergentes e transpiler isolado; inspecionar output.

**Relações:** ts_enum

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_overload-inference — Inferência em overloads

**Definição:** Utilities que inferem função sobreloaded geralmente consideram assinatura de forma específica, frequentemente última.

**Mecanismo:** Tipo de retorno extraído não equivale necessariamente ao retorno de cada call escolhido por overload resolution.

**Falhas comuns:** ReturnType usado como prova de todos casos pode ampliar ou perder relação entrada/saída.

**Escolha:** Publicar tipos auxiliares claros e testar calls concretas.

**Verificação proposta:** Comparar ReturnType com chamadas específicas e argumentos union.

**Relações:** ts_overloads

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_nominal-runtime — Brand estática e nominalidade runtime

**Definição:** Brand protege troca acidental no checker; não carrega autenticação nem necessariamente marcador real.

**Mecanismo:** unique symbol usado apenas em tipo é apagado; instance checks exigem representação runtime correspondente.

**Falhas comuns:** Teste in brand pode falhar se brand nunca foi atribuído; forged cast passa checker.

**Escolha:** Escolher marca só estática ou objeto runtime e documentar invariantes separados.

**Verificação proposta:** Comparar valor serializado e reconstrução via factory; testar cast fora do escopo confiável.

**Relações:** ts_brands

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_type-erasure-security — Tipos não são controle de acesso

**Definição:** Permissão expressa em tipo ajuda desenho interno, mas request direto ignora tipagem do cliente.

**Mecanismo:** Servidor valida principal e recurso a cada boundary; token de capability precisa integridade no runtime.

**Falhas comuns:** AdminUser tipo em frontend não impede chamada por atacante; brand de Authorized não substitui verificação.

**Escolha:** Centralizar authorization e emitir resultado de política a partir de fonte confiável.

**Verificação proposta:** Executar request sem UI com papel inadequado e trocar IDs.

**Relações:** seguranca_authn-authz

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_type-test-errors — Fixtures negativas específicas

**Definição:** @ts-expect-error confirma existência de algum diagnóstico na linha, não necessariamente o erro pretendido.

**Mecanismo:** Cada fixture deve ter motivo isolado e linha válida no restante; ferramentas de assertion de tipo refinam evidência.

**Falhas comuns:** Uma importação quebrada pode fazer expect-error passar pela razão errada.

**Escolha:** Usar fixtures mínimas e teste positivo vizinho; revisar diagnóstico de forma deliberada.

**Verificação proposta:** Remover proteção específica e verificar que expect-error se torna unused.

**Relações:** ts_type-tests

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_generic-defaults — Defaults e constraints genéricas

**Definição:** Default define tipo quando argumento não é informado/inferido; constraint limita formas aceitas.

**Mecanismo:** Default precisa satisfazer constraint; inferência pode substituir default conforme call.

**Falhas comuns:** Default any enfraquece contrato; constraint ampla permite operações só da base, não das extensões.

**Escolha:** Escolher defaults seguros como unknown onde apropriado e manter relação explícita.

**Verificação proposta:** Compilar chamada sem tipo, inferida e explicitamente inválida.

**Relações:** ts_generics

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_builder-protocol — Builders e protocolo de construção

**Definição:** Builder pode representar etapas obrigatórias e evitar build antes de configuração mínima.

**Mecanismo:** Tipo por estado ou retorno de interface especializada expressa protocolo; runtime ainda valida quando entrada arbitrária.

**Falhas comuns:** API fluent com casts infinitos finge garantir passo obrigatório; reaproveitar builder mutável vaza estado.

**Escolha:** Usar builder só quando há etapas reais; preferir factory simples para construção pequena.

**Verificação proposta:** Compilar build prematuro e executar reuse/config inválida.

**Relações:** corretude_design-by-contract

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

## ts_type-budget — Orçamento de complexidade de tipos

**Definição:** Abstração de tipos tem custo em compiler/editor e compreensão humana.

**Mecanismo:** Recursão, unions grandes e interfaces públicas instanciadas muitas vezes afetam check; medir extendedDiagnostics.

**Falhas comuns:** Tornar todos invariantes type-level pode gerar sistema lento e pouco usável, sem garantia runtime.

**Escolha:** Distribuir provas entre tipos simples, validação runtime e testes; limitar recursão documentada.

**Verificação proposta:** Comparar clean/incremental e consumo de memória com projeto consumidor representativo.

**Relações:** ts_type-performance

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html); [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/)

