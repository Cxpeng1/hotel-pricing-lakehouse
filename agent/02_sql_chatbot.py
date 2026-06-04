"""
Interactive terminal chatbot for the hotel booking warehouse.

Run examples:
    python agent/02_sql_chatbot.py
    python agent/02_sql_chatbot.py --sample
    python agent/02_sql_chatbot.py --question "Which hotel has the highest cancellation rate?"
"""

from __future__ import annotations

import argparse

from sql_agent_core import (
    DEFAULT_MODEL,
    SAMPLE_QUESTIONS,
    ask,
    create_hotel_sql_agent,
    load_environment,
)


def run_interactive_chat(agent_executor) -> None:
    print("\nHotel Booking SQL Chatbot")
    print("Ask a question about bookings, revenue, cancellations, or predictions.")
    print("Type 'exit', 'quit', or 'q' to stop.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in {"exit", "quit", "q"}:
            print("Goodbye.")
            break
        if not question:
            continue

        try:
            response = ask(agent_executor, question)
        except Exception as exc:
            print(f"Agent error: {exc}")
            continue

        print(f"\nAgent: {response['output']}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chat with the hotel booking PostgreSQL warehouse using LangChain."
    )
    parser.add_argument("--question", help="Ask one question and exit.")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Run a small set of sample business questions and exit.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAI chat model to use. Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show LangChain agent reasoning/tool logs in the terminal.",
    )
    return parser.parse_args()


def main() -> None:
    load_environment()
    args = parse_args()
    agent_executor = create_hotel_sql_agent(model=args.model, verbose=args.verbose)

    if args.question:
        print(ask(agent_executor, args.question)["output"])
        return

    if args.sample:
        for question in SAMPLE_QUESTIONS:
            print("\n" + "=" * 80)
            print(f"Question: {question}")
            print(f"Answer: {ask(agent_executor, question)['output']}")
        return

    run_interactive_chat(agent_executor)


if __name__ == "__main__":
    main()
