# PostgreSQL Cloud Setup

This document describes the database preparation step for deploying the Streamlit AI dashboard beyond a local machine.

## Why This Is Needed

The local project uses PostgreSQL through environment variables such as:

```text
POSTGRES_HOST=localhost
POSTGRES_PORT=8118
```

This works only on the developer machine.

After deployment to Azure App Service, `localhost` refers to the Azure App Service environment itself, not the local laptop. Therefore, the SQL chatbot needs a cloud-accessible PostgreSQL database.

## Recommended Target

Recommended Azure target:

```text
Azure Database for PostgreSQL
```

Other acceptable managed PostgreSQL options:

- Supabase
- Neon
- Render PostgreSQL
- Railway PostgreSQL

## Database Loading Script

Use this script to create and load the PostgreSQL warehouse from the project CSV outputs:

```powershell
scripts/load_postgres_warehouse.ps1
```

The script:

- Reads database connection values from environment variables
- Runs `sql/create_gold_tables.pgsql`
- Loads Gold dimension tables
- Loads `fact_bookings`
- Creates and loads `fact_booking_predictions`
- Prints row counts after loading

## Required Environment Variables

Set these before running the script:

```powershell
$env:POSTGRES_USER="postgres"
$env:POSTGRES_PASSWORD="your_password"
$env:POSTGRES_HOST="your_cloud_postgres_host"
$env:POSTGRES_PORT="5432"
$env:POSTGRES_DB="hotel_booking_db"
```

For Azure App Service, configure the same values in:

```text
App Service -> Settings -> Environment variables
```

## Run The Load Script

From the project root:

```powershell
.\scripts\load_postgres_warehouse.ps1
```

If the tables already exist and you only want to reload data:

```powershell
.\scripts\load_postgres_warehouse.ps1 -SkipCreate
```

## Important Notes

- The script requires the PostgreSQL `psql` command-line tool.
- The script uses `\copy`, so CSV files are read from the machine running the script and loaded into the target database.
- The script can load either a local PostgreSQL database or a cloud PostgreSQL database as long as the connection settings are correct.
- For production, use a read-only database user for the Streamlit SQL chatbot after loading is complete.

## Deployment Workflow

```text
Create cloud PostgreSQL database
-> Set POSTGRES_* environment variables
-> Run scripts/load_postgres_warehouse.ps1
-> Confirm row counts
-> Configure Azure App Service with the same database settings
-> Start Streamlit app
-> Test SQL chatbot
```
