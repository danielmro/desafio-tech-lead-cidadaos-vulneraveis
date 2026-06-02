# Backend (FastAPI)

API para servir dados transformados (DuckDB) ao frontend. Inclui autenticação mock (JWT) e controle de acesso por roles.

## Pré-requisitos
- Python 3.10+
- Banco DuckDB gerado pelo dbt em `pipeline/pic.duckdb` (rode o pipeline antes)

## Instalação
```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Execução (desenvolvimento)
```bash
uvicorn src.app:app --reload --port 8000
```
Acesse a documentação: http://localhost:8000/docs

## Configuração
- Variáveis de ambiente suportadas:
  - `DUCKDB_PATH` (padrão: `pipeline/pic.duckdb`)
  - `JWT_SECRET` (padrão: `dev-secret-change-me`)
  - `JWT_EXPIRES_MINUTES` (padrão: `60`)

## Endpoints principais
- `POST /auth/login` — recebe `username`, `role` (operador|admin|super_admin) e retorna JWT (mock, sem senha real)
- `GET /chamados` — listagem com filtros (data, secretaria, status, tipo), ordenação e paginação
- `GET /dashboard` — métricas agregadas (pré-calculadas no dbt)
- `GET /export` — exporta CSV dos filtros aplicados

## Testes

Este projeto segue uma abordagem orientada a testes (TDD pragmático) no backend. Cada nova funcionalidade da API recebe (ou é precedida por) casos de teste em `pytest`, cobrindo fluxos felizes e cenários de erro.

### Estrutura dos testes
- `backend/tests/test_api.py`: sanity checks do serviço
  - Login mock (`/auth/login`)
  - Listagem (`/chamados`) com paginação/ordenação por `data_alvo_finalizacao`
  - Dashboard (`/dashboard`)
- `backend/tests/test_chamados_filters.py`: filtros e ordenação
  - Combinações de filtros: `tipo` + `subtipo` + `status` + `situacao`
  - Igualdade por `data_inicio` e `data_fim`
  - Filtro exato por `id_chamado`
  - Fallback seguro quando `order_by` é inválido (cai para `data_inicio`)
- `backend/tests/test_export_and_auth.py`: exportação e autenticação
  - `/export` respeita filtros e retorna CSV com cabeçalho esperado
  - Endpoints protegidos sem token retornam `401`

Todos os testes constroem um DuckDB temporário com as tabelas mínimas esperadas, sem depender dos Parquets reais.

### Como rodar
1. Instale as dependências (incluindo pytest) no ambiente virtual indicado acima.
2. Execute:
```bash
pytest -q
```

### Desenvolvimento guiado por testes (TDD)
- Escrevemos (ou expandimos) testes primeiro para cada requisito da API (ex.: novo filtro), observando a falha inicial.
- Implementamos a menor mudança no código para fazer o teste passar.
- Fazemos refactor mantendo a suíte verde.

### Observação sobre dados/DB
A API em execução normal espera que você rode o pipeline dbt antes para gerar `pipeline/pic.duckdb`. Em testes, usamos um banco temporário e não dependemos dos Parquets reais.
