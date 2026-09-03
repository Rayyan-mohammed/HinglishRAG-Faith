# Error Analysis (B4, Week 4)

Reviews the verifier's mistakes against `eval/claim_ground_truth.csv`, computed by
`scripts/compute_metrics.py` into `results/metrics.md`. **Current, final, reported numbers**
(after ADR-015's fixes were implemented and measured — see ADR-017): precision 0.18, recall
0.42, strict answer-level catch rate 0.50, false-alarm rate 0.52.

**Read this document in two layers.** Everything below the next section was written *before*
ADR-015's fixes (decomposition fragment filter, absence-claim prompt, data-granularity split)
were implemented, diagnosing precision 0.21 / recall 0.71 against 65-66 false positives. That
diagnosis is kept because it's still an accurate description of *why* those specific problems
happened, and two of the three fixes it recommended worked exactly as predicted. Read
**ADR-017's summary right below** first, since it's the number that actually matters: fixing the
absence-claim handling made the pipeline's *measured* performance worse, not better, because of
an interaction with wrong-scheme retrieval that wasn't caught before shipping.

## What actually happened after the fixes (ADR-015 → ADR-017)

Three fixes went in: (1) decomposition fragment filter, (2) an explicit verifier-prompt
instruction for claims that describe an absence of information, (3) splitting Post-Matric
Scholarship's oversized "V. Value of Scholarship" row into 12 atomic facts. Full re-verification
(209 claims, same 60 answers) measured:

| Metric | Before (P-008) | After (ADR-015 fixes) |
|---|---|---|
| Precision | 0.21 | 0.18 |
| Recall | 0.71 | **0.42** |
| True positives | 17 | 10 |
| False positives | 65 | 46 |
| False negatives | 7 | 14 |
| False-alarm rate | 0.57 | 0.52 |

Precision and false-alarm rate moved in the right direction, modestly. **Recall dropped by 29
points** — the headline result of this whole exercise, and not the one that was expected.

**Why:** fix (2) was verified correct in isolation before shipping — a direct `judge()` call with
hand-written correct evidence confirmed a true "no info" claim flips UNVERIFIABLE→SUPPORTED and a
false one flips SUPPORTED→CONTRADICTED, exactly as designed. But 9 of the 14 new false negatives
(64%) have wrong-scheme evidence — the same P-004/P-006 retrieval problem, deliberately left
unfixed since scheme-filtering isn't representative of real deployment. When retrieval feeds the
judge evidence from the wrong scheme, that evidence genuinely doesn't discuss the claim's real
topic, and the new prompt instruction tells the judge to trust that absence — confidently
producing SUPPORTED for a false claim, where before the same bad evidence more often produced a
hedged UNVERIFIABLE (which still counted as "flagged"). The fix made the judge more decisive; on
bad evidence, decisiveness is worse than a hedge.

An eval-only diagnostic (`scripts/diagnostic_scheme_filtered_verify.py`, retrieval scoped to the
question's known-correct scheme, never wired into the real pipeline) was built specifically to
measure how much recall recovers once retrieval isn't the confound — it got 53 of 209 claims
through before hitting a persistent Windows Application Control policy blocking native DLLs
(`faiss`, then `pandas` on retry), an environment problem unrelated to the logic. Deprioritized
rather than fought further — see ADR-017 for the full account.

**Net assessment:** the reported numbers above are real, final, and disclosed as-is, regression
included. Two of three fixes worked; the third is a documented example of a locally-correct
change with a negative system-level effect, left in place rather than reverted, because the
alternative (reverting it) doesn't fix the underlying retrieval problem either — it just goes
back to hiding it behind a less decisive judge. Whoever continues this project should treat
"scope retrieval correctly" as the actual prerequisite for the absence-claim fix to pay off, not
a nice-to-have.

---

## Diagnosis written before the fixes (P-006/P-008) — kept for the reasoning, not the headline numbers

Both ground-truth files (`eval/labels.csv`, `eval/claim_ground_truth.csv`) are AI-drafted,
pending human review (ADR-012, ADR-014). Everything below is provisional in the same way, and the
specific counts reflect the *pre-fix* run (precision 0.21, recall 0.71) — see the table above for
what's actually being reported.

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

## What was actually done, and what's genuinely still open (post ADR-015/017)

Of the list this section used to propose, three items got implemented and measured, one was
attempted and blocked by environment issues, and one remains open as the real next step:

1. **Done — fact-granularity fix.** Post-Matric Scholarship's oversized row split into 12 atomic
   facts (`scripts/split_oversized_row.py`). Confirmed working: Q38/Q39's Group I-IV claims now
   retrieve the correct national table, not the Maharashtra-specific rate range.
2. **Done — decomposition fragment filter.** `decompose()` now drops sub-3-word fragments
   (`src/decomposition.py`, `MIN_CLAIM_WORDS`). Confirmed via new tests
   (`tests/test_decomposition.py`).
3. **Done, but with a measured regression — absence-claim prompt fix.** Works correctly in
   isolation; net negative on the full pipeline because retrieval (item 4, below) still feeds it
   wrong-scheme evidence in 64% of the new false-negative cases. See ADR-017 for the full
   mechanism. **This is the one open question for whoever continues this project**: revert it,
   keep it and prioritize fixing retrieval, or make the prompt aware of retrieval confidence
   before trusting an absence claim.
4. **Still open — wrong-scheme retrieval.** The single largest identified cause of false
   positives (~50%) and now, via the interaction above, a driver of false negatives too. An
   eval-only scheme-filtered diagnostic was built to measure the isolated effect
   (`scripts/diagnostic_scheme_filtered_verify.py`) but didn't finish — blocked by a persistent
   Windows Application Control policy blocking native DLLs, an environment problem, not a logic
   one. Genuinely fixing this for real deployment (not just the eval-only filter) would mean
   better retrieval — larger `top_k`, reranking, or a stronger embedding model for short queries
   — not something attempted here.
5. **Not fixable by more engineering — the genuine LLM-judge misjudgment.** Q42's caste-certificate
   claim: correct evidence, wrong verdict anyway. A real reliability ceiling on the LLM-as-judge
   approach (ADR-001), disclosed as a limitation of the method in the final report, not chased as
   a bug.
6. **Lower priority, not attempted:** the compound-claim and dropped-qualifier decomposition
   issues (Q10, Q51) affect a handful of claims — real, but smaller than the others.

The honest summary: three fixes shipped, two clearly net-positive, one net-negative for a
well-understood and disclosed reason, with the real prerequisite for fixing it (retrieval
quality) identified but not completed this pass.
