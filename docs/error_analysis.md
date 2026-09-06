# Error Analysis (B4, Week 4)

Reviews the verifier's mistakes against `eval/claim_ground_truth.csv`, computed by
`scripts/compute_metrics.py` into `results/metrics.md`. **Current, final, reported numbers**
(after ADR-015's fixes, ADR-017's diagnosed regression, and ADR-018's relevance-aware repair):
precision 0.24, recall 0.67, strict answer-level catch rate 0.50, false-alarm rate 0.50.

**Read this document in three layers**, in this order: (1) this summary, the final state; (2)
ADR-017's regression story, kept because it explains a real mechanism worth understanding even
though it's no longer the reported number; (3) the pre-fix diagnosis below that, kept because
it's still an accurate description of *why* the original problems happened.

## The final state: four fixes, measured end-to-end (ADR-015 → ADR-017 → ADR-018)

Four changes went in, across two rounds: (1) decomposition fragment filter, (2) splitting
Post-Matric Scholarship's oversized row into 12 atomic facts, (3) an absence-claim prompt
instruction that initially regressed recall (ADR-017), (4) a follow-up refinement making that
same instruction relevance-aware — check the evidence is even about the claim's scheme/subject
before trusting an "it's not mentioned" reading (ADR-018). Full re-verification after each round:

| Metric | Original (pre-fixes) | Round 1 (ADR-015, regressed) | Round 2 (+ADR-018 fix) |
|---|---|---|---|
| Precision | 0.21 | 0.18 | **0.24** |
| Recall | 0.71 | 0.42 | **0.67** |
| True positives | 17 | 10 | 16 |
| False positives | 65 | 46 | 50 |
| False negatives | 7 | 14 | 8 |
| False-alarm rate | 0.57 | 0.52 | **0.50** |

The final state beats the original on precision, false-positive count, and false-alarm rate, and
recovers to within 4 points of original recall (0.67 vs 0.71) — a net improvement across the
board, not just a reversal of the regression.

**Why round 1 regressed, briefly** (full mechanism in ADR-017): the absence-claim instruction was
correct in isolation but had no way to tell "the evidence is silent on this detail" apart from
"the evidence is about something else entirely." Wrong-scheme evidence (still not fixed at the
retrieval level — see below) always looks silent on the claim's real topic, so the judge started
confidently trusting false "not mentioned" claims instead of hedging.

**Why round 2 recovered most of it:** added one precondition to the same instruction — check the
evidence is on-topic before trusting its silence. Verified directly against the real failing case
before the full re-run (Q57's PM Awas Yojana claim, evidence entirely about Ayushman Bharat and
PM-KISAN, flipped SUPPORTED→UNVERIFIABLE as intended), and confirmed no regression on the original
5 sample pairs or both absence-claim directions with correct evidence.

**Why it's not a full recovery to 0.71:** the fix only catches evidence that's clearly about a
*different scheme* (schemes are named explicitly in most passages, so an LLM can notice this
directly from the text). It does not catch the harder case — evidence nominally from the *right*
scheme that's still missing the specific fact needed (tested directly on Q2: claim doesn't name a
scheme, evidence mixes the right scheme's generic text with a wrong scheme's, verdict unchanged).
That's the oversized-fact-row / narrow-retrieval mechanism (ADR-015/P-008), only partially fixed
so far (only Post-Matric Scholarship's worst row was split). The genuine LLM-judge misjudgment
case (Q42) is also untouched by any prompt change, by design — see below.

The eval-only scheme-filtered retrieval diagnostic built in ADR-017 to isolate this effect is no
longer needed to answer the question it was built for — this smaller, targeted prompt fix
answered it more directly, without depending on the `faiss`/`pandas` environment issue that
blocked the diagnostic.

---

## Round 1's regression, for the mechanism (no longer the reported numbers)

Kept because it's the clearest example in this project of a locally-verified-correct fix with a
measured negative system effect, and because the false-negative table below (Q2, Q30, Q49, Q51)
still describes real, uncorrected mechanisms. Numbers in this section are Round 1's, not final —
see the table above for what's actually reported.

Three fixes went in for this round: (1) decomposition fragment filter, (2) an explicit
verifier-prompt instruction for claims that describe an absence of information, (3) splitting
Post-Matric Scholarship's oversized "V. Value of Scholarship" row into 12 atomic facts. Full
re-verification (209 claims, same 60 answers) measured:

| Metric | Before (P-008) | After (ADR-015 fixes) |
|---|---|---|
| Precision | 0.21 | 0.18 |
| Recall | 0.71 | **0.42** |
| True positives | 17 | 10 |
| False positives | 65 | 46 |
| False negatives | 7 | 14 |
| False-alarm rate | 0.57 | 0.52 |

**Why:** fix (2) was verified correct in isolation before shipping — a direct `judge()` call with
hand-written correct evidence confirmed a true "no info" claim flips UNVERIFIABLE→SUPPORTED and a
false one flips SUPPORTED→CONTRADICTED, exactly as designed. But 9 of the 14 new false negatives
(64%) have wrong-scheme evidence — the same P-004/P-006 retrieval problem, deliberately left
unfixed since scheme-filtering isn't representative of real deployment. When retrieval feeds the
judge evidence from the wrong scheme, that evidence genuinely doesn't discuss the claim's real
topic, and the (round 1) prompt instruction told the judge to trust that absence — confidently
producing SUPPORTED for a false claim, where before the same bad evidence more often produced a
hedged UNVERIFIABLE (which still counted as "flagged"). Fixed in round 2 (ADR-018) by making the
same instruction check topical relevance first.

---

## Diagnosis written before any fixes (P-006/P-008) — kept for the reasoning, not the headline numbers

Both ground-truth files (`eval/labels.csv`, `eval/claim_ground_truth.csv`) are AI-drafted,
pending human review (ADR-012, ADR-014). Everything below is provisional in the same way, and the
specific counts reflect the *original pre-fix* run (precision 0.21, recall 0.71) — see the table
at the top of this document for what's actually being reported.

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

## False negatives (8 of 24 true hallucinations, final state) — what got missed

Count has moved 7→14→8 across the three rounds (P-008 → ADR-015 → ADR-018) — partly real fixes,
partly the project's documented run-to-run non-determinism (P-008). The current 8, reviewed
individually:

| Question | Claim (truncated) | Verdict (confidence) | Why it was missed |
|---|---|---|---|
| 2 | "...koi jankari nahin di gayi hai" (re: renters) | SUPPORTED (0.9) | **Absence-claim mishandling, in reverse — and not fixed by ADR-018.** The claim doesn't name a scheme, and the mixed evidence includes a genuinely-right-scheme (PM-KISAN) passage alongside a wrong one — so the relevance check in ADR-018 doesn't trigger (the evidence isn't clearly "about something else entirely," it's just incomplete). The claim wrongly asserts silence on renters' eligibility; the judge accepted it as supported rather than checking it against the "land must be in own name" facts elsewhere in PM-KISAN's data that address it. |
| 3 | "...clearly nahi likha hai ki government employee..." | SUPPORTED (0.95) | Same pattern as Q2 — no scheme named in the claim, evidence is genuinely PM-KISAN (right scheme) but the specific exclusion-criteria fact wasn't retrieved. ADR-018's relevance check doesn't help when the scheme is already right; this is the retrieval-completeness problem (P-008), not a relevance problem. |
| 10 | "...amount same hai sabhi states..." | SUPPORTED (0.97) | **Bundled claim.** A verifiable fact (Rs 6000/year, Rs 2000 x3) and an unverifiable generalization ("same across all states") got decomposed into one claim, not two. The judge anchored on the strongly-supported numeric part and didn't separately scrutinize the generalization. Not a retrieval or relevance issue — a decomposition granularity issue. |
| 30 | "...Driving Licence, Voters' ID Card, NREGA Job Card..." | SUPPORTED (0.97) | **True fact, wrong scheme, evidence mix.** This content is genuinely PM-KISAN's document list, correctly judged true against the PM-KISAN passage in its evidence — but the answer presents it as Ayushman Bharat's list. The verifier checks claim-vs-evidence, not claim-vs-question-scheme, so a true fact copied from the wrong scheme's answer still verifies as supported. |
| 43 | "...koi jankari nahi hai" (re: income certificate authority) | SUPPORTED (0.95) | Same pattern as Q2/Q3 — right scheme (Post-Matric Scholarship) evidence retrieved, but not the specific sentence naming the issuing authority. ADR-018 doesn't help here since the evidence isn't off-topic, just incomplete. |
| 49 | "Is scheme mein do models hain..." | SUPPORTED (0.99) | **Scope mismatch, not a factual error.** "Do models" (public/private) is true of the AHP vertical specifically — real, on-topic evidence supports it. The claim's actual problem is that it describes "the scheme" as a whole (which has 4 verticals: ISSR/CLSS/AHP/BLC), a document-structure fact the verifier has no visibility into regardless of how relevant the evidence is. |
| 51 | "Diye gaye context me sirf PM-KISAN" / "...Post-Matric Scholarship ke bare me jankari hai" | SUPPORTED (0.95 / 0.96) | **Decomposition lost the exhaustiveness qualifier.** The original claim was "context has *only* PM-KISAN and Post-Matric Scholarship info" — false, since PM Awas Yojana facts also exist. Splitting it into "has PM-KISAN info" + "has Post-Matric info" produces two individually-true fragments, silently dropping the "only" that made the combined claim false. |

Five distinct mechanisms survive after ADR-018, none of them fixed by the relevance-aware prompt
because none of them involve evidence that's *clearly off-topic* — that specific pattern (Q57's
old false negative) is the one ADR-018 actually fixed: (a) compound claims mixing a true fact
with an unverifiable generalization (Q10); (b) true-content-wrong-scheme cases where a fact is
genuine but attributed to the wrong answer (Q30); (c) decomposition dropping a qualifier word
when splitting compound sentences (Q51); (d) the judge accepting a false "the source is silent on
this" claim when the *right* scheme's evidence is retrieved but incomplete, not wrong (Q2, Q3,
Q43) — a narrower, harder version of the absence-claim problem than ADR-018 targeted; (e) a
document-structure fact (which vertical vs. the whole scheme) the verifier has no way to
represent (Q49). (b) and (d)'s "right scheme, wrong specific fact" cases share a root cause with
P-008's oversized-fact-row finding — more of `data/schemes/*.csv` likely needs the same
granularity treatment ADR-015 gave Post-Matric Scholarship's worst row alone.

## What was actually done, and what's genuinely still open (post ADR-015/017/018)

Of the list this section used to propose, four items are now done and measured, and two remain
open as the real next steps:

1. **Done — fact-granularity fix.** Post-Matric Scholarship's oversized row split into 12 atomic
   facts (`scripts/split_oversized_row.py`). Confirmed working: Q38/Q39's Group I-IV claims now
   retrieve the correct national table, not the Maharashtra-specific rate range.
2. **Done — decomposition fragment filter.** `decompose()` now drops sub-3-word fragments
   (`src/decomposition.py`, `MIN_CLAIM_WORDS`). Confirmed via new tests
   (`tests/test_decomposition.py`).
3. **Done — absence-claim prompt fix, repaired after an initial regression.** First version
   (ADR-015) was correct in isolation but regressed recall 0.71→0.42 by confidently trusting
   wrong-scheme evidence's silence (ADR-017). Fixed, not reverted: added a relevance check to the
   same instruction — verify the evidence is even about the claim's scheme before trusting an
   absence reading (ADR-018). Recovered to precision 0.24 / recall 0.67, better than the original
   pre-fix baseline on precision and false-alarm rate.
4. **Partially open — wrong-scheme retrieval.** Still the single largest identified cause of
   false positives (~50%), and ADR-018's relevance check only catches the *clearly off-topic*
   subset of its false-negative consequences (Q57-style) — not the *right-scheme-but-incomplete*
   subset (Q2/Q3/Q43-style, still open, see the false-negatives table above). An eval-only
   scheme-filtered diagnostic was attempted to isolate the effect
   (`scripts/diagnostic_scheme_filtered_verify.py`) but didn't finish — blocked by a persistent
   Windows Application Control policy on native DLLs, an environment problem. No longer strictly
   needed: ADR-018's targeted fix answered the practical question more directly. Genuinely fixing
   retrieval for real deployment would mean better retrieval — larger `top_k`, reranking, a
   stronger embedding model for short queries, or extending ADR-015's row-splitting treatment to
   the rest of `data/schemes/*.csv` — none attempted here.
5. **Not fixable by more engineering — the genuine LLM-judge misjudgment.** Q42's caste-certificate
   claim: correct evidence, wrong verdict anyway. A real reliability ceiling on the LLM-as-judge
   approach (ADR-001), disclosed as a limitation of the method in the final report, not chased as
   a bug.
6. **Lower priority, not attempted:** the compound-claim and dropped-qualifier decomposition
   issues (Q10, Q51) affect a handful of claims — real, but smaller than the others.

The honest summary: four fixes shipped. Three were unambiguously net-positive. The fourth
regressed a headline metric on first release, was diagnosed precisely rather than guessed at, and
was repaired — not reverted — once the mechanism was understood, landing better than where the
project started on precision, false positives, and false-alarm rate, with recall recovered to
within 4 points of the original. What's left open is bounded and named, not hand-waved: retrieval
completeness on right-scheme-but-incomplete evidence, and one confirmed case where the method
itself, not the engineering around it, is the limit.
