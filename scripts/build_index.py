"""Builds the FAISS index from documents in data/schemes/. Run this after adding scheme docs."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.retrieval import build_index

if __name__ == "__main__":
    index, passages = build_index()
    print(f"Indexed {len(passages)} passages from data/schemes/")
