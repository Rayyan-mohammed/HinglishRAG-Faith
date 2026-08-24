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

**33 of 66 (50%): correct-scheme evidence, still flagged wrongly.** Split further on a systematic
re-check (not just a handful of examples — see correction in P-006), into two genuinely distinct
sub-causes:

- **7 of 33: true absence-claim mishandling.** The verifier prompt (`VERDICT_PROMPT`) has no
  instruction for what to do when the claim itself is a statement *about the evidence's
  completeness* ("context mein X ka ullekh nahi hai," "koi jankari nahi hai"). These are often
  true — the source genuinely doesn't mention whatever's being asked — but the judge tends to
  mark them UNVERIFIABLE or CONTRADICTED regardless. Example: Q6's "Context mein naye kisan
  registration ke liye last date ka ullekh nahi hai" is true — no such deadline exists anywhere
  in the PM-KISAN facts — but was still flagged UNVERIFIABLE.
- **26 of 33 (the majority — 39% of all 66 false positives): decomposition fragments that aren't
  complete, checkable claims.** `"EWS"`, `"Assam, Meghalaya"`, `"550 rupees per month day scholars
  ke liye hai"` (with no group specified — the antecedent was in an earlier claim, split off by
  an "aur"). These aren't meta-claims and they aren't wrong-scheme; they're pieces of a sentence
  that `decompose()` split too aggressively to still stand alone as a checkable statement. The
  verifier marking these UNVERIFIABLE is arguably *correct behavior given the input* — there's no
  complete claim to confirm or deny. This means the headline 0.21 precision understates how the
  verifier performs on genuinely well-formed claims, and the real lever to pull is decomposition
  quality (a third failure mode for ADR-003, beyond the two already documented), not the verifier
  prompt.
- **One separate, confirmed data-staleness case:** Q9's "Total 6000 rupees... 2000 rupees" claim
  (factually correct) was marked CONTRADICTED at 0.95 confidence. This verifier run used an index
  built *before* A fixed the corrupted `Rs.60001`/`Rs.20001` rupee amounts in `PM-KISAN.csv`
  (P-007) — the judge correctly flagged a true claim against evidence that was, at the time,
  actually wrong. Not re-measured after the fix; a known small skew in the current numbers.

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

Corrected priority order (see P-006's correction — the original "50/50" split undercounted the
biggest single cause):

1. **Highest-value fix, revised:** tighten `decompose()` so it stops emitting fragments that
   aren't complete, independently-checkable claims (bare entities like "EWS", clauses that lost
   their antecedent across an "aur" split). This is 26 of 66 false positives (39%) — the single
   largest cause found, bigger than either wrong-scheme retrieval or absence-claim handling alone.
   A cheap first pass: drop any decomposed claim under some minimum token length, or that has no
   verb, before sending it to verification.
2. **Second:** stop `judge()` from treating "no info" / absence claims the same as ordinary
   factual claims — either exclude them from verification or give the prompt explicit
   instructions for this claim type. Smaller than first thought (7 of 66, not 33), but still a
   real, distinct, fixable category.
3. **Third:** the wrong-scheme retrieval problem (33 of 66 false positives, and 2 of 6 false
   negatives) could be fixed for evaluation purposes by filtering retrieval to the question's
   known scheme, but that's evaluation-only — a deployed system doesn't know the "correct" scheme
   in advance, so this isn't a legitimate architectural fix, only a way to isolate whether
   decomposition/verification are sound independent of retrieval quality.
4. **Lower priority:** the compound-claim and dropped-qualifier decomposition issues (Q10, Q51)
   affect 3 of 212 claims — real, but a smaller share than the others.
5. **Housekeeping, not a design fix:** re-run `scripts/verify_answers.py` against the index built
   from the post-P-007 corrected `PM-KISAN.csv`, and re-run `compute_metrics.py` — at least one
   false positive (Q9) is a direct artifact of verifying against stale, corrupted evidence, not a
   real pipeline weakness.

None of this was implemented — Week 4 ran out of scope for a re-run and re-measurement cycle.
Recorded as findings for the report and as next steps if the project continues past this
submission.
