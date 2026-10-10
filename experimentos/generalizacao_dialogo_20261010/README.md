# Continuidade e generalização — 10/10/2026

**Experimento de treino próprio concluído; integração reprovada.** O chat
continua usando o checkpoint aprovado do #130. Este diretório registra um
candidato, não uma nova capacidade publicada no site.

Base medida: `431191b34e767a672921b0d0b79070ff8dd8293e`.

## Antes e depois

| Avaliação | Antes (#130) | Candidato |
|---|---:|---:|
| Conjunto congelado, motor: peça + conteúdo + referentes | 80/114 | 96/114 |
| Subconjunto de 35 pedidos novos | 1/35 | 17/35 |
| 79 casos anteriores preservados | 79/79 | 79/79 |
| Casos com referentes ausentes | 30 | 16 |
| Desvios proibidos nos 114 casos | 8 | 5 |
| Trocas de domínio detectadas nos 114 casos | 0 | 0 |
| Dez sessões novas completas, revisão pelo agente | 0/10 | 1/10 |
| Sequências controladas: 64 × 8 etapas, gerador isolado | 0/512 | 512/512 |

Meta de integração: pelo menos **103/114**, zero perda de referente e
troca de domínio, e pelo menos 6/10 sessões mantendo o fio. O candidato
não passa. `controle.aprovado=false`, `ativo_no_chat=false`.

O piloto inicial fez 95/114. Corrigir a escolha de variante durante a
continuação e ampliar alguns comandos elevou para 96/114; os dois resultados
ficam arquivados. A medição final corresponde a `piloto_integracao.patch`,
SHA-256 `998e9a84e8554913a9e578c2c16b46d765271136ab195937bb68cbfa6d27c1e6`.
O patch foi removido do runtime após a reprovação e fica apenas como evidência
reproduzível, para aplicar em checkout isolado.

## O que foi realmente executado

1. Congeladas dez sondas autorais novas (104 turnos) antes de consultar o motor
   e o site. Escrita repetida, acontecimentos e correções, tom, restrições,
   história cotidiana, frações, desenho de bicicleta, horta e troca de tarefa.
   São conversas de teste do agente, não sessões de dez participantes humanos.
2. Executados os 104 turnos no motor e no HTTP público do #130; health antes
   e depois confirma commit e checkpoint. O replay público usa até dez
   mensagens anteriores, como o navegador. Uma primeira tentativa enviou
   onze e recebeu HTTP 400: erro do instrumento, preservado no log, corrigido
   antes do replay completo. Isso não foi contado como falha do modelo.
3. Selecionados 35 pedidos realmente observados de escrita/continuação;
   somados aos 79 anteriores, sem mudar esses casos. Critérios e entradas
   congelados antes de implementar o piloto. Não são 35 falhas puras: um
   desses pedidos já passava. As quatro sessões práticas novas estão no
   relatório qualitativo e ainda não integram os 114 casos automáticos.
4. Treino CPU de checkpoint próprio, separado de fatos e do chat. Repetição
   completa gerou **arquivo idêntico byte a byte**, em cerca de dois minutos
   no treino original (109,29 s) e três minutos na repetição (193 s).
5. Gerador isolado, piloto no motor e leitura das dez sessões. Nenhum treino,
   API ou peso de modelo externo foi usado. Todos os 35 arquivos anteriores
   de pesos/metadados, mais o checkpoint aprovado de diálogo, são iguais
   byte a byte à base Git.

`baseline_congelados.json` reaproveita a medição final do #130 para os 79
antigos e pontua as respostas das sondas do motor para os 35 novos.
`piloto_final_congelados_motor.json` reexecuta todos os 114 no piloto. Isso é
avaliação **local de candidato**, não melhoria já obtida no site.

## Treino e medida de leitura do contexto

- GRU autorregressiva própria existente; ocultos 80, embeddings 40 → 38,
  vocabulário 181 → 187. Parâmetros **85.581 → 85.453**.
- Corpus anterior de 1.856 exemplos + 3.072 novos = **4.928**;
  4.096 treino, 832 validação. São combinações de templates autorais,
  não milhares de histórias independentes.
- Novos exemplos: oito etapas de uma cadeia de acontecimentos, com presença
  ou ausência de cenário, companhia e relato literal. Diálogos inteiros e
  entidades de treino/validação separados; **as oito etapas são compartilhadas**.
  Não inclui as personagens nem respostas alvo das novas sondas.
- Semente 20261013, 32 épocas, lote 48, Adam taxa 0,0015, clip 5.
  Melhor validação na época 30. Hiperparâmetros e perdas em `treino.json`.
- A área existente de atributos do trecho anterior é usada; não foi criada
  arquitetura nova. Deixamos de misturar/apagar essa informação no treino,
  porque ela determina qual etapa vem em seguida.
- Nas 64 sequências de validação, depois do primeiro trecho a entrada é a
  **saída anterior do próprio gerador**, sem fornecer a resposta correta.
  512/512 etapas correspondem ao template alvo; removendo o trecho anterior,
  **0/512**. O checkpoint antigo faz 0/512 nesses mesmos novos templates.
  O antigo não foi treinado para esses textos: essa comparação não mede suas
  capacidades anteriores gerais. Igualdade de tokens aqui é diagnóstico do
  ensaio, não regra de cópia literal da rota de conversa.

O resultado demonstra dependência do contexto **dentro desses padrões**.
O codificador de texto anterior continua sendo um resumo de tokens por hash,
sem sequência ordenada aprendida. Não demonstra entendimento causal,
planejamento, diversidade de enredos ou generalização para qualquer conversa.

Checkpoint experimental SHA-256:
`b224d0ff250f267f60238989832de9d0ca1f175f27207ae43acd19326f206126`.
Corpus SHA-256:
`b7d5a085fb56ab55ad4fc82823547d5abe0466383a1c7609cb07c97729f795c6`.
Conjunto congelado SHA-256:
`9f5164f9aefbec71ec9e36aafebd7711cb95c2ab88c31b5b01975b67128645f8`.

## Falhas que impedem ativação

- Uma história de doze turnos no motor mantém quati, torre e companhia,
  avançando pelas etapas aprendidas. A revisão considera essa sessão
  aprovada em seu critério restrito; não é fôlego indefinido.
- “A caixa está vazia. Mostre a reação dos dois” pode apenas copiar o relato
  e gerar uma continuação incoerente. Copiar o acontecimento não é realizá-lo.
- O piloto copia até “Continue a partir disso” em um relato. A correção da
  chave passa a aparecer, mas concluir a história com relato ainda recua.
- Tom divertido, “sem viagem e sem mapa”, resumo, bolsa rasgada e linha azul
  continuam falhando. Um comando de restrição pode apagar a tarefa de escrita.
- Frações novas são calculadas pelo executor existente, mas explicar de outro
  jeito, variar exercícios e guardar quinze minutos continuam limitados.
  Desenho de bicicleta, observação de luz da horta e retomada de frações
  também não mantêm o fio. Esses pedidos não foram treinados neste ensaio.
- O motor conserva sessão viva; HTTP reconstrói apenas dez mensagens.
  Não certificamos o piloto longo por HTTP nem contornamos esse contrato
  truncando referências para marcar sucesso.

## Reprodução

Na raiz do repositório, usando NumPy próprio e CPU:

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python experimentos/generalizacao_dialogo_20261010/preparar.py
python experimentos/generalizacao_dialogo_20261010/treinar.py --destino /tmp/crivo-dialogo-repro.json.gz
cmp /tmp/crivo-dialogo-repro.json.gz experimentos/generalizacao_dialogo_20261010/checkpoint_gru_dialogo.json.gz
python experimentos/generalizacao_dialogo_20261010/avaliar_modelo.py --checkpoint /tmp/crivo-dialogo-repro.json.gz --saida /tmp/crivo-dialogo-isolado.json
python -m unittest testes_generalizacao_dialogo -v
```

Somente num checkout isolado, para reproduzir a **integração reprovada**:

```bash
git apply experimentos/generalizacao_dialogo_20261010/piloto_integracao.patch
python experimentos/generalizacao_dialogo_20261010/avaliar.py --modo motor --candidato experimentos/generalizacao_dialogo_20261010/checkpoint_gru_dialogo.json.gz --saida /tmp/crivo-piloto-114.json --so-congelado
python experimentos/generalizacao_dialogo_20261010/sondar.py --modo motor --candidato experimentos/generalizacao_dialogo_20261010/checkpoint_gru_dialogo.json.gz --saida /tmp/crivo-piloto-104.json
```

Adicionar `--exigir-meta` à avaliação acima deve falhar: o candidato está
reprovado. O CI verifica isolamento/proveniência e os 79 casos já aprovados
do chat; não finge que o piloto passou, não treina e não abre a matriz completa.
`manifesto.json` fixa hashes dos dados, código, resultados, patch e pesos.

**Próximo passo único:** corrigir interpretação e realização de acontecimentos
e restrições de escrita enquanto a tarefa permanece ativa, usando os mesmos
35 pedidos congelados. Ampliar supervisão autoral de acontecimentos/finais e
enredos distintos, sem copiar os alvos do teste. Só promover quando o conjunto,
sessões completas e HTTP passarem. Utilidade prática nova e diálogo geral
continuam pendentes; não criar memória, acervo ou aumentar parâmetros.
