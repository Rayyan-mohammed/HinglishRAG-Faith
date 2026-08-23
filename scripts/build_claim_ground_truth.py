"""Builds eval/claim_ground_truth.csv: per-claim hallucination ground truth, derived from a
manual atomic-level re-check of each claim in the 18 answers flagged in eval/labels.csv (the
other 42 fully_correct answers' claims are ground-truth non-hallucinated by construction).

This is a second, finer-grained pass beyond eval/labels.csv's answer-level labels -- see ADR-014
in docs/problems_and_decisions.md for why answer-level labels aren't sufficient to compute the
claim-level precision/recall the blueprint (Section 13.2) actually asks for, and what the
atomic-level re-check found that the answer-level pass missed."""

import csv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

VERIFIER_RESULTS = "results/verifier_results.csv"
OUTPUT = "eval/claim_ground_truth.csv"

# (question_id, distinctive substring of the claim) for every claim independently confirmed
# hallucinated (contradicted by or absent from the source facts) on a claim-by-claim re-check.
# Everything else -- including claims in the other 12 flagged answers whose problem turned out
# to be relevance/completeness rather than a false individual claim -- is not hallucinated.
HALLUCINATED_MARKERS = [
    (2, "Nahin, PM-KISAN scheme sirf un kisano ke liye nahin hai jinke paas apni zameen hai"),
    (2, "ismein kya kiraye ki zameen wale apply kar sakte hain"),
    (2, "yeh nahin bataya gaya hai ki kiraye ki zameen wale"),
    (3, "Arre, yeh to context mein clearly nahi likha hai"),
    (3, "exclusion criteria ke baare mein kuch nahi likha hai"),
    (10, "sabhi states ke kisano ke liye amount same hai"),
    (24, "diya gaya context iska jawaab nahin deta"),
    (24, "Diye gaye context mein sirf Ayushman Bharat ke udeshya"),
    (24, "iske bare mein koi jaankari nahin hai ki yeh cover ek baar"),
    (30, "Driving Licence, Voters' ID Card, NREGA Job Card"),
    (43, "Income certificate kis authority se banwana padta hai, iska context"),
    (43, "Context mein sirf income certificate ki jarurat"),
    (43, "yeh nahi bataya gaya hai ki kis authority se banwana padta hai"),
    (44, "Nahin, caste certificate submit karna mandatory nahin hai"),
    (49, "Is scheme mein do models hain - ek public sector agencies dwara"),
    (49, "doosra private sector dwara"),
    (51, "aapka sawal mere paas diye gaye context se related nahi hai"),
    (51, "Diye gaye context me sirf PM-KISAN"),
    (51, "Post-Matric Scholarship ke bare me jankari hai"),
    (51, "subsidy claim ya construction ke bare me koi jankari nahi hai"),
    (57, "PM Awas Yojana ke liye documents ke baare mein context mein kuchh specific jankari nahin hai"),
    (57, "application ke liye konsi documents chahiye, iske baare mein koi jankari nahin di gayi hai"),
    (60, "PAN card ki zaroorat nahi hai"),
    (60, "PAN card ki koi zaroorat nahi hai"),
]


def is_hallucinated(question_id, claim):
    for qid, marker in HALLUCINATED_MARKERS:
        if int(question_id) == qid and marker in claim:
            return True
    return False


def main():
    with open(VERIFIER_RESULTS, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    matched = set()
    out_rows = []
    for row in rows:
        qid, claim = row["question_id"], row["claim"]
        hallucinated = is_hallucinated(qid, claim)
        if hallucinated:
            for marker in HALLUCINATED_MARKERS:
                if int(qid) == marker[0] and marker[1] in claim:
                    matched.add(marker)
        out_rows.append(
            {"question_id": qid, "claim": claim, "true_hallucinated": hallucinated}
        )

    unmatched = set(HALLUCINATED_MARKERS) - matched
    if unmatched:
        print(f"WARNING: {len(unmatched)} markers never matched a claim: {unmatched}")

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["question_id", "claim", "true_hallucinated"])
        writer.writeheader()
        writer.writerows(out_rows)

    n_true = sum(1 for r in out_rows if r["true_hallucinated"])
    print(f"{len(out_rows)} claims total, {n_true} marked true_hallucinated, {len(out_rows) - n_true} not")


if __name__ == "__main__":
    main()
