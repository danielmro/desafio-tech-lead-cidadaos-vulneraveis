"""
Testes funcionais mínimos da API usando um banco DuckDB temporário.

- Prepara tabelas `intermediate_chamados_clean` e `mart_dashboard_metrics` com dados sintéticos.
- Valida fluxo de autenticação mock e autorização via Bearer Token.
- Verifica paginação/ordenação por `data_alvo_finalizacao` e resposta do dashboard.
"""

import os
import tempfile
from datetime import datetime, timedelta

import duckdb
from fastapi.testclient import TestClient


def setup_temp_db() -> str:
    """Cria um arquivo DuckDB temporário com as tabelas mínimas esperadas pela API.

    Observação: deixamos o DuckDB criar o arquivo do zero (não pré-criamos com mkstemp),
    pois abrir um arquivo vazio gera erro de "not a valid DuckDB database file".
    """
    temp_dir = tempfile.mkdtemp()
    path = os.path.join(temp_dir, "temp.duckdb")

    con = duckdb.connect(path, read_only=False)
    con.execute("INSTALL parquet; LOAD parquet;")

    # Tabela materializada pelo dbt consumida pelos endpoints /chamados e /export
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

    # Tabela do mart para o /dashboard
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
    con.execute(
        """
        INSERT INTO mart_dashboard_metrics VALUES
          (DATE '2024-01-01', 'SMS', 'ENCERRADO', 1, 1, 1.0, 25.0),
          (DATE '2024-01-01', 'SME', 'EM ANDAMENTO', 1, 0, 0.0, NULL);
        """
    )

    con.close()
    return path


def get_client_with_temp_db() -> TestClient:
    # Configura caminho do banco ANTES de importar a app, para que settings capte o valor
    db_path = setup_temp_db()
    os.environ["DUCKDB_PATH"] = db_path

    # Import atrasado para usar o DUCKDB_PATH recémd ef inido
    from backend.src.app import app  # type: ignore

    return TestClient(app)


def test_auth_login_and_use_token():
    client = get_client_with_temp_db()

    # Login mock
    res = client.post("/auth/login", json={"username": "demo", "role": "operador"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert token

    # Acessa /chamados com token
    headers = {"Authorization": f"Bearer {token}"}
    res2 = client.get("/chamados?page=1&page_size=10", headers=headers)
    assert res2.status_code == 200
    data = res2.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total"] == 2
    assert len(data["items"]) >= 1


def test_ordering_by_data_alvo_finalizacao():
    client = get_client_with_temp_db()

    token = client.post("/auth/login", json={"username": "demo", "role": "operador"}).json()[
        "access_token"
    ]
    headers = {"Authorization": f"Bearer {token}"}

    # Ordena ascendente por data_alvo_finalizacao
    res = client.get(
        "/chamados",
        headers=headers,
        params={"page": 1, "page_size": 50, "order_by": "data_alvo_finalizacao", "order_dir": "asc"},
    )
    assert res.status_code == 200
    items = res.json()["items"]
    # O primeiro item deve ser o com data_alvo_finalizacao '2024-01-03...' (id 1)
    assert items[0]["id_chamado"] == 1


def test_dashboard_endpoint():
    client = get_client_with_temp_db()

    token = client.post("/auth/login", json={"username": "demo", "role": "operador"}).json()[
        "access_token"
    ]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/dashboard", headers=headers)
    assert res.status_code == 200
    payload = res.json()
    assert isinstance(payload, list) and len(payload) >= 1
    keys = set(payload[0].keys())
    assert {"mes", "secretaria", "status", "total_chamados", "resolvidos_no_prazo", "taxa_sla", "tma_horas"}.issubset(
        keys
    )
