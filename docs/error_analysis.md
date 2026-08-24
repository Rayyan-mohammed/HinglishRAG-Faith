# Error Analysis (B4, Week 4)

Reviews the verifier's mistakes against `eval/claim_ground_truth.csv`, computed by
`scripts/compute_metrics.py` into `results/metrics.md`. Current numbers (from the P-008 re-run
against the post-P-007 corrected data): precision 0.21, recall 0.71, strict answer-level catch
rate 0.50 — see `results/metrics.md` for the full table.

**Read the exact counts below as illustrative of the shape of the problem, not as fixed,
reproducible figures.** P-008 found real run-to-run non-determinism even at `temperature=0` — a
second run on identical claim text moved recall from 0.75 to 0.71 and flipped 3 individual
verdicts on true-hallucinated claims. The specific claims making up any bucket below can shift
between runs; the two root causes P-008 diagnosed (oversized multi-topic fact rows losing the
retrieval race, and genuine LLM-judge misjudgment on correct evidence) are the stable finding,
confirmed reproducible across both runs on the same example claims.

Both ground-truth files (`eval/labels.csv`, `eval/claim_ground_truth.csv`) are AI-drafted,
pending human review (ADR-012, ADR-014). Everything below is provisional in the same way.

## False positives (65 of 82 flagged claims) — why precision is low

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
- **12 of 33 (from the first run): retrieval-or-judge failures on well-formed, accurate,
  correctly-scoped claims — now diagnosed, not unexplained.** Added `evidence_text` logging
  (P-008) and re-ran verification specifically to find out what was going wrong here. Found two
  distinct, confirmed causes:
  - **Oversized, multi-topic fact rows losing the retrieval race.** Several `data/schemes/*.csv`
    rows are massive multi-paragraph blocks covering a dozen unrelated sub-topics in one row
    (e.g. Post-Matric Scholarship's "V. Value of Scholarship" row covers book banks, CPL courses,
    disability allowances, *and* the Group I-IV maintenance-allowance table all at once). A query
    about one specific sub-fact competes against that entire diluted embedding and loses to a
    short, topically-adjacent-but-wrong fact instead. Confirmed reproducible: 5 of Q38's "Group N
    ke liye 1200/820/570/380 rupees hostellers" claims retrieved Post-Matric Scholarship's
    separate *Maharashtra-specific* rate range (₹250-700, ₹400-1350/month) both times this was
    tested — never the correct national Group I-IV table, even though it exists in the dataset.
  - **Genuine LLM-judge misjudgment on complete, correct evidence.** Q42's "Agar aap SC category
    se hain toh aapko caste certificate ki copy bhi lagani hogi" retrieved the *entire* correct
    "Procedure for Applying" passage — including item (d), the exact sentence requiring a caste
    certificate — and still came back **CONTRADICTED (0.86-0.92 confidence across two separate
    runs)**. Nothing to blame on retrieval, decomposition, or scheme-matching: the judge had the
    right answer directly in front of it and got it wrong anyway. A genuine reliability limit on
    the LLM-as-judge approach itself.

  See P-008 in `docs/problems_and_decisions.md` for the full writeup, including a third finding:
  re-running verification on identical claim text isn't fully reproducible even at
  `temperature=0` — recall moved from 0.75 to 0.71 between two runs on the same 212 claims.
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

So the illustrative shape of the ~65 false positives: ~32-33 wrong-scheme, ~13 decomposition
damage, ~12 split between oversized-fact-block retrieval misses and genuine judge misjudgment
(P-008), ~7 absence-claim mishandling, 1 confirmed data staleness (now fixed). Judged purely by
how much is left unexplained after diagnosis, the picture is now much better than the original
"12 unexplained" made it look — but the judge-misjudgment share of that 12 (illustrated by Q42)
is a real ceiling on the LLM-as-judge approach itself, not something more engineering fixes.

Full breakdown in P-006 and P-008 (`docs/problems_and_decisions.md`).

## False negatives (7 of 24 true hallucinations, post-P-008) — what got missed

The original run had 6; this run has 7 — Q57 flipped to caught, Q2 and Q43 flipped to missed,
none of which reflects a code change (see P-008's non-determinism finding). All 7, reviewed
individually:

| Question | Claim (truncated) | Verdict (confidence) | Why it was missed |
|---|---|---|---|
| 2 | "...koi jankari nahin di gayi hai" (re: renters) | SUPPORTED (0.73) | **Absence-claim mishandling, in reverse.** The mirror image of P-006's absence-claim false positives: here the claim wrongly asserts silence on renters' eligibility, and the judge accepted it as supported rather than checking it against the "land must be in own name" facts that do address it. |
| 10 | "...amount same hai sabhi states..." | SUPPORTED (0.97) | **Bundled claim.** A verifiable fact (Rs 6000/year, Rs 2000 x3) and an unverifiable generalization ("same across all states") got decomposed into one claim, not two. The judge anchored on the strongly-supported numeric part and didn't separately scrutinize the generalization. |
| 30 | "...Driving Licence, Voters' ID Card, NREGA Job Card..." | SUPPORTED (0.95) | **True fact, wrong scheme, evidence mix.** This content is genuinely PM-KISAN's document list. `verify_claim()`'s `top_k=2` likely retrieved one PM-KISAN passage and one Ayushman Bharat passage; the judge matched against the PM-KISAN one and correctly called it supported — but `evidence_source` (which only records the top-ranked passage) shows "Ayushman Bharat," which is what made this look wrong in ground truth. The claim's factual *content* is true; it's misapplied to the wrong scheme's answer. |
| 43 | "...koi jankari nahi hai" (re: income certificate authority) | SUPPORTED (0.8) | Same pattern as Q2 — claim wrongly asserts the source is silent on who issues the income certificate; source actually specifies employer / self-declaration affidavit, and the judge accepted the false "silent" claim anyway. |
| 49 | "Is scheme mein do models hain..." | SUPPORTED (0.98) | **Scope mismatch, not a factual error.** "Do models" (public/private) is true of the AHP vertical specifically — real evidence supports it. The claim's actual problem is that it describes "the scheme" as a whole (which has 4 verticals: ISSR/CLSS/AHP/BLC), a document-structure fact the verifier has no visibility into. |
| 51 | "Diye gaye context me sirf PM-KISAN" / "...Post-Matric Scholarship ke bare me jankari hai" | SUPPORTED (0.85 / 0.95) | **Decomposition lost the exhaustiveness qualifier.** The original claim was "context has *only* PM-KISAN and Post-Matric Scholarship info" — false, since PM Awas Yojana facts also exist. Splitting it into "has PM-KISAN info" + "has Post-Matric info" produces two individually-true fragments, silently dropping the "only" that made the combined claim false. |

Four distinct mechanisms, not one: (a) compound claims mixing a true fact with an unverifiable
generalization, (b) true-content-wrong-scheme cases where the verifier's narrow claim-vs-evidence
check has no way to judge scheme relevance, (c) decomposition dropping a qualifier word when
splitting compound sentences, (d) the judge accepting a false "the source is silent on this" claim
at face value instead of checking it — the inverse failure mode of P-006's absence-claim false
positives, confirming that absence claims are unreliable for the verifier in *both* directions,
not just as over-flagged. (b) and P-006's wrong-scheme false positives share a root cause; (c) is
a decomposition failure mode documented in ADR-003's update.

## What this suggests, if there's time to act on it before submission

Final priority order, after two corrections and one completed investigation (P-008):

1. **Highest value: fix the fact-granularity problem.** Split the oversized, multi-topic rows in
   `data/schemes/*.csv` (Post-Matric Scholarship's "V. Value of Scholarship" row is the worst
   offender — one row covering book banks, CPL courses, disability allowances, and the Group I-IV
   table all at once) into one row per sub-fact, matching the grain everything else in the dataset
   already uses. This is a data-quality fix, not a code fix, and it's the confirmed cause of
   several of the worst retrieval misses found in P-008.
2. **Second: tighten `decompose()`** so it stops emitting fragments that aren't complete,
   independently-checkable claims (bare entities, clauses that lost their antecedent across an
   "aur" split). ~13 of 65 false positives (~20%). A cheap first pass: drop any decomposed claim
   under some minimum token length, or that has no verb, before sending it to verification.
3. **Third: the wrong-scheme retrieval problem** (the single largest *identified-cause* bucket,
   ~33 of 65 false positives, and 2 of 7 false negatives) could be fixed for evaluation purposes
   by filtering retrieval to the question's known scheme, but that's evaluation-only — a deployed
   system doesn't know the "correct" scheme in advance, so this isn't a legitimate architectural
   fix, only a way to isolate whether decomposition/verification are sound independent of
   retrieval quality.
4. **Fourth: fix absence-claim handling in both directions**, not just the over-flagging half —
   P-008's false-negative re-check found the judge also *accepts* false "the source is silent on
   this" claims at face value (Q2, Q43) as readily as it wrongly flags true ones. Either exclude
   absence-style claims from verification entirely, or give the prompt explicit instructions for
   this claim type specifically.
5. **Fifth, and not really fixable by more engineering:** the genuine LLM-judge misjudgment found
   in P-008 (Q42's caste-certificate claim, correct evidence, wrong verdict anyway) is a real
   reliability ceiling on the LLM-as-judge approach (ADR-001). Worth disclosing plainly in the
   final report as a limitation of the method, not chasing as a bug.
6. **Lower priority:** the compound-claim and dropped-qualifier decomposition issues (Q10, Q51)
   affect a handful of claims — real, but a smaller share than the others.
7. **Already done (P-008):** re-ran `scripts/verify_answers.py` against the index built from the
   post-P-007 corrected `PM-KISAN.csv`. Confirmed the fix worked (Q9 now SUPPORTED) but also
   surfaced real run-to-run non-determinism as a separate finding — see P-008.

None of this was implemented — Week 4 ran out of scope for a re-run and re-measurement cycle.
Recorded as findings for the report and as next steps if the project continues past this
submission.
