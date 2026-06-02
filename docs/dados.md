# Guia de dados: como extrair do BigQuery e preparar localmente

Este guia explica como baixar os dados públicos do 1746 no BigQuery e preparar os arquivos para uso local pelo DuckDB/dbt e pela API.

## 1) Pré-requisitos
- Conta Google com BigQuery habilitado (gratuito até determinado volume; ver limites).
- SDK do Google Cloud (gcloud) se quiser usar a CLI `bq` (opcional, mas recomendado).
- Espaço em disco local. O corte `data_particao >= '2023-01-01'` reduz bastante, mas ainda podem ser alguns GB.
- O link público do Google Drive que disponibilizei (vou apagar depois de algumas semanas) para baixar os arquivos de banco utilizados no projeto é:
https://drive.google.com/drive/folders/1dLgaGwqE5GSvbJVT6yBtog7IT8bYvAFJ?usp=sharing

## 2) Consulta base (filtro por partição)
A tabela principal é `datario.adm_central_atendimento_1746.chamado`.
Use o filtro por partição para reduzir custos e volume: `data_particao >= '2023-01-01'`.

SQL sugerido (também salvo em `pipeline/sql/bigquery_export.sql`):
```sql
SELECT
  id_chamado,
  data_inicio,
  data_fim,
  data_alvo_finalizacao,
  tipo,
  subtipo,
  status,
  situacao,
  longitude,
  latitude,
  data_particao
FROM `datario.adm_central_atendimento_1746.chamado`
WHERE data_particao >= '2023-01-01';
```
obs.: o campo que era solicitado na demanda original (README), era "prazo_atendimento", porém não existe este campo no banco de dados e o mais próximo que encontrei foi o "data_alvo_finalizacao", que então substituí no lugar.

## 3) Opção A — Exportar pelo Console do BigQuery
1. No Console Cloud, abra BigQuery.
2. Cole a query acima no editor.
3. Clique em "Salvar resultado" (Save results) → escolha "Parquet".
4. Destino:
   - Google Cloud Storage (GCS) — crie um bucket se necessário.
   - Ative particionamento de arquivos (o BigQuery geralmente particiona automaticamente em múltiplos arquivos).
5. Baixe os arquivos `.parquet` do bucket para sua máquina local.
6. Organize localmente em:
   - `data/chamados/` → coloque aqui todos os Parquets exportados.

## 4) Opção B — Exportar via CLI `bq`
Assumindo que você autenticou com `gcloud auth login` e setou o projeto:
```bash
bq --location=US query \
  --use_legacy_sql=false \
  --format=parquet \
  --destination_table=my_temp_ds.chamados_export \
  "SELECT id_chamado, data_inicio, data_fim, prazo_atendimento, tipo, subtipo, status, situacao, longitude, latitude, data_particao
     FROM `datario.adm_central_atendimento_1746.chamado`
     WHERE data_particao >= '2023-01-01'"

# Exporta a tabela temporária para GCS em Parquet
bq extract --destination_format=PARQUET my_temp_ds.chamados_export gs://meu-bucket/chamados/*.parquet

# Baixe os arquivos do GCS (gsutil)
gsutil -m cp -r gs://meu-bucket/chamados/*.parquet ./data/chamados/
```
Ajuste `my_temp_ds`, `meu-bucket` e `--location` conforme seu projeto/região.

## 5) Verificando localmente com DuckDB (opcional)
Com DuckDB instalado (ou via Python), você pode inspecionar rapidamente:
```sql
-- no cliente duckdb, por exemplo
INSTALL parquet; LOAD parquet;
SELECT * FROM read_parquet('data/chamados/*.parquet') LIMIT 10;
```

## 6) Preparando para o dbt
- O projeto dbt está em `pipeline/` e usa DuckDB.
- Você pode apontar os modelos para ler diretamente os Parquets em `data/chamados/*.parquet` ou materializar uma tabela interna .duckdb.
- Arquivo de perfil de exemplo: `pipeline/profiles.yml.example`.

## 7) Próximos passos: rodar o pipeline
1. Instale dependências (ver `pipeline/README.md`).
2. Configure `profiles.yml` (copie do exemplo) para que o `dbt` localize seu arquivo `.duckdb` e/ou parquet.
3. Rode:
```bash
dbt deps
dbt run
```
4. As saídas agregadas estarão em `pipeline/target/` e também como tabelas no arquivo `pipeline/pic.duckdb` (padrão deste projeto).

Observação: não fazemos commit dos dados em `data/`. O `.gitignore` já ignora essa pasta por padrão.
