# Demo

Working demo for Objective O6: takes a Hinglish question, shows the generated answer with
each claim tagged supported / contradicted / unverifiable.

Started in A3 (skeleton: question in, answer out) — done. Finished in A4 (claim tags added) —
not yet, waiting on B's verifier wiring (B1) landing in `src/pipeline.py`'s `verify=True` path.

Framework: Streamlit (`demo/app.py`), fastest to wire to `src/pipeline.answer_question()` at
this scale. Run it with:

```
uv run streamlit run demo/app.py
```

The file watcher is disabled in `.streamlit/config.toml` — with `sentence-transformers`/
`transformers` installed, Streamlit's default watcher repeatedly scans that package's entire
(large) submodule tree on every file-change check, which was slow enough to noticeably delay
the page mounting. Not needed anyway since this isn't a live-reload dev workflow.
