"""Builds the FAISS index from the per-scheme CSVs in data/schemes/. Run this after updating
the dataset (e.g. via scripts/fetch_scheme_data.py)."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.retrieval import build_index

if __name__ == "__main__":
    index, passages = build_index()
    print(f"Indexed {len(passages)} facts from data/schemes/*.csv")
