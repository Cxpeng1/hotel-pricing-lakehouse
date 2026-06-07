# Azure Resources Plan

This document defines the Azure resources needed to deploy the Hotel Pricing Lakehouse Streamlit AI dashboard.

## Deployment Goal

Deploy the Streamlit app so users can access it through a public Azure App Service URL.

App entry point:

```text
agent/03_streamlit_sql_chatbot.py
```

Startup command:

```bash
bash startup.sh
```

## Minimum Resource Plan

| Resource | Purpose |
|---|---|
| Resource Group | Logical container for all Azure resources |
| App Service Plan | Defines compute size and pricing tier for the web app |
| Azure App Service | Hosts the Streamlit AI dashboard |

## Recommended Resource Names

These names can be adjusted if Azure reports a naming conflict.

| Resource | Suggested Name |
|---|---|
| Resource Group | `rg-hotel-pricing-lakehouse-dev` |
| App Service Plan | `asp-hotel-pricing-lakehouse-dev` |
| Web App | `app-hotel-pricing-lakehouse-dev` |

## Recommended Runtime

| Setting | Value |
|---|---|
| Publish | Code |
| Runtime stack | Python |
| Python version | Python 3.11 |
| Operating system | Linux |
| Region | Closest available region |
| Startup command | `bash startup.sh` |

## Required App Service Settings

Configure these as App Service environment variables.

| Setting | Required For |
|---|---|
| `OPENAI_API_KEY` | SQL chatbot and RAG chatbot LLM calls |
| `POSTGRES_USER` | PostgreSQL connection |
| `POSTGRES_PASSWORD` | PostgreSQL connection |
| `POSTGRES_HOST` | PostgreSQL connection |
| `POSTGRES_PORT` | PostgreSQL connection |
| `POSTGRES_DB` | PostgreSQL connection |

## Database Dependency

The deployed App Service should not use:

```text
localhost
```

For the deployed SQL chatbot, `POSTGRES_HOST` must point to a cloud-accessible PostgreSQL database.

Recommended target:

```text
Azure Database for PostgreSQL
```

## Manual Creation Workflow

Use this sequence when creating resources manually in Azure Portal:

```text
Create Resource Group
-> Create App Service Plan
-> Create Web App / App Service
-> Select Python 3.11 on Linux
-> Set startup command to bash startup.sh
-> Add App Service environment variables
-> Deploy code
-> Check /_stcore/health
-> Open app URL
```

## Health Check

Streamlit health endpoint:

```text
/_stcore/health
```

Expected response:

```text
ok
```

## Future Production Resources

These are recommended for a more production-ready version.

| Resource | Purpose |
|---|---|
| Azure Database for PostgreSQL | Cloud PostgreSQL warehouse for SQL chatbot |
| Azure Key Vault | Secure storage for OpenAI and database secrets |
| Application Insights | App performance and error monitoring |
| Log Analytics Workspace | Centralized logs and diagnostics |
| Storage Account / Data Lake | Stores Raw, Bronze, Silver, Gold, and ML output files |

## Future IaC Option

After manually understanding the Azure resources, the next improvement is to define them using Infrastructure as Code.

Recommended options:

- Bicep
- Terraform

IaC would make Dev, UAT, and Production environments repeatable.
