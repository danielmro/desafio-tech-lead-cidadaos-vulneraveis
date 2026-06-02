"""
Testes de filtros e ordenação do endpoint /chamados com banco DuckDB temporário.

Coberturas:
- Combinação de filtros: tipo + subtipo + status + situacao
- Igualdade por data_inicio e data_fim
- Filtro por id_chamado
- Fallback seguro quando order_by é inválido (usa data_inicio por padrão)
"""
import os
import tempfile

import duckdb
from fastapi.testclient import TestClient


def _setup_temp_db() -> str:
    """Cria um DuckDB temporário com duas linhas de chamados e métricas básicas."""
    temp_dir = tempfile.mkdtemp()
    path = os.path.join(temp_dir, "temp.duckdb")
    con = duckdb.connect(path, read_only=False)
    con.execute("INSTALL parquet; LOAD parquet;")

    con.execute(
        """
        CREATE TABLE intermediate_chamados_clean AS
        SELECT * FROM (
            SELECT
              1::BIGINT AS id_chamado,
              TIMESTAMP '2024-01-01 08:00:00' AS data_inicio,
              TIMESTAMP '2024-01-02 09:00:00' AS data_fim,
              TIMESTAMP '2024-01-03 23:59:59' AS data_alvo_finalizacao,
              'SAÚDE - TESTE' AS tipo,
              'SUBTIPO A' AS subtipo,
              'ENCERRADO' AS status,
              'FINALIZADO' AS situacao,
              1.23::DOUBLE AS longitude,
              -2.34::DOUBLE AS latitude,
              DATE '2024-01-01' AS data_particao,
              'SMS' AS secretaria
            UNION ALL
            SELECT
              2::BIGINT,
              TIMESTAMP '2024-01-05 10:00:00',
              NULL,
              TIMESTAMP '2024-01-10 12:00:00',
              'EDUCAÇÃO - TESTE',
              'SUBTIPO B',
              'EM ANDAMENTO',
              'ABERTO',
              3.21::DOUBLE,
              -4.32::DOUBLE,
              DATE '2024-01-05',
              'SME'
        );
        """
    )

    con.execute(
        """
        CREATE TABLE mart_dashboard_metrics (
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

    con.close()
    return path


def _client_with_db() -> TestClient:
    os.environ["DUCKDB_PATH"] = _setup_temp_db()
    from backend.src.app import app  # type: ignore

    return TestClient(app)


def _auth_headers(client: TestClient):
    token = client.post("/auth/login", json={"username": "demo", "role": "operador"}).json()[
        "access_token"
    ]
    return {"Authorization": f"Bearer {token}"}


def test_combined_filters_tipo_subtipo_status_situacao():
    client = _client_with_db()
    headers = _auth_headers(client)

    res = client.get(
        "/chamados",
        headers=headers,
        params={
            "page": 1,
            "page_size": 50,
            "tipo": "SAÚDE",
            "subtipo": "SUBTIPO A",
            "status": "ENCERRADO",
            "situacao": "FINALIZADO",
        },
    )
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["id_chamado"] == 1


def test_filter_by_exact_dates_and_id():
    client = _client_with_db()
    headers = _auth_headers(client)

    # Igualdade por data_inicio (YYYY-MM-DD)
    res1 = client.get(
        "/chamados",
        headers=headers,
        params={"data_inicio": "2024-01-01", "page": 1, "page_size": 100},
    )
    assert res1.status_code == 200
    ids1 = {it["id_chamado"] for it in res1.json()["items"]}
    assert 1 in ids1 and 2 not in ids1

    # Igualdade por data_fim (somente id 1 tem data_fim)
    res2 = client.get(
        "/chamados",
        headers=headers,
        params={"data_fim": "2024-01-02", "page": 1, "page_size": 100},
    )
    assert res2.status_code == 200
    ids2 = {it["id_chamado"] for it in res2.json()["items"]}
    assert ids2 == {1}

    # Filtro por id_chamado
    res3 = client.get(
        "/chamados",
        headers=headers,
        params={"id_chamado": 2, "page": 1, "page_size": 100},
    )
    assert res3.status_code == 200
    items3 = res3.json()["items"]
    assert len(items3) == 1 and items3[0]["id_chamado"] == 2


def test_invalid_order_by_fallbacks_to_data_inicio_desc():
    client = _client_with_db()
    headers = _auth_headers(client)

    # order_by inválido → backend deve cair para data_inicio
    res = client.get(
        "/chamados",
        headers=headers,
        params={"order_by": "__hack__", "order_dir": "desc", "page": 1, "page_size": 10},
    )
    assert res.status_code == 200
    items = res.json()["items"]
    # data_inicio desc → id 2 (2024-01-05) vem antes de id 1 (2024-01-01)
    assert items[0]["id_chamado"] == 2
