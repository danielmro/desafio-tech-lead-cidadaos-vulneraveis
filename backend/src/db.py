"""
Acesso ao banco DuckDB utilizado pela API.

Mantemos uma única conexão process-wide com `lru_cache(maxsize=1)` para evitar
reabrir o arquivo a cada requisição e para reutilizar extensões carregadas.
"""

import duckdb
from .config import settings
from functools import lru_cache


@lru_cache(maxsize=1)
def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Retorna (e memoriza) uma conexão DuckDB para o arquivo definido em `settings.DUCKDB_PATH`.

    - Ativa a extensão Parquet para leitura eficiente de arquivos `.parquet` quando necessário.
    - `read_only=False` permite criar/materializar tabelas durante o `dbt run`.
    """
    con = duckdb.connect(settings.DUCKDB_PATH, read_only=False)
    con.execute("INSTALL parquet; LOAD parquet;")  # garante extensão disponível
    return con
