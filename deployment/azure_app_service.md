# Azure App Service Configuration

This document describes the configuration needed to deploy the Streamlit AI dashboard to Azure App Service.

## App Entry Point

Streamlit app:

```text
agent/03_streamlit_sql_chatbot.py
```

Azure App Service startup command:

```bash
bash startup.sh
```

The `startup.sh` script starts Streamlit with:

```bash
python -m streamlit run agent/03_streamlit_sql_chatbot.py \
  --server.address 0.0.0.0 \
  --server.port "${APP_PORT}" \
  --server.headless true \
  --browser.gatherUsageStats false
```

## Runtime

Recommended runtime:

```text
Python 3.11
```

Dependencies are installed from:

```text
requirements.txt
```

## Required Application Settings

For local development, these values can be stored in `.env`.

For Azure App Service, configure them in:

```text
App Service -> Settings -> Environment variables
```

Required settings:

| Setting | Purpose |
|---|---|
| `OPENAI_API_KEY` | Authenticates LangChain/OpenAI chatbot calls |
| `POSTGRES_USER` | PostgreSQL username |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `POSTGRES_HOST` | PostgreSQL host |
| `POSTGRES_PORT` | PostgreSQL port |
| `POSTGRES_DB` | PostgreSQL database name |

## Database Requirement

The local database value:

```text
localhost
```

will not work after deployment.

In Azure App Service, `localhost` means the App Service container/server itself, not the developer's laptop.

For full deployment, use a cloud PostgreSQL database such as:

- Azure Database for PostgreSQL
- Supabase
- Neon
- Render PostgreSQL
- Railway PostgreSQL

The Gold and prediction tables should be loaded into the cloud PostgreSQL database before enabling the SQL chatbot in production.

## Security Notes

- Do not upload `.env` to Azure.
- Do not commit API keys or database passwords.
- Use Azure App Service environment variables for basic deployment.
- Use Azure Key Vault for a more production-ready setup.
- Use a read-only PostgreSQL user for the SQL chatbot where possible.

## Health Check

Streamlit health endpoint:

```text
/_stcore/health
```

Local example:

```text
http://localhost:8501/_stcore/health
```

Expected response:

```text
ok
```

## Deployment Readiness Checklist

- `startup.sh` exists.
- `requirements.txt` contains all Python dependencies.
- Streamlit app starts successfully from `startup.sh`.
- Azure App Service startup command is set to `bash startup.sh`.
- Environment variables are configured in Azure App Service.
- PostgreSQL host points to a cloud database, not `localhost`.
- `.env` remains excluded from Git.
- CI pipeline passes before deployment.
