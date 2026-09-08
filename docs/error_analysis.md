# Error Analysis (B4, Week 4)

Reviews the verifier's mistakes against `eval/claim_ground_truth.csv`, computed by
`scripts/compute_metrics.py` into `results/metrics.md`. **Current, final, reported numbers**
(after ADR-015/017/018's fix-and-repair cycle, ADR-019/020's data-granularity extension and
majority-vote judging, and ADR-021's switch to Claude with hybrid evidence retrieval): precision
0.27, recall 0.71, strict answer-level catch rate 0.39, false-alarm rate 0.40 — the best precision
and recall recorded simultaneously anywhere in this project.

**Read this document in five layers**, in this order: (1) this summary, the final state; (2)
round 4 (ADR-021) below, the most recent and largest single jump in claim-level accuracy; (3) the
ADR-015→018 cycle after that, where the numbers first moved from the original baseline; (4)
ADR-017's regression story, kept because it explains a real mechanism worth understanding even
though it's no longer the reported number; (5) the pre-fix diagnosis at the bottom, kept because
it's still an accurate description of *why* the original problems happened.

## Round 4 (ADR-021): switched Groq → Claude, LLM decomposition, hybrid evidence retrieval — the first round to move precision and recall together

Three changes, made as one arc: (1) switched `src/generation.py`/`decomposition.py`/
`verification.py` from Groq to Claude (Haiku 4.5) after Groq's daily quota repeatedly paused full
runs; (2) replaced regex decomposition with `decompose_llm()`, an LLM prompt that preserves
exclusivity qualifiers and splits bundled claims correctly, verified against both known bug cases
before rollout; (3) changed `verify_claim()`'s evidence pool.

Step (3) went through two versions in the same day. First tried context-passages-only — verify
each claim against exactly the passages that generated its answer, on the theory that this avoids
the wrong-scheme evidence a short claim's own retrieval often pulls in (the single largest
diagnosed false-positive cause, P-006). It worked for that (false-alarm rate improved 0.48→0.40)
but regressed recall (0.67→0.50): confirmed by reading `evidence_text` directly, it ties
verification's blind spots to generation's — if the question-level retrieval that produced the
answer missed a fact, verification saw exactly the same gap and confirmed a false "the context
doesn't say this" claim as SUPPORTED. While diagnosing this, also found and fixed a genuine data
corruption bug: a `PM-KISAN.csv` row titled "exclusion criteria" had a body that duplicated a
different fact entirely, sourced from the same malformed PDF P-007 already flagged. Fixed (not
reverted) by merging context passages with a fresh per-claim `retrieve()` call, deduplicated,
giving the judge both the wrong-scheme protection and a second independent chance to find facts
the original retrieval missed.

| Metric | ADR-020 (round 3, Groq) | Round 4a (Claude, context-only) | Round 4b (Claude, hybrid + data fix) |
|---|---|---|---|
| Precision | 0.25 | 0.20 | **0.27** |
| Recall | 0.67 | 0.50 | **0.71** |
| True positives | 16 | 10 | 12 |
| False positives | 49 | 41 | **32** |
| False negatives | 8 | 10 | **5** |
| Strict answer-level catch rate | 0.44 | 0.44 | 0.39 |
| Loose answer-level catch rate | 0.72 | 0.56 | 0.50 |
| False-alarm rate | 0.48 | 0.40 | 0.40 |

Total claim count moved 209→240→244 purely from LLM decomposition producing a different (finer,
more internally consistent) number of atomic claims per answer, not a change in what's measured —
`eval/claim_ground_truth.csv`'s hallucination markers were re-derived from `eval/labels.csv`'s
per-question notes each time claim text changed, not carried over as stale strings.

**Why answer-level catch rate moved the other way.** Both strict and loose catch rate dropped even
though precision and recall both improved. This is a real, understood side effect, not a hidden
regression: catch rate rewards an answer having *any* qualifying claim flagged, and fewer false
positives means fewer of the 18 flagged answers get a claim flagged "by accident" for an unrelated
reason. A more precise verifier that flags less liberally will, all else equal, catch fewer
answers on loose catch rate even while being more trustworthy per flag — the two metrics measure
different things and don't have to move together.

**A decomposition-stability finding, incidental to this round but worth its own note.**
Re-running `decompose_llm()` on the *same* source answer text (round 4a vs. 4b) produced slightly
different claim text for a few claims — most notably Q2's first claim, which dropped a "nahin"
(negation) on the second run, flipping "PM-KISAN is NOT only for landowners" (the original
hallucination) into "PM-KISAN IS only for landowners" (a true statement). Ground truth was
re-graded against the claim text as actually produced each run, not the original answer's intent
— a claim-level verifier can only be judged against the claims it's actually asked to check.

## Round 3 (ADR-019/020): extended data-granularity fix + majority-vote judging — a wash, not a further win

After the ADR-018 state below, two more changes went in: splitting PM-KISAN's and PM Awas
Yojana's remaining oversized rows (183→197 facts, ADR-019), and majority-vote judging — 3
independent judge calls per claim, majority wins (ADR-020). The second change exists *because* of
what was found investigating the first: diffing two full runs' verdicts found 12 of 20 flips had
byte-identical evidence text, direct proof the judge isn't fully deterministic even at
`temperature=0`. That made the row-split's own single-run before/after comparison unreliable —
most of its apparent effect was judge noise, not the data change.

| Metric | ADR-018 (round 2) | Round 3 (ADR-019+020) |
|---|---|---|
| Precision | 0.24 | 0.25 |
| Recall | 0.67 | 0.67 |
| True positives | 16 | 16 |
| False positives | 50 | 49 |
| False negatives | 8 | 8 |
| Strict answer-level catch rate | 0.50 | 0.44 |
| Loose answer-level catch rate | 0.78 | 0.72 |
| False-alarm rate | 0.50 | 0.48 |

Claim-level numbers are flat to marginally better. Answer-level catch rate is measurably *worse*
despite identical tp/fn counts — diagnosed by checking which of the 18 not-fully-correct answers
had a hallucination caught in each run: the same *total* number of true positives landed on a
different subset of answers, covering one fewer answer at the strict level even though nothing
about total catch count changed. This is reported plainly as a wash rather than framed as further
progress — see ADR-020 for the full reasoning on why the data split and majority voting were kept
anyway (sound engineering on their own terms, even without a demonstrated score gain on this one
run).

---

## Round 2 (ADR-015 → ADR-017 → ADR-018): four fixes, measured end-to-end

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

## False negatives (5 of 17 true hallucinations, final state) — what got missed

Count has moved 7→14→8→8→**5** across the five rounds (P-008 → ADR-015 → ADR-018 → ADR-019/020 →
ADR-021) — both the count of hallucinated claims (24→20→17, as decomposition granularity changed)
and the count missed shrank. Q2, Q43, and Q44's false negatives from round 3 are gone in round 4 —
Q2 and Q43 caught correctly now (the fresh per-claim retrieval half of the hybrid evidence pool
finds the specific fact the context-passages-only evidence was missing), and Q44 no longer exists
as a distinct hallucinated claim after decomposition changed (see round 4's note above on
`decompose_llm()` run-to-run instability). The current 5, reviewed individually:

| Question | Claim (truncated) | Verdict (confidence) | Why it was missed |
|---|---|---|---|
| 10 | "...amount same hai sabhi states..." | SUPPORTED (0.95) | **Bundled claim, unchanged since round 2.** `decompose_llm()` still keeps "amount is Rs 6000/year" and "amount is same across all states" as one claim here rather than splitting them (it does split this pattern correctly elsewhere, e.g. Q49 below) — the judge anchors on the strongly-supported numeric part and doesn't separately scrutinize the generalization. A decomposition consistency issue, not a retrieval or evidence issue. |
| 24 | "...jaankari nahin hai ki Ayushman Bharat cover ek baar ke liye hai ya har saal renew hota hai" | SUPPORTED (0.95) | Same absence-claim-in-mixed-evidence pattern as Q2/Q3/Q43 in earlier rounds — the fresh per-claim retrieval half of the hybrid evidence pool didn't happen to surface the "per annum" fact for this specific phrasing, even though it exists in the corpus and fixed the analogous Q3 case. |
| 30 | "...Driving Licence, Voters' ID Card, NREGA Job Card submit karne pad sakte hain" | SUPPORTED (0.95) | **True fact, wrong scheme — unchanged since round 2.** This is genuinely PM-KISAN's alternate-ID document list, correctly judged true against PM-KISAN evidence in the pool — but the answer presents it as Ayushman Bharat's. The verifier checks claim-vs-evidence, not claim-vs-question-scheme, so a true fact attributed to the wrong scheme's answer still verifies as supported. Neither the model switch nor the hybrid evidence design targets this — it needs claim-vs-question-scheme checking, which no version of this verifier does. |
| 49 | "...do models hain - ek public sector agencies dwara aur doosra private sector dwara" | SUPPORTED (0.94) | **Scope mismatch, unchanged since round 2** (though decomposition bundled the sub-details back into one claim this round, unlike round 2's split version). "Do models" is true of the AHP vertical specifically, not "the scheme" as a whole (which has 4 verticals). A document-structure fact the verifier has no way to represent regardless of evidence quality. |
| 51 | "...construction ke bare mein koi jankari nahi hai" | SUPPORTED (0.95) | **Retrieval-completeness gap, one of three related Q51 claims — the only one still missed.** The other two ("only PM-KISAN and Post-Matric info exists", "no info about subsidy claims") are now correctly caught; PM Awas Yojana construction-related facts exist in the corpus (added in ADR-019's row-splitting) but the fresh per-claim retrieval for this specific phrasing didn't surface them. |

Three of five remaining mechanisms are the same ones documented since round 2 and untouched by any
version of this project's fixes so far: (a) inconsistent decomposition granularity on bundled
claims (Q10); (b) true-content-wrong-scheme attribution, which needs claim-vs-question-scheme
checking the verifier was never designed to do (Q30); (c) a document-structure scope mismatch the
verifier has no representation for (Q49). The other two (Q24, Q51) are retrieval-completeness
gaps of the same general shape ADR-021's hybrid evidence pool fixed for several other cases (Q2,
Q3, Q43 in round 3) — this round's fresh per-claim retrieval simply didn't happen to surface the
right fact for these two specific phrasings, suggesting the fix is directionally right but not a
complete solution to retrieval completeness.

## What was actually done, and what's genuinely still open (post ADR-015/017/018/019/020/021)

Of the list this section used to propose, nine items are now done and measured, and three remain
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
4. **Substantially fixed — wrong/ambiguous-scheme retrieval for claims that don't name a
   scheme.** Was the single largest identified cause of false positives (~50%). ADR-018's
   relevance check only caught the *clearly off-topic* subset (Q57-style); ADR-021's hybrid
   evidence pool (context passages + a fresh per-claim retrieval, merged) fixed most of the
   *right-scheme-but-incomplete* subset too — Q2, Q3, and Q43's false negatives from round 3 are
   gone in round 4. Not a complete fix: Q24 and Q51 (construction) still miss for the same
   underlying reason in round 4's evidence pool, and Q30's true-content-wrong-scheme case is a
   different mechanism entirely (see item 10). An eval-only scheme-filtered diagnostic was
   attempted earlier to isolate this effect (`scripts/diagnostic_scheme_filtered_verify.py`) but
   never finished (Windows DLL environment issue) — no longer needed, since the practical question
   it was built to answer has now been answered more directly by shipped fixes.
5. **Not fixable by more engineering — the genuine LLM-judge misjudgment.** Q42's caste-certificate
   claim: correct evidence, wrong verdict anyway. A real reliability ceiling on the LLM-as-judge
   approach (ADR-001), disclosed as a limitation of the method in the final report, not chased as
   a bug. Not re-tested against Claude specifically, since the original Groq-based `verifier_results.csv`
   snapshot that surfaced it is no longer the active run.
6. **Still open — decomposition granularity/consistency issues.** Q10's bundled numeric-fact +
   generalization claim (unchanged since round 2 despite the LLM decomposer fixing this exact
   pattern for other claims, e.g. Q49). `decompose_llm()` also isn't perfectly stable run-to-run on
   identical input (ADR-021's Q2 negation-drop finding) — a genuinely new, smaller-scope version of
   the old rule-based decomposer's inconsistency, not eliminated by switching to an LLM.
7. **Done — extended data-granularity fix.** PM-KISAN's and PM Awas Yojana's remaining oversized
   rows split into 18 more atomic facts (`scripts/split_more_oversized_rows.py`, ADR-019).
   Confirmed it doesn't fix Q2/Q3/Q44's specific false negatives (checked first — those facts live
   in already-reasonably-sized rows), pursued anyway as a general data-quality improvement.
8. **Done — majority-vote judging.** `verify_claim()` now takes the majority of 3 independent
   judge calls (ADR-020), added after directly proving the judge isn't fully deterministic even at
   `temperature=0`. Kept through the model switch (ADR-021) — still 3 samples per claim, now on
   Claude.
9. **Done — switched Groq → Claude.** Escaped Groq's daily-quota ceiling that had repeatedly
   paused full evaluation runs across multiple days; also required fixing two integration bugs
   (removed `temperature` param, fence-wrapped JSON responses) and a decomposition-prompt
   correctness issue (a qualifier-splitting bug caught by manual testing before rollout) — see
   ADR-021 for the full debugging account.
10. **Still open — true-content-wrong-scheme attribution (Q30).** A fact that's genuinely true
    somewhere in the dataset gets presented as belonging to the wrong scheme's answer, and every
    version of this verifier checks claim-vs-evidence, not claim-vs-question-scheme, so it verifies
    as supported regardless of evidence quality. Would need a structurally different check (e.g.
    comparing the evidence's source scheme against the question's declared scheme) — not attempted.
11. **Done — fixed a genuine data corruption bug.** `data/schemes/PM-KISAN.csv`'s "exclusion
    criteria" row had a mismatched body (duplicate of an unrelated fact), sourced from the same
    malformed PDF as P-007. Found while diagnosing ADR-021's context-only regression, fixed
    directly, matching P-007's precedent for hand-patching confirmed source corruption.

The honest summary: nine fixes shipped across three post-submission cycles. The first cycle's four
fixes were three unambiguously net-positive plus one that regressed a headline metric on first
release, diagnosed precisely and repaired rather than reverted. The second cycle (extended
data-granularity fix + majority-vote judging) was a wash relative to that point — kept for sound
engineering reasons, not a demonstrated score gain. The third cycle (Claude switch + LLM
decomposition + hybrid evidence retrieval + a data fix) is the first to move precision and recall
together, landing at **0.27 precision / 0.71 recall**, the best simultaneous result recorded
anywhere in this project — beating even the very first pre-fix baseline. What's left open is
bounded and named, not hand-waved: a still-inconsistent decomposer on bundled claims (Q10),
true-content-wrong-scheme attribution needing a structurally different check (Q30), a
document-structure scope mismatch the verifier has no representation for (Q49), and one confirmed
case where the method itself, not the engineering around it, is the limit (Q42).
