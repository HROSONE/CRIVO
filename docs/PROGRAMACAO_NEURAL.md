# Programação: acervo ativo e Transformer próprio

A consulta do Crivo agora usa as 300 fichas do catálogo de programação, com
fontes e SHA-256 registrados no histórico. As respostas introdutórias existentes
continuam prioritárias; a consulta avançada preenche lacunas. Exemplo:
`Explique event loop em JavaScript` e `Como funciona conditional types em TS?`.
O catálogo não entra em bases personalizadas que não o contenham.
A seleção lexical exige termos do título e respeita JS/TS. Não é compreensão
semântica completa: comparações, formulações ambíguas e retomadas podem não casar.
A revisão editorial integral do acervo continua pendente.

Os campos de estado do catálogo original e seu manifesto descrevem o snapshot
de pesquisa preservado. O consumidor de runtime é `conhecimento_programacao.py`;
o corpus e os relatórios abaixo registram a integração e o treino posteriores.
O pacote da API Vercel inclui explicitamente o catálogo, sem instalar PyTorch.

## Resultado efetivamente medido em 03/10/2026

Treino piloto **executado**, em CPU, com o Transformer próprio de **2.612.352
parâmetros**, inicializado do checkpoint de diálogo existente. Foram 200 passos,
lote 4, LR 0,0001, 204.800 tokens de entrada e 55.939 tokens de alvo, em 86,92 s.
O tokenizer original foi preservado byte a byte. Não foram baixados pesos externos.

| Medida | Antes | Depois |
| --- | ---: | ---: |
| Perplexidade de diálogo, validação | 308,41 | 103,74 |
| Perplexidade de linguagem, validação | 299,19 | 77,49 |
| Exercícios JS que compilam, teste | 0/8 | 0/8 |
| Exercícios TS que compilam, teste | 0/8 | 0/8 |
| Gerações JS que terminam | 4/8 | 8/8 |
| Gerações TS que terminam | 6/8 | 8/8 |

**Não aprovado para ativação normal.** Melhor perda e término não comprovam
correção. Nenhuma geração inicial compilou. A avaliação registra pass@1 = 0
para esse conjunto; não houve execução de candidatos. O host também bloqueou
namespaces bubblewrap, portanto a execução funcional isolada permanece pendente.
As 40 respostas de referência JS/TS compilam. O benchmark é pequeno e sintético,
não certifica programação sênior, projetos completos nem capacidade de fronteira.

Os pesos candidatos estão em `artefatos/programacao_experimental/`, separados
dos pesos gerais. O checkpoint completo de Adam/RNG permanece em
`/workspace/crivo-candidato/checkpoint.pt` nesta sessão. O workflow manual publica
checkpoint, corpus e relatórios como artefatos, com retenção de 30 dias.

Relatórios com saídas reais e hashes: [baseline](resultados/programacao/baseline.json),
[candidato](resultados/programacao/candidato.json),
[corpus](resultados/programacao/corpus.json),
[referências](resultados/programacao/referencias.json).

## Dados e separação

`dados/programacao/tarefas.json` contém 40 exercícios: JS/TS de 20 famílias.
8 famílias são treino, 4 validação e 8 teste. As duas linguagens da mesma família
ficam juntas. Os 60 desafios públicos antigos não foram usados como avaliação.
O preparador acrescenta quatro operações didáticas por unidade do catálogo:
definição, mecanismo, cuidados e verificação. Famílias e respostas duplicadas
não atravessam partições. O resultado é 988 exemplos de treino, 96 de validação
e 156 de teste. Isso é um currículo inicial autoral, não um corpus de escala LLM.

Em avaliação, a geração recebe somente o contrato da tarefa. Não há retrieval
do catálogo reservado nem acesso à implementação de referência. Uma tentativa
extra pode receber o código anterior e diagnóstico de compilação/teste. Reparo
que excede o contexto é registrado como recusado; nenhum contrato é truncado.
A métrica pass@1 usa apenas a primeira geração completa e funcionalmente correta.
Os resultados de reparo são contados separadamente.

As perdas de treino misturam SFT com 20% de passos de linguagem **do mesmo corpus
de programação**; isso não prova preservação das capacidades gerais. Regressão
geral do modelo candidato e revisão independente são requisitos pendentes.
A suíte do motor determinístico é uma verificação diferente.

## Experimentar e reproduzir

Python 3.11+, torch CPU e tokenizers são dependências opcionais do laboratório.
O motor normal continua funcionando sem elas. Node e TypeScript são necessários
para a avaliação de código; fixe a versão do compilador.

```sh
python -m pip install 'torch>=2.2,<3' --index-url https://download.pytorch.org/whl/cpu
python -m pip install 'numpy>=1.24,<3' 'tokenizers>=0.20,<1'
npm install --prefix /tmp/ts typescript@5.9.3
python scripts/treinar_programacao.py --perfil atual --passos 200 \
  --saida /tmp/ciclo-programacao --tsc /tmp/ts/node_modules/typescript/lib/tsc.js
python programacao_neural.py --modelo artefatos/programacao_experimental \
  --mensagem 'Em javascript, implemente function resolver(n) para dobrar n. Retorne somente código.'
python web_local.py --modelo-programacao artefatos/programacao_experimental \
  --programacao-experimental
```

O último comando disponibiliza a geração no chat local, claramente rotulada como
experimental e não verificada. O cliente HTTP não pode escolher modelos nem caminhos.
O chat não executa código gerado. Sem `--programacao-experimental`, o servidor exige
`--relatorio-programacao` aprovado, com hashes do modelo/tokenizer/tarefas correspondentes.
A geração ainda é limitada ao contexto de 256 tokens do candidato; projetos longos
exigem ampliar contexto e treinar, além de ferramentas de edição e execução.

Retomada exata do piloto desta sessão, com o código e o corpus originais:

```sh
python scripts/treinar_linguagem_profunda.py --corpus /workspace/crivo-corpus \
  --saida /workspace/crivo-candidato --fase dialogo --retomar --passos 200 \
  --lote 4 --lr .0001 --avaliar-a-cada 100 --salvar-a-cada 100
```

Para continuar com novo horizonte de LR, prepare uma nova etapa com `--inicial`
e `--ajustar-proprio`; a retomada conserva o horizonte original. Essa opção
exige arquitetura e tokenizer idênticos e registra o hash do checkpoint anterior.
A opção `--inicial` sem ajuste mantém as restrições antigas do pré-treino/SFT.

## Escala gradual

| Perfil | Parâmetros com vocab. 4096 | Dimensão/camadas | Contexto |
| --- | ---: | --- | ---: |
| atual | 2.612.352 | 192 / 4 | 256 |
| 10m | 10.634.880 | 384 / 5 | 512 |
| 30m | 27.563.008 | 512 / 8 | 512 |

As contagens foram conferidas instanciando as três arquiteturas. Só o perfil
atual recebeu o ajuste publicado. Os maiores iniciam pré-treino do zero;
nenhum peso é ampliado por cópia. O tokenizer novo pode ter menos de 4096 tokens;
a contagem real fica no relatório do treinador. `escalar_programacao.py` informa
memória mínima de pesos/gradientes/Adam, sem incluir ativações e runtime.

O workflow `Programação - recuperação e laboratório` verifica regressões em PRs;
treino ocorre somente por `workflow_dispatch`, com perfil e passos explícitos,
limite de 45 minutos e publicação de artefatos mesmo quando interrompido.
O orquestrador também limita tempo local. Checkpoints já salvos podem ser retomados
pelo treinador original. O corpus não é sobrescrito silenciosamente.

Gates exigem teste, execução isolada, pelo menos 50 famílias e 50 tarefas por
linguagem, pass@1 >= 90%, todas as gerações completas, regressão geral aprovada
e revisão independente. O benchmark atual de 8 famílias **não basta**, mesmo
que todas passassem. Ampliar o benchmark e introduzir avaliação independente
são trabalhos necessários antes da promoção; os booleanos não substituem essa evidência.

## Limites da execução

O verificador compila JS com `node --check` e TS com `tsc --strict --noEmitOnError`.
Executar candidatos exige bubblewrap: namespaces separados de rede/PID/usuário,
sem montagem de home/workspace/credenciais, input somente leitura, CPU e saída
limitadas, timeout de parede, espaço virtual limitado a 1 GiB, máximo de 64
processos e heap Node limitado (JIT desativado). Se não puder criar isolamento,
a execução é bloqueada. Não há fallback que execute candidato no host.
O sandbox precisa ser testado no host escolhido; o CI publica essa disponibilidade
no relatório. Uma falha de infraestrutura não é certificação de segurança nem
prova de incorreção funcional do código que chegou a compilar.

## Tempo de regressão

A regressão chamada “300 combinações” executava 13.695 pares para 166 conceitos.
Agora garante participação de todos os conceitos e completa 300 pares com semente
fixa, escolhidos antes de observar respostas. Para catálogos maiores que 300
conceitos, a cobertura cresce linearmente. A matriz factual e as sondas reservadas
continuam completas. O workflow de regressões tem limite de 20 minutos e cancela
execuções anteriores da mesma referência quando entra uma atualização.

## Notebook pronto para Google Colab

[Abra o notebook de programação com GPU T4](https://colab.research.google.com/github/HROSONE/CRIVO/blob/codex/programacao-transformer-ciclo/notebooks/treinar_programacao_colab.ipynb).

Execute as células em ordem e autorize a montagem do seu Google Drive quando
solicitado pelo Colab. O padrão é o perfil atual com 2.000 passos; o código do
treinador fica fixado na revisão `ab17e971042afa6081e922000cbdec615f44438a`.
Os perfis maiores iniciam pré-treino do zero e não substituem a necessidade
de ampliar o corpus de código.

Para retomar após uma desconexão, informe o `EXECUCAO_ID` exibido e mantenha
os mesmos parâmetros e versões de ambiente. A leitura do corpus usa disco
local; checkpoints, estado de Adam/RNG, logs e uma cópia do corpus permanecem
no Drive. O notebook verifica a configuração antes de retomar, mostra progresso
e permite exportar um ZIP de pesos de inferência e relatórios. A GPU e o acesso
ao Drive precisam ser habilitados na conta do usuário; criar o notebook não
inicia um treinamento no Colab.
