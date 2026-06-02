# Pipeline de Dados (dbt + DuckDB)

Este diretório contém o projeto dbt para transformar os dados brutos do 1746 exportados do BigQuery em modelos prontos para a API e o frontend.

## Pré-requisitos
- Python 3.10+
- dbt-core e dbt-duckdb
- DuckDB com extensão `parquet`
- Dados exportados do BigQuery em `data/chamados/*.parquet` (ver `../docs/dados.md`)

## Instalação
Crie um ambiente virtual e instale:
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install dbt-core dbt-duckdb
```

## Configuração
1. Copie `profiles.yml.example` para o diretório de perfis do dbt.
   - Windows: `%USERPROFILE%\.dbt\profiles.yml`
2. Ajuste caminhos conforme desejar. Por padrão, o arquivo do DuckDB será `./pipeline/pic.duckdb`.

## Modelos
- `models/intermediate/chamados_source.sql`: lê Parquet de `data/chamados/*.parquet`.
- `models/intermediate/chamados_clean.sql`: normaliza campos e deriva `secretaria`.
- `models/mart/dashboard_metrics.sql`: métricas agregadas para o dashboard.

## Executando
Dentro da pasta `pipeline/`:
```bash
dbt deps
dbt run
```
Resultados:
- Tabelas/Views materializadas no arquivo `pipeline/pic.duckdb`.
- Artefatos em `pipeline/target/`.

## Inspecionando o banco DuckDB (opcional)
Use o cliente DuckDB ou Python para consultar as tabelas criadas:
```sql
.open pic.duckdb
.tables
SELECT * FROM mart_dashboard_metrics LIMIT 10;
```

## SQL de export do BigQuery
A query usada para exportar está em `sql/bigquery_export.sql`.
