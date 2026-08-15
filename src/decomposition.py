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
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


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


def decompose(answer):
    claims = []
    for sentence in split_sentences(answer):
        claims.extend(split_on_connectors(sentence))
    return [c.strip(" ,.") for c in claims if c.strip(" ,.")]
