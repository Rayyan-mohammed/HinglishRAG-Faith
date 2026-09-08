"""Per-claim retrieval + LLM-as-judge verification against evidence."""

import json
from collections import Counter

from .settings import VERIFIER_MODEL
from .generation import get_client
from .retrieval import retrieve

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
- First check: does the evidence appear to be about the same scheme/subject as the claim at
  all, or does it read as being about a completely different scheme, topic, or context? If the
  evidence looks like it was retrieved for the wrong subject entirely (not just silent on this
  one detail, but about something else altogether), that means retrieval likely failed to find
  the right passage — mark UNVERIFIABLE. Do not treat unrelated evidence as proof the claim's
  topic is genuinely absent from the source as a whole.
- Only if the evidence is clearly about the same scheme/subject as the claim: if it genuinely
  never discusses the specific topic the claim asks about, the claim is an accurate description
  of that silence — mark it SUPPORTED, not UNVERIFIABLE. If it actually does discuss that topic,
  the claim is factually wrong to say it's absent — mark it CONTRADICTED.
- Do not default this claim type to UNVERIFIABLE out of general caution — only use UNVERIFIABLE
  here for the wrong-subject-evidence case above, or when the evidence is genuinely ambiguous.

CLAIM: {claim}

EVIDENCE: {evidence}
"""


def _extract_json(raw):
    """Claude often wraps JSON in a markdown code fence and adds explanatory prose after it,
    despite being told to respond with JSON only -- find the first JSON value in the text and
    parse just that, ignoring a fence and any trailing commentary around it. Raises
    json.JSONDecodeError (same as a plain json.loads failure) if no JSON value is found."""
    decoder = json.JSONDecoder()
    for i, ch in enumerate(raw):
        if ch in "{[":
            try:
                obj, _ = decoder.raw_decode(raw, i)
                return obj
            except json.JSONDecodeError:
                continue
    raise json.JSONDecodeError("No JSON value found in response", raw, 0)


def judge(claim, evidence_text):
    """Core LLM-as-judge call: a claim against a block of evidence text.
    No retrieval involved — usable directly on hand-written claim/evidence pairs.

    Switched from Groq to Claude in ADR-021. No manual retry/failover loop needed here --
    Claude's paid API doesn't have Groq's free-tier daily-quota problem that made ADR-016's
    multi-key failover necessary; the Anthropic client already retries 429/5xx with backoff
    (see get_client() in src/generation.py)."""
    client = get_client()
    response = client.messages.create(
        model=VERIFIER_MODEL,
        max_tokens=256,
        messages=[
            {"role": "user", "content": VERDICT_PROMPT.format(claim=claim, evidence=evidence_text)}
        ],
    )
    raw = next(b.text for b in response.content if b.type == "text")
    try:
        result = _extract_json(raw)
    except json.JSONDecodeError:
        result = {"verdict": "UNVERIFIABLE", "confidence": 0.0}

    result["claim"] = claim
    return result


def verify_claim(claim, index, passages, top_k=2, n_samples=3, context_passages=None):
    """Judges a claim against evidence by majority vote over n_samples independent judge() calls.

    If context_passages is given -- the passages that were actually retrieved and handed to the
    generator to produce the answer this claim came from -- those are merged with a fresh
    per-claim retrieval into one evidence pool (deduplicated), rather than either alone.
    Context-only was tried first (ADR-021) on the theory that checking faithfulness to what the
    generator actually saw would avoid the wrong-scheme evidence a short, scheme-ambiguous claim
    often pulls in on its own -- and it worked for that (false-alarm rate improved). But it also
    tied verification's blind spots to generation's: if the question-level retrieval that
    produced the answer missed a fact (e.g. a specific exclusion clause) that exists elsewhere in
    the corpus, verification saw exactly the same gap and confirmed a false "the context doesn't
    say this" claim as SUPPORTED -- confirmed directly by inspecting evidence_text for several of
    the resulting false negatives. Merging in a fresh per-claim lookup gives the judge a second,
    independent chance to find that fact without giving up the wrong-scheme protection
    context_passages provides on their own. Falls back to fresh retrieve() only when
    context_passages isn't supplied at all, e.g. calling verify_claim() standalone without a
    generation step.

    Also judges by majority vote over n_samples independent judge() calls -- added after ADR-019
    found the judge is not fully deterministic even at temperature=0: re-running the full pipeline
    with byte-identical evidence text still flipped some verdicts. Majority voting trades
    n_samples-x API cost for a verdict that doesn't depend on a single unlucky sample. On a full
    split (no verdict wins more than half the votes), falls back to UNVERIFIABLE as the
    conservative default rather than picking arbitrarily."""
    if context_passages is not None:
        extra_passages = retrieve(claim, index, passages, top_k=top_k)
        seen = set()
        evidence_passages = []
        for p in list(context_passages) + extra_passages:
            key = (p["source"], p["text"])
            if key not in seen:
                seen.add(key)
                evidence_passages.append(p)
    else:
        evidence_passages = retrieve(claim, index, passages, top_k=top_k)
    evidence_text = "\n\n".join(p["text"] for p in evidence_passages)

    samples = [judge(claim, evidence_text) for _ in range(n_samples)]
    votes = Counter(s["verdict"] for s in samples)
    winning_verdict, winning_count = votes.most_common(1)[0]
    if winning_count * 2 <= n_samples:
        winning_verdict = "UNVERIFIABLE"
    agreeing = [s for s in samples if s["verdict"] == winning_verdict]

    result = {
        "claim": claim,
        "verdict": winning_verdict,
        "confidence": sum(s["confidence"] for s in agreeing) / len(agreeing) if agreeing else 0.0,
        "evidence": evidence_passages,
    }
    return result
