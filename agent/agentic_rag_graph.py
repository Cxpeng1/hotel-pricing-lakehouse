"""
Step 1 for the Agentic RAG assistant: hybrid question routing.

The router first handles high-confidence questions with deterministic rules.
When the question is ambiguous, it asks an LLM to choose the route. Later steps
will connect these routes to the documentation retriever, SQL agent, and final
answer synthesis nodes.
"""

from __future__ import annotations

from typing import Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from rag_doc_core import build_chunks, format_context, retrieve_chunks
from sql_agent_core import (
    DEFAULT_MODEL,
    ask,
    create_hotel_sql_agent,
    extract_sql_queries,
    load_environment,
)


Route = Literal["sql", "rag", "hybrid", "unsupported"]
RouteSource = Literal["rules", "llm", "fallback"]


class AgenticRagState(TypedDict):
    question: str
    route: Route
    route_source: RouteSource
    route_confidence: float
    route_reason: str
    docs_context: str
    sources: list[dict]
    sql_answer: str
    sql_queries: list[str]
    sql_error: str
    final_answer: str
    answer_error: str


SQL_SIGNALS = [
    "how many",
    "total",
    "highest",
    "lowest",
    "average",
    "rate",
    "cancellation rate",
    "cancellation",
    "cancellations",
    "cancelled",
    "revenue",
    "expected revenue at risk",
    "adr",
    "bookings",
    "booking volume",
    "risk level",
    "high-risk",
    "which hotel",
    "which month",
    "which segment",
    "by hotel",
    "by month",
    "by segment",
]

RAG_SIGNALS = [
    "explain",
    "methodology",
    "pipeline",
    "cleaning",
    "silver layer",
    "gold layer",
    "bronze layer",
    "random forest",
    "model selected",
    "model selection",
    "why was",
    "limitation",
    "architecture",
    "implementation",
    "documentation",
    "formula",
    "calculated",
    "calculation",
]

HYBRID_SIGNALS = [
    "recommend",
    "recommendation",
    "should",
    "focus on",
    "business impact",
    "risky",
    "risk",
    "why is",
    "how much",
    "what should",
    "management",
]

UNSUPPORTED_SIGNALS = [
    "next year",
    "future revenue",
    "forecast",
    "predict future",
    "stock price",
    "weather",
    "ceo",
]

ROUTER_SYSTEM_PROMPT = """
You are a router for a hotel analytics Agentic RAG assistant.

Choose exactly one route:

sql:
Use when the user asks for metrics, counts, rankings, aggregations, revenue,
ADR, cancellation rates, booking volume, or data from warehouse tables.

rag:
Use when the user asks about methodology, data pipeline, cleaning steps,
model selection, documentation, limitations, architecture, or implementation.

hybrid:
Use when the user needs both business explanation and metrics, such as
recommendations, risk analysis, "why" plus "how much", or management decisions.

unsupported:
Use when the question is outside the hotel booking project, asks for future
forecasts not supported by this project, private information, or anything not
answerable from the project documentation or hotel warehouse.

Return only one word: sql, rag, hybrid, unsupported.
"""

SYNTHESIS_SYSTEM_PROMPT = """
You are a hotel analytics Agentic RAG assistant.

Answer the user using only the evidence provided by the graph.
If documentation context is available, use it and mention relevant source names.
If a SQL answer is available, use it as warehouse evidence.
If SQL failed, clearly say that live warehouse metrics are unavailable.
If the route is unsupported, say the current project does not contain enough
information to answer.

Be concise, business-focused, and specific. Do not invent numbers, tables, or
project details that are not present in the evidence.

Write formulas in plain text, not raw LaTeX. For example, write:
"Cancellation Rate (%) = Canceled Bookings / Total Bookings x 100".
When a percentage formula is used, include the "x 100" step.
"""


def count_signals(question: str, signals: list[str]) -> int:
    normalized = question.lower()
    return sum(signal in normalized for signal in signals)


def classify_with_rules(question: str) -> tuple[Route | None, float, str]:
    sql_score = count_signals(question, SQL_SIGNALS)
    rag_score = count_signals(question, RAG_SIGNALS)
    hybrid_score = count_signals(question, HYBRID_SIGNALS)
    unsupported_score = count_signals(question, UNSUPPORTED_SIGNALS)

    if unsupported_score > 0:
        return "unsupported", 0.85, "Question contains unsupported/out-of-scope signals."

    if hybrid_score > 0 and (sql_score > 0 or rag_score > 0):
        return "hybrid", 0.9, "Question combines business/risk language with SQL or documentation signals."

    if sql_score >= 2 and rag_score == 0 and hybrid_score == 0:
        return "sql", 0.85, "Question has strong metric or warehouse signals."

    if rag_score >= 2 and sql_score == 0 and hybrid_score == 0:
        return "rag", 0.85, "Question has strong methodology or documentation signals."

    return None, 0.0, "Rule confidence is low; LLM router is needed."


def normalize_route(value: str) -> Route:
    route = value.strip().lower()
    if route in {"sql", "rag", "hybrid", "unsupported"}:
        return route  # type: ignore[return-value]
    return "unsupported"


def classify_with_llm(question: str, model: str = DEFAULT_MODEL) -> tuple[Route, float, str]:
    load_environment()
    llm = ChatOpenAI(model=model, temperature=0)
    response = llm.invoke(
        [
            SystemMessage(content=ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=f"Question: {question}"),
        ]
    )
    route = normalize_route(str(response.content))
    return route, 0.7, "LLM router selected the route for an ambiguous question."


def classify_question(question: str, model: str = DEFAULT_MODEL) -> tuple[Route, RouteSource, float, str]:
    route, confidence, reason = classify_with_rules(question)
    if route is not None and confidence >= 0.8:
        return route, "rules", confidence, reason

    try:
        llm_route, llm_confidence, llm_reason = classify_with_llm(question, model=model)
        return llm_route, "llm", llm_confidence, llm_reason
    except Exception as exc:
        return (
            "unsupported",
            "fallback",
            0.0,
            f"LLM router failed, so the question was marked unsupported: {exc}",
        )


def router_node(state: AgenticRagState) -> AgenticRagState:
    route, source, confidence, reason = classify_question(state["question"])
    return {
        **state,
        "route": route,
        "route_source": source,
        "route_confidence": confidence,
        "route_reason": reason,
    }


def rag_node(state: AgenticRagState) -> AgenticRagState:
    chunks = build_chunks()
    matches = retrieve_chunks(state["question"], chunks, top_k=5)
    docs_context = format_context(matches)
    sources = [
        {
            "source": chunk.source,
            "heading": chunk.heading,
            "score": round(score, 3),
            "preview": chunk.text[:300].strip(),
        }
        for chunk, score in matches
    ]

    return {
        **state,
        "docs_context": docs_context,
        "sources": sources,
    }


def sql_node(state: AgenticRagState) -> AgenticRagState:
    try:
        agent_executor = create_hotel_sql_agent(return_intermediate_steps=True)
        response = ask(agent_executor, state["question"])
        return {
            **state,
            "sql_answer": response["output"],
            "sql_queries": extract_sql_queries(response),
            "sql_error": "",
        }
    except Exception as exc:
        return {
            **state,
            "sql_answer": "",
            "sql_queries": [],
            "sql_error": str(exc),
        }


def format_sources_for_prompt(sources: list[dict]) -> str:
    if not sources:
        return "No documentation sources were retrieved."

    lines = []
    for index, source in enumerate(sources, start=1):
        lines.append(
            f"[{index}] {source['source']} | {source['heading']} | "
            f"score={source['score']}"
        )
    return "\n".join(lines)


def build_rule_based_final_answer(state: AgenticRagState) -> str:
    if state["route"] == "unsupported":
        return (
            "I cannot answer this from the current hotel booking project. "
            "The available evidence sources are the project documentation and "
            "the PostgreSQL hotel warehouse."
        )

    if state["sql_error"] and not state["docs_context"]:
        return (
            "I routed this to the SQL warehouse because it needs live metrics, "
            f"but the SQL step failed: {state['sql_error']}"
        )

    if state["docs_context"] and state["sql_error"]:
        source_names = ", ".join(
            f"{source['source']} > {source['heading']}"
            for source in state["sources"][:3]
        )
        evidence_preview = "\n\n".join(
            f"- {source['source']} > {source['heading']}: {source['preview']}"
            for source in state["sources"][:2]
        )
        return (
            "I found relevant project documentation, but the SQL warehouse step "
            f"failed: {state['sql_error']}\n\n"
            f"Retrieved sources: {source_names}\n\n"
            f"Evidence preview:\n{evidence_preview}"
        )

    if state["docs_context"]:
        source_names = ", ".join(
            f"{source['source']} > {source['heading']}"
            for source in state["sources"][:3]
        )
        evidence_preview = "\n\n".join(
            f"- {source['source']} > {source['heading']}: {source['preview']}"
            for source in state["sources"][:3]
        )
        return (
            f"I retrieved relevant documentation sources for this question: {source_names}\n\n"
            f"Evidence preview:\n{evidence_preview}"
        )

    return "I could not gather enough evidence to answer this question."


def synthesis_node(state: AgenticRagState) -> AgenticRagState:
    if state["route"] == "unsupported" or state["sql_error"]:
        return {
            **state,
            "final_answer": build_rule_based_final_answer(state),
            "answer_error": "",
        }

    try:
        load_environment()
        llm = ChatOpenAI(model=DEFAULT_MODEL, temperature=0)
        response = llm.invoke(
            [
                SystemMessage(content=SYNTHESIS_SYSTEM_PROMPT),
                HumanMessage(
                    content=(
                        f"User question:\n{state['question']}\n\n"
                        f"Selected route: {state['route']}\n\n"
                        f"Documentation sources:\n{format_sources_for_prompt(state['sources'])}\n\n"
                        f"Documentation context:\n{state['docs_context'] or 'No documentation context.'}\n\n"
                        f"SQL answer:\n{state['sql_answer'] or 'No SQL answer.'}\n\n"
                        f"SQL queries:\n{state['sql_queries'] or 'No SQL queries.'}\n\n"
                        "Write the final answer."
                    )
                ),
            ]
        )
        return {
            **state,
            "final_answer": str(response.content),
            "answer_error": "",
        }
    except Exception as exc:
        return {
            **state,
            "final_answer": build_rule_based_final_answer(state),
            "answer_error": str(exc),
        }


def route_after_router(state: AgenticRagState) -> str:
    if state["route"] in {"rag", "hybrid"}:
        return "rag"
    if state["route"] == "sql":
        return "sql"
    return "synthesis"


def route_after_rag(state: AgenticRagState) -> str:
    if state["route"] == "hybrid":
        return "sql"
    return "synthesis"


def build_router_graph():
    graph = StateGraph(AgenticRagState)
    graph.add_node("router", router_node)
    graph.add_node("rag", rag_node)
    graph.add_node("sql", sql_node)
    graph.add_node("synthesis", synthesis_node)
    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "rag": "rag",
            "sql": "sql",
            "synthesis": "synthesis",
        },
    )
    graph.add_conditional_edges(
        "rag",
        route_after_rag,
        {
            "sql": "sql",
            "synthesis": "synthesis",
        },
    )
    graph.add_edge("sql", "synthesis")
    graph.add_edge("synthesis", END)
    return graph.compile()


def run_agentic_rag_router(question: str) -> AgenticRagState:
    state: AgenticRagState = {
        "question": question,
        "route": "unsupported",
        "route_source": "fallback",
        "route_confidence": 0.0,
        "route_reason": "",
        "docs_context": "",
        "sources": [],
        "sql_answer": "",
        "sql_queries": [],
        "sql_error": "",
        "final_answer": "",
        "answer_error": "",
    }
    graph = build_router_graph()
    return graph.invoke(state)


def run_agentic_rag(question: str) -> AgenticRagState:
    return run_agentic_rag_router(question)


def main():
    demo_questions = [
        "Which hotel has the highest cancellation rate?",
        "What cleaning steps were applied in the Silver layer?",
        "Why was Random Forest selected as the final model?",
        "Why is Online TA risky and how much revenue is exposed?",
        "What should management focus on to reduce cancellations?",
        "Can you forecast next year revenue?",
        "Who is the CEO of OpenAI?",
    ]

    for demo_question in demo_questions:
        result = run_agentic_rag_router(demo_question)
        print(
            f"{demo_question} -> {result['route']} "
            f"({result['route_source']}, confidence={result['route_confidence']:.2f})"
        )
        for source in result["sources"]:
            print(
                f"  - {source['source']} | {source['heading']} "
                f"(score={source['score']})"
            )
        if result["sql_answer"]:
            print(f"  SQL answer: {result['sql_answer']}")
        for query in result["sql_queries"]:
            print(f"  SQL query: {query}")
        if result["sql_error"]:
            print(f"  SQL error: {result['sql_error']}")
        if result["final_answer"]:
            print(f"  Final answer: {result['final_answer']}")
        if result["answer_error"]:
            print(f"  Answer error: {result['answer_error']}")

if __name__ == "__main__":
    main()
