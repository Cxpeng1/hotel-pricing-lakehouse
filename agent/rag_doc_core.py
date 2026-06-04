"""
Documentation RAG chatbot for the hotel pricing lakehouse project.

The retriever reads README.md and docs/*.md, ranks relevant text chunks with a
lightweight local similarity search, then asks the chat model to answer using
only the retrieved project context.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from sql_agent_core import DEFAULT_MODEL, load_environment


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOC_PATHS = [PROJECT_ROOT / "README.md", *sorted((PROJECT_ROOT / "docs").glob("*.md"))]

RAG_SUGGESTED_QUESTIONS = [
    "What cleaning steps were applied in the Silver layer?",
    "Why was Random Forest selected as the final model?",
    "What are the main business findings from the analysis?",
    "How does the Gold star schema support reporting?",
    "What are the limitations of this project?",
]

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "why",
    "with",
}

SYSTEM_PROMPT = """
You are a documentation assistant for the Hotel Pricing Lakehouse project.

Answer using only the provided project documentation context.
If the context does not contain enough information, say what is missing.
Be concise, business-focused, and specific.
When useful, mention the source document names.
"""


@dataclass(frozen=True)
class DocumentChunk:
    source: str
    heading: str
    text: str
    tokens: Counter[str]
    norm: float


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    return [word for word in words if word not in STOPWORDS and len(word) > 1]


def split_markdown(path: Path, chunk_size: int = 900, overlap: int = 150) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8")
    sections: list[tuple[str, str]] = []
    current_heading = path.name
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("#"):
            if current_lines:
                sections.extend(chunk_section(current_heading, "\n".join(current_lines), chunk_size, overlap))
                current_lines = []
            current_heading = line.lstrip("#").strip() or path.name
        else:
            current_lines.append(line)

    if current_lines:
        sections.extend(chunk_section(current_heading, "\n".join(current_lines), chunk_size, overlap))

    return sections


def chunk_section(
    heading: str,
    text: str,
    chunk_size: int,
    overlap: int,
) -> list[tuple[str, str]]:
    clean_text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not clean_text:
        return []

    if len(clean_text) <= chunk_size:
        return [(heading, clean_text)]

    chunks: list[tuple[str, str]] = []
    start = 0
    while start < len(clean_text):
        end = min(start + chunk_size, len(clean_text))
        chunk = clean_text[start:end].strip()
        if chunk:
            chunks.append((heading, chunk))
        if end == len(clean_text):
            break
        start = max(0, end - overlap)

    return chunks


def build_chunks() -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for path in DOC_PATHS:
        if not path.exists():
            continue
        for heading, text in split_markdown(path):
            tokens = Counter(tokenize(f"{heading}\n{text}"))
            norm = math.sqrt(sum(value * value for value in tokens.values()))
            if tokens and text.strip():
                chunks.append(
                    DocumentChunk(
                        source=str(path.relative_to(PROJECT_ROOT)),
                        heading=heading,
                        text=text,
                        tokens=tokens,
                        norm=norm,
                    )
                )
    return chunks


def score_chunk(query_tokens: Counter[str], query_norm: float, chunk: DocumentChunk) -> float:
    if query_norm == 0 or chunk.norm == 0:
        return 0.0
    dot_product = sum(weight * chunk.tokens.get(token, 0) for token, weight in query_tokens.items())
    return dot_product / (query_norm * chunk.norm)


def retrieve_chunks(question: str, chunks: list[DocumentChunk], top_k: int = 5) -> list[tuple[DocumentChunk, float]]:
    query_tokens = Counter(tokenize(question))
    query_norm = math.sqrt(sum(value * value for value in query_tokens.values()))

    ranked = [
        (chunk, score_chunk(query_tokens, query_norm, chunk))
        for chunk in chunks
    ]
    ranked = [item for item in ranked if item[1] > 0]
    ranked.sort(key=lambda item: item[1], reverse=True)
    return ranked[:top_k]


def format_context(matches: list[tuple[DocumentChunk, float]]) -> str:
    context_blocks = []
    for index, (chunk, score) in enumerate(matches, start=1):
        context_blocks.append(
            f"[Source {index}: {chunk.source} | {chunk.heading} | score={score:.3f}]\n"
            f"{chunk.text}"
        )
    return "\n\n---\n\n".join(context_blocks)


def answer_document_question(
    question: str,
    model: str = DEFAULT_MODEL,
    top_k: int = 5,
) -> dict:
    load_environment()
    chunks = build_chunks()
    matches = retrieve_chunks(question, chunks, top_k=top_k)

    if not chunks:
        return {
            "answer": "No Markdown documentation was found in README.md or docs/*.md.",
            "sources": [],
        }

    if not matches:
        return {
            "answer": "I could not find relevant documentation for that question in README.md or docs/*.md.",
            "sources": [],
        }

    context = format_context(matches)
    llm = ChatOpenAI(model=model, temperature=0)
    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"Project documentation context:\n{context}\n\n"
                    f"Question: {question}\n\n"
                    "Answer from the context above."
                )
            ),
        ]
    )

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
        "answer": response.content,
        "sources": sources,
    }
