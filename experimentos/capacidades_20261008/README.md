# Capacidades do Crivo — 8 de outubro de 2026

O Crivo da `main` foi medido com a geração própria habilitada. Os experimentos
melhoraram a síntese limitada de código e a conservação de correções pessoais.
A conversa espontânea continua sendo o principal limite observado.

| Sonda autoral | Antes | Depois das mudanças |
| --- | ---: | ---: |
| Conhecimento factual | 51/51 perguntas | Não repetida integralmente |
| Raciocínio sob premissas | 15/15 contratos | Regressões de integração verificadas separadamente |
| Histórias, poemas e reparos de escrita | 28/28 turnos | 28/28 |
| Execução, reparo e síntese de código | 10/12 problemas | 12/12 |
| Conversa espontânea | 45/72 turnos | 47/72 |
| Diálogos espontâneos inteiramente aprovados | 1/18 | 1/18 |
| Controle de síntese com entradas reservadas | 3/10 problemas | 10/10 |
| Controle de correção e reset de memória | 2/6 diálogos | 6/6 |

As respostas completas estão em [resultados](resultados/), e as contagens
estão em [resumo.json](resultados/resumo.json). Os critérios de conversa são
os mesmos antes e depois, com assinatura
`6cc7ca80126a8ca1e49b9d21736ebc1a18c7753cde3eb32bdd6c4184df1d503e`.

## Experimentos realizados

**Síntese estrutural.** A gramática anterior não encontrava `3*x+1` nem o
máximo de um array. A nova extensão tenta expressões com duas operações e
reduções de mínimo/máximo depois que a busca inicial falha. Usa o parser e
executor próprios, com até 1.000 candidatos somando as duas etapas. O maior
número observado no controle final foi 825. Para arrays vazios, as reduções
candidatas retornam `null`; os exemplos fornecidos continuam decidindo se
esse comportamento atende ao contrato. As soluções anteriormente suficientes
continuam sendo escolhidas antes da extensão.

Os dez controles contêm seis funções afins, mínimo, máximo e duas funções
simples de compatibilidade. As 30 entradas reservadas são usadas apenas
depois da resposta única, sem alimentar síntese, reparo ou segunda tentativa.
O código da busca V3 congelada e seus hashes permanecem intactos.

**Correções de memória.** Uma correção direta como “Corrigindo, Brisa é meu
gato” pode retratar uma única cláusula anterior “Meu cachorro se chama Brisa”.
Cláusulas independentes são preservadas. A atualização alcança relatos,
snapshots de retomada e nomes do perfil; o histórico original permanece como
fonte. A extensão não aplica correções condicionais, citadas, negadas, sem
referência ou ambíguas. Isso não é um resolvedor geral de contradições.

Pedidos explícitos para esquecer os relatos reiniciam os estados da sessão;
perguntas pessoais de lembrança usam a mensagem original antes das camadas
cotidianas e da resolução de pronomes. Após o reset, a pergunta sobre o que o
usuário queria cuidar pede contexto em vez de responder com uma ficha de
cuidados de plantas. O fluxo HTTP com replay também foi verificado.

**Resultados negativos.** Ativar o módulo contextual antigo reduziu a
conversa de 45/72 para 37/72: essa opção foi rejeitada. O primeiro candidato
de memória ficou em 2/6, porque outra camada respondia antes de alcançar a
correção. A versão final corrige essa ordem; os testes de integração cobrem
esse caminho.

## Limites da medição

São sondas pequenas, autorais, de desenvolvimento e regressão. Não são um
benchmark externo nem evidência de inteligência geral. Acertar os contratos
de escrita não certifica qualidade literária; acertar programação não significa
criar aplicações arbitrárias.

O [controle](controle_prospectivo.json) e seu hash foram registrados no commit
`39d2658aaa441b4d8675f31120836262b76a761c`, antes de alterar o produto. Ele
foi reutilizado após correções motivadas pelos contratos de unidade e de
integração HTTP. Portanto, a avaliação final **não é cega**. Os exemplos
reservados continuam separados da entrada do sintetizador.

Os tempos dos JSONs incluem inicialização e cargas concorrentes diferentes.
Não permitem concluir aceleração ou regressão de latência. Só um dos dezoito
diálogos espontâneos passou inteiro: as melhorias são específicas, e as
outras falhas continuam registradas.

Nenhum peso foi treinado, substituído ou promovido. O leitor experimental do
PR 112 permanece desativado na configuração padrão. Usamos apenas arquitetura,
tokenizadores, pesos e executor próprios; nenhum dado privado do Drive entra
nestes resultados.

## Verificação do código

Foram aprovados 46 testes de regressão de conversa, memória, programação,
raciocínio e crise, além dos dois testes HTTP reais executados separadamente
com acesso à rede local: 48 testes distintos. Os oito contratos novos também
passaram em Python 3.8 sem NumPy. A integridade dos arquivos da busca V3
congelada é conferida sem dependências opcionais.

Na primeira execução, o sandbox impediu a criação do socket dos dois testes
HTTP. A primeira tentativa com rede local excedeu o timeout de oito segundos
durante a carga concorrente. Uma repetição com inicialização aquecida passou,
e a repetição final sem esse aquecimento também passou nos dois testes,
em 10,178 segundos no total. Não aumentamos os timeouts nem alteramos esses
testes para conseguir aprovação. Isso não constitui uma medição de latência
de produção. A aprovação da CI do PR deve ser acompanhada separadamente.

## Reproduzir

Na raiz do repositório, com as dependências usuais do Crivo:

```bash
python experimentos/capacidades_20261008/medir.py programacao --saida /tmp/programacao-nova.json
python experimentos/capacidades_20261008/avaliar_controle.py programacao --saida /tmp/controle-codigo-novo.json
python experimentos/capacidades_20261008/avaliar_controle.py memoria --saida /tmp/controle-memoria-novo.json
python avaliar_dialogo_real.py --permitir-falhas --saida /tmp/dialogo-novo.json
python -m unittest testes_capacidades_compostas testes_motor_programacao_chat
```

As saídas precisam ser novas. O controle confere seu hash e recusa mudanças
nos arquivos do produto durante a execução. A configuração, os hashes e as
decisões estão no [manifesto](resultados/manifesto.json).
