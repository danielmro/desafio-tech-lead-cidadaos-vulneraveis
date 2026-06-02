"""
Rotas de listagem e exportação de chamados.
- `GET /chamados`: aplica filtros, ordenação e paginação no DuckDB e retorna página de itens.
- `GET /export`: exporta CSV dos resultados filtrados (sem paginação), respeitando os mesmos filtros.
Observação: as consultas leem tabelas materializadas pelo dbt (ex.: `intermediate_chamados_clean`).
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
import duckdb
import io
import csv

from ..db import get_connection
from ..security import require_role

router = APIRouter()


@router.get("/chamados", dependencies=[Depends(require_role("operador"))])
def list_chamados(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    order_by: str = Query("data_inicio"),
    order_dir: str = Query("desc", pattern=r"^(asc|desc)$"),
    # Filtros existentes (intervalo por datas + campos categóricos)
    dt_ini: Optional[str] = Query(None, description="YYYY-MM-DD"),
    dt_fim: Optional[str] = Query(None, description="YYYY-MM-DD"),
    secretaria: Optional[str] = None,
    status: Optional[str] = None,
    tipo: Optional[str] = None,
    # Novos filtros solicitados
    id_chamado: Optional[int] = Query(None, description="Filtra por id exato"),
    data_inicio: Optional[str] = Query(None, description="YYYY-MM-DD (igualdade)"),
    data_fim: Optional[str] = Query(None, description="YYYY-MM-DD (igualdade)"),
    subtipo: Optional[str] = None,
    situacao: Optional[str] = None,
):
    """Retorna uma página de chamados filtrados/ordenados.
    - `dt_ini`/`dt_fim`: recorte por intervalo (datas); `data_inicio`/`data_fim` (igualdade exata, opcional)
    - `tipo` habilita a filtragem de `subtipo` (frontend cuida da habilitação visual)
    - Todos os filtros são opcionais e combináveis via AND.
    """
    con: duckdb.DuckDBPyConnection = get_connection()

    where = ["1=1"]
    params = []

    # Filtros por intervalo (backwards compat)
    if dt_ini:
        where.append("data_inicio::date >= ?")
        params.append(dt_ini)
    if dt_fim:
        where.append("COALESCE(data_fim, data_inicio)::date <= ?")
        params.append(dt_fim)

    # Filtros por igualdade/texto
    if id_chamado is not None:
        where.append("id_chamado = ?")
        params.append(id_chamado)
    if data_inicio:
        where.append("data_inicio::date = ?")
        params.append(data_inicio)
    if data_fim:
        where.append("data_fim::date = ?")
        params.append(data_fim)
    if secretaria:
        where.append("secretaria = ?")
        params.append(secretaria.upper())
    if status:
        where.append("status = ?")
        params.append(status.upper())
    if tipo:
        where.append("tipo LIKE ?")
        params.append(f"%{tipo.upper()}%")
    if subtipo:
        where.append("subtipo LIKE ?")
        params.append(f"%{subtipo.upper()}%")
    if situacao:
        where.append("situacao = ?")
        params.append(situacao.upper())

    # Whitelist de colunas para ORDER BY
    valid_order_cols = {
        "id_chamado",
        "data_inicio",
        "data_fim",
        "data_alvo_finalizacao",
        "tipo",
        "subtipo",
        "status",
        "situacao",
        "secretaria",
        "data_particao",
    }
    if order_by not in valid_order_cols:
        order_by = "data_inicio"
    order_stmt = f"ORDER BY {order_by} {order_dir.upper()}"

    offset = (page - 1) * page_size
    from_table = "intermediate_chamados_clean"

    count_sql = f"SELECT COUNT(*) FROM {from_table} WHERE {' AND '.join(where)}"
    total = con.execute(count_sql, params).fetchone()[0]

    # Agora incluindo todos os campos solicitados + secretaria
    data_sql = (
        f"SELECT id_chamado, data_inicio, data_fim, data_alvo_finalizacao, tipo, subtipo, status, situacao, "
        f"longitude, latitude, data_particao, secretaria "
        f"FROM {from_table} WHERE {' AND '.join(where)} {order_stmt} LIMIT ? OFFSET ?"
    )
    rows = con.execute(data_sql, params + [page_size, offset]).fetchall()
    cols = [d[0] for d in con.description]

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "items": [dict(zip(cols, r)) for r in rows],
    }


@router.get("/export", dependencies=[Depends(require_role("operador"))])
def export_csv(
    # Mesmos filtros de /chamados (sem paginação)
    dt_ini: Optional[str] = None,
    dt_fim: Optional[str] = None,
    secretaria: Optional[str] = None,
    status: Optional[str] = None,
    tipo: Optional[str] = None,
    id_chamado: Optional[int] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    subtipo: Optional[str] = None,
    situacao: Optional[str] = None,
):
    con: duckdb.DuckDBPyConnection = get_connection()

    where = ["1=1"]
    params = []

    if dt_ini:
        where.append("data_inicio::date >= ?")
        params.append(dt_ini)
    if dt_fim:
        where.append("COALESCE(data_fim, data_inicio)::date <= ?")
        params.append(dt_fim)

    if id_chamado is not None:
        where.append("id_chamado = ?")
        params.append(id_chamado)
    if data_inicio:
        where.append("data_inicio::date = ?")
        params.append(data_inicio)
    if data_fim:
        where.append("data_fim::date = ?")
        params.append(data_fim)
    if secretaria:
        where.append("secretaria = ?")
        params.append(secretaria.upper())
    if status:
        where.append("status = ?")
        params.append(status.upper())
    if tipo:
        where.append("tipo LIKE ?")
        params.append(f"%{tipo.upper()}%")
    if subtipo:
        where.append("subtipo LIKE ?")
        params.append(f"%{subtipo.upper()}%")
    if situacao:
        where.append("situacao = ?")
        params.append(situacao.upper())

    from_table = "intermediate_chamados_clean"

    sql = (
        f"SELECT id_chamado, data_inicio, data_fim, data_alvo_finalizacao, tipo, subtipo, status, situacao, "
        f"longitude, latitude, data_particao, secretaria "
        f"FROM {from_table} WHERE {' AND '.join(where)}"
    )
    rs = con.execute(sql, params)
    cols = [d[0] for d in rs.description]

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(cols)
    for row in rs.fetchall():
        writer.writerow(row)
    buf.seek(0)

    return StreamingResponse(
        content=io.BytesIO(buf.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=chamados.csv"},
    )
