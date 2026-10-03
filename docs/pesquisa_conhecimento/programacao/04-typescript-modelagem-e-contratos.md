# TypeScript: modelar estados e estabelecer fronteiras

## Da entrada unknown ao estado válido
A aplicação recebe bytes e valores, não tipos confiáveis. O ciclo é parse, limite de tamanho, validação de estrutura, normalização explícita, criação de valor de domínio, regra de negócio, transação e serialização. Um type assertion não executa nenhuma destas etapas.

```ts
type Pedido =
  | { estado: 'rascunho'; itens: readonly string[] }
  | { estado: 'confirmado'; itens: readonly string[]; pagamentoId: string }
  | { estado: 'cancelado'; motivo: string };

function descrever(p: Pedido): string {
  switch (p.estado) {
    case 'rascunho': return String(p.itens.length);
    case 'confirmado': return p.pagamentoId;
    case 'cancelado': return p.motivo;
    default: return impossivel(p);
  }
}
function impossivel(x: never): never {
  throw new Error('Estado não reconhecido');
}
```
Esta união elimina determinadas combinações estáticas, mas não autentica pagamento nem valida objeto vindo de JSON. A função impossivel fornece falha runtime se a fronteira foi violada; a prova estática depende de entrada honestamente tipada.

## Configuração e efeitos observáveis
Use strict. Considere noUncheckedIndexedAccess, exactOptionalPropertyTypes e useUnknownInCatchVariables. Compile em configuração separada por host. Para Node ESM escolha module/moduleResolution compatíveis e teste extensão no output. Para bundler escolha configuração coerente com bundler e rode typecheck independente. paths não é reescritor runtime.

## Relações de tipos
Generic deve preservar relação: get<T,K extends keyof T>(obj:T,key:K):T[K]. Se T só aparece no retorno, pergunte de onde vem sua prova. Condicionais distributivas operam em cada membro de união; tuple wrapper impede distribuição. Intersections exigem cumprir ambos contratos, podendo resultar em propriedade never. Tipos muito complexos precisam orçamento de tempo de compilação.

## Designs que escondem bugs
Partial<Entidade> como DTO de patch pode permitir apagar campo indevidamente; readonly não congela grafo; structural compatibility não estabelece identidade/autorização; branded ID não é credencial; satisfies verifica expressão autoral, não payload externo; excess property checks não selam objetos.

Separe DTO de escrita/leitura, entidade e valor de domínio. Para patch defina operações como manter/substituir/remover, incluindo distinção entre null e ausência. Para IDs de contextos diferentes, brand com factory validada reduz troca acidental. Centralize casts inevitáveis em boundary pequena com teste.

## Biblioteca consumível
Avalie JS emitido, declaration files e export maps no pacote publicado, não só source tree. Teste consumidores ESM/CJS se prometer ambos. Documente versão mínima de TS e runtime. Um pacote que compila mas não resolve imports no consumidor ainda está quebrado.

## Critério de domínio
A partir de requisito, propor união que impossibilite estados inválidos; rejeitar payload hostil; demonstrar narrowing e limite de aliasing; explicar variância; justificar generic; compilar fixture de consumidor e testes negativos. O sistema de tipos é ferramenta de engenharia e possui concessões de soundness documentadas.

