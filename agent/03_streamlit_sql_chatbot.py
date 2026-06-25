"""
Streamlit chatbot UI for the hotel booking analytics SQL agent.

Run:
    streamlit run agent/03_streamlit_sql_chatbot.py
"""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from agentic_rag_graph import run_agentic_rag
from rag_doc_core import RAG_SUGGESTED_QUESTIONS, answer_document_question
from sql_agent_core import (
    DEFAULT_MODEL,
    SAMPLE_QUESTIONS,
    ask,
    create_hotel_sql_agent,
    extract_sql_queries,
    load_environment,
)

AGENTIC_SUGGESTED_QUESTIONS = [
    "Which hotel has the highest cancellation rate?",
    "What cleaning steps were applied in the Silver layer?",
    "Why was Random Forest selected as the final model?",
    "Why is Online TA risky and how much revenue is exposed?",
    "What should management focus on to reduce cancellations?",
    "Can you forecast next year revenue?",
]

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
    components.iframe(
        POWERBI_EMBED_URL,
        height=780,
        scrolling=True,
    )


@st.cache_resource(show_spinner=False)
def get_agent(model: str, verbose: bool):
    load_environment()
    return create_hotel_sql_agent(
        model=model,
        verbose=verbose,
        return_intermediate_steps=True,
    )


def initialize_state() -> None:
    if "agentic_messages" not in st.session_state:
        st.session_state.agentic_messages = [
            {
                "role": "assistant",
                "content": (
                    "Ask one question and I will route it to the SQL warehouse, "
                    "project documentation, or both."
                ),
                "route": "",
                "route_source": "",
                "route_confidence": 0.0,
                "route_reason": "",
                "sources": [],
                "sql_queries": [],
                "sql_error": "",
                "answer_error": "",
            }
        ]
    if "sql_messages" not in st.session_state:
        st.session_state.sql_messages = [
            {
                "role": "assistant",
                "content": (
                    "Ask me about hotel bookings, cancellation risk, revenue, "
                    "ADR, market segments, or prediction output."
                ),
                "sql": [],
            }
        ]
    if "rag_messages" not in st.session_state:
        st.session_state.rag_messages = [
            {
                "role": "assistant",
                "content": (
                    "Ask me about the project methodology, data pipeline, "
                    "model findings, dashboard, or documentation."
                ),
                "sources": [],
            }
        ]
    if "pending_sql_question" not in st.session_state:
        st.session_state.pending_sql_question = None
    if "pending_rag_question" not in st.session_state:
        st.session_state.pending_rag_question = None
    if "pending_agentic_question" not in st.session_state:
        st.session_state.pending_agentic_question = None


def submit_agentic_question(question: str) -> None:
    st.session_state.agentic_messages.append(
        {
            "role": "user",
            "content": question,
            "route": "",
            "route_source": "",
            "route_confidence": 0.0,
            "route_reason": "",
            "sources": [],
            "sql_queries": [],
            "sql_error": "",
            "answer_error": "",
        }
    )

    with st.spinner("Running Agentic RAG workflow..."):
        try:
            response = run_agentic_rag(question)
            message = {
                "role": "assistant",
                "content": response["final_answer"],
                "route": response["route"],
                "route_source": response["route_source"],
                "route_confidence": response["route_confidence"],
                "route_reason": response["route_reason"],
                "sources": response["sources"],
                "sql_queries": response["sql_queries"],
                "sql_error": response["sql_error"],
                "answer_error": response["answer_error"],
            }
        except Exception as exc:
            message = {
                "role": "assistant",
                "content": f"Agentic RAG workflow error: {exc}",
                "route": "error",
                "route_source": "fallback",
                "route_confidence": 0.0,
                "route_reason": "",
                "sources": [],
                "sql_queries": [],
                "sql_error": "",
                "answer_error": str(exc),
            }

    st.session_state.agentic_messages.append(message)


def submit_question(question: str, agent_executor) -> None:
    st.session_state.sql_messages.append(
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

    st.session_state.sql_messages.append(
        {"role": "assistant", "content": answer, "sql": sql_queries}
    )


def submit_rag_question(question: str, model: str) -> None:
    st.session_state.rag_messages.append(
        {"role": "user", "content": question, "sources": []}
    )

    with st.spinner("Searching project documentation..."):
        try:
            response = answer_document_question(question=question, model=model)
            answer = response["answer"]
            sources = response["sources"]
        except Exception as exc:
            answer = f"Documentation agent error: {exc}"
            sources = []

    st.session_state.rag_messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )


def render_sql_chat_history(show_sql: bool) -> None:
    for message in st.session_state.sql_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if show_sql and message.get("sql"):
                for index, query in enumerate(message["sql"], start=1):
                    with st.expander(f"SQL query {index}", expanded=False):
                        st.code(query, language="sql")


def render_agentic_chat_history(show_sql: bool) -> None:
    for message in st.session_state.agentic_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

            if message.get("route"):
                st.caption(
                    f"Route: `{message['route']}` | "
                    f"Router: `{message['route_source']}` | "
                    f"Confidence: `{message['route_confidence']:.2f}`"
                )
                if message.get("route_reason"):
                    st.caption(message["route_reason"])

            if message.get("sources"):
                with st.expander("Retrieved sources", expanded=False):
                    for source in message["sources"]:
                        st.markdown(
                            f"**{source['source']}** - {source['heading']} "
                            f"`score={source['score']}`"
                        )
                        st.caption(source["preview"])

            if show_sql and (message.get("sql_queries") or message.get("sql_error")):
                with st.expander("SQL trace", expanded=False):
                    if message.get("sql_error"):
                        st.error(message["sql_error"])
                    for query in message["sql_queries"]:
                        st.code(query, language="sql")

            if message.get("answer_error"):
                st.caption(f"Answer fallback used: {message['answer_error']}")


def render_rag_chat_history() -> None:
    for message in st.session_state.rag_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message.get("sources"):
                with st.expander("Retrieved sources", expanded=False):
                    for source in message["sources"]:
                        st.markdown(
                            f"**{source['source']}** - {source['heading']} "
                            f"`score={source['score']}`"
                        )
                        st.caption(source["preview"])


def render_suggested_sql_questions() -> None:
    st.caption("Suggested questions")
    columns = st.columns(len(SAMPLE_QUESTIONS))
    for index, (column, question) in enumerate(zip(columns, SAMPLE_QUESTIONS)):
        if column.button(question, key=f"sql_suggested_{index}", use_container_width=True):
            st.session_state.pending_sql_question = question


def render_suggested_agentic_questions() -> None:
    st.caption("Suggested agentic questions")
    columns = st.columns(3)
    for index, question in enumerate(AGENTIC_SUGGESTED_QUESTIONS):
        column = columns[index % len(columns)]
        if column.button(question, key=f"agentic_suggested_{index}", use_container_width=True):
            st.session_state.pending_agentic_question = question


def render_suggested_rag_questions() -> None:
    st.caption("Suggested documentation questions")
    columns = st.columns(len(RAG_SUGGESTED_QUESTIONS))
    for index, (column, question) in enumerate(zip(columns, RAG_SUGGESTED_QUESTIONS)):
        if column.button(question, key=f"rag_suggested_{index}", use_container_width=True):
            st.session_state.pending_rag_question = question


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
            st.session_state.agentic_messages = []
            st.session_state.sql_messages = []
            st.session_state.rag_messages = []
            st.session_state.pending_agentic_question = None
            st.session_state.pending_sql_question = None
            st.session_state.pending_rag_question = None
            st.rerun()

    return model, show_sql, verbose


def main() -> None:
    configure_page()
    initialize_state()

    st.title("Hotel Analytics AI Agent")
    st.markdown(
        '<div class="agent-subtitle">Power BI dashboard plus SQL and documentation chatbots for your analytics project.</div>',
        unsafe_allow_html=True,
    )

    model, show_sql, verbose = render_sidebar()

    report_tab, agentic_tab, chat_tab, rag_tab = st.tabs(
        ["Dashboard", "Agentic RAG Assistant", "SQL Chatbot", "Project Q&A"]
    )

    with report_tab:
        render_powerbi_report()

    with agentic_tab:
        render_suggested_agentic_questions()
        render_agentic_chat_history(show_sql=show_sql)

        agentic_question = st.chat_input(
            "Ask about hotel metrics, project methodology, or business recommendations",
            key="agentic_chat_input",
        )
        if agentic_question:
            submit_agentic_question(agentic_question)
            st.rerun()

        if st.session_state.pending_agentic_question:
            pending_question = st.session_state.pending_agentic_question
            st.session_state.pending_agentic_question = None
            submit_agentic_question(pending_question)
            st.rerun()

    with chat_tab:
        render_suggested_sql_questions()
        render_sql_chat_history(show_sql=show_sql)

        question = st.chat_input(
            "Ask a business question about the hotel booking data",
            key="sql_chat_input",
        )
        if question:
            agent_executor = get_agent(model=model, verbose=verbose)
            submit_question(question, agent_executor)
            st.rerun()

        if st.session_state.pending_sql_question:
            pending_question = st.session_state.pending_sql_question
            st.session_state.pending_sql_question = None
            agent_executor = get_agent(model=model, verbose=verbose)
            submit_question(pending_question, agent_executor)
            st.rerun()

    with rag_tab:
        render_suggested_rag_questions()
        render_rag_chat_history()

        rag_question = st.chat_input(
            "Ask about README.md or docs/*.md",
            key="rag_chat_input",
        )
        if rag_question:
            submit_rag_question(rag_question, model=model)
            st.rerun()

        if st.session_state.pending_rag_question:
            pending_question = st.session_state.pending_rag_question
            st.session_state.pending_rag_question = None
            submit_rag_question(pending_question, model=model)
            st.rerun()


if __name__ == "__main__":
    main()
