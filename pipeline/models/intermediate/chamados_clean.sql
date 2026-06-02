-- Modelo: intermediate.chamados_clean
-- Objetivo: normalizar campos (datas, texto, coordenadas) e derivar `secretaria` a partir de `tipo`.
-- Entrada: {{ ref('chamados_source') }} (Parquet exportado do BigQuery, filtrado por partição)
-- Saída: tabela materializada `intermediate_chamados_clean` consumida pela API.

{{ config(materialized='table') }}

WITH base AS (
  SELECT
    id_chamado,
    -- normalização de datas
    CAST(data_inicio AS TIMESTAMP) AS data_inicio,
    CAST(data_fim AS TIMESTAMP) AS data_fim,
    CAST(data_alvo_finalizacao AS TIMESTAMP) AS data_alvo_finalizacao,
    UPPER(TRIM(tipo)) AS tipo,
    UPPER(TRIM(subtipo)) AS subtipo,
    UPPER(TRIM(status)) AS status,
    UPPER(TRIM(situacao)) AS situacao,
    TRY_CAST(longitude AS DOUBLE) AS longitude,
    TRY_CAST(latitude AS DOUBLE) AS latitude,
    CAST(data_particao AS DATE) AS data_particao
  FROM {{ ref('chamados_source') }}
),
regras AS (
  SELECT
    id_chamado,
    data_inicio,
    data_fim,
    data_alvo_finalizacao,
    tipo,
    subtipo,
    status,
    situacao,
    longitude,
    latitude,
    data_particao,
    CASE
      WHEN tipo LIKE '%SAÚDE%' THEN 'SMS'
      WHEN tipo LIKE '%EDUCAÇÃO%' THEN 'SME'
      WHEN tipo LIKE '%ASSIST%SOCIAL%' OR tipo LIKE '%DESENVOLVIMENTO SOCIAL%' THEN 'SMAS'
      WHEN tipo LIKE '%LIMPEZA%' OR tipo LIKE '%COMLURB%' THEN 'COMLURB'
      WHEN tipo LIKE '%TRANSPORTE%' OR tipo LIKE '%CET-RIO%' OR tipo LIKE '%TRÂNSITO%' THEN 'CET-RIO'
      ELSE 'OUTRAS'
    END AS secretaria
  FROM base
)
SELECT * FROM regras
