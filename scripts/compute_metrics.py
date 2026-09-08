"""Computes precision/recall (claim-level) and answer-level catch rate (Section 13.2),
using results/verifier_results.csv (predictions), eval/claim_ground_truth.csv (claim-level
ground truth) and eval/labels.csv (answer-level ground truth). Writes results/metrics.md."""

import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.evaluate import answer_level_catch_rate, precision_recall

VERIFIER_RESULTS = "results/verifier_results.csv"
CLAIM_GROUND_TRUTH = "eval/claim_ground_truth.csv"
ANSWER_LABELS = "eval/labels.csv"
OUTPUT = "results/metrics.md"


def load_rows(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    verdicts = load_rows(VERIFIER_RESULTS)
    claim_truth = load_rows(CLAIM_GROUND_TRUTH)
    answer_labels = {r["question_id"]: r["label"] for r in load_rows(ANSWER_LABELS)}

    assert len(verdicts) == len(claim_truth), "verifier_results.csv and claim_ground_truth.csv must be row-aligned"

    predicted_flags = [v["verdict"] != "SUPPORTED" for v in verdicts]
    true_flags = [t["true_hallucinated"] == "True" for t in claim_truth]

    claim_metrics = precision_recall(predicted_flags, true_flags)

    # per-question aggregation for answer-level catch rate
    per_question = {}
    for v, t in zip(verdicts, claim_truth):
        qid = v["question_id"]
        per_question.setdefault(qid, []).append(
            {"flagged": v["verdict"] != "SUPPORTED", "true_hallucinated": t["true_hallucinated"] == "True"}
        )

    answers = []
    for qid, claims in per_question.items():
        has_hallucination = answer_labels.get(qid) != "fully_correct"
        correctly_flagged = any(c["flagged"] and c["true_hallucinated"] for c in claims)
        any_flag_raised = any(c["flagged"] for c in claims)
        has_any_true_hallucinated_claim = any(c["true_hallucinated"] for c in claims)
        answers.append(
            {
                "question_id": qid,
                "has_hallucination": has_hallucination,
                "flagged": correctly_flagged,
                "any_flag_raised": any_flag_raised,
                "has_any_true_hallucinated_claim": has_any_true_hallucinated_claim,
            }
        )

    catch_rate_strict = answer_level_catch_rate(
        [{"has_hallucination": a["has_hallucination"], "flagged": a["flagged"]} for a in answers]
    )
    catch_rate_loose = answer_level_catch_rate(
        [{"has_hallucination": a["has_hallucination"], "flagged": a["any_flag_raised"]} for a in answers]
    )

    # false-alarm rate on the 42 fully_correct answers: how often did the verifier flag
    # something anyway
    correct_answers = [a for a in answers if not a["has_hallucination"]]
    false_alarms = sum(1 for a in correct_answers if a["any_flag_raised"])

    n_total = len(verdicts)
    n_hallucinated = sum(true_flags)
    n_not = n_total - n_hallucinated

    n_not_fully_correct = sum(1 for a in answers if a["has_hallucination"])
    n_zero_false_claim_answers = sum(
        1
        for a in answers
        if a["has_hallucination"] and not a["has_any_true_hallucinated_claim"]
    )
    n_fully_correct = len(correct_answers)

    report = f"""# Verification Layer Results

Computed from `results/verifier_results.csv` ({n_total} claim verdicts) against two ground
truths: `eval/claim_ground_truth.csv` (claim-level, derived per ADR-014) and `eval/labels.csv`
(answer-level, ADR-012 — both are AI-drafted, pending human review).

## Claim-level precision/recall (Section 13.2, metrics 1-2)

| Metric | Value |
|---|---|
| Precision on flagged claims | {claim_metrics['precision']:.2f} |
| Recall on hallucinated claims | {claim_metrics['recall']:.2f} |
| True positives | {claim_metrics['tp']} |
| False positives | {claim_metrics['fp']} |
| False negatives | {claim_metrics['fn']} |

Of {n_total} total claims, {n_hallucinated} were ground-truth hallucinated (a false or
unsupported individual statement), {n_not} were not.

## Answer-level catch rate (Section 13.2, metric 3)

| Definition | Value |
|---|---|
| Strict — verifier flagged a claim that IS a true hallucination | {catch_rate_strict:.2f} |
| Loose — verifier flagged *any* claim in the answer, correct or not | {catch_rate_loose:.2f} |

{n_not_fully_correct} of {len(answers)} answers are ground-truth not-fully-correct (partially or
fully hallucinated, per `eval/labels.csv`). The gap between strict and loose above matters: loose
counts an answer as "caught" even if the verifier flagged an unrelated claim for the wrong reason
while missing the actual problem — see ADR-014 for why {n_zero_false_claim_answers} of the
{n_not_fully_correct} flagged answers have zero individually-false claims at all (the problem was
relevance/completeness, not a false statement), which the strict number correctly treats as *not*
catchable by a claim-level verifier.

## False alarm rate on correct answers

{false_alarms} of {n_fully_correct} fully_correct answers had at least one claim flagged
(CONTRADICTED or UNVERIFIABLE) despite the answer being ground-truth correct — a false-alarm rate
of {false_alarms/n_fully_correct:.2f}. Not one of the blueprint's named metrics, but relevant to
precision: it's the direct source of false positives.
"""

    Path(OUTPUT).write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
