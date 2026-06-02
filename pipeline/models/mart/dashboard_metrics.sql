-- Modelo: mart.dashboard_metrics
-- Objetivo: produzir métricas prontas para o dashboard (sem cálculo na API)
-- Métricas: total de chamados, resolvidos no prazo (SLA), taxa de SLA, TMA (horas) por mês/secretaria/status.
-- Entrada: {{ ref('chamados_clean') }}
-- Saída: tabela materializada `mart_dashboard_metrics` consumida pelo endpoint `/dashboard`.

WITH base AS (
  SELECT * FROM {{ ref('chamados_clean') }}
),
calc AS (
  SELECT
    DATE_TRUNC('month', COALESCE(data_fim, data_inicio)) AS mes,
    secretaria,
    status,
    COUNT(*) AS total_chamados,
    SUM(CASE WHEN data_fim IS NOT NULL AND data_alvo_finalizacao IS NOT NULL AND data_fim <= data_alvo_finalizacao THEN 1 ELSE 0 END) AS resolvidos_no_prazo,
    AVG(CASE WHEN data_fim IS NOT NULL AND data_inicio IS NOT NULL THEN EXTRACT(EPOCH FROM (data_fim - data_inicio)) / 3600.0 END) AS tma_horas
  FROM base
  GROUP BY 1,2,3
)
SELECT
  mes,
  secretaria,
  status,
  total_chamados,
  resolvidos_no_prazo,
  CASE WHEN total_chamados > 0 THEN resolvidos_no_prazo::DOUBLE / total_chamados ELSE NULL END AS taxa_sla,
  tma_horas
FROM calc
ORDER BY mes, secretaria, status