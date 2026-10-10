# Continuidade de escrita — 10/10/2026

## Diagnóstico observado antes da mudança

Foram executadas seis novas sessões autorais de seis turnos no motor e
no site publicado em `3e8eed593288af6be17c83d11aeae5d14d1e598e`.
São sondas do agente, não transcrições do dono nem seis participantes humanos.
`baseline_site.json` preserva os 36 pedidos/respostas, traces e saúde antes/depois.

As três sessões práticas continuam reprovadas: desenho, estudos e horta.
O sistema lembra objetivos, mas dá instruções genéricas, perde perguntas
de seguimento e pede reformulação indevida. Não foram convertidas em sucessos
por acertar a memória. Estão preservadas como prioridade seguinte.

Nas três sessões de escrita, imperativos comuns e referentes falhavam:
“mude o final”, “continue depois desse final”, “mais uma vez”, “essa personagem”.
Os 18 turnos foram acrescentados aos 43 casos anteriores **sem alterar estes**,
antes de modificar a implementação. A linha de base foi **47/61**, com 12
respostas sem referentes obrigatórios. Novas entidades/alvos não entram no treino.

## Mudança focalizada

- Reutiliza o roteador, histórico e última escrita existentes. Não adiciona
  memória, acervo, arquitetura, parâmetros ou modelo externo.
- Aceita aventura como ficção explícita, mude/muda, continuação após final,
  e resolve “essa personagem” nos pedidos naturais medidos.
- Separa lugares reconhecidos em `tema2`; companhia permanece em `detalhe`.
  Nova correção substitui a companhia anterior, sem transformá-la em lugar.
- A GRU própria foi realmente treinada a continuar com personagem, cenário
  opcional e companhia. Todos os detalhes específicos vêm dos argumentos.
- Uma nova continuação com companhia avança para outra cena dos oito arcos;
  reescrever preserva a última cena e todos os participantes. A seleção da cena
  é estrutural: não é descoberta neural de um plano ou compreensão geral.
- O texto residual foi neutralizado após revisão detectar mistura/repetição;
  o trace mostra o ato, a cena e os argumentos efetivamente usados. A rede
  continua gerando tokens a partir desse contexto selecionado.

## Treino e proveniência

`preparar.py` reaproveita o corpus autoral anterior e canoniza a companhia,
acrescentando **384 exemplos**, equivalentes a **16 padrões autorais**.
São **1.536 exemplos de treino / 320 de validação**. Diálogos e novas entidades
separados; os oito arcos são compartilhados entre as partições. Não representa
diversidade humana nem pré-treino amplo.

Mesmo vocabulário de 181 tokens, GRU de 80 ocultos/40 embeddings e
**85.581 parâmetros**, sem aumento. Base própria fixa de #128, 24 épocas,
semente 20261012, lote 48, taxa 0,0015, regularização de texto 0,4/0,15,
clip 5. `treino.json` registra a execução real. A reprodução byte a byte
está em `reproducibilidade.json`; `treinar.py --destino ARQUIVO` reproduz os pesos.

O checkpoint experimental conserva `aprovado=false, ativo_no_chat=false`.
Somente `aprovar.py`, após resultados completos e revisão, escreve a cópia
aprovada de produção. Os 35 pesos anteriores e experimentos antigos são
conferidos intactos. Corpus/checkpoint preliminares reprovados foram preservados
e não sustentam a aprovação.

## Validação e limites

`avaliar.py` mede os 61 casos no motor e no servidor HTTP real, além das
dez sessões anteriores intactas. `testes_dialogo_continuidade.py` cobre papéis,
correção repetida, avanço de cena/reescrita, aprovação e fronteiras factuais.
O CI usa o job existente de roteamento; não aciona a matriz completa a cada PR.

Não há conversa livre geral. São oito arcos; a seleção de cena, intenção e
referentes ainda depende da estrutura. Contagens e estilos arbitrários
permanecem limitados. As três conversas de ajuda prática seguem falhando.
Uma bateria verde de escrita não autoriza alegar planejamento útil, raciocínio
humano ou treino de conversação humana. Após merge, verificar commit/pesos
publicados e repetir no site os casos e diálogos; registrar os resultados reais.

Resultado final antes do merge: **47/61 → 61/61** no motor e HTTP, zero
troca de domínio/referente ausente, 21/21 entregas de escrita exigidas.
Dez sessões anteriores preservadas nos critérios restritos; três novas de
escrita corrigidas e **0/3** práticas aprovadas. Sete contratos novos passaram;
os 34 anteriores passaram. Reprodução idêntica. `relatorio.json` e
`revisao_conversas.json` registram números, evidências e limites.
