import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

GENERATOR_MODEL = "openai/gpt-oss-120b"
VERIFIER_MODEL = "openai/gpt-oss-120b"
EMBEDDING_MODEL = "BAAI/bge-m3"

SCHEMES_DIR = "data/schemes"
INDEX_DIR = "index"
EVAL_DIR = "eval"

TOP_K = 4
