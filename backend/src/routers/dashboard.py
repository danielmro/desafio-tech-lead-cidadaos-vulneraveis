"""
Rotas do dashboard.

Serve métricas já agregadas pelos modelos dbt (não recalcula na API):
- Evolução mensal por secretaria e status
- Total de chamados, resolvidos no prazo (SLA), taxa de SLA e TMA (horas)
"""

from fastapi import APIRouter, Depends
import duckdb

from ..db import get_connection
from ..security import require_role

router = APIRouter()


@router.get("/dashboard", dependencies=[Depends(require_role("operador"))])
def get_dashboard():
    """Retorna métricas agregadas pré-calculadas pelo dbt."""
    con: duckdb.DuckDBPyConnection = get_connection()
    # Tabela materializada pelo dbt
    table = "mart_dashboard_metrics"
    # Consulta simples ordenada para consumo direto no frontend
    rows = con.execute(
        f"SELECT mes, secretaria, status, total_chamados, resolvidos_no_prazo, taxa_sla, tma_horas FROM {table} ORDER BY mes, secretaria, status"
    ).fetchall()
    cols = [d[0] for d in con.description]
    return [dict(zip(cols, r)) for r in rows]
