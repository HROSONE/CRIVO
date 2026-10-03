# Fichas avançadas: typescript

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## ts_apagamento — Apagamento de tipos

**Definição:** TypeScript verifica código estaticamente e normalmente remove anotações na emissão; não valida dados no runtime.

**Mecanismo:** Tipos não alteram automaticamente representação de valores; interface/type desaparecem. Algumas construções como enums podem emitir JS.

**Falhas comuns:** JSON.parse tipado por as Usuario continua aceitando payload inválido; compilação bem-sucedida não garante ausência de erro.

**Escolha:** Tratar toda fronteira externa como unknown e validar antes de construir tipo de domínio.

**Verificação proposta:** Enviar payload faltando campo e verificar rejeição real; inspecionar JS emitido.

**Referências recomendadas:** [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)

## ts_strict — Configuração estrita

**Definição:** strict ativa família de checagens, incluindo null e parâmetros implícitos; opções adicionais tratam índices e propriedades opcionais.

**Mecanismo:** noUncheckedIndexedAccess adiciona undefined ao acesso não provado; exactOptionalPropertyTypes distingue ausência de propriedade de valor undefined.

**Falhas comuns:** strict sozinho não elimina any, assertions, limites do sistema nem dados externos inválidos.

**Escolha:** Adotar strict e opções adicionais conforme baseline; migrar por módulo sem silenciar diagnósticos globalmente.

**Verificação proposta:** Compilar fixtures de null, índice fora de faixa, optional undefined e catch unknown.

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

**Pré-requisitos:** ts_narrowing, ts_unknown-any

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

**Pré-requisitos:** ts_generics, ts_unioes

**Relações:** ts_infer, ts_type-performance

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

**Relações:** ts_schemas, seguranca_authn-authz

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

**Relações:** ts_apagamento, backend_validation

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


