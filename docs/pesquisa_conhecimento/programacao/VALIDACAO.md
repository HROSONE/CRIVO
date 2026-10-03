# Validação da segunda ampliação — 03/10/2026

## Executado nesta revisão
- Node.js **v24.19.0**: 27 testes iniciais + 31 testes de engenharia + oito testes do JavaScript emitido de TypeScript = **66 testes aprovados**, sem falhas ou skips.
- TypeScript **5.9.3**: typecheck strict de contratos.ts, modelagem.ts e modelagem.types.ts. noUncheckedIndexedAccess, exactOptionalPropertyTypes, useUnknownInCatchVariables; lib ES2022.
- Emissão TypeScript para diretório temporário e execução do módulo compilado. Pacote/lock/runtime do CRIVO não foram alterados para instalar compilador.
- **Dez regressões Python aprovadas**: preservação de operadores/C++/C#, filtro de domínio, duplicação/links inválidos, ciclos, fonte/schema, paths/traversal/symlinks, profundidade de grafo, adulteração de Markdown/hash, validação sob Python -O, rebuild determinístico e export JSONL.
- Validador de catálogo/manifesto aprovado: **300 fichas, 22 domínios, 44 referências e 60 desafios**, relações válidas, exportação exata e hashes.
- Busca JS/TS, grafo por ID e exportação por domínio verificadas. Busca lexical não equivale a retrieval semântico.
- **Seis consultas pontuais** à documentação oficial de TypeScript/Node com HTTP 200 e revisão do tema: assertions apagadas, conditional distributivo, optional exato, EventEmitter síncrono, write/drain e AbortSignal/listener cleanup. URLs, hashes e escopo em conferencia-fontes-2.json.

## Melhoria frente à primeira revisão
Typecheck deixou de ser pendência. Validação não usa assert e continua ativa sob Python -O.
Markdown agora é gerado deterministicamente do catálogo e comparado por conteúdo completo;
manifesto compara inventário/bytes/hashes; paths fora do escopo são recusados. Regressões de
tooling usam cópia isolada só do acervo, sem copiar modelos e histórico da aplicação.

## Limites
Revisão integral de todas as fontes/fichas continua pendente; seis temas corroborados não
validam todas as afirmações da unidade nem toda documentação. Páginas consultadas são
referências vivas; hash registra resposta desta consulta, não permanência do documento remoto.

Não houve treinamento, alteração de roteador/runtime, avaliação de geração do CRIVO,
benchmark de senioridade nem regressão geral da aplicação. Os testes verificam exemplos
didáticos e curadoria. SQL dos capítulos é ilustrativo e não foi executado em banco real.

Desafios são públicos/didáticos, não holdout. JSON/Markdown duplicam os mesmos 300 conceitos.
Reconstruir hashes após revisão é operação de curadoria; hash não demonstra veracidade.
Os exemplos têm limites de segurança, concorrência, escala e host descritos no README local.

## Reprodução
Ver comandos em [exemplos/README.md](exemplos/README.md) e [README do acervo](README.md).
Compilador foi instalado em cache temporário, com versão fixada 5.9.3; artifacts emitidos
não foram publicados como parte do código do CRIVO.
