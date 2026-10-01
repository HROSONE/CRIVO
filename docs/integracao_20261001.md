# Integração das pendências — 01/10/2026

As PRs #4, #34, #41, #42 e #43 foram reunidas em uma árvore validada, preservando seus commits como ancestrais. A avaliação histórica `perguntas_externas.json`, que estava numa branch sem PR, também foi recuperada sem entrar no treino.

Foram corrigidos o alias da Lua terrestre, o conflito do workflow de ordem das palavras, documentação desatualizada e a invalidação dos pesos após ampliar a base. As verificações de rede ativa e ausência de prova nas reformulações foram restauradas: a PR #42 havia colocado as duas asserções dentro de um comentário contendo escapes literais de quebra de linha.

## Treinos e promoção

Oito treinos completos executaram backpropagation desde inicialização aleatória, sem pesos de terceiros ou APIs de inferência. O pipeline grava candidatos separados e não promove modelos automaticamente.

| Rede | Configuração executada | Resultado da integração |
| --- | --- | --- |
| Classificador factual | 48 neurônios, 60 épocas, semente 42 | Novo checkpoint ativo: 241 classes e 2.030 perguntas |
| Astronomia experimental | 96 neurônios, 100 épocas, semente 42 | Candidato em `artefatos/rede_astronomia_experimental_241.json` |
| Atos de diálogo | 90 épocas, semente 73 | Matrizes idênticas às publicadas |
| Operações e trechos de linguagem | 70 épocas, semente 42 | Novo checkpoint promovido; 77/77 quadros na validação |
| Intenção gerativa | 110 épocas, semente 107 | Matrizes idênticas às publicadas |
| Escrita controlada | 40 épocas, semente 91 | Matrizes idênticas às publicadas |
| Compreensão BiGRU | 15 épocas, semente 2718; seleção da época 5 | Matrizes idênticas às publicadas |
| Diálogo com atenção/cópia | 12 épocas, semente 173; seleção da época 8 | Matrizes idênticas; geração experimental desligada |

O acelerador NumPy do MLP preserva SGD por exemplo, ordem de sorteio e gradientes; a equivalência foi testada contra a implementação Python. A execução sem NumPy continua disponível. Comparações e treinos demorados permanecem sob demanda.

```bash
python -m pip install -r requirements.txt
python scripts/treinar_redes_integradas.py --saida /tmp/crivo-treinos --jobs 2
python scripts/avaliar_astronomia_independente.py --modelo artefatos/rede_astronomia_experimental_241.json --relatorio /tmp/astronomia96.json
```

O avaliador astronômico retorna código 1 quando o gate de recuperação não é atingido; o relatório permanece disponível. Nunca usar seus enunciados como treino ou mudar a rubrica para obter aprovação.

## Verificação e limites

562 testes locais aprovados, 65/65 originais e dez sondas de regressão/diagnóstico. O fluxo no navegador confirmou identidade, compreensão básica, definição da Lua, fontes e abstenção para planeta inventado, sem erros de console. O CI verifica Python 3.8, 3.11 e 3.13; seus resultados ficam na PR de integração.

Conversa livre ainda não está resolvida: a sonda congelada permanece em 31/72 no serviço padrão e 29/72 com geração experimental, com 2/18 conversas completas em ambos. Repetir o treino com os mesmos dados reproduziu as matrizes do gerador. O checkpoint de 96 neurônios acertou 20/29 na avaliação neural de astronomia, contra 21/29 com 48; não foi promovido. Nenhum módulo astronômico foi certificado. São reavaliações diagnósticas de provas já consultadas, sem alegação de teste cego.

O experimento de ordem obteve 170/467 contra 167/467 na representação de referência, usando as mesmas dobras e sementes do corpus editorial. Isso mede uma pequena diferença nessa validação, sem demonstrar compreensão de papéis ou vantagem geral. A representação continua isolada da produção. O contrato de voz foi integrado e testado, mas ainda não existe sintetizador ou áudio offline.

O relatório com comandos, sementes, hashes, tempos, decisões e avaliações completas está em `avaliacoes/integracao_20261001.json` e na pasta de mesmo nome. As avaliações históricas permanecem intactas.

## Limpeza

O trabalho local anterior foi preservado na branch `archive/dialogo-antes-integracao-20261001` e num bundle local antes de qualquer limpeza. O workflow `limpar-integrados.yml` executa após a integração na main e usa um inventário explícito de nomes e SHAs. Só exclui heads ancestrais da main ou comprovadamente mesclados por uma PR na main. Branches alteradas, não comprovadas ou protegidas são preservadas. A exclusão usa `--force-with-lease` para o servidor recusar uma branch que recebeu commits depois da verificação. O workflow publica o resultado de cada branch.

Pendências de capacidade continuam registradas: corpus conversacional mais diverso, prova prospectiva inédita, revisão científica humana e implementação real de áudio. Integrar código validado não declara essas metas concluídas.
