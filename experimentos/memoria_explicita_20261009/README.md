# Memória explícita para fatos e hipóteses

Continuação após rejeitar os dois treinos de `../memoria_fontes_20261009`. Mantém o checkpoint anterior próprio e o preparo novo. O transformer propõe uma operação; a composição intervém apenas nas operações e situações da gramática suportada. Não há novos pesos ou treino nesta etapa.

Um registro separa fontes factuais e alternativas por entidade/papel. Uma nova hipótese parte dos fatos; correção real encerra a hipótese; confirmar promove a alternativa preservando o trecho literal de origem; retorno descarta a alternativa, mantendo fatos confirmados. Perguntas explícitas selecionam entidades. Ambiguidade ou operação fora do suporte preserva a proposta neural. Sem gold, família, evento correto ou futuro na interface.

Este ganho, se confirmado, é **engenharia de memória e gramática do sistema híbrido**, não prova de que o transformer aprendeu a raciocinar ou redigir conversa livre. Não há modelo ou tokenizer externo. Cópia literal limitada e executor próprio continuam partes do resultado. Nenhum peso ativo é alterado.

Antes de abrir os novos casos, ficam congelados ledger, testes, avaliador, pesos, dependências, protocolo e hashes dos casos/gerador de outra autoria. O painel novo será escrito sem leitura do ledger ou previsões. É autoria diferente dentro da equipe, com gramática finita, não avaliação externa independente. Os quatro painéis anteriores já são conhecidos. O avaliador conserva todos os traços, cobertura, abstenções, fontes exatas, episódios completos e erros.

Critério prévio para esta composição: ≥80% em cada correção/hipótese/retorno/confirmação; ≥90% em cada família; ≥80% de sessões completas no painel novo; ganho geral ≥10pp sobre anterior+preparo novo; queda máxima de5pp nos quatro painéis conhecidos:408 da rodada anterior, retenção, associação e contextual. Mesmo passar isso não aprova chat livre.

O `aplicar(turnos, proposta_neural)` não lê rótulos. Em abstenção, deve devolver proposta neural intacta. A avaliação do painel novo executa o modelo anterior; regressões reutilizam traços congelados do mesmo baseline com IDs/fontes equivalentes, evitando inferência repetida.

## Resultado concluído

16 testes de comportamento/integridade passaram antes do congelamento e da abertura do painel. São casos úteis de confirmação, abandono, nova hipótese baseada nos fatos, escopo negado, entidades distratoras, ordem da pergunta, inventário e abstenção sem mutação. No caderno com o modelo real, baseline4/5 e memória5/5: a confirmação de19 permanece19 no retorno, com fonte literal do turno da hipótese. Registro completo em `verificacao_caderno.json`.

| Painel | Baseline | Memória | Sessões completas baseline→memória | Cobertura memória |
|---|---:|---:|---:|---:|
| novo_reservado | 133/368 | 143/368 | 1→1/72 | 11/368 |
| prospectivo_anterior_conhecido | 247/408 | 246/408 | 14→12/80 | 23/408 |
| retencao_conhecida | 230/370 | 280/370 | 9→23/80 | 140/370 |
| associacao_conhecida | 295/400 | 306/400 | 34→39/100 | 53/400 |
| contextual_conhecido | 391/400 | 391/400 | 94→94/100 | 0/400 |

**Não passou o critério registrado.** O painel novo melhora apenas10/368 contratos,36,14%→38,86%, com uma sessão completa em72. A memória intervém em apenas11/368 (2,99%). Fora das construções reconhecidas, usa a proposta neural anterior, que continua insuficiente. Não há evidência de conversa livre ou raciocínio geral. O ganho do painel conhecido de retenção230→280/370 (62,16%→75,68%) é diagnóstico/regressão, não generalização nova. O painel408 conhecido perde um contrato e duas sessões completas; esse efeito também foi preservado.

A utilidade comprovada é corrigir transições e fontes na gramática reconhecida, especialmente a sequência de confirmação/retorno do caderno. O parser restritivo tem cobertura pequena para formulações novas. Ampliar a gramática exige nova avaliação: não foram ajustadas regras depois de abrir este painel. A camada permanece experimental, sem ativação automática no chat. Os ganhos não são atribuídos a treinamento do transformer.

A avaliação nova executa o mesmo checkpoint anterior com preparo novo. Os quatro caches conhecidos vêm da rodada congelada de memória de fontes; protocolo/peso/preparo/avaliador e hashes dos caches foram verificados. As métricas de evento neural antigo foram omitidas da comparação composta por não representarem uma classificação treinada válida.

## Reprodução

Na raiz, com Torch/NumPy/tokenizers:

```bash
python experimentos/memoria_explicita_20261009/test_ledger.py
python experimentos/memoria_explicita_20261009/avaliar_ledger.py --laboratorio /tmp/crivo-ledger-repro --protocolo-sha256 e2df426baa1a69d2a39942c7a02a52621caac8361f227b8abeaddabf6e630d57
```

Antes, copie `protocolo.json` e `avaliacao_autoria/` para uma pasta nova `/tmp/crivo-ledger-repro`; deixe-a sem `avaliacao/`. Os pesos/caches e dependências ficam nos caminhos do repositório, conferidos pelo protocolo. O notebook `notebooks/crivo_memoria_confirmada.ipynb` inspeciona os pesos e a memória sem iniciar treino. Sua execução da sequência guiada foi verificada localmente em CPU; Colab real não executado.
