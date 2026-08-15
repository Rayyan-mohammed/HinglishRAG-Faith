"""Fetches the 4 government scheme facts live from their official .gov.in sources and writes
data/schemes/scheme_facts.csv. Run this to (re)build the dataset directly from source.

Sources:
  PM-KISAN                 -> pmkisan.gov.in (Operational Guidelines PDF)
  Ayushman Bharat           -> ayushmanbharat.haryana.gov.in (official FAQ page)
  PM Awas Yojana            -> pmay-urban.gov.in (official FAQ page)
  Post-Matric Scholarship   -> sewa.haryana.gov.in (Scheme of Post Matric Scholarship PDF)
"""

import csv
import html
import io
import re
import sys
import urllib.request
from pathlib import Path

from pypdf import PdfReader

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config.settings import SCHEMES_DIR

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CodeSwitchVerify/1.0)"}

SOURCES = {
    "PM-KISAN": {
        "url": "https://pmkisan.gov.in/Documents/RevisedPM-KISANOperationalGuidelines(English).pdf",
        "type": "pdf",
        "start": "1. Scheme",
        "end": "*******",
    },
    "Ayushman Bharat": {
        "url": "https://ayushmanbharat.haryana.gov.in/frequently-asked-questions/",
        "type": "faq",
        "start": "Frequently Asked Questions under Ayushman Bharat",
        "end": "Website Policies",
    },
    "PM Awas Yojana": {
        "url": "https://pmay-urban.gov.in/faq",
        "type": "faq",
        "start": "1. What is Pradhan Mantri Awas Yojana",
        "end": "Address",
    },
    "Post-Matric Scholarship": {
        "url": "https://cdnbbsr.s3waas.gov.in/s3229754d7799160502a143a72f6789927/uploads/2023/02/2023020129-1.pdf",
        "type": "pdf",
        "start": "I. Object",
        "end": "References",
    },
}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def html_to_lines(raw_bytes):
    text = raw_bytes.decode("utf-8", errors="ignore")
    text = re.sub(r"<script[\s\S]*?</script>", " ", text)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = html.unescape(text)
    return [line.strip() for line in text.split("\n") if line.strip()]


def pdf_to_lines(raw_bytes):
    reader = PdfReader(io.BytesIO(raw_bytes))
    lines = []
    for page in reader.pages:
        for line in (page.extract_text() or "").split("\n"):
            s = line.strip()
            if s and not re.fullmatch(r"\d{1,3}", s):
                lines.append(s)
    return lines


def slice_between(lines, start_marker, end_marker):
    start_idx = next(i for i, l in enumerate(lines) if l.startswith(start_marker))
    end_idx = next(
        (i for i in range(start_idx, len(lines)) if lines[i].startswith(end_marker)), len(lines)
    )
    return lines[start_idx:end_idx]


def parse_faq(lines):
    """'N. Question...?' followed by answer lines until the next numbered question.
    Requires the line to end in '?' so numbered sub-lists inside an answer (e.g. '1. In-situ
    Slum Redevelopment (ISSR)') aren't mistaken for a new question."""
    q_re = re.compile(r"^(\d{1,2})\.\s+(.+\?)$")
    rows, i = [], 0
    while i < len(lines):
        m = q_re.match(lines[i])
        if not m:
            i += 1
            continue
        question = m.group(2)
        i += 1
        answer_lines = []
        while i < len(lines) and not q_re.match(lines[i]):
            answer_lines.append(lines[i])
            i += 1
        rows.append(f"{question} {' '.join(answer_lines)}")
    return rows


def parse_sections(lines):
    """Numbered/lettered clause headers (e.g. '4 Exclusions', 'V. Value of Scholarship')
    followed by their body text, one fact per clause."""
    header_re = re.compile(r"^([0-9]{1,2}\.?|[IVX]{1,4}\.)\s+[A-Z][A-Za-z' ,&()/-]{2,60}$")
    rows, i = [], 0
    while i < len(lines):
        if not header_re.match(lines[i]):
            i += 1
            continue
        header = lines[i]
        i += 1
        body_lines = []
        while i < len(lines) and not header_re.match(lines[i]):
            body_lines.append(lines[i])
            i += 1
        body = " ".join(body_lines).strip()
        if body:
            rows.append(f"{header} {body}")
    return rows


def categorize(text):
    t = text.lower()
    if "rs." in t or "₹" in t or "lakh" in t or "allowance" in t:
        return "amount"
    if "document" in t or "certificate" in t or "aadhaar" in t or "card" in t:
        return "documents"
    if re.search(r"\bdate\b|deadline|cut-off|announce|last date", t):
        return "deadline"
    if "eligib" in t or "beneficiary" in t or "family" in t or "exclu" in t:
        return "eligibility"
    return "process"


def collect(cfg):
    raw = fetch(cfg["url"])
    lines = pdf_to_lines(raw) if cfg["type"] == "pdf" else html_to_lines(raw)
    section = slice_between(lines, cfg["start"], cfg["end"])
    facts = parse_faq(section) if cfg["type"] == "faq" else parse_sections(section)
    return [
        {"category": categorize(f), "fact": f, "source_url": cfg["url"]}
        for f in facts
        if len(f) > 20
    ]


if __name__ == "__main__":
    out_dir = Path(SCHEMES_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    for scheme, cfg in SOURCES.items():
        rows = collect(cfg)
        print(f"{scheme}: {len(rows)} facts from {cfg['url']}")

        out_path = out_dir / f"{scheme}.csv"
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["category", "fact", "source_url"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"  wrote {out_path}")
