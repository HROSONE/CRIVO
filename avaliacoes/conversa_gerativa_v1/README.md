# Treino de geração de conversa

O chat público ainda usa predominantemente respostas cadastradas. O Transformer
causal próprio tem 2.612.352 parâmetros, mas o checkpoint anterior não sustenta
conversa aberta coerente. A baseline preserva suas respostas livres, inclusive
repetições e texto sem sentido. Este trabalho não declara essa limitação resolvida.

O novo treino atualiza pesos por AdamW e perda de próximo token, condicionada a
histórico e pergunta. Tokens do usuário e do histórico ficam mascarados na perda
supervisionada. Nenhum peso, tokenizer ou modelo de terceiros é importado.
Continuação usa exclusivamente `artefatos/linguagem_profunda` do próprio projeto.

Dados: mensagens humanas públicas revisadas OASST2, Apache-2.0, revisão e hashes
fixados; textos da Wikipedia em português, CC-BY-SA-3.0/GFDL, revisão e hashes
fixados; demonstrações sintéticas autorais preparadas pelo assistente. Textos
sintéticos não são atribuídos a humanos. Nenhum arquivo enviado pelo usuário
entra no corpus. As referências factuais dos exercícios constam no manifesto;
dados humanos públicos não são automaticamente evidências verificadas do chat.

As partições humanas permanecem separadas por árvore. Exercícios de transferência
separam nomes de componentes e memória entre treino, validação e teste. Alvos
normalizados compartilhados entre partições são removidos. O tokenizer permanece
o mesmo do checkpoint próprio: não é ajustado nos exemplos reservados novos.
A sonda de desenvolvimento foi escrita antes do currículo, não é lida pelo
preparador e não seleciona checkpoints. Ela não é uma certificação independente.

O avaliador registra cada resposta gerada, término, diversidade, cópia exata de
alvos e perda separada em humanos/sintéticos reservados. Sua triagem por palavras
é fraca e não certifica correção semântica. Respostas integrais exigem revisão.
Os contratos independentes de `contratos_dialogo_real.py` permanecem inalterados.
Seleção do checkpoint usa validação; o teste não altera os pesos.

O workflow `treinar-conversa-gerativa.yml` inicia na publicação desta branch e
também permite execução manual. Continua o pré-treino em português antes de SFT
com metade dos exemplos do lote humanos. Salva corpus, pesos, Adam, RNG, progresso
e relatórios em artefato por 30 dias. Orçamento de tempo pode pausar antes do número
de passos pedido; o relatório registra os passos realmente executados. Download
do artefato é necessário para preservar esses arquivos além da retenção.

Não há promoção automática ao site. Um modelo que gere texto gramatical, mas
invente fatos ou ignore contexto, não deve substituir o motor público por causa
de uma queda na loss ou de uma pontuação lexical.

Execução local (dependências de treino instaladas):

```sh
python scripts/preparar_conversa_gerativa.py --oasst2 fontes/oasst2.messages.jsonl.gz --saida corpus
python scripts/treinar_linguagem_profunda.py --corpus corpus --saida candidato --fase dialogo --inicial artefatos/linguagem_profunda --ajustar-proprio --passos 1800 --lr 0.0004 --podar-padding --selecionar-melhor
python scripts/avaliar_conversa_gerativa.py --modelo candidato/melhor --corpus corpus --saida resultado.json
python dialogo_linguagem_profunda.py --modelo candidato/melhor
```

Para ampliar o pré-treino, use `--wikipedia fontes/wikipedia.pt.parquet` ao preparar
o corpus. Cada documento mantém URL, título e identificação nos JSONL do artefato.

`gerador_dialogo_numpy.py` disponibiliza geração dos mesmos pesos no servidor leve,
sem instalar PyTorch ou tokenizers. Reutiliza o BPE e implementa cache K/V; testes
comparam logits, tokenização, marcadores literais e rebase da janela ao PyTorch.
O adaptador escolhe NumPy para um diretório que contenha `pesos_numpy.npz` e
`tokenizer.json`, sem `pesos.pt` (como `trabalho/numpy` no artefato do workflow).
Isso torna a execução possível; não ativa nem aprova o candidato no site público.
