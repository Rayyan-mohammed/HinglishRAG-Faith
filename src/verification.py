"""Per-claim retrieval + LLM-as-judge verification against evidence."""

import json
import time

from groq import RateLimitError

from config.settings import VERIFIER_MODEL
from src.generation import get_clients
from src.retrieval import retrieve

VERDICT_PROMPT = """You are a strict fact-checker. Given a CLAIM and an EVIDENCE passage, decide if the
evidence supports the claim.

Respond with a JSON object only, in this exact format:
{{"verdict": "SUPPORTED" | "CONTRADICTED" | "UNVERIFIABLE", "confidence": 0.0-1.0}}

- SUPPORTED: the evidence confirms the claim.
- CONTRADICTED: the evidence conflicts with the claim.
- UNVERIFIABLE: the evidence does not mention this at all.

Special case — the claim is itself a statement ABOUT what the evidence does or doesn't say
(e.g. "the context doesn't mention X", "there is no information about Y", "iska koi jankari
nahi hai"):
- If the evidence genuinely never discusses that topic, the claim is an accurate description
  of that silence — mark it SUPPORTED, not UNVERIFIABLE.
- If the evidence actually does discuss that topic, the claim is factually wrong to say it's
  absent — mark it CONTRADICTED.
- Do not default this claim type to UNVERIFIABLE — decide based on whether the topic the claim
  says is missing genuinely appears in the evidence or not.

CLAIM: {claim}

EVIDENCE: {evidence}
"""


_last_good_client = 0  # remembers which key last worked, so we don't re-try exhausted ones first


def judge(claim, evidence_text, max_retries=5):
    """Core LLM-as-judge call: a claim against a block of evidence text.
    No retrieval involved — usable directly on hand-written claim/evidence pairs.

    On a rate limit, first fails over to any other configured API key (GROQ_API_KEY_2, ...)
    before waiting at all -- a key hitting its daily quota (P-001) doesn't mean another key
    is out too. Only sleeps with exponential backoff once every configured key has been
    tried and failed in the same round (all keys share Groq's short-term tokens-per-minute
    limit even when their daily budgets differ)."""
    global _last_good_client
    clients = get_clients()
    if not clients:
        raise RuntimeError("No GROQ_API_KEY configured — check .env")
    response = None

    for attempt in range(max_retries):
        last_error = None
        for offset in range(len(clients)):
            client_idx = (_last_good_client + offset) % len(clients)
            try:
                response = clients[client_idx].chat.completions.create(
                    model=VERIFIER_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": VERDICT_PROMPT.format(claim=claim, evidence=evidence_text),
                        }
                    ],
                    temperature=0,
                )
                _last_good_client = client_idx
                break
            except RateLimitError as e:
                last_error = e
        if response is not None:
            break
        if attempt == max_retries - 1:
            raise last_error
        time.sleep(2**attempt)

    raw = response.choices[0].message.content.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"verdict": "UNVERIFIABLE", "confidence": 0.0}

    result["claim"] = claim
    return result


def verify_claim(claim, index, passages, top_k=2):
    evidence_passages = retrieve(claim, index, passages, top_k=top_k)
    evidence_text = "\n\n".join(p["text"] for p in evidence_passages)

    result = judge(claim, evidence_text)
    result["evidence"] = evidence_passages
    return result
