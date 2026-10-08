# Resgate experimental pelo leitor próprio

A função deste Transformer é selecionar um fato cadastrado que se relaciona
com a pergunta. Ele não gera texto livre nem inventa uma resposta. A integração
preparada aqui consulta o leitor **depois da recusa final** e oferece apenas uma
aproximação, com o fato completo, sua fonte e a ressalva de que não é uma
resposta exata.

**Pesos desativados.** O candidato com verificação de campos acrescentou apenas
uma aproximação correta nos quatro controles, sem erros adicionais observados.
Não melhorou os dois conjuntos congelados; no prospectivo realmente novo para
essa versão também não houve ganho. Isso é insuficiente para promover os
pesos. Todos os artefatos desta pasta mantêm `controle.aprovado: false`.

## Resultados do chat completo

A comparação usa `Crivo(usar_geracao=False)`, igual à comparação factual
anterior. Cada pergunta começa em uma instância nova, tanto no baseline como
no candidato. Contam como acerto uma afirmação correta ou uma aproximação que
mostra o fato correto. Aproximações erradas também são contadas.

| Controle | Perguntas | Acertos anteriores | Acertos com verificador | Aproximações erradas antes → depois |
| --- | ---: | ---: | ---: | ---: |
| Congelado v1 | 72 | 33 | 33 | 5 → 5 |
| Congelado v2 | 70 | 22 | 22 | 1 → 1 |
| Prospectivo inicial | 32 | 3 | 4 | 4 → 4 |
| Prospectivo novo para o verificador | 32 | 9 | 9 | 0 → 0 |
| Total descritivo | 206 | 67 | 68 | 10 → 10 |

Nenhuma resposta anteriormente aceita foi alterada. As afirmações erradas do
baseline permanecem; este experimento não certifica o chat inteiro como livre
de erros. A ausência de novos erros nesta amostra não garante segurança fora
dela. Apenas o segundo prospectivo é novo para a versão com verificador; os
três conjuntos anteriores já tinham servido para diagnosticar a primeira
versão. O total da tabela não é um teste independente de 206 perguntas.

Os relatórios `controle_chat_campo_*.json` contêm somente agregados. O backend
foi PyTorch executando o próprio modelo em CPU; a paridade com a inferência
NumPy foi conferida em duas perguntas de desenvolvimento, não em todas as
perguntas do controle. O prospectivo inicial completo foi depois repetido
com inferência NumPy nativa: todas as métricas agregadas permaneceram idênticas
(`controle_chat_numpy_prospectivo.json`). Não foi avaliado ganho com a geração
habilitada.

`candidato_campo_antes_controle.json` fixa os hashes anteriores à avaliação.
Depois dela houve uma correção das unidades: símbolos como `/`, `°` e `²` são
preservados, e velocidade, área e volume não passam como comprimento. Os
predicados permaneceram idênticos nos 843 pares pergunta/fato dos quatro
controles, conforme `controle_correcao_unidades.json`. A cópia anterior do
verificador está em `historico/`; `conferir_unidades.py --saida CAMINHO`
reproduz a comparação agregada. O histórico ganhou também `verified_field`;
esse acréscimo de diagnóstico não altera a seleção nem a resposta.

## O que foi treinado e o que foi descartado

A base própria tem **17.428.609 parâmetros**, com 8 camadas, dimensão 384,
8 cabeças de atenção e contexto de 256 tokens. Seu backbone permanece
congelado: foram ajustados **385 parâmetros** da cabeça de seleção e
**21 coeficientes** do calibrador. O tamanho da base foi reaproveitado dos
pesos existentes; esta adaptação não precisa treinar novamente os 17 milhões.
Arquitetura, tokenizador, pesos, supervisão e fichas são próprios do Crivo.
Nenhum modelo de terceiros ou checkpoint privado do Drive foi usado.

As 226 perguntas públicas do tutor, sobre 62 assuntos, são supervisão:
161 têm fato-alvo e 65 não têm resposta cadastrada. O treino separa assuntos
em cinco blocos externos e quatro internos; não usa os conjuntos congelados
nem prospectivos para ajustar pesos ou limiares. A regularização final da
cabeça é 0,1; a do calibrador é 0,01; o limiar final é 0,65, obtido pela mediana
das escolhas internas. As 253 linhas de ajuste do calibrador incluem perguntas
repetidas sob diferentes contextos de treino interno; não são 253 exemplos
independentes. O resultado 77 → 80 em `controle_evidencia.json` pertence ao
calibrador antes do verificador de campos, não ao candidato composto final.
Esse diagnóstico usa uma política simplificada da leitura; os controles do
chat completo são a medida efetiva das respostas entregues.

A cabeça linear teve 97/161 seleções corretas na validação por assunto,
contra 89/161 da cabeça original. Isso não representa o acerto do chat. Uma
cabeça residual com oito neurônios também teve 97/161, com AUC ligeiramente
menor (0,770 contra 0,772), e foi descartada (`controle_cabeca_mlp.json`).

A primeira integração, sem verificar o campo pedido, acrescentou dois acertos
no congelado v1, um no v2 e dois no primeiro prospectivo. Acrescentou também
uma aproximação errada no prospectivo e foi rejeitada. Seus resultados e seu
artefato estão preservados como `controle_chat_resgate_*.json` e `candidato/`.
A combinação com o buscador acrescentou erros no desenvolvimento e foi
rejeitada antes de avaliar os controles (`controle_busca.json`). As demais
políticas examinadas estão registradas nos relatórios de desenvolvimento.

## Contrato da integração

- `estado_interno.resgatar` entra após arbitragem, reinterpretação e geração,
  apenas quando a resposta final é uma recusa revisável.
- A pergunta precisa citar uma única entidade e ser factual e direta. Negação,
  perguntas pessoais, comandos de escrita e afirmações absolutas ficam fora.
- O fato precisa pertencer à ficha citada, ter tipo compatível, confiança
  calibrada suficiente e evidência do campo pedido, como autoria ou unidade.
- O resultado sempre é uma aproximação. A probabilidade neural não autoriza
  uma afirmação, mesmo se for 1,0.
- Em execução normal, `ResgateLeitor` procura `artefatos/leitor_resgate/`, exige
  aprovação explícita do conjunto e valida os hashes da base, do tokenizador
  e da cabeça. **Essa pasta não é instalada por este experimento.** Metadados
  ausentes, incompatíveis ou não aprovados mantêm o comportamento anterior.
- `exigir_aprovacao=False` é usado somente para a avaliação experimental em
  memória. Os scripts nunca alteram a aprovação nem instalam o candidato.

O verificador é conservador e não cobre todas as paráfrases, unidades ou
relações possíveis. Sua presença também não prova que qualquer fato com esse
campo responde à pergunta: a seleção neural continua sujeita a erro.

## Reprodução em CPU

Use um ambiente separado com NumPy, PyTorch e tokenizers compatíveis com os
scripts do Crivo. A execução original usou Python 3.12.14, NumPy 2.5.3 e
PyTorch 2.14.1+cpu. Outras versões podem mudar os últimos bits do resultado.

```bash
python experimentos/integracao_leitor_v3/reproduzir.py --saida /tmp/leitor-reproducao
```

A saída deve estar vazia. O script confere hashes da base, do tutor, do cache,
dos traços, do código de inferência e das fichas. O cache contém estados
ocultos extraídos exclusivamente de pesos e textos públicos do repositório,
carregados com `allow_pickle=False`. A reprodução numérica da cabeça, dos
21 coeficientes e do limiar já foi conferida em CPU. O resultado continua
experimental e com aprovação falsa.

Para repetir o controle agregado de um candidato já presente nesta pasta:

```bash
python experimentos/integracao_leitor_v3/avaliar_chat.py teste --saida /tmp/controle-leitor --backend torch
python experimentos/integracao_leitor_v3/avaliar_chat.py teste_v2 --saida /tmp/controle-leitor --backend torch
python experimentos/integracao_leitor_v3/avaliar_chat.py prospectivo --saida /tmp/controle-leitor --backend torch
python experimentos/integracao_leitor_v3/avaliar_chat.py prospectivo_campo --saida /tmp/controle-leitor --backend torch
```

O padrão é `--candidato campo`. `--candidato classificador` reproduz a primeira
versão rejeitada; `--backend numpy` usa a inferência nativa. Resultados
existentes nunca são sobrescritos. A execução pode levar vários minutos;
nenhum desses comandos treina ou publica pesos.

Os manifestos prospectivos foram fixados antes da avaliação. O segundo
conjunto declara antecipadamente fatos alternativos aceitáveis quando mais
de um fato cadastrado responde à pergunta; os rótulos dos conjuntos anteriores
não foram alterados. Não use os resultados desses controles para escolher
novos limiares, pesos ou regras particulares às perguntas.

Os testes de contrato são `python -m unittest testes_resgate_leitor -v`.
Suas fixtures sintéticas verificam integração e validação de artefatos; não
medem qualidade neural. Passaram 38 testes com Python 3.8 e NumPy (23 novos e 15 regressões da
leitura anterior). Sem NumPy, os 22 contratos aplicáveis passaram e um foi
ignorado. A descoberta completa encontrou 1.205 testes sem erro de importação;
a suíte inteira não foi executada localmente. As contagens e limites finais
estão em `resultado.json`.
