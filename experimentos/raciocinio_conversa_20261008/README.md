# Memória de trabalho e raciocínio em conversa — 2026-10-08

O chat agora calcula conclusões sobre custos compostos, duração de atividades,
disponibilidade de participantes e requisitos declarados. Conserva correções,
recusa referências ambíguas e calcula hipóteses numa cópia do estado real.
Também conserva objetivos, impedimentos e alternativas pessoais para um resumo
fiel. São componentes estruturais próprios; os ajustes de transformer abaixo
continuam experimentais e não foram ativados no chat.

## Resultado e limites

| Painel | Resultado |
| --- | --- |
| Primeiro controle numérico e de memória | 39/48 contratos, sem exceções |
| Mesmo controle depois das correções (diagnóstico conhecido) | 48/48 contratos |
| Transferência autoral com falas, nomes e números novos | 24/24 contratos no motor e 24/24 no adaptador web |
| Conversas pessoais na transferência | 5 respostas adequadas, 3 parciais, 0 falhas, por leitura autoral |
| Sessões pessoais completas, exigindo todas as respostas adequadas | 0/2 |

O agregado de contratos verifica valores e operações, não palavras na resposta.
As 8 falas pessoais/criativas não entram nesse agregado automático. A leitura
manual considera a associação inicial e a abertura do dilema parcialmente
atendidas porque apenas resumem a fala; a alteração do narrador também é parcial.
As cenas são molduras textuais limitadas. Não demonstram criação irrestrita ou
raciocínio neural geral. Nenhum desses painéis é uma avaliação independente.

As coletas integrais estão nos arquivos `controle_*.json` e
`transferencia_*.json`. O primeiro coletor podia anexar uma análise anterior
quando a rota de recusa não acrescentava histórico; essa falha foi corrigida
antes da transferência. A coleta inicial permanece preservada. Seus acertos
exigiam resultado e operação corretos; a análise anterior não transforma a
recusa daquele turno em acerto. O baseline registra 2/48 contratos (preservação
de consulta factual e reinício). Como ele não exportava o novo contrato, esse
número não é uma medida semântica comparável das respostas antigas.

O controle foi fixado no commit `76acc16`; sua primeira execução usou
`6f9d8a7`. Depois de ler os erros, ele virou diagnóstico conhecido. A
transferência foi fixada em `8ba36b2`, antes das correções seguintes, e coletada
no commit `a1b48d0`. SHA-256 dos conjuntos estão em `protocolo.json`.

## Experimentos com os pesos próprios

| Experimento | Resultado retido | Decisão |
| --- | --- | --- |
| Cabeça linear de 1.925 parâmetros sobre transformer 2.612.352 congelado | 132/240 classificações corretas; 70,7% de precisão mesmo entre propostas com confiança ≥ 0,9 | Rejeitada |
| Ajuste do corpo próprio 2.612.352 + cabeça de 965 parâmetros, 600 atualizações | 12/20 classificações corretas em famílias novas; 7/10 entre as propostas de alta confiança | Rejeitado |
| Ajuste de redação do transformer 2.612.352, 600 atualizações | Fidelidade numérica: 0/48 antes, 37/48 depois | Rejeitado para redação no chat |

Os dois testes de interpretação são diferentes e não permitem comparar seus
percentuais diretamente. A redação recebe a conclusão já calculada no prompt:
seu acerto não significa que o transformer realizou a conta. Os números de
entrada do teste de redação estão entre 100 e 199; o treino usa 1 a 99. O
verificador desse piloto avalia número, direção e opção, e não toda a semântica
de eventuais frases extras. Mesmo nesse contrato limitado, 11 respostas trocaram
números. Não selecionamos checkpoints usando o controle de conversas.

`comparacao_bruta.json` e `comparacao_modular_bruta.json` preservam também a
geração direta dos três checkpoints existentes, sem recuperador: linguagem
2,6M, leitor 17,4M e piloto modular 17,4M. O leitor e o modular têm funções e
formatos de treinamento específicos; essas saídas não medem sua qualidade
nas funções originais. Mostram que eles não podem simplesmente substituir o
chat. O export modular exigiu copiar sua configuração externa para o campo
`meta` do executor; os arrays ficaram intactos e os pesos de origem não mudaram.

Scripts, corpus sintético, resultados integrais e hashes dos checkpoints foram
preservados em `treinos/`. Os pesos candidatos ficam em:

- `/workspace/experimentos/crivo-interpretador-operacoes-20261008/cabeca.json`
- `/workspace/experimentos/crivo-ajuste-interpretacao-20261008/pesos.pt`
- `/workspace/experimentos/crivo-ajuste-redacao-20261008/pesos.pt`

O runtime do chat não referencia essas pastas. Não houve aumento de arquitetura,
download de pesos de terceiros ou uso de modelos externos. CPU, NumPy e PyTorch
foram usados nos pilotos. Dados pessoais reais não entraram no treinamento.

## Como funciona

`raciocinio_conversa.py` separa extração de argumentos, memória, operação e
redação. Dinheiro usa `Decimal`. Agendas usam interseção de conjuntos. Requisitos
usam `SistemaPremissas`, com suporte explícito de afirmações e negações.
O alvo da prova é **cumprir os requisitos informados**, não garantir que uma
ação ocorrerá no mundo. Itens desconhecidos permanecem desconhecidos.

Cada atualização tem origem e fala de suporte; uma hipótese não sobrescreve a
realidade. A memória numérica limita participantes, atividades e opções, e
conserva até 48 eventos. `argumentos_conversa.py` mantém até 4 objetivos, 3
impedimentos e 12 fontes pessoais por instância. Cenas ficam em escopo de ficção
e não alimentam os fatos pessoais. Não inferimos doença, sentimento ou causa
a partir de uma associação mencionada pela pessoa.

O adaptador publica `conversational_reasoning` ou `conversational_arguments`
apenas para o turno atendido por esses componentes. `has_proof` continua falso
para reflexões pessoais, cenas e contas; a análise proposicional efetiva fica
no campo `prova` do contrato de requisitos. Não há armazenamento no servidor.
O navegador ainda reconstrói a sessão com até 10 mensagens: dados fora dessa
janela não têm persistência adicional. Os pesos e as rotas factuais, de código,
de crise e de memória anteriores continuam com seus contratos próprios.

## Reproduzir

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest testes_raciocinio_conversa testes_argumentos_conversa -v
python -S -m unittest testes_raciocinio_conversa.TestesRaciocinioConversa testes_argumentos_conversa.TestesArgumentosConversa -v
python experimentos/raciocinio_conversa_20261008/avaliar_conversas.py --raiz . --conjunto transferencia --saida /tmp/transferencia-reproducao.json
```

Para treinar novamente, use uma **pasta nova**. Os scripts recusam sobrescrever
um candidato existente. Dependências de treino são as próprias do projeto.

```sh
python experimentos/raciocinio_conversa_20261008/treinar_interpretador.py /tmp/cabeca-nova
python experimentos/raciocinio_conversa_20261008/ajustar_transformer.py interpretacao /tmp/interpretacao-nova
python experimentos/raciocinio_conversa_20261008/ajustar_transformer.py redacao /tmp/redacao-nova
```

O próximo ganho de linguagem exigirá corpus próprio mais diverso e avaliações
independentes de diálogo, extração de argumentos e fidelidade de redação. Os
resultados atuais não sustentam ativar geração livre nem exigir 17 milhões de
parâmetros como solução por si só.
