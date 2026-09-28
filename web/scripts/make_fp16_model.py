"""Save a half-precision copy of bge-m3 to web/models/bge-m3-fp16.

Lambda on this account is capped at 3008MB; loading the stock fp32 model (and converting at
load time) peaks past that. A pre-converted fp16 copy is ~1.1GB and loads directly.
Run once before `docker build`; the folder is copied into the image but not committed.
"""
from pathlib import Path

import torch
from sentence_transformers import SentenceTransformer

out = Path(__file__).resolve().parent.parent / "models" / "bge-m3-fp16"
model = SentenceTransformer("BAAI/bge-m3", model_kwargs={"torch_dtype": torch.float16})
model.save(str(out))
print("saved to", out)
