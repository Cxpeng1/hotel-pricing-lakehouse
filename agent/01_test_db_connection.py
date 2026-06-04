# ==============================
# Hotel Booking Analytics Chatbot
# Test LangChain PostgreSQL Connection
# ==============================

import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from openai import api_key

load_dotenv()

postgres_user = os.getenv("POSTGRES_USER")
postgres_password = quote_plus(os.getenv("POSTGRES_PASSWORD"))
postgres_host = os.getenv("POSTGRES_HOST")
postgres_port = os.getenv("POSTGRES_PORT")
postgres_db = os.getenv("POSTGRES_DB")

database_uri = (
    f"postgresql+psycopg2://{postgres_user}:{postgres_password}"
    f"@{postgres_host}:{postgres_port}/{postgres_db}"
)

db = SQLDatabase.from_uri(database_uri)
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=api_key
)
print("Database connected successfully.")
print("\nDatabase dialect:")
print(db.dialect)

print("\nAvailable tables:")
print(db.get_usable_table_names())

print("\nTable schema preview:")
print(db.get_table_info())