"""Generates a Hinglish RAG answer from retrieved passages using Claude."""

import anthropic

from .settings import ANTHROPIC_API_KEY, GENERATOR_MODEL

_client = None


def get_client():
    """Returns the shared Anthropic client. Single-key -- Claude's paid API doesn't have
    Groq's free-tier daily-quota problem, so the multi-key failover ADR-016 added for Groq
    isn't needed here (see ADR-021)."""
    global _client
    if _client is None:
        # max_retries raised above the SDK default (2) -- a long batch run over hundreds of
        # calls is more likely to transiently hit a 429/5xx than a single interactive request.
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, max_retries=6)
    return _client


SYSTEM_PROMPT = """You are a helpful assistant answering questions about Indian government schemes.
Answer naturally in Hinglish (mixed Hindi-English, written in Roman script), the way people actually text.
Only use facts from the given context. Do not add details that are not present in it.
If the context does not answer the question, say so plainly instead of guessing."""


def generate_answer(question, passages):
    context = "\n\n".join(f"[{p['source']}]\n{p['text']}" for p in passages)
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer in Hinglish:"

    client = get_client()
    response = client.messages.create(
        model=GENERATOR_MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return next(b.text for b in response.content if b.type == "text").strip()
