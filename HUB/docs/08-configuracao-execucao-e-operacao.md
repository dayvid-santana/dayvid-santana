# Configuração, execução e operação

## Backend local

```powershell
cd HUB_acesso_Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .[dev]
Copy-Item .env.example .env
python scripts/prepare_database.py
uvicorn app.main:app --reload --port 8088
```

O banco padrão é SQLite local. Para consultar CSV, crie `data/colaboradores.csv` com as dez colunas obrigatórias.

## Frontend local

```powershell
cd HUB_acesso_Frontend
npm install
npm run dev
```

Abra `http://localhost:5173`. O Vite encaminha `/api` para o backend em `localhost:8088`.

## Variáveis relevantes

| Variável | Padrão/uso |
| --- | --- |
| `APP_ENV` | `development`; `production` ativa validações rigorosas |
| `DATABASE_URL` | SQLite local ou PostgreSQL persistente |
| `SENIOR_SOURCE` | `csv` ou `sql` |
| `SENIOR_CSV_PATH` | caminho do CSV |
| `SENIOR_SQL_DATABASE_URL` | conexão da fonte SQL |
| `SENIOR_SQL_VIEW` | `vw_colaboradores_hub` |
| `INGESTION_BATCH_SIZE` | 200 |
| `REQUEST_CONCURRENCY_PER_SYSTEM` | 10 |
| `SENIOR_CACHE_TTL_SECONDS` | 30 para leituras; `0` desativa |
| `AUTO_SCAN_ENABLED` | `true` |
| `SCAN_INTERVAL_MINUTES` | 15 |
| `CORS_ORIGINS` | origens separadas por vírgula |
| `LOGO_STORAGE_PATH` | `static/logos` |
| `LOGO_MAX_BYTES` | 512000 |
| `SESSION_PROVIDER` | `mock` atualmente |

## Docker de desenvolvimento

No backend:

```powershell
cd HUB_acesso_Backend
docker compose up --build -d postgres mock-erp
docker compose run --rm --no-deps api python scripts/prepare_database.py
docker compose up --build api
```

A API fica em `http://localhost:8088`, o PostgreSQL é persistido em volume e `mock-erp` simula um sistema externo HTTPS local.

Para desenvolvimento com recarga do backend:

```powershell
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

No frontend, `docker-compose.dev.yml` fornece Node e Vite em `http://localhost:5173`; `docker-compose.yml` serve a build pelo Nginx em `http://localhost:8080`.

## Produção

Use `compose.production.yaml` sobre `compose.yaml` e forneça:

- `APP_ENV=production`;
- `DATABASE_URL` PostgreSQL do Hub;
- `SENIOR_SOURCE=sql`;
- `SENIOR_SQL_DATABASE_URL` e `SENIOR_SQL_VIEW`;
- `CORS_ORIGINS` com os domínios reais;
- `MOCK_DATA_ENABLED=false`.

Antes de iniciar a API, execute a preparação como etapa controlada de migration/provisionamento:

```powershell
docker compose --env-file .env.production -f compose.yaml -f compose.production.yaml run --rm api python scripts/prepare_database.py
docker compose --env-file .env.production -f compose.yaml -f compose.production.yaml up --build -d api
```

O healthcheck usa `/ready`; portanto, banco e view Senior precisam estar acessíveis para o container ficar pronto.

## Procedimento de diagnóstico

1. `GET /health`: confirma que o processo responde.
2. `GET /ready`: separa falha no banco de falha no Senior.
3. `GET /api/monitoramento/varreduras`: verifica trava, última execução, contagens e causa da última falha.
4. Logs do container: `docker compose logs --tail=200 api`.
5. Teste administrativo: `POST /api/sistemas/{slug}/teste` com CPF de teste.
6. Para lista, conferir página de falha, parâmetros, páginas/registros lidos e indexados.

Não registre tokens, API keys, CPF completo ou payloads sensíveis em logs de troubleshooting.

