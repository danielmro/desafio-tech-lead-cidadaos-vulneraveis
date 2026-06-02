"""
Testes do endpoint /export e cenários de autenticação.

Coberturas:
- /export respeita filtros e retorna CSV com cabeçalho esperado
- Acesso aos endpoints protegidos sem token gera 401
"""
import os
import tempfile
import csv
from io import StringIO

import duckdb
from fastapi.testclient import TestClient


def _setup_temp_db() -> str:
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


def test_export_respects_filters_and_headers_csv():
    client = _client_with_db()
    headers = _auth_headers(client)

    res = client.get(
        "/export",
        headers=headers,
        params={"tipo": "SAÚDE", "subtipo": "SUBTIPO A"},
    )
    assert res.status_code == 200
    assert res.headers.get("content-type", "").startswith("text/csv")

    # Lê CSV em memória e valida cabeçalho + 1a linha
    content = res.content.decode("utf-8")
    sio = StringIO(content)
    reader = csv.reader(sio)
    header = next(reader)
    first_row = next(reader)

    expected_cols = [
        "id_chamado",
        "data_inicio",
        "data_fim",
        "data_alvo_finalizacao",
        "tipo",
        "subtipo",
        "status",
        "situacao",
        "longitude",
        "latitude",
        "data_particao",
        "secretaria",
    ]
    assert header == expected_cols
    # Após filtrar por tipo+subtipo deve sobrar só o id 1
    assert int(first_row[0]) == 1


def test_protected_endpoints_require_bearer_token():
    client = _client_with_db()

    # /chamados sem token → 401
    res1 = client.get("/chamados")
    assert res1.status_code == 401

    # /dashboard sem token → 401
    res2 = client.get("/dashboard")
    assert res2.status_code == 401

    # /export sem token → 401
    res3 = client.get("/export")
    assert res3.status_code == 401
