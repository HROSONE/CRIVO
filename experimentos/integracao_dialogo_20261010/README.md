# Integração seletiva do diálogo próprio — Fase 2, 10/10/2026

O gerador próprio treinado no #126 recebe agora personagem e argumentos da
sessão para entregar **história curta, continuação e final**. Capacidades,
funcionamento, autoria, fatos, cálculos e preferências preservam seus
executores atuais. O checkpoint não demonstrou qualidade para substituí-los.

## Antes → depois

| Medida congelada | Base #126 | Integração |
|---|---:|---:|
| 37 casos reais: peça correta com conteúdo | 35/37 | **37/37 motor e HTTP real** |
| Troca de domínio | 0 | **0** |
| Casos com referente ausente | 0 | **0** |
| Histórias pedidas no conjunto real | 0/2 | **2/2** |
| Dez sessões de 6–7 mensagens: mantém o fio | 4/10 | **7/10 motor e HTTP real** |

Os 37 casos são **o mesmo arquivo** da Fase 1, SHA-256
`d0d39fce5d40ffe024f03ffede68d0d3d852ff96040a59a5890fc509f2c20798`.
Não alteramos exemplos, mínimos ou critérios depois de medir.

As dez sessões/62 mensagens em `conversas_congeladas.json` foram fixadas
**antes da implementação**. São sessões novas de revisão pelo agente
como usuário, não relatos de dez participantes humanos. As respostas
foram submetidas a leitura qualitativa, registrada em `revisao_conversas.json`;
não usamos um modelo externo como juiz nem contamos só presença de palavras.
`candidato_motor.json` e `candidato_http.json` preservam todas as respostas.

Motor e HTTP concordam literalmente nas sete sessões aprovadas. Na sessão
de desenho, três aberturas variam palavras sociais; a falha de retomada
permanece nos dois. O servidor HTTP recebe somente `message/history` e
reconstrói a sessão, sem memória pré-preenchida no corpo pelo avaliador.

## Mudança de produção

- `conversa_dialogo.py` carrega a **mesma GRU própria** de 88.969 parâmetros
  da Fase 1. Não houve novo treino, parâmetros ou pesos de terceiros.
- `rotear_escrita` reutiliza a gramática de pedidos existente e a última
  escrita. O roteador resolve referências indiretas, continuação e final.
  Nenhuma nova memória estruturada foi adicionada.
- O modelo recebe ato, argumentos selecionados, mensagem e histórico curto.
  Sua influência textual continua residual; os argumentos decidem o estado.
  Isso não significa interpretar livremente todos os detalhes do histórico.
- A guarda de conversa permite linguagem composta, sem exigir cópia de
  uma resposta alvo. Proíbe tokens fora do vocabulário avaliado, nomes ou
  números literais não fornecidos, argumentos ausentes, troca de personagem
  e declarações de gosto/preferência como se fossem fatos reais. Ficção
  permanece marcada e não é enviada à memória como declaração do usuário.
- Fatos, cálculo, fonte e consultas de memória mantêm a guarda rígida.
  Uma história factual/verdadeira pede esclarecimento em vez de usar ficção.
- Falta de personagem não permite usar o “amigo” do final como personagem.
  Estilo ou quantidade de argumentos fora do escopo preservam o executor
  anterior; uma geração rejeitada não vira a escrita ativa.
- `dialogue_generation` no HTTP e `dialogo` no trace de roteamento informam
  uso da rede, uso do estado da sessão, argumentos, checkpoint, recuo e
  política. A flag experimental de laboratório não pode entrar no JSON
  público. O endpoint GET também informa a ativação aprovada de diálogo.

Duas falhas reais das sessões novas foram corrigidas no roteamento já
existente: “gosto de histórias sobre…” passa a resolver a personagem;
“Pernélia mudou de ideia: agora gosta de graviola” atualiza só a pessoa
mencionada, mantendo a fala original como fonte. A resposta estrutural de
autoria identifica os argumentos ativos, sem tentar gerar uma explicação
que o checkpoint ainda não sabe fornecer.

## Aprovação e isolamento

`aprovar.py` exige os resultados do motor e HTTP, os hashes congelados,
as duas narrativas e ≥6/10 sessões na revisão. Só então publica
`rede_dialogo_conversa.json.gz`, com aprovação restrita a
`historia/continuar/corrigir`. O arquivo original experimental do #126
continua **`aprovado:false`, `ativo_no_chat:false`**. Os 35 pesos anteriores
mantêm os hashes; o checkpoint factual não foi sobrescrito.

A cópia de produção contém os mesmos valores de pesos, vocabulário e
dimensões; apenas acrescenta a aprovação e seus metadados. O carregador
confere o digest dos pesos avaliados. `aprovado:true` isoladamente não
ativa um arquivo: faltam escopo, origem e métricas obrigatórias.
`aprovacao.json` registra as condições pré-merge e os hashes. A validação
no site após o merge é obrigatória e não é substituída por esse certificado.

## Validação e reprodução

Ambiente local: Python 3.12.14, NumPy 2.3.5, CPU, um thread BLAS/OMP.
O modo HTTP usa um servidor real de loopback com o mesmo handler público.

```sh
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python experimentos/integracao_dialogo_20261010/avaliar.py --modo motor --candidato experimentos/dialogo_20261010/checkpoint_gru_dialogo.json.gz --saida /tmp/candidato-motor.json --exigir-meta
python experimentos/integracao_dialogo_20261010/avaliar.py --modo http --candidato experimentos/dialogo_20261010/checkpoint_gru_dialogo.json.gz --saida /tmp/candidato-http.json --exigir-meta
python -m unittest testes_conversa_dialogo testes_roteamento_natural testes_roteamento_natural_v2 -v
python -m unittest discover -s experimentos/dialogo_20261010 -p testes_experimento.py -v
python experimentos/integracao_dialogo_20261010/avaliar.py --modo http --so-congelado --saida /tmp/padrao-http.json --exigir-meta
```

O CI existente ganha os contratos da integração e os 37 casos HTTP no
job de roteamento. Não é uma correção lateral de CI; é o check de entrega
obrigatório desta capacidade. A matriz completa permanece manual/semanal.

## Falhas restantes e próximo passo

As três sessões reprovadas continuam no conjunto, sem suavizar o critério:

1. **Desenho depois de pausa:** “Voltei. O que estávamos fazendo?” não
   retoma a mariposa jardineira/caderno, embora o objetivo continue guardado.
2. **Resposta ao esclarecimento:** “Quero saber de Dorlécio” cai em busca
   factual. A consulta nominal explícita seguinte funciona; isso não apaga
   a falha desse turno.
3. **História com cenário e restrições:** final com personagem/cenário não
   concluído; “Não invente um nome” cancela escrita; pedido posterior de
   cinco frases não reconhecido. Esse percurso usa o gerador anterior.

Os enredos da nova GRU são curtos e repetitivos, vindos do corpus de
**31 padrões deslexicalizados**. Não são conversa humana plena ou
raciocínio geral. Sete sessões aprovadas incluem respostas estruturadas,
fatos e cálculo; não são sete sessões inteiramente geradas pela rede.

Depois de validar esta versão no site, o próximo passo único da Fase 3
é incorporar essas falhas e aumentar a diversidade dos diálogos autorais
antes do segundo treino. Não adicionar memória, acervo ou parâmetros.
