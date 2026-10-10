# Escrita condicionada a acontecimentos — 10/10/2026

**Integração aprovada no recorte medido. Não é conversa livre geral.**
A cópia de produção usa a GRU própria; o candidato original continua
`aprovado=false`, `ativo_no_chat=false`. Nenhum modelo externo foi usado.

Base: `ed2bf1a7d59846acd2192568c16e2e6bb4ce276e` (#131). Os mesmos
114 casos e dez sessões autorais anteriores foram preservados byte a byte.
Os critérios não foram afrouxados para aprovar respostas novas.

| Medida | Base | Integração |
|---|---:|---:|
| 114 casos, peça + conteúdo + referentes, motor | 80/114 | 110/114 |
| 114 casos, HTTP local real | — | 110/114 |
| 79 casos anteriores, motor e HTTP da integração | 79/79 | 79/79 |
| Casos com referentes ausentes, nos 114 | 30 | 0 |
| Desvios proibidos, nos 114 | 8 | 0 |
| Trocas de domínio detectadas, nos 114 | 0 | 0 |
| Histórias entregues com argumentos, integração | — | 52/52 |
| Dez sessões completas, revisão pelo agente | 0/10 | 6/10 motor e HTTP |

São dez sessões **autorais do agente**, 104 turnos por modo; não dez
participantes humanos nem avaliação cega. Os seis critérios mínimos de
escrita passam, com fraquezas registradas em `revisao_sessoes.json`.
As quatro sessões práticas continuam falhando. As 64 respostas das seis
sessões de escrita são idênticas no motor e HTTP; seis saudações/relatos
não neurais variam nas outras sessões, sem mudar os 104 identificadores.

Quatro casos congelados ainda não pontuam: restrição de nome, participantes,
restrição de cor e resumo. O conjunto espera a peça `escrita`; os executores
usam `esclarecimento`, preservando o conteúdo/referentes pedidos. Não se
alterou o conjunto para transformar esses quatro em acertos.

## Mudança concreta

- Acontecimentos explícitos da ficção ativa chegam ao realizador: perda,
  recuperação, encontro/caixa vazia, retorno, ajuda, costura/devolução,
  companhia/conserto, cotidiano e humor. Correção de recuperação substitui
  a perda anterior. Pessoas, lugar, objetos declarados e restrições usam
  o estado de escrita já existente; não se criou outra memória geral.
- A GRU recebe o ato, argumentos, tipo de reação e variante. Para a
  continuação clássica, recebe sua própria saída anterior. A escolha de
  classe e algumas transições são **estruturais**, não planejamento neural.
  Texto residual é neutralizado no caminho de acontecimentos: não se
  demonstrou que a rede compreende todo o histórico bruto.
- Dois tipos de acontecimento colidiam no hash de entrada. Dois sinais
  por classe distinguem as doze representações sem mudar os 192 atributos.
- A guarda exige reação compatível além de copiar a declaração em
  `@relato`, e conserva restrições explícitas. É uma verificação lexical
  limitada às classes, não um juiz geral de significado. Humor não exige
  a palavra “riu”. Simplificação sem mudar conteúdo esclarece seu limite.
- Pedido de ajuda dirigido à companhia gera ajuda recebida; o bilhete
  pedindo ajuda gera resposta da personagem. O ajuste final repetiu os
  seis casos congelados afetados e a sessão completa, motor/HTTP.
- Realização clássica, finais e reescrita em cinco frases sem eventos
  conservam o caminho já treinado. Fatos/cálculos/fontes mantêm executores
  rígidos. Nenhum dos 35 arquivos anteriores de pesos/metadados mudou;
  o checkpoint anterior de diálogo foi preservado integralmente.
- Navegador e API aceitam até vinte mensagens anteriores, com as mesmas
  regras por mensagem e 24.000 caracteres totais. Doze turnos foram
  reconstruídos por HTTP sem truncar a abertura. Não prova memória infinita.

## Treino realmente executado

GRU existente, ocultos 80, vocabulário 321, embeddings 9. Parâmetros:
**85.581 → 85.130**, sem aumento ou nova arquitetura.

9.024 exemplos próprios combinados: 6.144 treino, 2.880 validação.
Incluem os 4.928 anteriores e 4.096 combinações autorais de acontecimentos,
argumentos, estilo e final. Entidades/dialogos separados; classes, padrões
**e muitos vetores após substituir os argumentos são compartilhados**.
Validação não é teste independente de enredo nem generalização de nomes.
Entidades específicas das sondas estão fora do corpus; entram como argumentos.

Quatro rodadas estão arquivadas. A segunda fez 110/114, mas com repetição
qualitativa e desvio no resumo. A terceira ampliou variedade e regrediu:
101/114, três casos perdem referentes; foi reprovada. A última recupera o
recorte antigo e realiza os novos acontecimentos. Os intermediários não
foram publicados no chat.

Último treino: 32 épocas, seleção da época 27, semente 20261014, lote 48,
Adam 0,0015, clip 5, CPU/NumPy. Parte de checkpoint próprio da terceira
rodada. 564,42 segundos; repetição completa 791,08 segundos, **arquivo
idêntico byte a byte**, com concorrência de avaliações. Hashes no manifesto.

Gerador isolado, sem fornecer prefixo alvo: **2.048/2.048** exemplos de
validação de acontecimentos produzem os tokens autorais esperados.
Isso diagnostica aprendizagem dos padrões compartilhados; não é métrica
independente de raciocínio ou o critério de aprovação de conversa.

## Evidência e reprodução

- `baseline_motor.json`: execução dos 114 antes de alterar o runtime.
- `final_motor.json`, `final_http.json`: replay completo do candidato e
  substituição documentada dos seis casos após o ajuste final de papéis.
  A parcial nunca pode aprovar o candidato; `escopo_reavaliacao_ajuda.json`
  e arquivos `antes_ajuste_ajuda_*` preservam a origem das duas medições.
- `final_sessoes_*`: todos os 104 turnos, respostas e traces; a única
  sessão afetada pelo ajuste final foi repetida integralmente.
- `revisao_sessoes.json`: julgamento qualitativo e falhas restantes.
- `reproducibilidade.json`, `gerador_validacao_livre.json`: treino e
  diagnóstico de saída livre do gerador.
- `aprovacao.json`: origem, métricas e hash da cópia habilitada.
  Original isolado: `a042a271…`; produção: `4e5894e2…`.
- `manifesto.json`: hashes de dados, avaliações, runtime e pesos preservados.

Em checkout desta versão, com Python/NumPy e pesos próprios versionados:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/escrita_acontecimentos_20261010/treinar.py --epocas 32 --destino /tmp/dialogo-repetido.json.gz
python experimentos/escrita_acontecimentos_20261010/avaliar.py --modo motor --saida /tmp/dialogo-motor.json --so-congelado --exigir-meta
python experimentos/escrita_acontecimentos_20261010/avaliar.py --modo http --saida /tmp/dialogo-http.json --so-congelado --exigir-meta
```

CI: contratos de aprovação/papéis/corpus/HTTP e os 114 casos no chat
aprovado, por escopo, em Python 3.11. Sem gatilho `push` na bateria nova;
não reinicia após o merge. Matriz completa continua manual/semanal.
A publicação só se confirma consultando commit/checkpoint no HTTP público.

## Limites e próximo passo único

Ainda há transições genéricas, declarações repetidas, episódios de mapa
reutilizados e pouca participação da companhia fora das ações treinadas.
Oito etapas clássicas e doze classes não cobrem acontecimentos arbitrários.
Não demonstrou planejamento, diálogo humano, fôlego indefinido nem
simplificação fiel. As quatro conversas práticas novas ainda falham.

Próximo passo: congelar e corrigir essas falhas de utilidade prática —
frações/tempo, bicicleta/rodas, horta/condições e troca/retomada de tarefa —
sem nova memória, acervo, arquitetura ou aumento de parâmetros. Preservar
os 114 e o recorte de escrita aprovado.
