"""Splits a generated Hinglish answer into atomic, independently-checkable claims."""

import re

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
