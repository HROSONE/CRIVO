# Gerador com histórico textual — experimento isolado, 10/10/2026

O gerador de produção preserva argumentos selecionados, mas neutraliza
boa parte do texto/histórico e usa uma representação sem ordem. Este
experimento testa diretamente a arquitetura **própria já existente** em
`dialogo_seq2seq.py`: encoder BiGRU, decoder GRU, atenção e cópia aprendida.
Ela recebe somente mensagens e papéis; nenhuma intenção, ação, slot ou
resposta do avaliador entra na inferência. Não há alteração no chat.

## Separação antes do treino

`avaliacao_congelada.json` e `protocolo.json` foram registrados primeiro,
no commit `9b9eac9`. São 12 sessões de três turnos (36 respostas livres),
com formulações, nomes e situações novos, mais uma pergunta real do dono
sobre dinossauros/IA. Seu SHA-256 é
`70bfd19538677e6f617f0ab79b8a3856e844d9b3600865d876442e69f4e72d01`.
O dono escreveu seu pedido; as outras sessões e a revisão foram escritas
pelo agente. **Não é avaliação humana independente ou cega.**

As sessões usam as respostas efetivamente geradas como histórico nos
turnos seguintes. Não existe alimentação das respostas corretas. A mesma
rede é comparada sem histórico e com histórico invertido. Triagem lexical
serve para encontrar falhas, não para certificar naturalidade ou ausência
de toda invenção. Aprovação exige revisão qualitativa e os critérios do
protocolo; ambos os checkpoints permanecem `false/false`.

## Corpus e preparação

- Piloto: 100 famílias/80 no treino/20 inteiras na validação;
  979 exemplos únicos de treino e 184 de validação. Expansões lexicais
  são deduplicadas. A validação tinha 396/3.219 tokens-alvo impossíveis
  de gerar/copiar; interrompeu na época 12, selecionando a época 4.
  As respostas de desenvolvimento eram ruins. Piloto preservado.
- Rodada 2: mesmos 100 padrões autorais em dez grupos; 100 reformulações diferentes
  reservadas ao desenvolvimento e 24 aberturas conversacionais.
  **3.707 treino + 334 validação**, 1.313 respostas literais distintas.
  Zero token-alvo impossível, fonte inteira até 57 tokens, alvo até 26.
  Reformulações de desenvolvimento compartilham operações/saídas com
  treino: **não medem generalização a tarefas novas**. Os prefixos e
  nomes variados não são contados como novas famílias semânticas.

Cobrem conversa sem personagem, preferência/correção, mudanças de assunto,
hipóteses distintas de fatos, esclarecimento, escrita, continuação e ajuda
prática. São exemplos autorais de supervisão, não banco consultado pelo
gerador nem diálogos humanos observados. Nenhum pedido congelado ou tema
dinossauros/meteoro foi inserido no treino.

## Treino real

Pesos aleatórios próprios, semente 173, NumPy, CPU, uma thread BLAS.
Piloto: **81.166 parâmetros/717 tokens**. Rodada 2: **81.433/720**,
menor que os 85.130 parâmetros da GRU de produção. As três GRUs têm 24
unidades, embeddings 16, subpalavras em 128 buckets, fonte 192,
resposta 64, Adam 0,003. Até 30 épocas, validação a cada duas,
parada após oito épocas sem melhora, dropout 0,1, dropout lexical 0,05,
amostragem autoregressiva até 0,05. Hiperparâmetros iguais nas duas rodadas.
Nenhum checkpoint factual/produção é sobrescrito e nenhum peso de terceiros
é baixado, executado ou integrado.

O segundo corpus foi preparado usando apenas a perda e as saídas de
**desenvolvimento** do piloto; `protocolo_rodada2.json` documenta essa
revisão antes do segundo treino. A avaliação final ficou reservada.
Hashes dos dados, scripts, arquitetura, treinador e pesos são registrados
nos manifestos. Duração fica no relatório. Não afirmar reprodução byte a
byte sem executar e comparar outro treino.

## Medição — checkpoint REPROVADO

Treino efetivo: **20 épocas / 330,13 segundos**, melhor época 12.
Entropia teacher-forcing: treino **0,1195**, desenvolvimento **2,3756**.
Na amostra livre de desenvolvimento, apenas **1/48** corresponde ao alvo
(igualdade literal não é requisito de conversa). Perda de treino baixa
não representa compreensão do pedido.

| Caminho | Sessões na triagem | Turnos na triagem |
|---|---:|---:|
| Aleatório com mesmas dimensões do piloto | 0/12 | 0/36 |
| Seq2Seq próprio preexistente, 971.578 parâmetros | 2/12 | 14/36 |
| Novo checkpoint, histórico real dos dois papéis | **0/12** | 6/36 |
| Mesmo checkpoint, sem histórico | 0/12 | 9/36 |
| Mesmo checkpoint, histórico invertido | 0/12 | 8/36 |

Rede antiga e nova têm capacidades/dados diferentes: não é comparação
controlada de tamanho. Nenhum dos acertos lexicais aprova naturalidade.
Os controles do **mesmo checkpoint** não mostram benefício no holdout.
Não houve truncamento de fonte em nenhuma das 36 respostas por condição;
todas chegaram ao EOS. Terminar a frase não garante frase coerente.

Revisão das 36 respostas com histórico: **0/12 mantêm o fio**. Pelo menos
duas inversões observadas: quarta reaparece depois da mudança para domingo;
bússola reaparece depois da correção para caleidoscópio. A triagem aceita
fragmentos incoerentes por encontrar palavras como chefe/prazo/estação.
Não afirmar zero invenção nem fidelidade geral. Ver
`revisao_qualitativa.json` e saídas completas dos três controles.

Pergunta real do dono (reservada fora do treino):

> Você pode mais meteoro um meteoro com o que a divisão para as ela ficou
> para para outra vez para para outra meteoro?

**Reprovada**: não responde ao dilema ético nem à comparação dinossauros/IA.
Não foi treinada uma resposta específica depois de ver esse resultado.

Diagnóstico separado nos **100 pedidos vistos no treino**: 87/100 alvos
literais com histórico, contra 32/100 sem histórico. Quatro nomes novos
foram copiados corretamente usando a mesma pergunta treinada sobre nome.
Isso mostra uso textual em padrões conhecidos; **não é generalização de
linguagem**. O controle de correções congeladas com a mesma bolsa de tokens
e ordem diferente dá 0/2: respostas distintas não bastam para acertar.

O checkpoint experimental `1027f94344ca2f0853a7dbecf709f797757763cf89bc219625448771c8d6d080`
continua `aprovado: false`, `ativo_no_chat: false`. O piloto
`e993b0aa…` também foi preservado. A auditoria confirma pesos de raiz,
arquitetura, treinador, motor, integração e configuração de publicação
idênticos à base; somente experimentos e passagem/roadmap mudam.

O site público foi consultado nos 36 turnos mais o pedido real:
`antes_site.json`. O contrato público recebe somente mensagens anteriores
do usuário, enquanto a rede experimental recebe os dois papéis. Por isso
esses caminhos não são uma comparação controlada de treinamento.
Na pergunta real, a produção reconhece IA e informa ausência de evidência
para a pergunta completa, sem acompanhar a comparação/merecimento.

## Reprodução

Em um checkout isolado do commit `ef3454d` (antes do resultado da rodada 2),
com NumPy instalado, o corpus e protocolo já estão versionados:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/gerador_historico_textual_20261010/rodada2.py treinar
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/gerador_historico_textual_20261010/rodada2.py avaliar
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experimentos/gerador_historico_textual_20261010/testes_experimento.py -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest testes_seq2seq -v
```

Treinadores recusam sobrescrever checkpoints. O piloto já está preservado
nesse commit; não precisa sobrescrevê-lo. Corpus, protocolos e avaliação são arquivos versionados; não
recongelar as sondas ou regenerar dados silenciosamente. Não reexecutar a
avaliação após adaptar o treino às suas respostas e chamá-la inédita.

## Limites e próximo passo

100 padrões de supervisão continuam sendo um corpus estreito; variantes lexicais e
prefixos repetidos podem favorecer memorização. Rede pequena, respostas
curtas, vocabulário restrito e nenhuma garantia geral de verdade, gramática,
referentes, opinião contextual ou longas sessões. Não há integração no
site, nem nova memória, regra de orientação, guarda ou workflow de CI.
**Portão falhou: não integrar nem promover.** O próximo trabalho único é
variar as formulações de entrada por ato no corpus próprio, além das
trocas de nomes e prefixos, e congelar outra avaliação antes de novo treino.
Estes 12 casos viram regressão conhecida, não holdout inédito novamente.
Não aumentar parâmetros para tentar compensar a memorização observada.
Validação local: 19 testes da matemática/inferência e cinco de integridade
dos dados/isolamento verdes. CI por escopo existente; nenhuma matriz nova.
