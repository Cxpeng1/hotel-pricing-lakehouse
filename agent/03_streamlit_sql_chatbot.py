"""
Streamlit chatbot UI for the hotel booking analytics SQL agent.

Run:
    streamlit run agent/03_streamlit_sql_chatbot.py
"""

from __future__ import annotations

import html

import streamlit as st
import streamlit.components.v1 as components

from sql_agent_core import (
    DEFAULT_MODEL,
    SAMPLE_QUESTIONS,
    ask,
    create_hotel_sql_agent,
    load_environment,
)


POWERBI_EMBED_URL = (
    "https://app.powerbi.com/reportEmbed?"
    "reportId=37198e33-2448-47b6-9619-f129bf3124a2"
    "&autoAuth=true"
    "&ctid=ef7a487a-77ca-410a-803d-e426b62a587f"
    "&actionBarEnabled=false"
    "&reportCopilotInEmbed=false"
    "&filterPaneEnabled=false"
    "&navContentPaneEnabled=false"
)


def configure_page() -> None:
    st.set_page_config(
        page_title="Hotel Analytics AI Agent",
        page_icon=":bar_chart:",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 0.8rem;
            padding-bottom: 1rem;
            max-width: 1440px;
        }
        div[data-testid="stMetric"] {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 12px 14px;
            background: #ffffff;
        }
        iframe {
            border-radius: 8px;
            display: block;
        }
        .agent-subtitle {
            color: #475569;
            margin-top: -0.6rem;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_powerbi_report() -> None:
    iframe = f"""
    <iframe
        title="Hotel_analysis"
        width="100%"
        height="760"
        src="{html.escape(POWERBI_EMBED_URL, quote=True)}"
        frameborder="0"
        allowFullScreen="true">
    </iframe>
    """
    components.html(iframe, height=780)


@st.cache_resource(show_spinner=False)
def get_agent(model: str, verbose: bool):
    load_environment()
    return create_hotel_sql_agent(
        model=model,
        verbose=verbose,
        return_intermediate_steps=True,
    )


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


def initialize_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Ask me about hotel bookings, cancellation risk, revenue, "
                    "ADR, market segments, or prediction output."
                ),
                "sql": [],
            }
        ]
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None


def submit_question(question: str, agent_executor) -> None:
    st.session_state.messages.append(
        {"role": "user", "content": question, "sql": []}
    )

    with st.spinner("Querying the warehouse..."):
        try:
            response = ask(agent_executor, question)
            answer = response["output"]
            sql_queries = extract_sql_queries(response)
        except Exception as exc:
            answer = f"Agent error: {exc}"
            sql_queries = []

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sql": sql_queries}
    )


def render_chat_history(show_sql: bool) -> None:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if show_sql and message.get("sql"):
                for index, query in enumerate(message["sql"], start=1):
                    with st.expander(f"SQL query {index}", expanded=False):
                        st.code(query, language="sql")


def render_suggested_questions() -> None:
    st.caption("Suggested questions")
    columns = st.columns(len(SAMPLE_QUESTIONS))
    for column, question in zip(columns, SAMPLE_QUESTIONS):
        if column.button(question, use_container_width=True):
            st.session_state.pending_question = question


def render_sidebar() -> tuple[str, bool, bool]:
    with st.sidebar:
        st.header("Agent")
        model = st.selectbox(
            "Model",
            options=[DEFAULT_MODEL, "gpt-4o", "gpt-4.1-mini"],
            index=0,
        )
        show_sql = st.toggle("Show generated SQL", value=True)
        verbose = st.toggle("Verbose LangChain logs", value=False)

        st.divider()
        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.pending_question = None
            st.rerun()

    return model, show_sql, verbose


def main() -> None:
    configure_page()
    initialize_state()

    st.title("Hotel Analytics AI Agent")
    st.markdown(
        '<div class="agent-subtitle">Power BI dashboard plus a LangChain SQL chatbot for your PostgreSQL warehouse.</div>',
        unsafe_allow_html=True,
    )

    model, show_sql, verbose = render_sidebar()

    report_tab, chat_tab = st.tabs(["Dashboard", "SQL Chatbot"])

    with report_tab:
        render_powerbi_report()

    with chat_tab:
        render_suggested_questions()
        agent_executor = get_agent(model=model, verbose=verbose)
        render_chat_history(show_sql=show_sql)

        question = st.chat_input("Ask a business question about the hotel booking data")
        if question:
            submit_question(question, agent_executor)
            st.rerun()

        if st.session_state.pending_question:
            pending_question = st.session_state.pending_question
            st.session_state.pending_question = None
            submit_question(pending_question, agent_executor)
            st.rerun()


if __name__ == "__main__":
    main()
