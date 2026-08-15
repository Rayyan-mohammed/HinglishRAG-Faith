# Problems and Decisions Log

Running log. Append new entries at the bottom of each section, don't rewrite history.

## Architecture Decisions

### ADR-001: Same model (Groq llama-3.3-70b-versatile) for both generation and verification
**Decision:** Use one Groq-hosted model for both answering the question and judging claims against evidence, with separate prompts for each role.
**Why:** Free tier, no GPU, one API key to manage, fast enough to run 50-80 questions in minutes.
**Impact:** Open risk — a model may be more likely to rate its own generation style as supported (self-verification bias). Not corrected for; worth checking during error analysis (Week 4) whether missed hallucinations cluster around a particular phrasing style.

### ADR-002: BAAI/bge-m3 as the sole embedding model, run locally
**Decision:** One pretrained multilingual embedding model for all retrieval (question-level and per-claim), no fine-tuning.
**Why:** Handles Hindi-English mixed text out of the box; free; no training budget or GPU in scope.
**Impact:** Retrieval quality is whatever bge-m3 gives on Hinglish — not tunable within the project. A retrieval failure and a verification failure will look identical from the outside unless logged separately.

### ADR-003: Rule-based claim decomposition (sentence boundaries + connector-word list)
**Decision:** Split generated answers into atomic claims with regex sentence splitting plus a fixed connector-word list (aur, lekin, but, however, ...), not a trained parser.
**Why:** Transparent, debuggable, sufficient at this scale; a full parser is unnecessary engineering for a 4-week course project.
**Impact:** Known failure mode — will mis-split some code-mixed sentences. Mitigation is manual review of decomposition output during Week 3 (see B3) and adjusting the connector list, not a general fix.

### ADR-004: FAISS flat index (in-memory, local), no vector DB server
**Decision:** `IndexFlatIP` over normalized embeddings, rebuilt from scratch by `scripts/build_index.py`.
**Why:** 3-5 documents means brute-force cosine similarity is instant; a server-backed vector DB would be pure overhead.
**Impact:** Doesn't scale past course-project size — fine here, would need revisiting for more documents.

### ADR-005: Per-claim retrieval, not reuse of the question-level retrieval
**Decision:** Stage 4 re-queries the index with each individual claim rather than reusing the passages retrieved for the original question.
**Why:** The passage that best supports the whole answer isn't always the passage that supports any one claim inside it.
**Impact:** Doubles retrieval calls per question (cheap, local) but adds a second retrieval failure mode to account for during error analysis — a claim can be correct but get flagged wrong because per-claim retrieval missed the right passage.

### ADR-006: Single annotator for the 50-80 question ground-truth set
**Decision:** Partner B hand-labels every generated answer (fully correct / partially hallucinated / fully hallucinated) alone.
**Why:** Team of 2 at course-project scale; coordinating a second labeller for inter-annotator agreement isn't in the 4-week budget.
**Impact:** No inter-annotator agreement number. Disclosed as a limitation in the final report rather than hidden. Consider re-reviewing a random sample of labels a second time before finalizing (see risk table in blueprint Section 17).

### ADR-007: uv + pyproject.toml for dependency management
**Decision:** Project dependencies declared in `pyproject.toml`, resolved and locked with `uv` (`uv.lock`), no `requirements.txt`.
**Why:** Reproducible lockfile, faster installs than pip, single tool for venv + deps + running scripts.
**Impact:** Contributors need `uv` installed. `uv run pytest` doesn't work on this machine due to a Windows Application Control policy blocking `pytest.exe` — use `uv run python -m pytest` instead.

### ADR-008: `config/` package separated from `src/` pipeline code
**Decision:** All settings (model names, paths, API key loading) live in `config/settings.py`, imported by `src/*.py`, not inlined.
**Why:** Keeps model/version choices and paths in one place instead of scattered across pipeline modules.
**Impact:** One extra import line per module; negligible cost for the clarity.

### ADR-009: Fixed scheme list — PM-KISAN, Ayushman Bharat, Post-Matric Scholarship, PM Awas Yojana
**Decision:** These 4 schemes, chosen upfront so Track B could start writing evaluation questions in Week 1 without waiting on Track A's document collection.
**Why:** All well-known, high-traffic .gov.in schemes with clear eligibility/deadline/amount/document facts to ask about; matches the blueprint's example set in Section 12. 4 schemes keeps the 60-question set balanced at 15 questions each.
**Impact:** Track A's Week 1 document collection (A1) should target exactly these 4, using these names, so `eval/questions.csv`'s `scheme` column joins cleanly to `data/schemes/` once built.

### ADR-010: `judge()` split out from `verify_claim()` in `src/verification.py`
**Decision:** The LLM-as-judge prompt call now takes `(claim, evidence_text)` directly, with `verify_claim()` doing retrieval and then calling `judge()`.
**Why:** B1 needs to test the verifier prompt on 5 hand-written claim/evidence pairs before any retrieval index exists. Splitting the functions means that test doesn't need a fake index or fake passages.
**Impact:** None to existing behavior — `verify_claim()`'s output is unchanged, just calls through `judge()` now.

## Problems Encountered

No problems logged yet. Add entries as they come up, in this format:

### P-001: [short title]
**Week:**
**Problem:**
**Fix:**
**Lesson:**
