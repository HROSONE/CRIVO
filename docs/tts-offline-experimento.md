# Experimento TTS offline — etapa 0 (sem sintetizador integrado)

Objetivo: comparar Kokoro e Piper em **pt-BR** no Android, navegador e PC, sem API externa. A rede original do CRIVO continua intocada. **Este PR ainda não gera áudio**: contém contrato e testes de seleção de motores locais, para não confundir uma promessa de offline com execução offline verificada.

## Critérios de aprovação antes de integrar voz

1. Confirmar pesos, frontend de fonemização, licença e voz pt-BR reais para cada candidato. A presença de um arquivo ONNX não prova que a cadeia de texto→fonemas→áudio funciona em português.
2. Executar **o mesmo conjunto** de frases inéditas (números, siglas, perguntas, negações, abreviações, pontuação e nomes sintéticos) nos dois motores, no Android real, em navegador desktop e em PC Linux/Windows. Avaliar inteligibilidade/naturalidade por escuta cega, separando os resultados por plataforma.
3. Registrar tempo de primeiro áudio, RTF, RAM máxima, tamanho do pacote e falhas de inicialização, com hardware e configuração de cada medição. Nenhum resultado de desempenho é afirmado aqui.
4. Desconectar internet **antes de abrir a aplicação** após instalar/cachear os pesos e recarregar a página; verificar que não existem requests externos para pesos, scripts ou texto. Service worker/armazenamento persistente é necessário para o navegador realmente abrir offline; só ter os pesos em cache não basta.
5. Testar interrupção, fila de falas, cancelamento, textos extensos e descarte seguro de tags de código. Não enviar texto do usuário para terceiros.
6. Implementar adaptadores reais e testes de integração em PRs posteriores; no Android pode ser necessário runtime nativo, e no navegador WASM/WebGPU e armazenamento local. Sem pressupor paridade de desempenho.

## Estado desta etapa

- `public/tts/offline-core.js` só seleciona **metadados declarados como já instalados**, não verifica arquivos nem faz síntese. Nunca deve ser ligado diretamente ao botão de voz como se fosse motor completo.
- Sem modelos baixados, sem benchmarks de áudio, sem voz instalada e sem suporte offline de página comprovado.
- `node --test tests/tts_offline.test.cjs` testa as invariantes de seleção, ausência de fallback remoto e segmentação; GitHub Actions executará a suíte no PR.
- O TTS pode usar pesos de voz externos de licença compatível: a proibição de modelos externos refere-se ao **cérebro conversacional**, que continua autoral em Python. Kokoro e Piper não serão usados para responder perguntas.
