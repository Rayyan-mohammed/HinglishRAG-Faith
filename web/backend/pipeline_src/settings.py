import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

GENERATOR_MODEL = "claude-haiku-4-5"
VERIFIER_MODEL = "claude-haiku-4-5"
DECOMPOSER_MODEL = "claude-haiku-4-5"
EMBEDDING_MODEL = "BAAI/bge-m3"

SCHEMES_DIR = "data/schemes"
INDEX_DIR = "index"
EVAL_DIR = "eval"

TOP_K = 4
