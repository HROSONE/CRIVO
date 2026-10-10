# Segundo treino e correções — 10/10/2026

Base publicada: #127, `044ed446afd1c9b66c3b1ddd11b087c5c5a23658`.
Seis turnos das três sessões realmente reprovadas no site foram congelados
antes da mudança, somados aos 37 casos intactos. SHA dos **43 casos**:
`48ff1fabc11b1c3ae6deddb3205ffdd70c4f887c4bd6c5dbf77e76ed1a58f3d0`.
As dez sessões anteriores de 6–7 mensagens permanecem intactas.

| Medida | #127 | Motor e HTTP real após mudança |
|---|---:|---:|
| Peça correta, conteúdo e evidência | 37/43 | 43/43 |
| Casos com referente ausente | 5 | 0 |
| Troca de domínio no conjunto | 0 | 0 |
| Sessões mantendo tarefa/referentes, revisão pelo agente | 7/10 | 10/10 |
| Parâmetros do realizador | 88.969 | 85.581 |

Não são dez participantes humanos. A revisão inclui os executores de fatos,
memória e cálculo; não prova conselho específico, compreensão de qualquer
histórico, conversa humana ou raciocínio geral. O plano de desenho segue genérico.

## Corpus e treino

Oito arcos autorais: ponte, mapa, porta, chuva, bilhete, objeto perdido,
travessia e som. Há 48 novos padrões de narrativa + quatro antigos: **52
padrões**, não milhares de enredos humanos. 384 diálogos novos / 2.304 turnos;
com o corpus anterior, 8.064 turnos documentados. O treino usa apenas ficção:
1.216 respostas de treino e 256 de validação, com diálogos/personagens/cenários
separados. Os oito arcos são compartilhados entre partições.

Mesma GRU própria: 80 ocultos, 40 embeddings, 181 tokens; 24 épocas, lote 48,
taxa 0,0015, semente 20261011. Inicia nos pesos próprios da base #127, guardados
em `checkpoint_base_127.json.gz`. Reprodução completa produziu checkpoint
idêntico byte a byte. Dados, perdas, hiperparâmetros e hashes estão versionados.
Nenhum modelo externo foi usado. Os 35 pesos anteriores e o factual não mudaram.

O preliminar tinha finais de quatro frases; a revisão revelou que reescrever
restaurava a abertura e descartava o amigo. Os alvos autorais foram corrigidos
para ensinar finais de cinco frases, sem copiar alvos/entidades do teste.
Corpus, pesos e treino preliminares ficam preservados e desativados.

## Integração e avaliação

A escolha nominal usa o campo/candidatos da pergunta anterior. Retomada usa
objetivo e declarações já existentes. Restrição de nome não cancela escrita;
cancelamento real continua cancelamento. Personagem/cenário/amigo têm papéis
distintos; continuação/final mantêm o arco e reescrita conserva o desfecho.

Se texto residual sugere o ato anterior, a rede realiza novamente a mesma
ação/arco/argumentos neutralizando esse texto. Ambas as saídas passam pela
mesma guarda; trace `contexto_textual_neutralizado`. Não há catálogo substituindo
a saída nem aprovação do rascunho rejeitado. Temas de papel incerto conservam
o executor anterior; amigo do desfecho não vira cenário.

Checkpoint final de laboratório: **aprovado=false, ativo_no_chat=false**.
`aprovar.py` só gera a cópia de produção após 43/43 em ambos os caminhos,
zero troca/referente ausente, quatro histórias, revisão de pelo menos oito
sessões, reprodução e preservação dos 35 pesos. Origem/pesos/métricas
incompatíveis não ativam o checkpoint. Guardas factuais continuam rígidas.

Passaram 34 contratos relevantes; sonda anotada de 48 contextos/variantes:
48/48 com argumentos e contagem correta. A sonda recebe o ato, não mede
interpretação livre. Job HTTP existente agora verifica 43 casos. A matriz
completa permanece manual/semanal, sem workflow novo ou correção lateral de CI.

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
python experimentos/dialogo_v2_20261010/preparar.py
python experimentos/dialogo_v2_20261010/treinar.py --destino /tmp/dialogo-v2.json.gz
python -m unittest testes_dialogo_v2 testes_conversa_dialogo testes_roteamento_natural testes_roteamento_natural_v2
python experimentos/dialogo_v2_20261010/avaliar.py --modo http --saida /tmp/v2-http.json --exigir-meta
```

## Limites e próximo passo

São oito arcos condicionados. Capacidades/autoria/fatos/cálculo/preferências
usam executores existentes. Contagens arbitrárias, histórias longas, estilos
e instruções compostas gerais não estão resolvidos. Depois de final com amigo,
uma continuação pode esclarecer em vez de gerar. Não demonstra conversa livre.

Após checks verdes e merge, conferir commit/checkpoint e repetir os 43 casos
e dez sessões no site. Próximo passo único: medir diálogos reais variados,
principalmente orientação prática e continuação fora dos oito arcos, para
escolher a próxima ampliação do corpus autoral.
