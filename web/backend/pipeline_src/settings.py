import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Optional additional keys (e.g. from separate accounts) so the demo can fail over to another
# key's quota instead of erroring out when one key hits Groq's free-tier daily limit.
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
DECOMPOSER_MODEL = "openai/gpt-oss-120b"
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-m3")

SCHEMES_DIR = "data/schemes"
INDEX_DIR = "index"
EVAL_DIR = "eval"

TOP_K = 4
