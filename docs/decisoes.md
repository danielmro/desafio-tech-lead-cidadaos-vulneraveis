# Decisões Técnicas

Este documento registra decisões e trade-offs feitos durante o desenvolvimento.

## Autoria
Daniel Medeiros Rocha


## Visão Geral
- Objetivo: construir um sistema local (pipeline + API + frontend) para monitorar chamados do 1746 usando dados públicos exportados do BigQuery.
- Princípios: separação de responsabilidades, reprodutibilidade local, simplicidade operacional.

## Escolhas Tecnológicas
- Armazenamento/Transformação: dbt + DuckDB
  - Por quê: DuckDB é leve, embutido (sem servidor), ótimo para analytics e integra bem com dbt. Facilita rodar localmente e escalar para arquivos Parquet.
  - Alternativa: SQLite — possível, mas DuckDB tem suporte superior a colunas numéricas/temporais e Parquet.
- Extração de dados: BigQuery (dataset público `datario`)
  - Exportação filtrada por `data_particao >= '2023-01-01'` para reduzir volume.
  - Formato preferido: Parquet (melhor compressão e leitura vetorizada pelo DuckDB).
- Backend: FastAPI + duckdb + Polars (opcional) 
  - Por quê: FastAPI é rápido de prototipar, tipado, e possui ótima doc automática.
- Autenticação: fluxo OAuth2/OIDC mockado
  - Tokens JWT assinado localmente (apenas para demonstrar o fluxo). Integração real documentada.
- Frontend: Next.js (App Router) + React Query (sugestão) 
  - Consumindo a API paginada; exportação client-side via CSV.

## Estrutura de Dados (dbt)
- Camada `intermediate`:
  - `chamados_clean`: limpeza/normalização de datas, status, coordenadas, derivação de secretaria via mapeamento por `tipo`.
- Camada `mart`:
  - `dashboard_metrics`: agregados prontos para o dashboard (volume, SLA, TMA, série temporal por mês/secretaria/status).

### Derivação de Secretaria (rascunho inicial)
- Critério: mapeamento determinístico por prefixo/padrões do campo `tipo`.
- Exemplo de regras (a refinar após explorar valores reais):
  - tipo LIKE '%SAÚDE%' → 'SMS'
  - tipo LIKE '%EDUCAÇÃO%' → 'SME'
  - tipo LIKE '%ASSISTÊNCIA%' OR '%DESENVOLVIMENTO SOCIAL%' → 'SMAS'
  - Caso não identificado → 'OUTRAS'
- Ambiguidades: quando `tipo` mistura áreas ou é muito genérico. Estratégia: adicionar tabela de mapeamento externa (seed) com manutenção contínua.

## Agregações no dbt
- SLA (resolvidos no prazo): `data_fim <= data_alvo_finalizacao` considerando linhas com ambas as datas presentes.
- TMA: média de `data_fim - data_inicio` (horas) nos chamados encerrados.
- Evolução temporal: contagem por mês, por secretaria e status.

## API
- Endpoints:
  - `GET /chamados`: filtros por data, secretaria, status, tipo/subtipo; ordenação; paginação.
  - `GET /dashboard`: retorna métricas agregadas de `mart.dashboard_metrics`.
  - `GET /export`: exporta CSV dos resultados filtrados (pagina desabilitada).
- Cache: conexão DuckDB mantida em pool + queries parametrizadas. Possível cache in-memory TTL para agregados.

## Autenticação e Acesso
- Status atual (mock): a autenticação é simulada localmente. O backend gera e valida JWTs assinados com segredo local ao chamar `/auth/login` (usuário fictício). As claims agora seguem o formato do Keycloak (iss/aud/preferred_username/realm_access/resource_access) e a biblioteca `fastapi-keycloak` está presente no projeto em modo MOCK, sem chamadas externas, apenas para demonstrar compatibilidade e futura integração.
- Implicações: adequada para desenvolvimento e testes, mas não para produção (sem verificação de assinatura/claims contra IdP, sem gerenciamento de sessão/consentimento, sem rotacionar chaves).
- Como seria com Keycloak (resumo de desenho):
  - Frontend redireciona para o Authorization Endpoint do Keycloak (OIDC Authorization Code + PKCE). Após o login, recebe o authorization code e troca por tokens (access/refresh) no Token Endpoint.
  - Backend valida o access token assinado pelo Keycloak (RS256) usando JWKS (`/.well-known/openid-configuration` → `jwks_uri`), checa `exp`, `aud`, `iss` e `roles`/`realm_access`.
  - Refresh: frontend usa o refresh token no Token Endpoint para obter novo access token; backend não armazena refresh token.
  - Logout: chamar o `end_session_endpoint` do Keycloak e invalidar contexto local.
  - Configuração típica: `OIDC_ISSUER_URL`, `OIDC_CLIENT_ID`, `OIDC_AUDIENCE`, `OIDC_REQUIRED_ROLES` e cache de JWKS com TTL.
- Roles: `operador`, `admin`, `super_admin`.
  - Controle: dependências do FastAPI validando `role` presente no token (mock local) e, em cenário real, mapeando `realm/client roles` do Keycloak para as roles internas.
  - Regra: admin não concede acima do próprio nível.

## Padrões e Boas Práticas
- Python: ruff/black (sugestão), tipagem, camadas (`api`, `core`, `services`).
- Node/Next: ESLint + TS strict, estrutura `src`.
- dbt: nomes consistentes, documentação em `schema.yml` (a adicionar) e descrições.

## Escalabilidade
- Mais dados: manter em Parquet particionado e ler via DuckDB com `READ_PARQUET('data/chamados/*.parquet')` em views externas ou tabelas.
- Mais usuários: colocar API atrás de um Uvicorn/Gunicorn com workers; mover DuckDB para arquivo `.duckdb` e considerar migração para Postgres se necessário.

## Dívidas Técnicas (Backlog)
- Refinar mapeamento de secretaria via seed dedicados.
- Testes de integração (API) e unitários (mapeamento, paginação).
- Implementar cache TTL no endpoint de dashboard.
- Automatizar ingestão (script) da exportação do BigQuery para Parquet.

## Padrão de Comentários e Docstrings
- Objetivo: deixar o código autoexplicativo sem poluir com comentários redundantes.
- Convenção:
  - Cada arquivo deve começar com uma docstring/resumo (1–4 linhas) explicando seu papel.
  - Funções públicas recebem docstring curta explicando propósito e parâmetros principais.
  - Comentários inline somente para pontos não triviais (ex.: prevenção de SQL injection, decisões de performance, workarounds).
  - SQL (dbt) começa com cabeçalho indicando Entrada/Objetivo/Saída.
  - Frontend: comentários nos fluxos (ex.: login, fetch, estados de UI) — evitar comentar o óbvio do JSX.
- Linguagem: em português, direta e objetiva.
- Exemplo rápido:
  ```py
  """Acesso ao DuckDB; mantém conexão única via lru_cache."""
  @lru_cache(maxsize=1)
  def get_connection():
      # Garante extensão parquet disponível para leitura eficiente
      con.execute("INSTALL parquet; LOAD parquet;")
      return con
  ```


## Estratégia de Testes (TDD)
- Abordagem: priorizamos escrever (ou ampliar) testes antes/ao mesmo tempo das alterações no backend.
  - Ciclo: escrever teste que falha → implementar o mínimo para passar → refatorar com a suíte verde.
- Escopo coberto agora (pytest):
  - `backend/tests/test_api.py`: verificação do fluxo base (login mock, listagem paginada/ordenada, dashboard).
  - `backend/tests/test_chamados_filters.py`: filtros combinados (`tipo`, `subtipo`, `status`, `situacao`), igualdade por `data_inicio`/`data_fim`, filtro exato por `id_chamado`, e fallback de `order_by` inválido.
  - `backend/tests/test_export_and_auth.py`: exportação CSV (cabeçalho + aplicação de filtros) e negativa de acesso (401) sem token.
- Testes de integração isolados do dataset real:
  - Cada módulo de teste cria um arquivo DuckDB temporário com as tabelas mínimas esperadas pela API (`intermediate_chamados_clean` e, quando necessário, `mart_dashboard_metrics`).
  - Isso garante reprodutibilidade, execução rápida (≈1s) e independência dos Parquets em `data/`.
- Como executar: dentro de `backend/` com o ambiente virtual ativo, rode `pytest -q`.
- Próximos passos (sugeridos):
  - Adicionar fixtures reutilizáveis para seed de dados por cenário.
  - Cobrir erros de validação (ex.: parâmetros fora do domínio) e regras de controle de acesso para `admin/super_admin` quando implementadas.
