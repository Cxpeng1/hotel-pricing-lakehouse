# App Service Deployment Workflow

This document describes how the Streamlit AI dashboard can be deployed to Azure App Service.

## Deployment Goal

Move the app from local development to a hosted Azure App Service URL.

App entry point:

```text
agent/03_streamlit_sql_chatbot.py
```

Startup command:

```bash
bash startup.sh
```

## Current Deployment Readiness

The project already includes:

- `requirements.txt` for Python dependencies
- `startup.sh` for Azure-compatible Streamlit startup
- `azure-pipelines.yml` for CI validation
- `deployment/azure_resources_plan.md` for Azure resource planning
- `deployment/azure_app_service.md` for App Service configuration
- `deployment/postgresql_cloud_setup.md` for database setup planning

## Recommended Deployment Flow

```text
Developer pushes code
-> Azure DevOps CI pipeline runs
-> Python, RAG, SQL, CSV, data quality, and Streamlit checks pass
-> App code is deployed to Azure App Service
-> Azure App Service runs bash startup.sh
-> Health endpoint is checked
-> App is available through Azure URL
```

## Manual Deployment Workflow

Use this path first to understand the Azure setup before automating deployment.

```text
Create Azure resources
-> Configure App Service runtime
-> Set startup command
-> Add environment variables
-> Deploy code from GitHub or Azure Repos
-> Test health endpoint
-> Open app URL
```

### Manual Setup Checklist

1. Create Resource Group.
2. Create App Service Plan.
3. Create Azure App Service / Web App.
4. Select Python 3.11 on Linux.
5. Set startup command:

```bash
bash startup.sh
```

6. Configure environment variables:

```text
OPENAI_API_KEY
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DB
```

7. Deploy code from GitHub, Azure Repos, ZIP deploy, or Azure DevOps.
8. Check health endpoint:

```text
https://<app-name>.azurewebsites.net/_stcore/health
```

Expected response:

```text
ok
```

## Azure DevOps CD Workflow

After the manual deployment is understood, deployment can be automated with Azure DevOps.

Recommended CD flow:

```text
CI passes on main
-> Archive app files
-> Deploy package to Azure App Service
-> Azure App Service restarts
-> Run health check
```

Example future Azure DevOps deployment stages:

```yaml
stages:
  - stage: CI
    jobs:
      - job: ValidateProject
        steps:
          - script: echo "Run existing CI checks"

  - stage: Deploy
    dependsOn: CI
    condition: succeeded()
    jobs:
      - deployment: DeployStreamlitApp
        environment: dev
        strategy:
          runOnce:
            deploy:
              steps:
                - task: AzureWebApp@1
                  inputs:
                    azureSubscription: "$(AZURE_SERVICE_CONNECTION)"
                    appType: webAppLinux
                    appName: "$(AZURE_WEBAPP_NAME)"
                    package: "$(Pipeline.Workspace)/drop/app.zip"
```

This CD stage is intentionally not active yet because it requires:

- Azure App Service to exist
- Azure DevOps service connection
- App Service name
- Environment variables configured in Azure
- Cloud PostgreSQL database for full SQL chatbot functionality

## Deployment Package Contents

The deployed package should include:

```text
agent/
data/
docs/
powerbi/
sql/
startup.sh
requirements.txt
README.md
```

For a smaller production package, large local artifacts can be moved to cloud storage later.

## Health Check Workflow

After deployment, test:

```text
https://<app-name>.azurewebsites.net/_stcore/health
```

Then test the UI:

```text
https://<app-name>.azurewebsites.net
```

Expected result:

- Dashboard tab loads
- Project Q&A tab loads
- RAG documentation retrieval works when `OPENAI_API_KEY` is configured
- SQL chatbot works when cloud PostgreSQL settings are configured

## Rollback Idea

If deployment fails:

```text
Check App Service logs
-> Check environment variables
-> Check startup command
-> Re-run previous successful deployment
-> Review Azure DevOps pipeline logs
```

For production, use deployment slots:

```text
Deploy to staging slot
-> Test health endpoint
-> Swap staging to production
```

## What Is Not Automated Yet

The current project has CI but not full CD.

Not automated yet:

- Azure resource provisioning
- Azure App Service deployment
- Cloud PostgreSQL creation
- Key Vault setup
- App Service environment variable creation
- Deployment slot swap

These can be added later with Azure DevOps, Bicep, or Terraform.
