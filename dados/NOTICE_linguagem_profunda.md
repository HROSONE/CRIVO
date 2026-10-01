# Fontes do corpus amplo

O novo laboratório usa exclusivamente dados estáticos públicos e o currículo
autoral do repositório. Nenhum peso, tokenizer treinado, API de inferência,
conversa privada ou saída do próprio Crivo entra no corpus.

## Wikipedia em português

Autores: colaboradores da Wikipédia em português / Wikimedia Foundation.
Distribuição: [wikimedia/wikipedia](https://huggingface.co/datasets/wikimedia/wikipedia),
configuração `20231101.pt`, revisão `b04c8d1ceb2f5cd4588862100d08de323dccfbaa`.
Shard `train-00001-of-00006.parquet`, SHA-256
`5e9b4476c0d69b0bffdcf76529de424dfda9510e3a6867676e5d482e6c70f1be`.
O card da distribuição declara [CC-BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/legalcode)
e [GFDL](https://www.gnu.org/licenses/fdl-1.3.html).

Cada registro selecionado preserva título, ID e URL do artigo para atribuição
e consulta ao histórico de autores na Wikipédia. Os textos permanecem integrais:
descartam-se artigos com menos de 256 ou mais de 100.000 caracteres. Duplicatas
normalizadas são removidas. Selecionam-se 20.000 documentos pelos menores hashes
de conteúdo dentre os elegíveis do shard, em vez de escolher assuntos manualmente.
Partições: hash do documento, aproximadamente 95% treino, 3% validação, 2% teste.
Os artigos completos ficam no corpus local/artefato de treino, sob suas licenças;
este aviso não altera a licença do código do repositório.

O registro `origem_wikipedia_20261001.json` documenta o download original. Usá-lo
como entrada fixa permite reproduzir o manifesto; sua duração não descreve
downloads posteriores. O downloader escreve seu próprio registro de origem.

## Diálogos humanos OpenAssistant / LAION-AI

[OpenAssistant/oasst2](https://huggingface.co/datasets/OpenAssistant/oasst2),
revisão `179dd21fc55192153d94adb0e0ce8f69e222bf75`, licença Apache-2.0;
cópia integral em [LICENSE_OpenAssistant.txt](LICENSE_OpenAssistant.txt).
Referência: Köpf et al., *OpenAssistant Conversations — Democratizing Large
Language Model Alignment*, 2023, https://arxiv.org/abs/2304.07327.

O downloader verifica o gzip público e uma extração reproduzível das 2.699
mensagens PT-BR. A curadoria exige `synthetic=false`, revisão positiva, baixo
spam/PII e demais rótulos do filtro anterior, qualidade mínima quando rotulada,
ancestrais revisados e papéis alternados. Descarta contatos/referências com
domínios, identidade de outros assistentes e os erros já identificados na revisão
anterior. A seleção mais ampla inclui assuntos técnicos, escrita e reflexão;
essas respostas públicas não recebem certificação factual automática.

Mensagens, respostas e históricos não são traduzidos, resumidos nem corrigidos.
Somente IDs públicos de mensagem e árvore acompanham os textos selecionados;
campos de autoria, eventos e timestamps não são redistribuídos. A expansão
contém 497 pares: 387 treino, 44 validação e 66 teste; 137 árvores distintas.
Rótulos de origem não garantem autoria ou correção de cada texto.

Cada árvore fica inteira em uma partição. Mantém-se a validação do corpus humano
anterior; acrescenta-se teste em um dos buckets antes de treino. Este Transformer
começa do zero, sem herdar pesos que tenham visto essas árvores. Alvos iguais
entre partições são recusados. OASST2 já inclui OASST1: não duplicar as versões.

## Currículo sintético autoral

Os 10.478 exemplos de treino de `curriculo_compreensao.json.gz` complementam
os diálogos humanos, com identificação explícita de origem. Não são conversas
humanas novas. A validação antiga e as sondas de diálogo/astronomia não entram
no treino. A tokenização BPE aprende somente documentos e diálogos de treino.
No SFT, metade das janelas de cada lote vem do corpus humano; 20% dos passos
repetem linguagem para reduzir esquecimento. Apenas respostas têm perda no SFT.

Os manifests registram seleção, partições, contagens e hashes. Perplexidade e
acurácia de token não certificam compreensão, raciocínio ou conversa coerente.

## Expansão de instruções sintéticas públicas

O ciclo maior acrescenta textos de [TucanoBR/Tucano-SFT](https://huggingface.co/datasets/TucanoBR/Tucano-SFT),
revisão `0f5eb4d493e86d18abad5f9e085a74c49785ac76`, primeiro shard,
SHA-256 `2d3b0b096897bf1036fd4a9ec391b6e0f7e831d9dd3e90fbf27c0432586b30a9`.
Somente registros cujo campo `metadata` atribui a origem a
[cnmoro/GPT4-500k-Augmented-PTBR-Clean](https://huggingface.co/datasets/cnmoro/GPT4-500k-Augmented-PTBR-Clean)
são selecionados. Os cards dessas distribuições declaram MIT para essa fonte;
as demais fontes do shard são recusadas. A distribuição original descreve uma
tradução de Open-Orca/1million-gpt-4. Autores/distribuidores: cnmoro e TucanoBR;
a seleção preserva a URL de origem em cada conversa. Os cards de atribuição
consultados estão em `fontes_linguagem_profunda/`, junto a este aviso.

Esses textos foram gerados por modelos externos e não são diálogos humanos.
Nenhum peso ou tokenizer desses modelos é utilizado. A declaração de licença
é a dos distribuidores; este projeto não certifica a autoria/correção dos textos.
Há um limite de 50.000 conversas, selecionadas por hash determinístico. Pedidos
iniciais normalizados iguais ficam na mesma partição; conversas e respostas
duplicadas entre partições, identidades externas e coincidências com mensagens
reservadas da avaliação humana são recusadas. O conteúdo selecionado é integral.

Somente a partição de treino participa da tokenização e do SFT. As conversas
públicas de validação/teste são preservadas separadamente, sem entrar nas métricas
denominadas humanas. Augmentações semanticamente próximas podem atravessar
partições: a seleção pública não constitui avaliação externa cega. Os lotes de
SFT continuam equilibrados: metade de janelas humanas, metade do conjunto
sintético autoral e público. O piloto anterior não usou esta expansão.
