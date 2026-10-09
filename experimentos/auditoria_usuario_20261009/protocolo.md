# Conversar como usuário novo

Versão alvo: main `1e40650f28b5feb236ff619a182e8c833fe9068f` (#120).
Endpoint: https://crivo-mauve.vercel.app/api/chat.
Deployment de produção confirmado pela API da Vercel antes dos testes.

Auditoria exploratória, sem treino ou mudanças no motor. Perguntas de continuidade
podem ser escolhidas depois de ler as respostas. Não é conjunto cego, nem prova
estatística de generalização. A avaliação é manual: relevância ao pedido,
correção factual/numérica, uso das entidades e correções da sessão, coerência de
continuidade, cumprimento de restrições e honestidade sobre limites.

Histórico: somente mensagens do usuário, limitado às últimas dez, como o frontend.
Nenhum campo `memory`, IDs internos, checkpoints alternativos ou estado preenchido.
Respostas completas, mecanismos, uso neural, HTTP e tempo ficam nos arquivos JSON.
Uma recusa honesta pode ser segura e ainda falhar em utilidade conversacional.
Passar HTTP 200 não significa passar o objetivo da conversa.

Frentes: descobrir capacidades; curiosidade científica e analogias; pessoas e
correções; planejamento/cálculo; programação com acompanhamento; criação e
incerteza. A primeira rodada contém três inícios de quatro turnos; as continuações
e demais inícios serão registrados como entradas separadas, sem sobrescrever.
