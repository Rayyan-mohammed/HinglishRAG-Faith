# CodeSwitch-Verify

Faithfulness-checked RAG for Hinglish government-scheme Q&A.

A RAG chatbot answers questions about Indian government schemes in Hinglish. Every generated
answer is broken into individual claims, and each claim is checked against the retrieved source
text before being shown to the user, so unsupported claims get flagged instead of trusted blindly.

## Pipeline

1. Retrieve relevant passages for the question (bge-m3 + FAISS)
2. Generate a Hinglish answer grounded in those passages (Groq)
3. Decompose the answer into atomic claims
4. Retrieve evidence again, per claim
5. Verify each claim against its evidence (LLM-as-judge)
6. Show the answer with each claim tagged supported / contradicted / unverifiable

## Setup

```
uv sync
cp .env.example .env   # add your Groq API key
```

Add scheme documents (plain text) to `data/schemes/`, then build the index:

```
uv run scripts/build_index.py
```

Run tests:

```
uv run pytest
```

## Project layout

```
config/         settings (model names, paths, API key loading)
src/            pipeline code (retrieval, generation, decomposition, verification, evaluation)
scripts/        CLI entry points
tests/          unit tests
data/schemes/   source government scheme documents
eval/           hand-labelled evaluation set
docs/           project blueprint and planning docs (not pushed)
```

## Status

Week 1: project scaffold + retrieval/generation/verification skeleton in place. Scheme documents
and the evaluation question set are next.
