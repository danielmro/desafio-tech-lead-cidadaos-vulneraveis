-- Fonte: arquivos Parquet exportados do BigQuery e salvos em data/chamados/
-- Observação: requer extensão parquet habilitada no DuckDB.

{{ config(materialized='external') }}

SELECT *
FROM read_parquet('../data/chamados/*.parquet')
