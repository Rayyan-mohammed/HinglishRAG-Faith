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
# Everything else -- including claims in the other 7 flagged answers whose problem turned out
# to be relevance/completeness rather than a false individual claim -- is not hallucinated.
#
# Rewritten in ADR-021 to match Claude's decomposition wording (Groq's gpt-oss-120b produced
# different claim text, including some fragmented compound claims that Claude decomposes more
# cleanly). Re-derived from eval/labels.csv's per-question notes -- the underlying facts these
# markers point at are unchanged from before the model switch, only the exact claim strings are
# new. Where Claude's cleaner decomposition separates a true sub-fact from a false one that the
# old fragmented decomposition had bundled together (e.g. Q24, Q49), only the genuinely false
# part is marked here -- see ADR-021 for the specific reasoning per question.
# Q2/Q3/Q30 markers below were re-checked a second time after a follow-up re-run (still ADR-021,
# hybrid-evidence version): decompose_llm() is itself not perfectly stable claim-to-claim across
# runs on identical input -- Q2's first claim dropped a "nahin" (negation) this run, flipping it
# from the original hallucinated denial ("PM-KISAN is NOT only for landowners") into a literal
# true statement ("PM-KISAN IS only for landowners"), so it's correctly excluded from this list
# even though the same underlying sentence was hallucinated last run. Q30's three separate
# wrong-scheme document claims got bundled into one this run. Ground truth here tracks the claim
# text as actually decomposed, not the original answer's intent -- a claim-level verifier can
# only be graded against the claims it's actually asked to check.
HALLUCINATED_MARKERS = [
    (2, "yeh jankari nahin di gayi hai ki kiraye ki zameen wale apply kar sakte hain"),
    (2, "yeh nahin bataya gaya hai ki kiraye ki zameen wale ismein shaamil hain ya nahin"),
    (3, "Context mein clearly nahi likha hai ki government employee hone se PM-KISAN ka fayda milta hai ya nahi"),
    (3, "PM-KISAN ke exclusion criteria ke baare mein context mein kuch nahi likha hai"),
    (10, "sabhi states ke kisano ke liye amount same hai"),
    (24, "jaankari nahin hai ki Ayushman Bharat cover ek baar ke liye hai ya har saal renew hota hai"),
    (30, "Driving Licence, Voters' ID Card, NREGA Job Card submit karne pad sakte hain"),
    (43, "Income certificate kis authority se banwana padta hai, iska context mein koi jankari nahi hai"),
    (43, "Context mein yeh nahi bataya gaya hai ki income certificate kis authority se banwana padta hai"),
    (44, "Caste certificate submit karna mandatory nahin hai"),
    (49, "Pradhan Mantri Awas Yojana (Urban) 2.0 scheme mein do models hain"),
    (51, "Diye gaye context mein sirf PM-KISAN aur Post-Matric Scholarship ke bare mein jankari hai"),
    (51, "Diye gaye context mein subsidy claim ke bare mein koi jankari nahi hai"),
    (51, "Diye gaye context mein construction ke bare mein koi jankari nahi hai"),
    (57, "PM Awas Yojana ke liye documents ke baare mein context mein kuchh specific jankari nahin hai"),
    (57, "application ke liye konsi documents chahiye, iske baare mein koi jankari nahin di gayi hai"),
    (60, "Is scheme ke liye PAN card ki zaroorat nahi hai"),
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
