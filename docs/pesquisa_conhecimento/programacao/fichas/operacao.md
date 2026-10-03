# Fichas avançadas: operacao

Exportação legível de `catalogo-avancado.json`. Síntese autoral; referências remotas ainda precisam de conferência editorial. Acervo não integrado ao runtime.

## operacao_observability — Logs, métricas e traces

**Definição:** Logs registram eventos; métricas agregam sinais; traces relacionam etapas de operação.

**Mecanismo:** Propagação de contexto conecta spans; cardinalidade de labels determina custo; sampling influencia evidência.

**Falhas comuns:** ID de usuário em label gera cardinalidade enorme; secret em log é vazamento; média esconde cauda.

**Escolha:** Definir sinais por hipótese e SLO; logs estruturados com redaction e correlation.

**Verificação proposta:** Seguir request ponta a ponta e testar exportador indisponível sem bloquear aplicação.

**Referências recomendadas:** [OpenTelemetry specifications](https://opentelemetry.io/docs/specs/)

## operacao_slo — SLO, error budget e incidentes

**Definição:** SLO define objetivo mensurável de serviço; error budget quantifica tolerância a violações.

**Mecanismo:** Escolher SLI útil ao usuário, janela e alertas por burn rate. p99 precisa população/contexto claros.

**Falhas comuns:** CPU alta não é incidente por si só; 99% médio global pode esconder falha regional.

**Escolha:** Priorizar sintomas, capacidade de resposta e postmortem com ações verificáveis.

**Verificação proposta:** Simular dependência lenta e verificar alertas, fallback e consumo do budget.

**Referências recomendadas:** [Google Site Reliability Engineering](https://sre.google/books/)

## operacao_containers — Containers e imagens

**Definição:** Imagem empacota filesystem/configuração; container aplica isolamento e recursos do runtime.

**Mecanismo:** Multistage reduz tamanho; usuário não root, limites e filesystem readonly reduzem superfície.

**Falhas comuns:** Secret em layer persiste mesmo se removido depois; tag latest não fixa versão.

**Escolha:** Usar imagem mínima revisada e secrets fora do build context.

**Verificação proposta:** Inspecionar layers, UID, limites e funcionamento com filesystem restrito.

**Referências recomendadas:** [Docker documentation](https://docs.docker.com/)

## operacao_kubernetes — Reconciliação Kubernetes

**Definição:** Control plane converge estado observado para desired state via controllers.

**Mecanismo:** Readiness controla tráfego, liveness reinício e startup tempo inicial; requests/limits influenciam scheduling e execução.

**Falhas comuns:** Liveness de dependência externa provoca restart storm; readiness não deve derrubar todo cluster por falha comum.

**Escolha:** Configurar probes por responsabilidade e ensaiar rolling update.

**Verificação proposta:** Testar pod morto, dependência indisponível, resource pressure e rollout.

**Referências recomendadas:** [Kubernetes documentation](https://kubernetes.io/docs/)

## operacao_deployment — Rollout, rollback e flags

**Definição:** Deploy altera artefato; release expõe comportamento; podem ser separados por flag.

**Mecanismo:** Canary/blue-green reduzem blast radius; rollback exige compatibilidade de dados e versão.

**Falhas comuns:** Rollback do código não desfaz migração destrutiva nem side effects; flag permanente vira dívida.

**Escolha:** Definir métricas, janela e decisão automática/manual por risco observado.

**Verificação proposta:** Ensaiar canary com erro, rollback e coexistência de schemas.

**Referências recomendadas:** [Google Site Reliability Engineering](https://sre.google/books/)

## operacao_capacity — Capacidade e filas

**Definição:** Throughput, latência e concorrência estão relacionados sob condições de estabilidade.

**Mecanismo:** Lei de Little relaciona média de itens, chegada e tempo em sistema estável; saturação aumenta fila e tail latency.

**Falhas comuns:** Load test sem controlar taxa pode esconder saturação; fila ilimitada desloca falha para memória.

**Escolha:** Limitar admissão e medir demanda/capacidade com margem.

**Verificação proposta:** Testar ramp-up, burst, steady load e recuperação após overload.

**Referências recomendadas:** [Google Site Reliability Engineering](https://sre.google/books/)

## operacao_recovery — Backup, restore e disaster recovery

**Definição:** Backup útil precisa ser restaurável dentro de objetivos de perda e tempo.

**Mecanismo:** RPO limita perda tolerável; RTO tempo de recuperação; snapshots e WAL têm custos/requisitos específicos.

**Falhas comuns:** Backup verde não prova restore; réplica não substitui backup contra exclusão lógica.

**Escolha:** Automatizar restore test e isolar credenciais/retention.

**Verificação proposta:** Restaurar ambiente vazio, validar integridade e medir tempo/perda.

**Relações:** operacao_slo, dados_migrations

**Referências recomendadas:** [PostgreSQL documentation](https://www.postgresql.org/docs/current/)


