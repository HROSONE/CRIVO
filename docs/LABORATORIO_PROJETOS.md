# Laboratório de módulos JavaScript e TypeScript

O objetivo é começar a medir composição de módulos e reparo em pequenos projetos, além de funções isoladas. Esta primeira versão contém **16 miniprojetos autorais de dois arquivos**: 6 de treino, 2 de validação e 8 de teste (4 famílias reservadas, cada uma em JS e TS). Não representa APIs completas em produção nem comprova capacidade de programador sênior.

As famílias de treino são validação de pedidos, processamento de linhas e tentativas assíncronas; a validação usa carrinho com descontos. O teste usa codificação de query strings, autorização por permissões, transações de estoque e slugs Unicode. As entradas exercitam casos vazios, duplicatas, entradas inválidas, ordem e limites. Cada projeto tem um módulo de regra e um módulo de entrada que o importa. TypeScript usa contratos explícitos e compilação estrita.

## Geração e reparo

`laboratorio_projetos.py` gera um arquivo por vez, fornecendo o contrato e os módulos já escritos. Nos reparos também fornece a versão anterior do arquivo e o diagnóstico dos casos de desenvolvimento. O candidato recebe no máximo duas oportunidades de reparo. Contratos, módulos e diagnósticos que excedem o contexto causam erro explícito, sem corte silencioso. O contexto de 512 tokens do modelo atual provavelmente limitará vários reparos; o relatório registra essa limitação.

Os casos reservados são executados **depois** de encerrar os reparos. Seus diagnósticos não retornam ao modelo. O relatório preserva todos os módulos gerados, verificações, acerto da primeira tentativa, acerto final e projetos reparados. Geração incompleta nunca conta como acerto. A métrica inicial não aumenta quando o reparo funciona.

Execução exige Node em bubblewrap, sem rede, home ou workspace do host, com módulos somente leitura e `/tmp` efêmero. O harness recebe apenas entradas, nunca valores esperados. Há limites de CPU, tempo, memória e saída. Compilação TS e análise de sintaxe JS não executam módulos. Quando namespaces são indisponíveis, a avaliação para; não existe execução de projetos no host nem substituição de APIs Node por QuickJS. O workflow usa Ubuntu 22.04 e verifica o isolamento com execução real.

Este é um benchmark funcional, não uma análise de resistência a candidatos deliberadamente adversariais: o código executado compartilha processo com o harness. Testes e referências são públicos no repositório, por isso a reserva é em relação à preparação de treino, não sigilo. Não há revisão independente nem garantia de ausência de sobreposição semântica com bibliotecas externas.

## Dados de treino

`exemplos_projetos()` fornece **32 instruções** de criação e reparo somente das famílias de treino e validação. O reparo apresenta um módulo ainda não implementado e a exportação ausente. Os alvos são implementações completas; a integração Node verifica suas referências. As famílias de teste e suas referências são excluídas desse exportador. `preparar_codigo_real.py` inclui essas instruções nas próximas preparações, preservando partições, amostragem por família e hashes de procedência. O treino já em execução usa seu checkout anterior e não é alterado por esta mudança.

Não ampliamos parâmetros ou contexto antes de observar as métricas; o laboratório permite medir onde a arquitetura atual falha. Não há ativação automática de pesos.

## Executar

Conferir referências e testes reais em um Linux com namespaces habilitados:

```bash
CRIVO_LAB_NODE=1 CRIVO_TSC=/tmp/ts/node_modules/typescript/lib/tsc.js python -m unittest testes_laboratorio_projetos -v
python scripts/avaliar_projetos.py --referencias --tsc /tmp/ts/node_modules/typescript/lib/tsc.js --saida /tmp/laboratorio/referencias.json
```

Avaliar candidato já treinado:

```bash
python scripts/avaliar_projetos.py --modelo /caminho/candidato/melhor --tsc /tmp/ts/node_modules/typescript/lib/tsc.js --reparos 2 --saida /tmp/laboratorio/candidato.json
```

O workflow **Laboratório de projetos JS e TS** valida referências em PRs. Via `workflow_dispatch`, `run_candidato` identifica um treino concluído com artefato `crivo-codigo-real-ID`. O workflow baixa esse artefato, avalia `candidato/melhor` em CPU e preserva relatórios por 30 dias. Campo vazio apenas verifica as referências. Não inicia novo treino.
