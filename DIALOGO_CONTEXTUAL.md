# Conversa contextual treinada do zero

A nova arquitetura trabalha com a sequência real de mensagens e respostas.
**A geração candidata fica desativada por padrão.** O primeiro treino fez
25/72 turnos contra 29/72 da referência anterior. A segunda tentativa, com
regularização e amostragem autoregressiva, fez 26/72 na main atualizada antes
dos reparos gerais. A leitura humana encontrou frases sem sentido mesmo em
aprovações lexicais. Isso impede sua promoção como melhoria pronta.

A integração parte da **main `8985096`**, que já incorporou Astronomia, a
rede de 193 classes e o microcircuito associativo. Esses dados e pesos foram
preservados. O modo padrão acrescenta interpretação de pedidos de definição
com cortesia e verbos auxiliares, autodescrição básica e fontes da resposta
anterior. Essas melhorias são regras composicionais explícitas, não
resultados aprendidos pelo novo gerador. Na sonda de regressão, o padrão
passou de **29 para 31/72** turnos e de **uma para duas/18** conversas completas;
o padrão com geração experimental fez **29/72 e duas/18**. A meta de
conversação livre continua não atendida.

[Relatório com todas as respostas e comparação](avaliacoes/dialogo_contextual_20261001.json).

Para testar o candidato localmente, use `python web_local.py --dialogo-experimental`
ou `python crivo.py --dialogo-experimental`. O modo também é selecionável por
`Crivo(usar_dialogo_contextual=True)`; o payload HTTP não pode ativá-lo.

O encoder bidirecional com GRU aprende representações de palavras e
subpalavras, distingue a origem das falas e tem duas decisões separadas:
encaminhar conversa/consulta/escrita e interpretar atos e trechos literais.
O segundo resultado precisa ser aceito para alimentar a memória semântica.
Autorizar conversa não autoriza guardar uma interpretação incerta.

O gerador tem um encoder bidirecional, decoder GRU, atenção aprendida e
cópia de posições do texto. Recebe mensagem e histórico inteiros; não recebe
ação, estilo, slots, spans ou respostas de uma tabela. Seus pesos, vocabulário
e embeddings são aprendidos do zero. A cópia permite conservar palavras
novas, mas não comprova que seus conceitos foram aprendidos.

## Memória e evidências

Cada instância conserva até doze turnos reais, inclusive falhas de resposta.
Relatos do usuário, respostas geradas e evidências verificadas têm origens
distintas. Spans precisam conferir com os offsets do texto original.
Hipóteses e falas citadas não se tornam automaticamente estados reais.
Correções explícitas conservam as fontes anterior e corrigida; referências
ambíguas preservam alternativas. Mudar de assunto cria um segmento e retomar
usa somente fontes recentes disponíveis. Reiniciar limpa a memória.

A geração usa o segmento ativo e pode recuperar fontes literais de memória.
O encoder limita a mensagem atual a 96 tokens e o histórico a 64; o gerador
dispõe de 192 tokens de fonte e até 96 de resposta. Esses limites também
podem impedir a recuperação de um detalhe antigo.

Consultas reconhecidas pelo motor factual, relações, código, escrita
estruturada e fontes mantêm prioridade. Uma resposta conversacional não
recebe prova lógica nem escreve no conhecimento. O replay HTTP reconstrói
o estado com perguntas anteriores; não aceita IDs, quadros ou evidências
fornecidos pelo navegador. Nenhuma conversa da sessão treina os pesos.

## Dados e avaliação de desenvolvimento

O currículo autoral tem **10.478 exemplos de treino e 1.340 de desenvolvimento**,
em 633/152 famílias e 35/12 grupos separados. Contém 23 atos e nove papéis,
2.914/681 respostas distintas. Há 130 respostas genéricas compartilhadas
entre partições; não há contextos completos ou famílias compartilhados.
São exemplos sintéticos composicionais, não milhares de conversas humanas.

O complemento [OpenAssistant](dados/NOTICE_dialogos.txt) contém 62 pares
públicos sob Apache 2.0, separados por árvore. Apenas 26 de treino e cinco
de desenvolvimento cabem inteiros nos limites do gerador. O treino final
do gerador tem, portanto, 10.504/1.345 exemplos. Os textos são dados de
treino; não fornecem pesos, tokenizer ou modelo pré-treinado.

O encoder possui 68.573 parâmetros. Seu head de rota acerta **1.230/1.340**
no desenvolvimento, contra 1.169 de uma previsão sempre majoritária.
Entre 1.141 previsões aceitas, 1.127 estão corretas. A média mascara diferenças:
o recall é 97,9% para conversa, 68,6% para consulta e apenas 4% para escrita;
o recall macro é 56,8%. A escrita precisa dos operadores do motor existente.

O quadro fino continua fraco: **494/1.340** atos corretos, **106/142** entre
previsões aceitas e F1 de trechos emitidos de **0,348**. Por isso, ele não é
requisito para gerar conversa e seu aceite não representa certeza de
compreensão. Esse conjunto participou de seleção de época, calibração e
desenvolvimento da arquitetura; não é uma avaliação externa cega.

O gerador tem **971.578 parâmetros**, embeddings de 64 e estado de 96.
A segunda tentativa executou doze épocas e selecionou a oitava pelo
desenvolvimento. Usou dropout locked de 0,2, dropout lexical de 0,1 e
amostragem autoregressiva até 0,1 após aquecimento de três épocas. A
perplexidade de desenvolvimento caiu de 4,779 para 3,029; isso não melhorou
a conversa o suficiente. Nas cinco respostas humanas de desenvolvimento,
a perplexidade ainda é 17.968 e nenhuma geração coincide com o alvo.
Métricas de próxima palavra com a anterior correta fornecida são separadas
das respostas livres. Uma frase terminar ou copiar um nome não garante
gramática, pertinência ou raciocínio. A avaliação salva os textos completos.

`avaliar_dialogo_real.py` mantém 72 turnos em 18 conversas congelados antes
das novas respostas. A referência anterior atende 29/72 e uma conversa
completa. Os critérios originais não são dados de treino nem foram alterados. A sonda
foi consultada para diagnóstico e regressões; a reavaliação final não é
um teste cego independente do desenvolvimento. Mesmo sua pontuação não
mede conversa irrestrita; as saídas exigem leitura humana.

Os três artefatos grandes são versionados como `*.json.gz`, sem perdas.
A leitura aceita JSON e gzip; um JSON produzido por novo treino tem
precedência sobre o arquivo gzip de mesmo nome. O gerador do currículo
reconstitui o JSON original. Hashes do conteúdo descomprimido constam
no relatório comparativo.

## Reproduzir e continuar o treinamento

```bash
python -m pip install -r requirements.txt
python scripts/gerar_curriculo_compreensao.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python treinar_compreensao.py --epocas 15 --lote 48 --ocultos 40 --embeddings 24 --baldes 2048 --semente 2718 --dropout 0.3 --dropout-trechos 0.5 --suavizacao-atos 0.1 --paciencia 2 --avaliar-cada 5
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python treinar_dialogo_seq2seq.py --corpus curriculo_compreensao.json --dialogos-humanos dados/dialogos_humanos.json --limite-resposta 96 --epocas 12 --semente 173 --dropout 0.2 --dropout-tokens 0.1 --amostragem 0.1 --aquecimento 3 --relatorio avaliacao_seq2seq.json
python avaliar_dialogo_real.py --experimental --saida avaliacao-dialogo-real.json --permitir-falhas
python -m unittest discover -p 'testes*.py'
python -m unittest contratos_dialogo_real -v
```

O workflow manual **Treinar conversa contextual do zero** publica candidatos
e relatórios para revisão. Não promove automaticamente seus pesos.
`contratos_dialogo_real.py` conserva os contratos ainda não atendidos; sua
execução explícita pode falhar. Os testes padrão verificam os mecanismos e
as regressões existentes, sem transformar metas pendentes em aprovações.
Para ampliar os dados, mantenha textos pertinentes ao pedido, rótulos e
spans literais corretos, grupos de conversa separados e licenças registradas.
Não use as sondas como material de treino nem as respostas do próprio Crivo
como exemplos corretos sem revisão.

NumPy acelera o treino e a inferência; `requirements.txt` instala-o no
serviço. A inferência também funciona com Python padrão 3.8+, mas replay de
dez perguntas com gerações longas pode ultrapassar vinte segundos sem NumPy.
Os caches compartilham somente checkpoints, sem armazenar mensagens.

Essa arquitetura permite novos experimentos de aprendizado e contexto. O
volume de dados e a qualidade atual dos modelos ainda limitam a conversa;
não há consciência, pensamento humano ou evolução automática pela sessão.
