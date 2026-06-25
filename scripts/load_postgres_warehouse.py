"""
Load Gold-layer warehouse CSV files into PostgreSQL without requiring psql.

Required environment variables:
    POSTGRES_USER
    POSTGRES_PASSWORD
    POSTGRES_HOST
    POSTGRES_PORT
    POSTGRES_DB

Optional:
    POSTGRES_SSLMODE=require
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2


REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ENV_VARS = [
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
]

TABLE_LOADS = [
    ("dim_hotel", "data/gold/dim_hotel.csv", ["hotel_id", "hotel"]),
    (
        "dim_date",
        "data/gold/dim_date.csv",
        [
            "date_id",
            "arrival_date",
            "year",
            "month",
            "month_name",
            "day",
            "quarter",
            "is_weekend",
        ],
    ),
    (
        "dim_room_type",
        "data/gold/dim_room_type.csv",
        ["room_type_id", "room_type_code", "room_type_name"],
    ),
    ("dim_country", "data/gold/dim_country.csv", ["country_id", "country"]),
    (
        "dim_market_segment",
        "data/gold/dim_market_segment.csv",
        ["market_segment_id", "market_segment"],
    ),
    (
        "dim_customer_segment",
        "data/gold/dim_customer_segment.csv",
        ["customer_segment_id", "customer_type"],
    ),
    ("dim_meal", "data/gold/dim_meal.csv", ["meal_id", "meal", "meal_plan"]),
    (
        "fact_bookings",
        "data/gold/fact_bookings.csv",
        [
            "fact_booking_id",
            "hotel_id",
            "date_id",
            "reserved_room_type_id",
            "assigned_room_type_id",
            "country_id",
            "market_segment_id",
            "customer_segment_id",
            "meal_id",
            "is_canceled",
            "booking_status",
            "lead_time",
            "total_nights",
            "total_guests",
            "adr",
            "booking_value",
            "estimated_revenue",
            "booking_changes",
            "days_in_waiting_list",
            "required_car_parking_spaces",
            "total_of_special_requests",
        ],
    ),
    (
        "fact_booking_predictions",
        "data/ml/fact_booking_predictions.csv",
        [
            "prediction_id",
            "fact_booking_id",
            "cancellation_probability",
            "predicted_cancelled",
            "risk_level",
            "booking_value",
            "expected_revenue_at_risk",
            "model_name",
            "model_version",
            "prediction_timestamp",
        ],
    ),
]


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def connect():
    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    return psycopg2.connect(
        user=get_required_env("POSTGRES_USER"),
        password=get_required_env("POSTGRES_PASSWORD"),
        host=get_required_env("POSTGRES_HOST"),
        port=get_required_env("POSTGRES_PORT"),
        dbname=get_required_env("POSTGRES_DB"),
        sslmode=os.getenv("POSTGRES_SSLMODE", "prefer"),
    )


def copy_csv(
    cursor, table_name: str, relative_path: str, columns: list[str]
) -> None:
    csv_path = REPO_ROOT / relative_path
    column_list = ", ".join(columns)
    copy_sql = (
        f"COPY {table_name} ({column_list}) "
        "FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"
    )

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        cursor.copy_expert(copy_sql, csv_file)


def main() -> None:
    create_tables_sql = (REPO_ROOT / "sql/create_gold_tables.pgsql").read_text(
        encoding="utf-8"
    )
    prediction_table_sql = """
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
    """

    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(prediction_table_sql)
            cursor.execute(create_tables_sql)
            cursor.execute(prediction_table_sql)

            for table_name, relative_path, columns in TABLE_LOADS:
                print(f"Loading {table_name}...")
                copy_csv(cursor, table_name, relative_path, columns)

            print("\nLoaded row counts:")
            for table_name, _, _ in TABLE_LOADS:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                row_count = cursor.fetchone()[0]
                print(f"{table_name}: {row_count}")


if __name__ == "__main__":
    main()
