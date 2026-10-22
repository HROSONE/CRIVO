# Teste às cegas por agentes (21/10/2026)

Conversas novas, escritas por agentes (Claude, da Anthropic, usado como ferramenta de desenvolvimento,
fora do CRIVO que conversa) em vários jeitos de falar. Cada agente pegou uma área, conversou com o CRIVO
local (`web_core.responder_web`, com o histórico reenviado como no site) e marcou cada turno como
passou ou falhou, com o motivo.

**Estas conversas nunca entram no treino.** Elas não são dados humanos nem do criador: são frases
escritas por um modelo de terceiros para teste. Nenhum script de treino lê esta pasta.

| área | conversas | turnos | falharam | graves |
|---|---|---|---|---|
| ambiente | 32 | 102 | 57 | — |
| correção | 34 | 42 | 37 | — |
| crise | 42 | 58 | 18 | 16 |
| memória | 34 | 88 | 47 | — |
| programação | 35 | 49 | 7 | — |

Os números acima são do CRIVO de 21/10/2026 (main em `a7341b3`), **antes** das correções.

## Limites

- Quem escreveu as perguntas também julgou as respostas. O julgamento é do agente, não do criador,
  e não substitui a régua própria (casos às cegas do criador, paráfrases, frases reais).
- **Crise deixou de ser cega.** As 16 falhas graves foram lidas para corrigir o `crise.py` por família
  de frase (ideação passiva, erro de digitação, overdose, engasgo, sangramento, violência sofrida,
  cuidado no turno seguinte). Depois da correção: 0 falhas graves nos 16 turnos e 0 alarmes falsos
  nos 23 turnos sem risco, mas medir isso aqui já é medir no conjunto de desenvolvimento. Os testes
  novos (`testes_crise.FamiliasDoTesteAsCegas`) usam outras frases. Para uma medida cega de crise,
  é preciso um conjunto novo.
- As outras áreas continuam cegas enquanto ninguém ajustar código olhando para elas.
