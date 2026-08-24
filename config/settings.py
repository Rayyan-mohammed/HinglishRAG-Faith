import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Optional additional keys (e.g. from separate accounts) so a long batch run can fail over
# to another key's quota instead of waiting out one key's daily limit -- see P-001/P-008.
# Add GROQ_API_KEY_2, GROQ_API_KEY_3, ... to .env; only non-empty ones are used.
GROQ_API_KEYS = [
    k
    for k in [
        GROQ_API_KEY,
        os.environ.get("GROQ_API_KEY_2"),
        os.environ.get("GROQ_API_KEY_3"),
        os.environ.get("GROQ_API_KEY_4"),
    ]
    if k
]

GENERATOR_MODEL = "openai/gpt-oss-120b"
VERIFIER_MODEL = "openai/gpt-oss-120b"
EMBEDDING_MODEL = "BAAI/bge-m3"

SCHEMES_DIR = "data/schemes"
INDEX_DIR = "index"
EVAL_DIR = "eval"

TOP_K = 4
