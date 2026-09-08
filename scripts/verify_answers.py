"""Runs the verification layer (decompose -> per-claim retrieval -> LLM-judge) over every
plain-pipeline answer in results/generated_answers.csv, saving per-claim verdicts to
results/verifier_results.csv.

Resumable: re-running skips (question_id, claim) pairs already in the output file, and each
result is flushed to disk immediately -- originally to survive Groq's free-tier daily token
limit interrupting a run partway through (P-001), kept after the ADR-021 switch to Claude since
any batch job over hundreds of calls can still be interrupted for other reasons (network, a
crash, low local RAM loading the embedding model).

Logs the full evidence text (all top_k retrieved passages, not just the top one's source) --
added after error analysis found 12 false positives with no identifiable cause, only diagnosable
if the actual evidence the judge saw is available after the fact (see P-006's second correction
in docs/problems_and_decisions.md).

Uses decompose_llm() (not the regex decompose()) and reconstructs each question's context_passages
via a fresh question-level retrieve() call, matching what the live pipeline (src/pipeline.py) now
does after the context-reuse fix -- see ADR-021 in docs/problems_and_decisions.md. Retrieval is a
pure function of the question text and the current index, so this reproduces the same passages the
real pipeline would use, even though generated_answers.csv itself doesn't store them."""

import csv
import os
import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config.settings import TOP_K
from src.decomposition import decompose_llm
from src.retrieval import load_index, retrieve
from src.verification import verify_claim

GENERATED_ANSWERS = "results/generated_answers.csv"
QUESTIONS = "eval/questions.csv"
OUTPUT = "results/verifier_results.csv"
FIELDS = [
    "question_id",
    "claim",
    "verdict",
    "confidence",
    "evidence_source",
    "evidence_sources",
    "evidence_text",
]


def load_generated_answers():
    with open(GENERATED_ANSWERS, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r["pipeline"] == "plain"]


def load_questions_by_id():
    with open(QUESTIONS, encoding="utf-8") as f:
        return {r["id"]: r["question"] for r in csv.DictReader(f)}


def load_done_pairs():
    if not os.path.exists(OUTPUT):
        return set()
    with open(OUTPUT, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {(r["question_id"], r["claim"]) for r in rows}


def main():
    index, passages = load_index()
    answers = load_generated_answers()
    questions_by_id = load_questions_by_id()
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
            question_text = questions_by_id[qid]
            context_passages = retrieve(question_text, index, passages, top_k=TOP_K)
            claims = decompose_llm(row["answer"])
            for claim in claims:
                total_claims += 1
                if (qid, claim) in done:
                    continue
                result = verify_claim(
                    claim, index, passages, context_passages=context_passages
                )
                evidence = result["evidence"]
                evidence_source = evidence[0]["source"] if evidence else ""
                evidence_sources = ",".join(p["source"] for p in evidence)
                evidence_text = "\n---\n".join(f"[{p['source']}] {p['text']}" for p in evidence)
                writer.writerow(
                    {
                        "question_id": qid,
                        "claim": claim,
                        "verdict": result.get("verdict", "UNVERIFIABLE"),
                        "confidence": result.get("confidence", 0.0),
                        "evidence_source": evidence_source,
                        "evidence_sources": evidence_sources,
                        "evidence_text": evidence_text,
                    }
                )
                f.flush()
                new_claims += 1
                # LLM-decomposed claims can contain unicode punctuation (e.g. narrow no-break
                # spaces) that crash Windows' default cp1252 console encoding -- encode
                # defensively so a print-only failure never loses an already-saved row.
                line = f"q{qid}: {result.get('verdict')} ({result.get('confidence')}) -- {claim[:70]}"
                print(line.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace"))
                time.sleep(0.3)

    print(f"\n{new_claims} new claims verified, {total_claims - new_claims} already done, {total_claims} total")


if __name__ == "__main__":
    main()
