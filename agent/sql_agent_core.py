"""
Shared LangChain SQL agent setup for the hotel booking warehouse.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI


DEFAULT_MODEL = "gpt-4o-mini"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

WAREHOUSE_TABLES = [
    "fact_bookings",
    "dim_hotel",
    "dim_date",
    "dim_room_type",
    "dim_country",
    "dim_market_segment",
    "dim_customer_segment",
    "dim_meal",
    "fact_booking_predictions",
]

SAMPLE_QUESTIONS = [
    "How many total bookings are in fact_bookings?",
    "Which hotel has the highest cancellation rate?",
    "Which market segment has the most high risk bookings?",
    "What is the total expected revenue at risk?",
    "Which month generated the highest estimated revenue?",
]

AGENT_PREFIX = """
You are a careful hotel booking analytics assistant.

You are working with a {dialect} database.
Unless the user asks for a specific number of rows, limit query results to {top_k} rows.
Use only the available hotel warehouse tables to answer questions.
Prefer concise business explanations after running SQL.
Do not modify data. Only run read-only SELECT queries.
When calculating rates, show the numerator, denominator, and percentage when useful.
If a question cannot be answered from the schema, say what data is missing.
"""


def load_environment() -> None:
    load_dotenv(PROJECT_ROOT / ".env", override=True)


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def build_database_uri() -> str:
    load_environment()
    postgres_user = get_required_env("POSTGRES_USER")
    postgres_password = quote_plus(get_required_env("POSTGRES_PASSWORD"))
    postgres_host = get_required_env("POSTGRES_HOST")
    postgres_port = get_required_env("POSTGRES_PORT")
    postgres_db = get_required_env("POSTGRES_DB")
    postgres_sslmode = os.getenv("POSTGRES_SSLMODE", "prefer")

    return (
        f"postgresql+psycopg2://{postgres_user}:{postgres_password}"
        f"@{postgres_host}:{postgres_port}/{postgres_db}"
        f"?sslmode={postgres_sslmode}"
    )


def create_database() -> SQLDatabase:
    return SQLDatabase.from_uri(
        build_database_uri(),
        include_tables=WAREHOUSE_TABLES,
        sample_rows_in_table_info=3,
    )


def create_hotel_sql_agent(
    model: str = DEFAULT_MODEL,
    verbose: bool = False,
    return_intermediate_steps: bool = False,
):
    db = create_database()
    llm = ChatOpenAI(model=model, temperature=0)

    return create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        verbose=verbose,
        handle_parsing_errors=True,
        prefix=AGENT_PREFIX,
        agent_executor_kwargs={
            "return_intermediate_steps": return_intermediate_steps,
        },
    )


def ask(agent_executor, question: str):
    return agent_executor.invoke({"input": question})


def extract_sql_queries(response: dict) -> list[str]:
    queries: list[str] = []
    for step in response.get("intermediate_steps", []):
        if not isinstance(step, tuple) or len(step) < 1:
            continue

        action = step[0]
        tool_name = getattr(action, "tool", "")
        tool_input = getattr(action, "tool_input", None)

        if "query" not in tool_name.lower() and "sql" not in tool_name.lower():
            continue

        if isinstance(tool_input, dict):
            query = tool_input.get("query") or tool_input.get("sql")
        else:
            query = tool_input

        if isinstance(query, str) and query.strip():
            queries.append(query.strip())

    return queries
