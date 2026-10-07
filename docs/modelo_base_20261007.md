# Consolidação e início do modelo base — 07/10/2026

As etapas dos PRs #105–#110 foram reunidas numa única entrega. Análise de
conteúdo, correção por regras e acervo bíblico TNM permanecem disponíveis.
Os experimentos de inferência estão preservados, com aprovação dos pesos falsa.
Eles concluíram suas medições; não são funcionalidades aguardando promoção.

Falhas de integração corrigidas:

- Continuação «E uma árvore?» herda a definição anterior com artigo indefinido,
  preservando o ID editorial e a pergunta original no histórico.
- Composição ancorada preserva a ordem e a multiplicidade de palavras das
  evidências. A guarda anterior de raízes permitia apagar repetições legítimas
  como o padrão completo de uma escala musical. Pontuação da evidência em
  composição também permanece preservada.
- Referências bíblicas exatas continuam validadas; pedidos compostos passam ao
  planejador para executar explicação, resumo e fontes, em vez de parar após
  explicar o primeiro versículo.
- O contrato de preservação dos pesos ao ampliar o acervo verifica um mínimo
  de cobertura e a disponibilidade da rede; não fixa o número total de fichas.
- A matriz principal do CI instala o NumPy declarado em requirements.txt.
  Os workflows específicos continuam verificando execução sem dependências
  opcionais com `python -S`; nenhuma regressão foi retirada para esconder falhas.

## Integração generativa

`modelo_base.py` usa Chat Completions, configurado exclusivamente no backend.
O chat web e a API chamam o modelo após recuperar o contexto local. No replay,
não há chamadas externas: só o turno atual é gerado. Falha de rede, serviço
ocupado, resposta vazia, grande ou truncada conserva a resposta local e deixa
um diagnóstico. A UI identifica respostas geradas; `has_proof` permanece falso
para elas. Os metadados de análise extrativa e diffs por regras não são
reutilizados para certificar uma saída neural diferente. O diff consultado após
uma correção neural é recalculado entre o original e a saída realmente mostrada.

Raciocínio lógico, código, crise, memória, referências bíblicas exatas,
consulta de fontes e planos com contratos próprios permanecem com seus motores.
O modelo base recebe até quatro falas anteriores de usuário e o contexto
selecionado. Esta versão não persiste respostas anteriores do modelo no
cliente: retomadas podem perder detalhes exclusivos dessas respostas. Não há
agente de ferramentas ou ciclo de revisão neural implementado nesta etapa.

Configuração do site:

```
CRIVO_LLM_URL=https://seu-servidor/v1
CRIVO_LLM_MODEL=Qwen/Qwen2.5-1.5B-Instruct
CRIVO_LLM_API_KEY=chave-se-o-servico-exigir
```

URL e chave nunca entram no payload ou no JavaScript. Um servidor Ollama com
API compatível pode ser usado com `/v1` e seu nome de modelo. Sem URL, o chat
funciona com os motores locais. `base_generation.configured` informa a
configuração; não afirma que o provedor está saudável. `used` confirma que a
resposta do turno veio de uma chamada concluída. API com limite de 60 segundos,
cliente web de 65 segundos e provedor com timeout de 45 segundos.

## Modelo realmente executado

Qwen2.5-1.5B-Instruct público, licença Apache 2.0, quantização oficial Q4_K_M:

- Repositório: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF
- Revisão: `91cad51170dc346986eccefdc2dd33a9da36ead9`.
- Arquivo: `qwen2.5-1.5b-instruct-q4_k_m.gguf`, 1.117.320.736 bytes.
- SHA-256: `6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e`.
- Runtime llama.cpp `b11469`, pacote CPU Linux x64, SHA-256
  `bf10f78cb5929f8a745d7d752ff2ec2c183535024ce0e310b784d745be929a5d`.

Os pesos públicos e binários ficam fora do Git e do pacote Vercel. Tentativas
iniciais com Transformers excederam latência e memória deste ambiente; elas
não foram contadas como validação generativa. O runtime GGUF conseguiu gerar
as respostas reais registradas em `docs/resultados/modelo_base_fluxo_20261007.json`.

Esta é uma validação exploratória de integração, não benchmark de qualidade,
prova de equivalência na correção ou certificação de raciocínio geral. Não
há novo ajuste supervisionado desses pesos. O serviço foi executado localmente;
a ativação no site publicado depende de um endpoint hospedado e configurado.

## Executar localmente

O instalador automático usa Python 3.12+, Linux x64 e os arquivos/hashes acima.
Outras plataformas podem instalar llama.cpp e obter o mesmo GGUF oficial.

```bash
python scripts/preparar_modelo_base.py
python scripts/servidor_modelo_base.py --binario .modelos/qwen25/llama-b11469/llama-server --pesos .modelos/qwen25/qwen2.5-1.5b-instruct-q4_k_m.gguf
# Em outro terminal:
CRIVO_LLM_URL=http://127.0.0.1:8780/v1 npm run dev
```

O servidor modelo escuta somente localhost por padrão. Para hospedagem pública,
use autenticação e a camada de publicação do seu provedor. Instalar o runtime
não cria nem compra um serviço externo.
