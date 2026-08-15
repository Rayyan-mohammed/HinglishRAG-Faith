import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

GENERATOR_MODEL = "llama-3.3-70b-versatile"
VERIFIER_MODEL = "llama-3.3-70b-versatile"
EMBEDDING_MODEL = "BAAI/bge-m3"

DATA_DIR = "data/schemes"
INDEX_DIR = "index"
EVAL_DIR = "eval"

TOP_K = 4
