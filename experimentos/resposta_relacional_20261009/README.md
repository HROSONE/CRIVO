# Piloto causal de resposta relacional

Primeira versão congelada em `f3adda3`; dados com concordância revisada e
verificação congelados em `c9901d7`, antes do reinício dos dois treinos. Não altera
o chat nem os pesos ativos. As regras do projeto continuam proibindo pesos,
tokenizadores e APIs de inferência de terceiros.

## Pergunta e mudança concreta

O diagnóstico pareado encontrou falha mesmo com os fatos organizados. O
piloto anterior de resposta já falhou e sobreajustou com 242 pares. Os arquivos
compactos disponíveis não tinham exemplos completos com seis turnos de
histórico. A nova condição testa supervisão de relações ao longo de oito
mensagens, com respostas curtas que usam os dados: vínculo entre entidades,
correção versus confirmação, referência ordinal, hipótese versus causa,
autorização concedida versus negada e intenção pessoal versus fala de terceiro.

O currículo contém 4.770 entradas de treino distintas e 271 de validação,
após deduplicação. Há 1.548 entradas de treino com seis mensagens anteriores.
Todos os pares, incluindo a resposta, cabem integralmente no contexto 256.
São exercícios procedurais autorais com seis famílias e formas compartilhadas,
não 4.770 conversas humanas nem 4.770 relações independentes. A validação
compartilha gramática e léxico; mede aprendizagem no domínio dos exercícios.

## Comparação

- Mesmo checkpoint causal próprio de 2.612.352 parâmetros e mesmo tokenizer.
- Controle: 215 pares autorais antigos, mais os 27 pares humanos de replay.
- Relacional: novos exercícios, com o mesmo pool de 27 pares humanos.
- Lotes: seis exemplos autorais e dois humanos; AdamW, LR 0,0001, seed 20261009.
- Exatamente 180.000 tokens-alvo por braço; a última atualização mascara só
  alvos excedentes, preservando a entrada completa. Comprimentos e número de
  atualizações variam; esta é comparação de currículos sob orçamento fixo.
- Checkpoint escolhido pela menor perda de validação relacional, incluindo
  o passo zero, com o mesmo critério em ambos os braços.
- Perda no corpus autoral antigo e em cinco pares humanos reservados é
  acompanhada como diagnóstico de esquecimento. CE não é retenção comportamental.
- Cada braço para e salva ao atingir 30 minutos. O teto da investigação é
  90 minutos de computação ativa; não é prazo prometido para conversa livre.

`integridade.json` verifica perda somente na resposta, sequência inteira e
nenhuma entrada completa idêntica entre treino e validação. A deduplicação
não estabelece independência semântica: prefixos e formas podem coincidir.

`sessoes.json` contém 12 sessões de desenvolvimento, redigidas separadamente
e congeladas antes do treino. Na avaliação, cada modelo responde às quatro
falas e seus próprios textos retornam ao histórico. Preservam-se entrada real,
omissões e perda do prefixo durante geração. A leitura semântica verifica cada
turno e a sessão inteira; acertar uma palavra no final não aprova conversa.

Só há uma semente nesta triagem. As sondas pareadas anteriores ficam fora do
treino e da seleção. Não há avaliação externa cega. Se não atingir o critério
comportamental, não integrar e não gastar três sementes ou avaliação final de
60 sessões em um candidato já reprovado no desenvolvimento.

Os relatórios, hashes e respostas são versionados. Pesos candidatos continuam
locais e experimentais; `.gitignore` evita acumular cópias não aprovadas no Git.
Os registros da rodada interrompida também são mantidos; ela não é apresentada
como treino concluído. A versão original dos dados permanece no histórico Git.

## Reproduzir

Com as dependências opcionais de treino instaladas e os pesos próprios disponíveis:

```sh
python experimentos/resposta_relacional_20261009/curriculo.py
python experimentos/resposta_relacional_20261009/piloto.py treino --braco controle --antigo /caminho/para/dados_anteriores
python experimentos/resposta_relacional_20261009/piloto.py treino --braco relacional --antigo /caminho/para/dados_anteriores
python experimentos/resposta_relacional_20261009/coletar_sessoes.py --modelo artefatos/linguagem_profunda --saida experimentos/resposta_relacional_20261009/avaliacao/base.json
python experimentos/resposta_relacional_20261009/coletar_sessoes.py --modelo experimentos/resposta_relacional_20261009/controle --saida experimentos/resposta_relacional_20261009/avaliacao/controle.json
python experimentos/resposta_relacional_20261009/coletar_sessoes.py --modelo experimentos/resposta_relacional_20261009/relacional --saida experimentos/resposta_relacional_20261009/avaliacao/relacional.json
```

O gerador de dados recusa sobrescrever a pasta; o treino recusa sobrescrever
resultados existentes. Para repetir, use uma cópia do experimento com suas
pastas de saída vazias, preservando os relatórios desta rodada. Os dados antigos
estão no experimento versionado `geracao_dialogo_20261008` da branch
`codex/associacao-fatos-20261008`; este diretório não baixa fontes nem pesos.
