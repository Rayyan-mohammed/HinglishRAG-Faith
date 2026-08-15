"""Generates a Hinglish RAG answer from retrieved passages using Groq."""

from groq import Groq

from config.settings import GENERATOR_MODEL, GROQ_API_KEY

_client = None


def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


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
