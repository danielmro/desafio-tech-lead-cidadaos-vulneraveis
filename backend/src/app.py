"""
Aplicação FastAPI principal.

- Configura CORS para permitir o frontend local durante o desenvolvimento.
- Registra routers de autenticação, listagem/exportação de chamados e dashboard.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from .config import settings
from .routers import chamados, dashboard, auth

# Metadados básicos da API (aparecem na documentação automática /docs)
app = FastAPI(title="APP 1746 API", version="0.1.0")

# CORS: quando usamos Authorization (Bearer), não podemos usar "*" com allow_credentials=True.
# Permitimos explicitamente as origens do frontend (dev) e também suportamos override via env CORS_ORIGINS (CSV).
raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
)
allow_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de routers (organiza endpoints por domínio)
app.include_router(auth.router, prefix="/auth", tags=["auth"]) 
app.include_router(chamados.router, tags=["chamados"]) 
app.include_router(dashboard.router, tags=["dashboard"]) 


@app.get("/health", tags=["meta"]) 
def health():
    """Endpoint simples de saúde para verificação rápida do serviço."""
    return {"status": "ok", "duckdb_path": settings.DUCKDB_PATH, "allow_origins": allow_origins}
