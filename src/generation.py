"""Generates a Hinglish RAG answer from retrieved passages using Groq."""

from groq import Groq

from config.settings import GENERATOR_MODEL, GROQ_API_KEYS

_clients = None


def get_client():
    """Returns the first configured client, for callers that only need one."""
    return get_clients()[0]


def get_clients():
    """Returns one Groq client per configured API key (GROQ_API_KEY, GROQ_API_KEY_2, ...),
    so a long batch run can fail over to another key's quota instead of waiting out one
    key's daily limit -- see judge()'s retry loop in src/verification.py."""
    global _clients
    if _clients is None:
        _clients = [Groq(api_key=key) for key in GROQ_API_KEYS]
    return _clients


SYSTEM_PROMPT = """You are a helpful assistant answering questions about Indian government schemes.
Answer naturally in Hinglish (mixed Hindi-English, written in Roman script), the way people actually text.
Only use facts from the given context. Do not add details that are not present in it.
If the context does not answer the question, say so plainly instead of guessing."""


def generate_answer(question, passages):
    context = "\n\n".join(f"[{p['source']}]\n{p['text']}" for p in passages)
    user_prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer in Hinglish:"

    client = get_client()
    response = client.chat.completions.create(
        model=GENERATOR_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()
