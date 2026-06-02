# Script: scripts/teste_tudo.ps1
# Objetivo: executar uma verificação ponta-a-ponta local do backend
# - Prepara venv do backend e instala dependências
# - Roda pytest
# - Popula um DuckDB mínimo via seed
# - Sobe a API (Uvicorn), aguarda /health
# - Executa chamadas autenticadas: /auth/login, /chamados, /dashboard, /export
# - Encerra a API e imprime um resumo
# Observação: Frontend/Next não é iniciado aqui (é interativo). Use npm run dev separadamente.

param(
  [string]$HostUrl = "http://127.0.0.1:8000",
  [int]$Port = 8000,
  [switch]$SkipTests,
  [int]$RequestTimeoutSec = 15
)

$ErrorActionPreference = "Stop"

function Write-Info($msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Ok($msg) { Write-Host "[ OK ] $msg" -ForegroundColor Green }
function Write-Err($msg) { Write-Host "[ERR ] $msg" -ForegroundColor Red }

# 1) Preparar venv e instalar deps
Write-Info "Preparando ambiente do backend..."
Push-Location "$PSScriptRoot\..\backend"
if (!(Test-Path .venv)) { python -m venv .venv }
. .\.venv\Scripts\Activate.ps1
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt

# 2) Rodar pytest (opcionalmente pulando)
if (-not $SkipTests) {
  Write-Info "Executando pytest..."
  pytest -q
  if ($LASTEXITCODE -ne 0) { Write-Err "Testes falharam"; exit 1 } else { Write-Ok "Testes passaram" }
} else {
  Write-Info "Pulando pytest conforme solicitado"
}

Pop-Location

# 3) Seed do banco (gera pipeline/pic.duckdb)
Write-Info "Gerando seed no DuckDB (pipeline/pic.duckdb)..."
python .\backend\scripts\seed_db.py | Out-Host

# 4) Subir API
Write-Info "Subindo API (Uvicorn) em background..."
$env:DUCKDB_PATH = "pipeline/pic.duckdb"
$uv = Start-Process -FilePath ".\backend\.venv\Scripts\uvicorn.exe" -ArgumentList "src.app:app","--host","0.0.0.0","--port","$Port" -WorkingDirectory ".\backend" -PassThru
Start-Sleep -Seconds 1

# 4.1) Aguardar /health ficar OK (timeout 20s)
$deadline = (Get-Date).AddSeconds(20)
$healthUrl = "$HostUrl/health"
$healthy = $false
while((Get-Date) -lt $deadline) {
  try {
    $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 3
    if ($r.StatusCode -eq 200) { $healthy = $true; break }
  } catch { Start-Sleep -Milliseconds 700 }
}
if (-not $healthy) {
  try { Stop-Process -Id $uv.Id -Force } catch {}
  Write-Err "API não respondeu em /health dentro do tempo limite"
  exit 1
}
Write-Ok "/health respondeu 200"

# 5) Fluxo autenticado
try {
  Write-Info "Realizando login mock..."
  $loginRes = Invoke-RestMethod -Method POST -Uri "$HostUrl/auth/login" -Body (@{ username = "demo"; role = "operador" } | ConvertTo-Json) -ContentType 'application/json'
  $token = $loginRes.access_token
  if (-not $token) { throw "Token não recebido" }
  Write-Ok "Login ok"

  $headers = @{ Authorization = "Bearer $token" }

  Write-Info "Consultando /chamados..."
  $ch = Invoke-RestMethod -Method GET -Uri "$HostUrl/chamados?page=1&page_size=10&order_by=data_inicio&order_dir=desc" -Headers $headers
  if (-not $ch.items) { throw "/chamados não retornou items" }
  Write-Ok "/chamados ok (total=$($ch.total))"

  Write-Info "Consultando /dashboard..."
  $dash = Invoke-RestMethod -Method GET -Uri "$HostUrl/dashboard" -Headers $headers
  if (-not $dash) { throw "/dashboard vazio" }
  Write-Ok "/dashboard ok (registros=$($dash.Count))"

  Write-Info "Exportando CSV..."
  $csvPath = Join-Path $PSScriptRoot "chamados_export.csv"
  Invoke-WebRequest -Uri "$HostUrl/export?page=1&page_size=10" -Headers $headers -OutFile $csvPath -UseBasicParsing
  if (!(Test-Path $csvPath)) { throw "Export não gerou arquivo" }
  Write-Ok "CSV exportado em $csvPath"
}
catch {
  Write-Err $_
  try { Stop-Process -Id $uv.Id -Force } catch {}
  exit 1
}

# 6) Encerrar API
try {
  Stop-Process -Id $uv.Id -Force
  Write-Ok "API encerrada (PID $($uv.Id))"
} catch {
  Write-Err "Falha ao encerrar API: $_"
}

Write-Host "\nResumo:"
Write-Host "- pytest: OK"
Write-Host "- seed DuckDB: OK"
Write-Host "- /health, /auth/login, /chamados, /dashboard, /export: OK"
Write-Host "\nTudo pronto!" -ForegroundColor Green
