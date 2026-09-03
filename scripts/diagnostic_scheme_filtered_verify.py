"""EVAL-ONLY DIAGNOSTIC -- not part of the real pipeline. Re-runs verification with retrieval
restricted to the question's known-correct scheme (from eval/questions.csv), to isolate how
much of the current recall/precision gap is caused by wrong-scheme retrieval versus everything
else (decomposition, the verifier prompt, genuine judge misjudgment).

This does NOT get wired into src/retrieval.py or the demo -- a real user's question doesn't
arrive pre-labeled with which scheme it's about, so filtering retrieval this way would make the
pipeline unrepresentative of actual deployment. See ADR-015 in docs/problems_and_decisions.md
for why this stays a diagnostic, not a shipped feature.

Writes results/verifier_results_scheme_filtered.csv (separate file -- does not touch the real
results/verifier_results.csv)."""

import csv
import sys
import time
from pathlib import Path

import numpy as np

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.decomposition import decompose
from src.retrieval import get_embedder, load_index
from src.verification import judge

GENERATED_ANSWERS = "results/generated_answers.csv"
QUESTIONS = "eval/questions.csv"
OUTPUT = "results/verifier_results_scheme_filtered.csv"
TOP_K = 2
FIELDS = ["question_id", "claim", "verdict", "confidence", "evidence_source", "evidence_text"]


def load_scheme_by_qid():
    with open(QUESTIONS, encoding="utf-8") as f:
        return {r["id"]: r["scheme"] for r in csv.DictReader(f)}


def load_generated_answers():
    with open(GENERATED_ANSWERS, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r["pipeline"] == "plain"]


def load_done_pairs():
    if not Path(OUTPUT).exists():
        return set()
    with open(OUTPUT, encoding="utf-8") as f:
        return {(r["question_id"], r["claim"]) for r in csv.DictReader(f)}


def build_per_scheme_embeddings(passages):
    """Pre-embeds each scheme's passages once, so per-claim retrieval below is just a dot
    product against a small (<=60-row) matrix -- no FAISS needed at this scale."""
    embedder = get_embedder()
    by_scheme = {}
    for p in passages:
        by_scheme.setdefault(p["source"], []).append(p)

    embedded = {}
    for scheme, scheme_passages in by_scheme.items():
        vecs = embedder.encode([p["text"] for p in scheme_passages], normalize_embeddings=True)
        embedded[scheme] = (scheme_passages, np.array(vecs, dtype="float32"))
    return embedded


def retrieve_scheme_filtered(query, scheme, embedded, top_k=TOP_K):
    if scheme not in embedded:
        return []
    scheme_passages, vecs = embedded[scheme]
    embedder = get_embedder()
    query_vec = np.array(embedder.encode([query], normalize_embeddings=True)[0], dtype="float32")
    scores = vecs @ query_vec
    top_idx = np.argsort(-scores)[:top_k]
    return [
        {**scheme_passages[i], "score": float(scores[i])} for i in top_idx
    ]


def main():
    _, passages = load_index()
    scheme_by_qid = load_scheme_by_qid()
    answers = load_generated_answers()
    done = load_done_pairs()

    print("Pre-embedding each scheme's passages...")
    embedded = build_per_scheme_embeddings(passages)

    write_header = not Path(OUTPUT).exists()
    with open(OUTPUT, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if write_header:
            writer.writeheader()

        total, new = 0, 0
        for row in answers:
            qid = row["question_id"]
            scheme = scheme_by_qid[qid]
            for claim in decompose(row["answer"]):
                total += 1
                if (qid, claim) in done:
                    continue
                evidence = retrieve_scheme_filtered(claim, scheme, embedded)
                evidence_text = "\n---\n".join(f"[{p['source']}] {p['text']}" for p in evidence)
                result = judge(claim, evidence_text)
                writer.writerow(
                    {
                        "question_id": qid,
                        "claim": claim,
                        "verdict": result.get("verdict", "UNVERIFIABLE"),
                        "confidence": result.get("confidence", 0.0),
                        "evidence_source": evidence[0]["source"] if evidence else "",
                        "evidence_text": evidence_text,
                    }
                )
                f.flush()
                new += 1
                print(f"q{qid}: {result.get('verdict')} ({result.get('confidence')}) -- {claim[:70]}")
                time.sleep(0.3)

    print(f"\n{new} new claims verified, {total - new} already done, {total} total")


if __name__ == "__main__":
    main()
