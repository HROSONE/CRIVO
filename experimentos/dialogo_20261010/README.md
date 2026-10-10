# Diálogo próprio — Fases 0 e 1, 10/10/2026

Há dois checkpoints realmente treinados, um conjunto congelado de **37 casos
reais** e um corpus autoral de **5.760 turnos**. O melhor ensaio isolado passou
de **0/10 para 7/10** nos critérios mínimos dos dez pedidos dialógicos e
entregou as duas histórias com a capivara astronauta. Os pesos continuam
**`aprovado: false`, `ativo_no_chat: false`**. Esta etapa não altera o chat.

## Fase 0 encerrada

Base: `9ed051bf2b74668073e0ac480b43c652314b88e7`, merge do #125.
As seis combinações de `composicao` e `regressoes-b` em Python 3.8/3.11/3.13
passaram no run `38006360452` antes do merge. Foram 18 testes por composição
e 645 por regressão, sem falhas; a regressão manteve 37 skips conhecidos.
O CI após o merge executou os smokes por escopo, sem repetir a matriz longa.

As respostas HTTP públicas desse commit estão em `evidencias/`.
`fase0.json` registra os seis casos pedidos: primo/pessoa, descanso/tempo,
diferença de potencial, “Só isso?”, preferência corrigida e personagem
anterior. **Zero troca de domínio; referentes preservados.** A última
resposta ainda era um esclarecimento, sem entregar a história. Preservação
foi o critério da Fase 0; entrega de narrativa continua obrigatória na Fase 2.

O site no conjunto ampliado fez **35/37**, falhando nas duas narrativas.
Esse número descreve o sistema atual, com roteamento e respostas
estruturadas/factuais. O 0/10 → 7/10 abaixo compara geradores isolados,
não a qualidade anterior e posterior do site. Não somamos métricas dos dois
percursos para declarar uma integração aprovada.

## Conjunto congelado e corpus

- `casos_congelados.json`: os 35 casos reais anteriores, preservados sem
  modificar campos, mais dois pedidos realmente observados por HTTP:
  definição de diferença de potencial e “Só isso?”. SHA-256 em `SHA256`.
- Cada caso mantém anteriores, entrada, intenção/peça, referentes,
  desvios proibidos e resposta mínima aceitável. Grupos: roteamento,
  manutenção de tarefa/referente e diálogo/história/capacidades.
- `preparar.py` produz **480 diálogos autorais**, com seis pares por
  diálogo: 2.880 exemplos de resposta, **2.304 de treino e 576 de validação**.
  São 5.760 turnos contando usuário e assistente, não 5.760 respostas alvo.
- Tipos: capacidades, preferências, histórias, continuidade, esclarecimento
  e tempo. Não usamos chamadas de modelos externos para gerar dados.
- Partições separadas por diálogo, nomes, alguns objetos e formulações;
  nenhum contexto duplicado nem entrada exata do congelado no corpus.
  **Compartilham os mesmos seis tipos e padrões de resposta.** Isso não
  comprova generalização para novas famílias semânticas ou conversa livre.
- `corpus_gru.json` é uma outra codificação dos mesmos 2.880 exemplos:
  ato + argumentos, com valores substituídos por marcadores no alvo.
  Não acrescenta novos dados e não consulta respostas do conjunto real.
  Há **31 alvos distintos após remover valores dos argumentos**. A contagem
  de turnos vem de combinações; não são milhares de padrões de conversa.

## Medição dos dois ensaios

| Medida | Seq2seq próprio | GRU condicional própria |
|---|---:|---:|
| Parâmetros do checkpoint de origem | 971.578 | 153.704 |
| Parâmetros depois do treino | 577.277 | 88.969 |
| Dez pedidos reais: mínimo antes → depois | 0/10 → 3/10 | **0/10 → 7/10** |
| Histórias entregues depois | 0/2 | **2/2** |
| Respostas terminadas depois | 10/10 | 10/10 |
| Casos com referente ausente depois | 3 | 1 |
| Casos com nome sintético/número inventado | 0 | 0 |
| Amostra interna: mínimo preservado | 26/36 | 34/36 |

Os juízes verificam conteúdo mínimo, término, referentes e termos
proibidos. **Uma resposta com palavras certas pode ser incoerente.**
Os três positivos do primeiro ensaio não representam três conversas
úteis: a inspeção mostrou linguagem frágil e desvios. Esse ensaio permanece
reprovado. `checkpoint_antes.json`, `checkpoint_depois.json` e
`validacao_geracao.json` preservam inclusive as falhas.

A segunda GRU prevê palavras e marcadores; `renderizar` copia literalmente
os argumentos fornecidos. Não há busca da resposta alvo na avaliação.
O ato e os argumentos nos dez casos vêm do **trace HTTP já observado**,
nunca dos rótulos esperados. Isso mede um gerador condicionado, não sua
capacidade de extrair sozinho pessoas, tarefas e intenção do histórico.
O site atual já acerta oito desses dez pedidos com respostas estruturadas;
substituir essa rota inteira pela GRU de sete acertos seria regressão.

`gru_antes.json` e `gru_depois.json` guardam entradas e saídas; a revisão
em `revisao_qualitativa.json` confirma:

- História: cinco frases, preservando **capivara astronauta**.
- Final: mantém a personagem e encontra **um amigo**.
- Capacidades: respostas curtas, coerentes mas repetitivas e incompletas.
- Três falhas mantidas: perguntas não enumeradas (`real-03`), funcionamento
  incoerente (`real-04`) e autoria da geração incoerente (`real-21`).

O nome “ficção” sinaliza eventos inventados da narrativa. Não transforma
esses eventos em fatos da sessão ou do acervo. A guarda de integração
contra esse tipo de contaminação **ainda não foi implementada**.

## Treino e reprodução

Nenhum modelo externo foi baixado ou chamado. Reutilizamos pesos próprios
existentes; não alegamos que o histórico de seus treinos anteriores foi
produzido integralmente neste novo corpus. As arquiteturas e dimensões
ocultas permanecem iguais; a redução do vocabulário reduz parâmetros.
Os **35 arquivos de pesos ativos** auditados mantêm os hashes anteriores.

Ambiente: Python 3.12.14, NumPy 2.3.5, CPU, um thread BLAS/OMP. Não houve
GPU. Primeiro ensaio: 12 épocas, melhor época 9, lote 32, Adam 0,0008,
clip 5, semente 20261010, cerca de 413 segundos. Segundo: 14 épocas,
melhor época 14, lote 48, Adam 0,002, clip 5, dropout textual 0,65 e mistura
0,15, mesma semente, cerca de 24 segundos. Perdas e metadados completos
estão em `treino.json` e `treino_gru.json`.

Executar da raiz do repositório, com NumPy instalado:

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python experimentos/dialogo_20261010/preparar.py
python experimentos/dialogo_20261010/avaliar.py --saida /tmp/seq2seq_antes.json
python experimentos/dialogo_20261010/treinar.py
python experimentos/dialogo_20261010/avaliar.py --modelo experimentos/dialogo_20261010/checkpoint_dialogo.json.gz --saida /tmp/seq2seq_depois.json
python experimentos/dialogo_20261010/validar_geracao.py
python experimentos/dialogo_20261010/gru_dialogo.py preparar
python experimentos/dialogo_20261010/gru_dialogo.py avaliar --saida /tmp/gru_antes.json
python experimentos/dialogo_20261010/gru_dialogo.py treinar --epocas 14
python experimentos/dialogo_20261010/gru_dialogo.py avaliar --modelo experimentos/dialogo_20261010/checkpoint_gru_dialogo.json.gz --saida /tmp/gru_depois.json
python experimentos/dialogo_20261010/validar_gru.py
python -m unittest discover -s experimentos/dialogo_20261010 -p testes_experimento.py -v
```

O segundo treino foi repetido, gerando checkpoint **idêntico byte a byte**:
`823c44965cb7d9e3ec3830555b100aec373443e3b778cd719cc9804bc9e4ba47`.
`reproducibilidade_gru.json` registra versões e tempos. Não garantimos
identidade numérica entre outras bibliotecas ou plataformas. `manifesto.json`
registra hashes dos dados, código, evidências e pesos deste experimento.

## O que ainda falta — Fase 2

Fases 0 e 1 encerradas: dívida verde/mesclada, evidência pública, congelado,
corpus próprio, checkpoints realmente treinados e reprodução documentada.
**Nenhum checkpoint foi aprovado ou ligado ao chat.** Não alteramos CI,
guardas factuais, memória, acervo ou os pesos usados pelo site.

A próxima etapa única é a integração seletiva da rota de conversa,
preservando o percurso atual onde este candidato falha. Ela precisa de
guarda distinta para conversa, trace explícito, medição antes/depois no motor
e HTTP dos **37 casos**, ≥34/37 com peça certa, zero troca de domínio,
100% dos referentes exigidos e pelo menos 6/10 conversas reais de 6–8
turnos mantendo o fio. As dez conversas manuais e a validação pública
do checkpoint integrado **não ocorreram nesta Fase 1**.

Não ampliar parâmetros, memória, acervo ou abrir outra frente para disfarçar
as falhas. Os enredos são genéricos, a fluência ainda falha em alguns atos,
e o condicionamento depende do estado correto. Não é conversa humana plena.
