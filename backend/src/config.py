"""
Configurações da aplicação.

Leitura simples via variáveis de ambiente (com defaults seguros para desenvolvimento).
Em produção, defina as variáveis no ambiente do processo/contêiner.
"""

import os
from pydantic import BaseModel


class Settings(BaseModel):
    # Caminho do arquivo DuckDB gerado pelo dbt
    DUCKDB_PATH: str = os.getenv("DUCKDB_PATH", "../pipeline/pic.duckdb")
    # Segredo usado para assinar tokens JWT no ambiente local (mock)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    # Tempo de expiração padrão dos tokens (minutos)
    JWT_EXPIRES_MINUTES: int = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))


# Instância global de configurações
settings = Settings()