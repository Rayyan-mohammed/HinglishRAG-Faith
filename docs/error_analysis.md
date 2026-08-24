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

**33 of 66 (50%): correct-scheme evidence, still flagged wrongly.** First pass at this bucket
grouped it into "7 absence-claims + 26 decomposition fragments" — the second half was itself a
too-fast generalization (a keyword filter, not a read of all 26). Reading every one individually
found four genuinely distinct sub-causes, not two:

- **13 of 33: genuine decomposition damage.** Bare fragments with no predicate (`"EWS"`,
  `"Assam, Meghalaya"`), a dangling incomplete conditional (Q47's "agar aapke paas pucca ghar hai"
  cut off before its consequence clause), and list items that lost their shared antecedent when a
  compound sentence split on "aur" — 4 of Q38's "day scholars" figures got separated from the
  "Group N ke liye" reference naming which group they belong to (the "hostellers" halves of the
  same pairs kept their group reference and verified fine — see next bullet). Also Q25's "poora
  kharcha cover hota hai" claim, the same dropped-qualifier bug already documented for Q51
  (ADR-003) — split off from its own "lekin sirf 5 lakh tak" cap. The verifier marking these
  UNVERIFIABLE is arguably correct given the input — there's no complete claim left to check.
- **12 of 33: unexplained retrieval-or-judge failures on well-formed, accurate, correctly-scoped
  claims.** The concerning bucket — no decomposition damage, no scheme mismatch, no absence
  pattern, and still wrong. Concrete example: Q42's "Agar aap SC category se hain toh aapko caste
  certificate ki copy bhi lagani hogi" — complete sentence, factually correct (matches the
  source's application document list exactly), evidence correctly scoped to Post-Matric
  Scholarship — came back **CONTRADICTED at 0.92 confidence**. Also 5 of Q38's "Group N ke liye
  1200/820/570/380 rupees hostellers" figures, each a complete, specific, true claim naming its
  own group — not missing anything, still flagged. `verifier_results.csv` only logs the
  top-ranked evidence source, not the full evidence text sent to the judge, so it isn't possible
  after the fact to tell whether the judge saw the right passage and misjudged it, or saw a
  subtly-wrong one despite the scheme label matching — a logging gap worth fixing before the next
  run.
- **7 of 33: true absence-claim mishandling.** The verifier prompt (`VERDICT_PROMPT`) has no
  instruction for what to do when the claim itself is a statement *about the evidence's
  completeness* ("context mein X ka ullekh nahi hai," "koi jankari nahi hai"). These are often
  true — the source genuinely doesn't mention whatever's being asked — but the judge tends to
  mark them UNVERIFIABLE or CONTRADICTED regardless. Example: Q6's "Context mein naye kisan
  registration ke liye last date ka ullekh nahi hai" is true — no such deadline exists anywhere
  in the PM-KISAN facts — but was still flagged UNVERIFIABLE.
- **1 of 33: confirmed data staleness.** Q9's "Total 6000 rupees... 2000 rupees" claim
  (factually correct) was marked CONTRADICTED at 0.95 confidence. This verifier run used an index
  built *before* A fixed the corrupted `Rs.60001`/`Rs.20001` rupee amounts in `PM-KISAN.csv`
  (P-007) — the judge correctly flagged a true claim against evidence that was, at the time,
  actually wrong. Not re-measured after the fix; a known small skew in the current numbers.

So of all 66 false positives: 33 wrong-scheme, 13 decomposition damage, 12 unexplained
verifier/retrieval failures on good input, 7 absence-claim mishandling, 1 confirmed data
staleness. The 12 "unexplained" claims matter most for judging how good the underlying verifier
actually is, since nothing else can be blamed for those — everything else has an identifiable
cause with a plausible fix.

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

Twice-corrected priority order (see P-006's two corrections — each pass found the previous one
had generalized from too small a sample):

1. **Highest priority, but not a fix — an investigation:** find out what's actually going wrong
   in the 12 unexplained cases (18% of all false positives) before designing a fix for them.
   Nothing else can be blamed for those — correct scheme, complete claim, correct fact, still
   flagged wrong. Start by logging the *full* evidence text `judge()` receives, not just the top
   source label, so these can actually be diagnosed instead of guessed at.
2. **Second:** tighten `decompose()` so it stops emitting fragments that aren't complete,
   independently-checkable claims (bare entities, clauses that lost their antecedent across an
   "aur" split). 13 of 66 false positives (20%). A cheap first pass: drop any decomposed claim
   under some minimum token length, or that has no verb, before sending it to verification.
3. **Third:** the wrong-scheme retrieval problem (33 of 66 false positives — the single largest
   *identified-cause* bucket, and 2 of 6 false negatives) could be fixed for evaluation purposes
   by filtering retrieval to the question's known scheme, but that's evaluation-only — a deployed
   system doesn't know the "correct" scheme in advance, so this isn't a legitimate architectural
   fix, only a way to isolate whether decomposition/verification are sound independent of
   retrieval quality.
4. **Fourth:** stop `judge()` from treating "no info" / absence claims the same as ordinary
   factual claims — either exclude them from verification or give the prompt explicit
   instructions for this claim type. Smallest identified category (7 of 66), but still real and
   fixable.
5. **Lower priority:** the compound-claim and dropped-qualifier decomposition issues (Q10, Q51)
   affect 3 of 212 claims — real, but a smaller share than the others.
6. **Housekeeping, not a design fix:** re-run `scripts/verify_answers.py` against the index built
   from the post-P-007 corrected `PM-KISAN.csv`, and re-run `compute_metrics.py` — at least one
   false positive (Q9) is a direct artifact of verifying against stale, corrupted evidence, not a
   real pipeline weakness.

None of this was implemented — Week 4 ran out of scope for a re-run and re-measurement cycle.
Recorded as findings for the report and as next steps if the project continues past this
submission.
