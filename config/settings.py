import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Switched from Groq (openai/gpt-oss-120b) to Claude in ADR-021 -- Groq's 200k-tokens/day
# free-tier ceiling repeatedly paused full evaluation runs across several days, even with the
# multi-key failover ADR-016 added for it. Haiku 4.5 is cheap enough for this workload's volume
# (a few hundred short classification-shaped calls) to cost well under a dollar.
GENERATOR_MODEL = "claude-haiku-4-5"
VERIFIER_MODEL = "claude-haiku-4-5"
DECOMPOSER_MODEL = "claude-haiku-4-5"
EMBEDDING_MODEL = "BAAI/bge-m3"

SCHEMES_DIR = "data/schemes"
INDEX_DIR = "index"
EVAL_DIR = "eval"

TOP_K = 4
