# Instruções para Instalação, Inicialização e Utilização do Sistema
Este documento descreve o procedimento completo para configurar, rodar e usar todo o sistema de monitoramento de chamados, incluindo ambiente, pipelines, API e frontend.
## Requisitos
- Python 3.10 ou superior
- Node.js 20 ou superior
- Gerenciador de pacotes `pnpm` (recomendado) ou /`yarn` `npm`
- Git

## 1. Clonar o repositório
``` bash
git clone <URL_DO_REPOSITORIO>
cd nome-do-repositorio
```
## 2. Configurar o ambiente Python
### a) Criar e ativar ambiente virtual
``` bash
python -m venv .venv
# No Windows PowerShell:
. .venv/Scripts/Activate.ps1
# No Linux/macOS:
source .venv/bin/activate

#Para rodar o back-end e o front-end separadamente
#back-end
.venv\Scripts\uvicorn.exe src.app:app --reload --port 8000
#front-end
npm run dev
```
### b) Instalar dependências do pipeline
``` bash
pip install -r pipeline/requirements.txt
# Ou diretamente:
pip install dbt-core dbt-duckdb
```
## 3. Preparar o banco de dados DuckDB
- O arquivo `pipeline/pic.duckdb` será criado automaticamente na primeira execução dos modelos do dbt.
- Certifique-se de que seus arquivos `.parquet` estão na pasta `data/chamados/`.

obs.: Devido a exportação do banco BigQuery, o resultado precisou ser particionado/fragmentado em muitos 
arquivo por exceder 1GB não possibilitando 1 arquivo único com tudo, totalizando assim 50 arquivos (000000000000.parquet ao 000000000049.parquet) 
utilizando o filtro solicitado (data_particao >= '2023-01-01') para a tabela "datario.adm_central_atendimento_1746.chamado". As outras tabelas não 
foram utilizadas.

### a) Exportar os arquivos Parquet do BigQuery
Siga as orientações do para exportar os arquivos e colocá-los em `data/chamados/`. `dados.md`
## 4. Configurar o dbt
### a) Copiar o arquivo de perfil
``` bash
cp pipeline/profiles.yml.example ~/.dbt/profiles.yml
```
No Windows, ajuste o caminho para `%USERPROFILE%\.dbt\profiles.yml`.
### b) Ajustar o `profiles.yml`, se necessário
Verifique se o caminho do arquivo `.duckdb` está correto (padrão: `./pipeline/pic.duckdb`).
## 5. Rodar o pipeline de dados
### a) Instalar dependências do dbt
``` bash
cd pipeline
dbt deps
```
### b) Executar os modelos
``` bash
dbt run
```
Se tudo correr bem, as tabelas e views serão criadas no arquivo `pipeline/pic.duckdb`.
## 6. Rodar o servidor da API
### a) Instalar dependências do backend
``` bash
cd ../backend
pip install -r requirements.txt
```
### b) Inicializar o servidor
``` bash
uvicorn api.main:app --reload
```
A API estará acessível em [http://localhost:8000](http://localhost:8000).
## 7. Rodar o frontend
### a) Instalar dependências
``` bash
cd ../frontend
pnpm install
```
### b) Iniciar o servidor de desenvolvimento
``` bash
pnpm dev
```
A interface estará disponível em [http://localhost:3000](http://localhost:3000).
## 8. Autenticação e controle de acesso
- Status atual (MOCK): usamos JWT local gerado em `POST /auth/login` com claims compatíveis com Keycloak (iss/aud/preferred_username/realm_access/resource_access), mantendo o fluxo simples usado no frontend (botão de login mock).
- Biblioteca: `fastapi-keycloak` está adicionada como dependência para demonstrar uso e compatibilidade, porém NÃO realizamos chamadas externas nem integramos com um servidor Keycloak real neste projeto.
- Variáveis úteis:
  - `USE_KEYCLOAK_MOCK=1` (padrão): mantém o modo mock ativo (sem I/O externo).
  - `KEYCLOAK_MOCK_ISSUER` (padrão: `https://mock.keycloak.local/realms/demo`)
  - `KEYCLOAK_MOCK_CLIENT_ID` (padrão: `frontend-app`)
- Como testar: faça login e use o token nas requisições protegidas via `Authorization: Bearer <token>`. O backend aceita tokens com `aud` Keycloak sem exigir validação de audiência (apenas no modo MOCK).
- Controle de acesso por roles (mock): `operador`, `admin`, `super_admin`.

## Resumo final
Após seguir esses passos, todo o sistema estará operacional, permitindo consultar os chamados via API, visualizar dashboards, fazer filtros, exportar dados e testar a autenticação.
