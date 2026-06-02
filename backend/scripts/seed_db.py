"""
Seed simples para criar um DuckDB local com as tabelas mínimas
esperadas pela API para testes manuais.

Cria `pipeline/pic.duckdb` (se não existir) e popula:
- intermediate_chamados_clean
- mart_dashboard_metrics
"""
from pathlib import Path
import duckdb

DB_PATH = Path(__file__).resolve().parents[1].parents[0] / "pipeline" / "pic.duckdb"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(str(DB_PATH), read_only=False)
con.execute("INSTALL parquet; LOAD parquet;")

# Cria tabela de chamados "limpos"
con.execute(
    """
    CREATE OR REPLACE TABLE intermediate_chamados_clean (
      id_chamado BIGINT,
      data_inicio TIMESTAMP,
      data_fim TIMESTAMP,
      data_alvo_finalizacao TIMESTAMP,
      tipo VARCHAR,
      subtipo VARCHAR,
      status VARCHAR,
      situacao VARCHAR,
      longitude DOUBLE,
      latitude DOUBLE,
      data_particao DATE,
      secretaria VARCHAR
    );
    """
)

con.execute(
    """
    DELETE FROM intermediate_chamados_clean;
    INSERT INTO intermediate_chamados_clean VALUES
      (1, TIMESTAMP '2024-01-01 08:00:00', TIMESTAMP '2024-01-02 09:00:00', TIMESTAMP '2024-01-03 23:59:59',
       'SAÚDE - TESTE', 'SUBTIPO A', 'ENCERRADO', 'FINALIZADO', 1.23, -2.34, DATE '2024-01-01', 'SMS'),
      (2, TIMESTAMP '2024-01-05 10:00:00', NULL, TIMESTAMP '2024-01-10 12:00:00',
       'EDUCAÇÃO - TESTE', 'SUBTIPO B', 'EM ANDAMENTO', 'ABERTO', 3.21, -4.32, DATE '2024-01-05', 'SME');
    """
)

# Cria tabela de métricas do mart
con.execute(
    """
    CREATE OR REPLACE TABLE mart_dashboard_metrics (
      mes DATE,
      secretaria VARCHAR,
      status VARCHAR,
      total_chamados BIGINT,
      resolvidos_no_prazo BIGINT,
      taxa_sla DOUBLE,
      tma_horas DOUBLE
    );
    """
)

con.execute(
    """
    DELETE FROM mart_dashboard_metrics;
    INSERT INTO mart_dashboard_metrics VALUES
      (DATE '2024-01-01', 'SMS', 'ENCERRADO', 1, 1, 1.0, 25.0),
      (DATE '2024-01-01', 'SME', 'EM ANDAMENTO', 1, 0, 0.0, NULL);
    """
)

con.close()
print(f"Seed concluído em: {DB_PATH}")
