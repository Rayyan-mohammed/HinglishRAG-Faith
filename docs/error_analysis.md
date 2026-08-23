# Error Analysis (B4, Week 4)

Reviews the verifier's mistakes against `eval/claim_ground_truth.csv`, computed by
`scripts/compute_metrics.py` into `results/metrics.md`. Numbers here: precision 0.21, recall
0.75, strict answer-level catch rate 0.50 — see `results/metrics.md` for the full table.

Both ground-truth files (`eval/labels.csv`, `eval/claim_ground_truth.csv`) are AI-drafted,
pending human review (ADR-012, ADR-014). Everything below is provisional in the same way.

## False positives (66 of 84 flagged claims) — why precision is low

Checked whether P-004/P-005's cross-scheme retrieval problem explained the false positives.
It explains exactly half.

**33 of 66 (50%): wrong-scheme evidence.** The claim was fine; the evidence the verifier
compared it against wasn't from the scheme the question was actually about. Root cause is the
same as P-004: short, generic claim phrasing doesn't carry enough scheme-specific vocabulary for
bge-m3 to anchor retrieval correctly, so `top_k=2` per-claim retrieval pulls from elsewhere.

**33 of 66 (50%): correct-scheme evidence, still flagged wrongly.** This is a distinct problem —
the verifier prompt (`VERDICT_PROMPT`) has no instruction for what to do when the claim itself is
a statement *about the evidence's completeness* ("context mein X ka ullekh nahi hai," "koi
jankari nahi hai"). These meta-claims are often true — the source genuinely doesn't mention
whatever's being asked — but the judge tends to mark them UNVERIFIABLE or even CONTRADICTED
regardless, apparently because the evidence text doesn't literally "discuss" the meta-claim,
even when the meta-claim is an accurate description of that same evidence's silence. Example:
Q6's claim "Context mein naye kisan registration ke liye last date ka ullekh nahi hai" is true —
no such deadline exists anywhere in the PM-KISAN facts — but was still flagged UNVERIFIABLE.

Full breakdown in P-006 (`docs/problems_and_decisions.md`).

## False negatives (6 of 24 true hallucinations) — what got missed

All 6, reviewed individually:

| Question | Claim (truncated) | Verdict (confidence) | Why it was missed |
|---|---|---|---|
| 10 | "...amount same hai sabhi states..." | SUPPORTED (0.97) | **Bundled claim.** A verifiable fact (Rs 6000/year, Rs 2000 x3) and an unverifiable generalization ("same across all states") got decomposed into one claim, not two. The judge anchored on the strongly-supported numeric part and didn't separately scrutinize the generalization. |
| 30 | "...Driving Licence, Voters' ID Card, NREGA Job Card..." | SUPPORTED (0.97) | **True fact, wrong scheme, evidence mix.** This content is genuinely PM-KISAN's document list. `verify_claim()`'s `top_k=2` likely retrieved one PM-KISAN passage and one Ayushman Bharat passage; the judge matched against the PM-KISAN one and correctly called it supported — but `evidence_source` (which only records the top-ranked passage) shows "Ayushman Bharat," which is what made this look wrong in ground truth. The claim's factual *content* is true; it's misapplied to the wrong scheme's answer. The verifier isn't designed to check "is this evidence relevant to the scheme asked about," only "does the evidence support the claim text" — and by that narrower test, it isn't wrong. |
| 49 | "Is scheme mein do models hain..." | SUPPORTED (0.99) | **Scope mismatch, not a factual error.** "Do models" (public/private) is true of the AHP vertical specifically — real evidence supports it. The claim's actual problem is that it describes "the scheme" as a whole (which has 4 verticals: ISSR/CLSS/AHP/BLC), a document-structure fact the verifier has no visibility into. |
| 51 | "Diye gaye context me sirf PM-KISAN" / "...Post-Matric Scholarship ke bare me jankari hai" | SUPPORTED (0.85 / 0.95) | **Decomposition lost the exhaustiveness qualifier.** The original claim was "context has *only* PM-KISAN and Post-Matric Scholarship info" — false, since PM Awas Yojana facts also exist. Splitting it into "has PM-KISAN info" + "has Post-Matric info" produces two individually-true fragments, silently dropping the "only" that made the combined claim false. |
| 57 | "PM Awas Yojana...documents...koi specific jankari nahin" | SUPPORTED (0.92) | **Two errors cancelling out.** Evidence source was Ayushman Bharat (wrong scheme, same P-006 pattern) — but that wrong evidence *also* didn't mention documents, so it accidentally looked consistent with the "no info" claim. The real PM Awas Yojana facts (land ownership proof, building plan — rows 5.1.5/5.1.6) were never retrieved, so the actual contradiction was never seen. |

Three distinct mechanisms, not one: (a) compound claims mixing a true fact with an unverifiable
generalization, (b) true-content-wrong-scheme cases where the verifier's narrow claim-vs-evidence
check has no way to judge scheme relevance, (c) decomposition dropping a qualifier word when
splitting compound sentences. (b) and P-006's wrong-scheme false positives share a root cause;
(c) is a new decomposition failure mode not previously in `docs/problems_and_decisions.md`
(ADR-003's known limitations) — worth adding there.

## What this suggests, if there's time to act on it before submission

1. **Highest-value fix:** stop `judge()` from treating "no info" / absence claims the same as
   ordinary factual claims — either exclude them from verification (flag as a separate
   "unverifiable by design" category) or give the prompt explicit instructions for this claim
   type. This alone would likely fix roughly half the false positives (P-006).
2. **Second:** the wrong-scheme retrieval problem (the other half of false positives, and 2 of 6
   false negatives) could be fixed for evaluation purposes by filtering retrieval to the
   question's known scheme, but that's evaluation-only — a deployed system doesn't know the
   "correct" scheme in advance, so this wouldn't be a legitimate architectural fix, only a way to
   isolate whether decomposition/verification are sound independent of retrieval quality.
3. **Lower priority:** the compound-claim and dropped-qualifier decomposition issues (Q10, Q51)
   affect 3 of 212 claims — real, but a smaller share than the other two.

None of this was implemented — Week 4 ran out of scope for a re-run and re-measurement cycle.
Recorded as findings for the report and as next steps if the project continues past this
submission.
