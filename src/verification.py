"""Per-claim retrieval + LLM-as-judge verification against evidence."""

import json

from src.config import VERIFIER_MODEL
from src.generation import get_client
from src.retrieval import retrieve

VERDICT_PROMPT = """You are a strict fact-checker. Given a CLAIM and an EVIDENCE passage, decide if the
evidence supports the claim.

Respond with a JSON object only, in this exact format:
{{"verdict": "SUPPORTED" | "CONTRADICTED" | "UNVERIFIABLE", "confidence": 0.0-1.0}}

- SUPPORTED: the evidence confirms the claim.
- CONTRADICTED: the evidence conflicts with the claim.
- UNVERIFIABLE: the evidence does not mention this at all.

CLAIM: {claim}

EVIDENCE: {evidence}
"""


def verify_claim(claim, index, passages, top_k=2):
    evidence_passages = retrieve(claim, index, passages, top_k=top_k)
    evidence_text = "\n\n".join(p["text"] for p in evidence_passages)

    client = get_client()
    response = client.chat.completions.create(
        model=VERIFIER_MODEL,
        messages=[
            {"role": "user", "content": VERDICT_PROMPT.format(claim=claim, evidence=evidence_text)}
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"verdict": "UNVERIFIABLE", "confidence": 0.0}

    result["claim"] = claim
    result["evidence"] = evidence_passages
    return result
