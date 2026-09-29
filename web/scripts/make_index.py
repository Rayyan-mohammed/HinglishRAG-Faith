"""Pre-build the FAISS index and bake it into the image at web/prebuilt_index/.

Skips re-embedding all ~200 scheme facts on every cold start -- that embedding pass plus loading
bge-m3 itself was pushing total startup past CloudFront's origin read timeout. Run this whenever
data/schemes/*.csv changes, before `docker build`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from pipeline_src.retrieval import build_index  # noqa: E402

WEB_ROOT = Path(__file__).resolve().parent.parent
out = WEB_ROOT / "prebuilt_index"
build_index(schemes_dir=str(WEB_ROOT / "data" / "schemes"), index_dir=str(out))
print("saved to", out)
