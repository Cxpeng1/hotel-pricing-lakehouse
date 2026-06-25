param(
    [switch]$SkipCreate
)

$ErrorActionPreference = "Stop"

$requiredEnvVars = @(
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB"
)

foreach ($envVar in $requiredEnvVars) {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($envVar))) {
        throw "Missing required environment variable: $envVar"
    }
}

if (-not (Get-Command psql -ErrorAction SilentlyContinue)) {
    throw "psql was not found. Install PostgreSQL client tools before running this script."
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:PGPASSWORD = $env:POSTGRES_PASSWORD
$sslMode = [Environment]::GetEnvironmentVariable("POSTGRES_SSLMODE")
if ([string]::IsNullOrWhiteSpace($sslMode)) {
    $sslMode = "prefer"
}
$env:PGSSLMODE = $sslMode

function Convert-ToPsqlPath {
    param([string]$RelativePath)

    $resolvedPath = Resolve-Path (Join-Path $repoRoot $RelativePath)
    return $resolvedPath.Path.Replace("\", "/")
}

function Invoke-PsqlFile {
    param([string]$SqlFile)

    & psql `
        -v ON_ERROR_STOP=1 `
        -h $env:POSTGRES_HOST `
        -p $env:POSTGRES_PORT `
        -U $env:POSTGRES_USER `
        -d $env:POSTGRES_DB `
        -f $SqlFile

    if ($LASTEXITCODE -ne 0) {
        throw "psql failed while running $SqlFile"
    }
}

if (-not $SkipCreate) {
    Invoke-PsqlFile -SqlFile (Join-Path $repoRoot "sql/create_gold_tables.pgsql")
}

$loadSql = @"
TRUNCATE TABLE
    fact_bookings,
    dim_hotel,
    dim_date,
    dim_room_type,
    dim_country,
    dim_market_segment,
    dim_customer_segment,
    dim_meal
RESTART IDENTITY CASCADE;

\copy dim_hotel(hotel_id, hotel) FROM '$(Convert-ToPsqlPath "data/gold/dim_hotel.csv")' WITH (FORMAT csv, HEADER true);
\copy dim_date(date_id, arrival_date, year, month, month_name, day, quarter, is_weekend) FROM '$(Convert-ToPsqlPath "data/gold/dim_date.csv")' WITH (FORMAT csv, HEADER true);
\copy dim_room_type(room_type_id, room_type_code, room_type_name) FROM '$(Convert-ToPsqlPath "data/gold/dim_room_type.csv")' WITH (FORMAT csv, HEADER true);
\copy dim_country(country_id, country) FROM '$(Convert-ToPsqlPath "data/gold/dim_country.csv")' WITH (FORMAT csv, HEADER true);
\copy dim_market_segment(market_segment_id, market_segment) FROM '$(Convert-ToPsqlPath "data/gold/dim_market_segment.csv")' WITH (FORMAT csv, HEADER true);
\copy dim_customer_segment(customer_segment_id, customer_type) FROM '$(Convert-ToPsqlPath "data/gold/dim_customer_segment.csv")' WITH (FORMAT csv, HEADER true);
\copy dim_meal(meal_id, meal, meal_plan) FROM '$(Convert-ToPsqlPath "data/gold/dim_meal.csv")' WITH (FORMAT csv, HEADER true);

\copy fact_bookings(
    fact_booking_id,
    hotel_id,
    date_id,
    reserved_room_type_id,
    assigned_room_type_id,
    country_id,
    market_segment_id,
    customer_segment_id,
    meal_id,
    is_canceled,
    booking_status,
    lead_time,
    total_nights,
    total_guests,
    adr,
    booking_value,
    estimated_revenue,
    booking_changes,
    days_in_waiting_list,
    required_car_parking_spaces,
    total_of_special_requests
) FROM '$(Convert-ToPsqlPath "data/gold/fact_bookings.csv")' WITH (FORMAT csv, HEADER true);

DROP TABLE IF EXISTS fact_booking_predictions;

CREATE TABLE fact_booking_predictions (
    prediction_id INT PRIMARY KEY,
    fact_booking_id INT,
    cancellation_probability NUMERIC(10,6),
    predicted_cancelled INT,
    risk_level VARCHAR(50),
    booking_value NUMERIC(12,2),
    expected_revenue_at_risk NUMERIC(12,2),
    model_name VARCHAR(100),
    model_version VARCHAR(50),
    prediction_timestamp TIMESTAMP
);

\copy fact_booking_predictions FROM '$(Convert-ToPsqlPath "data/ml/fact_booking_predictions.csv")' WITH (FORMAT csv, HEADER true);

SELECT 'dim_hotel' AS table_name, COUNT(*) AS row_count FROM dim_hotel
UNION ALL
SELECT 'dim_date', COUNT(*) FROM dim_date
UNION ALL
SELECT 'dim_room_type', COUNT(*) FROM dim_room_type
UNION ALL
SELECT 'dim_country', COUNT(*) FROM dim_country
UNION ALL
SELECT 'dim_market_segment', COUNT(*) FROM dim_market_segment
UNION ALL
SELECT 'dim_customer_segment', COUNT(*) FROM dim_customer_segment
UNION ALL
SELECT 'dim_meal', COUNT(*) FROM dim_meal
UNION ALL
SELECT 'fact_bookings', COUNT(*) FROM fact_bookings
UNION ALL
SELECT 'fact_booking_predictions', COUNT(*) FROM fact_booking_predictions;
"@

$tempSqlFile = New-TemporaryFile
Set-Content -Path $tempSqlFile -Value $loadSql -Encoding UTF8

try {
    Invoke-PsqlFile -SqlFile $tempSqlFile
}
finally {
    Remove-Item -LiteralPath $tempSqlFile -Force -ErrorAction SilentlyContinue
    Remove-Item Env:\PGPASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:\PGSSLMODE -ErrorAction SilentlyContinue
}
