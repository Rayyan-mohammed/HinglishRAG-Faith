"""Splits a generated Hinglish answer into atomic, independently-checkable claims."""

import json
import re

from .settings import DECOMPOSER_MODEL
from .generation import get_client

CONNECTORS = [
    "aur", "lekin", "but", "however", "also", "and", "kyunki", "because",
    "isliye", "so that", "jabki", "whereas",
]

_connector_pattern = re.compile(
    r"\b(" + "|".join(re.escape(c) for c in CONNECTORS) + r")\b",
    re.IGNORECASE,
)


def split_sentences(text):
    # Negative lookbehind for "Rs." keeps rupee amounts (e.g. "Rs. 6.00 lakhs") from being
    # mistaken for a sentence boundary — see P-002 in docs/problems_and_decisions.md.
    return [s.strip() for s in re.split(r"(?<!Rs\.)(?<=[.!?])\s+", text) if s.strip()]


def split_on_connectors(sentence):
    parts = _connector_pattern.split(sentence)
    claims = []
    current = ""
    for part in parts:
        if _connector_pattern.fullmatch(part or ""):
            if current.strip():
                claims.append(current.strip())
            current = ""
        else:
            current += part
    if current.strip():
        claims.append(current.strip())
    return claims


MIN_CLAIM_WORDS = 3


def decompose(answer):
    claims = []
    for sentence in split_sentences(answer):
        claims.extend(split_on_connectors(sentence))
    stripped = (c.strip(" ,.") for c in claims)
    # Drop degenerate fragments (bare entities like "EWS", "Assam, Meghalaya") that
    # decomposition sometimes produces — they aren't checkable claims at all, and get
    # verified as if they were, inflating false positives. See P-008's diagnosis in
    # docs/problems_and_decisions.md. Threshold of 3 is deliberately conservative: it was
    # checked against real 1-2 word fragments (dropped) and real short claims like "Bank
    # account details" (3 words, kept) to avoid losing legitimate short claims. It does not
    # catch every damaged fragment (e.g. a claim that lost its antecedent across an "aur"
    # split but is still 4+ words) — that's a harder, unsolved case, not this fix's job.
    return [c for c in stripped if c and len(c.split()) >= MIN_CLAIM_WORDS]


DECOMPOSITION_PROMPT = """You are decomposing a Hinglish (Hindi-English code-switched) answer into
atomic, independently fact-checkable claims.

Rules:
- Each claim must be a complete, self-contained statement that can be checked true or false on
  its own, without needing the rest of the answer for context. Resolve pronouns/references (e.g.
  "isme", "yeh") using the surrounding text so each claim stands alone.
- Split compound sentences into separate claims ONLY when they express independently checkable
  facts. Never split a claim in a way that changes its meaning. In particular, an exclusivity
  qualifier ("sirf"/"only") that scopes over a LIST of items -- e.g. "sirf X aur Y ke liye hai"
  (only for X and Y, together) -- must stay as ONE claim covering the whole list. Do NOT split it
  into "sirf X" + "sirf Y" as two separate claims -- "only X and Y together" is a different,
  stronger statement than "only X" and "only Y" each individually, and splitting it that way can
  turn one true claim into two false-looking fragments, or vice versa.
- Do not bundle two independently checkable facts into one claim -- e.g. a specific number and a
  separate generalization about it ("Rs 6000 milte hain, aur yeh sabhi states mein same hai") must
  become two claims, not one, so each can be checked on its own.
- Do not produce fragments with no checkable content on their own (bare entity names, lone
  place-name lists, connector words). Every claim must have a subject and a predicate.
- Claims that state an absence of information (e.g. "context mein iske baare mein kuchh nahi kaha
  gaya hai", "iska koi jankari nahi hai") ARE valid, checkable claims -- keep them as their own
  claim, do not drop them.
- Preserve the original Hinglish wording as much as possible; do not translate or paraphrase
  beyond what's needed to make a claim self-contained.
- Skip pure filler with no factual content (greetings, apologies, "yeh raha aapka jawab").

Respond with a JSON array of strings only, one string per claim, in the order they appear. No
other text.

ANSWER: {answer}
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


def decompose_llm(answer):
    """LLM-based claim decomposition -- the pipeline's actual decomposition step, replacing
    decompose() (still kept, still tested, for its determinism and zero API cost).

    Added because the regex splitter above is the direct, named cause of several open bugs found
    during error analysis: dropping the "sirf X aur Y" qualifier when a compound sentence splits
    on "aur" (Q51), bundling a verifiable number together with an unverifiable generalization into
    one claim so the judge never separately scrutinizes the generalization (Q10), and producing
    degenerate bare-entity fragments that MIN_CLAIM_WORDS then has to filter back out. An LLM can
    resolve these directly from context instead of pattern-matching around each case one at a
    time.

    Switched from Groq to Claude in ADR-021 -- no manual retry/failover loop needed, the
    Anthropic client already retries 429/5xx with backoff (see get_client() in
    src/generation.py). Falls back to decompose() if the response isn't valid JSON, isn't a
    list, or comes back empty -- a malformed response degrades to the old, safe, deterministic
    behavior rather than losing an answer's claims entirely."""
    if not answer or not answer.strip():
        return []

    client = get_client()
    response = client.messages.create(
        model=DECOMPOSER_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": DECOMPOSITION_PROMPT.format(answer=answer)}],
    )
    raw = next(b.text for b in response.content if b.type == "text")
    try:
        claims = _extract_json(raw)
    except json.JSONDecodeError:
        return decompose(answer)

    if not isinstance(claims, list):
        return decompose(answer)

    cleaned = [c.strip() for c in claims if isinstance(c, str) and c.strip()]
    return cleaned if cleaned else decompose(answer)
