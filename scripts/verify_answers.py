"""Runs the verification layer (decompose -> per-claim retrieval -> LLM-judge) over every
plain-pipeline answer in results/generated_answers.csv, saving per-claim verdicts to
results/verifier_results.csv.

Resumable: re-running skips (question_id, claim) pairs already in the output file, and each
result is flushed to disk immediately, since Groq's free-tier daily token limit can interrupt a
full run partway through (see P-001 in docs/problems_and_decisions.md)."""

import csv
import os
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.decomposition import decompose
from src.retrieval import load_index
from src.verification import verify_claim

GENERATED_ANSWERS = "results/generated_answers.csv"
OUTPUT = "results/verifier_results.csv"
FIELDS = ["question_id", "claim", "verdict", "confidence", "evidence_source"]


def load_generated_answers():
    with open(GENERATED_ANSWERS, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r["pipeline"] == "plain"]


def load_done_pairs():
    if not os.path.exists(OUTPUT):
        return set()
    with open(OUTPUT, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {(r["question_id"], r["claim"]) for r in rows}


def main():
    index, passages = load_index()
    answers = load_generated_answers()
    done = load_done_pairs()

    write_header = not os.path.exists(OUTPUT)
    with open(OUTPUT, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if write_header:
            writer.writeheader()

        total_claims = 0
        new_claims = 0
        for row in answers:
            qid = row["question_id"]
            claims = decompose(row["answer"])
            for claim in claims:
                total_claims += 1
                if (qid, claim) in done:
                    continue
                result = verify_claim(claim, index, passages, top_k=2)
                evidence_source = result["evidence"][0]["source"] if result["evidence"] else ""
                writer.writerow(
                    {
                        "question_id": qid,
                        "claim": claim,
                        "verdict": result.get("verdict", "UNVERIFIABLE"),
                        "confidence": result.get("confidence", 0.0),
                        "evidence_source": evidence_source,
                    }
                )
                f.flush()
                new_claims += 1
                print(f"q{qid}: {result.get('verdict')} ({result.get('confidence')}) -- {claim[:70]}")
                time.sleep(0.3)

    print(f"\n{new_claims} new claims verified, {total_claims - new_claims} already done, {total_claims} total")


if __name__ == "__main__":
    main()
