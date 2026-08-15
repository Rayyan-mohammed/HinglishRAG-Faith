"""Fetches the 4 government scheme facts live from their official .gov.in sources and writes
data/schemes/scheme_facts.csv. Run this to (re)build the dataset directly from source.

Each scheme can have more than one source document; facts from all of them are concatenated
into that scheme's CSV.

Sources:
  PM-KISAN                 -> pmkisan.gov.in (Operational Guidelines, Revised FAQ, Additional FAQ)
  Ayushman Bharat           -> ayushmanbharat.haryana.gov.in (FAQ page, Benefits page)
  PM Awas Yojana            -> pmay-urban.gov.in (FAQ page, PMAY-U 2.0 Operational Guidelines PDF)
  Post-Matric Scholarship   -> sewa.haryana.gov.in (guidelines PDF), sjsa.maharashtra.gov.in (page)
"""

import csv
import html
import http.client
import io
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

from pypdf import PdfReader

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config.settings import SCHEMES_DIR

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CodeSwitchVerify/1.0)"}

SOURCES = {
    "PM-KISAN": [
        {
            "url": "https://pmkisan.gov.in/Documents/RevisedPM-KISANOperationalGuidelines(English).pdf",
            "type": "sections",
            "doc": "pdf",
            "start": "1. Scheme",
            "end": "*******",
        },
        {
            "url": "https://pmkisan.gov.in/Documents/RevisedFAQ.pdf",
            "type": "faq",
            "doc": "pdf",
            "start": "1. What is Pradhan Mantri",
            "end": "",
        },
        {
            "url": "https://pmkisan.gov.in/Documents/ADDITIONAL-FAQ-IN-RESPECTIVE-OF-THE-PM2.pdf",
            "type": "numbered",
            "doc": "pdf",
            "start": "1. There is no distinction",
            "end": "",
        },
    ],
    "Ayushman Bharat": [
        {
            "url": "https://ayushmanbharat.haryana.gov.in/frequently-asked-questions/",
            "type": "faq",
            "doc": "html",
            "start": "Frequently Asked Questions under Ayushman Bharat",
            "end": "Website Policies",
        },
        {
            "url": "https://ayushmanbharat.haryana.gov.in/benefits-of-ab-pmjay/",
            "type": "bullets",
            "doc": "html",
            "start": "BENEFICIARY LEVEL",
            "end": "Website Policies",
        },
    ],
    "PM Awas Yojana": [
        {
            "url": "https://pmay-urban.gov.in/faq",
            "type": "faq",
            "doc": "html",
            "start": "1. What is Pradhan Mantri Awas Yojana",
            "end": "Address",
        },
        {
            "url": "https://pmay-urban.gov.in/uploads/guidelines/Operational-Guidelines-of-PMAY-U-2.pdf",
            "type": "clauses",
            "doc": "pdf",
            "start": "5.1.1",
            "end": "",
            "limit": 40,
        },
    ],
    "Post-Matric Scholarship": [
        {
            "url": "https://cdnbbsr.s3waas.gov.in/s3229754d7799160502a143a72f6789927/uploads/2023/02/2023020129-1.pdf",
            "type": "sections",
            "doc": "pdf",
            "start": "I. Object",
            "end": "References",
        },
        {
            "url": "https://sjsa.maharashtra.gov.in/en/scheme/post-matric-scholarship-by-the-government-of-india/",
            "type": "bullets",
            "doc": "html",
            "start": "Funding Source",
            "end": "Feedback",
        },
    ],
}


def fetch(url, retries=3):
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read()
        except (urllib.error.URLError, http.client.IncompleteRead):
            if attempt == retries - 1:
                raise


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
    start_idx = next((i for i, l in enumerate(lines) if l.startswith(start_marker)), 0)
    end_idx = (
        next(
            (i for i in range(start_idx, len(lines)) if lines[i].startswith(end_marker)),
            len(lines),
        )
        if end_marker
        else len(lines)
    )
    return lines[start_idx:end_idx]


def parse_faq(lines):
    """'N. Question...?' followed by its answer, up to the next numbered question. Works on the
    whole section as one text blob (not line-by-line) so a question or answer that wraps across
    PDF/HTML line breaks is still captured correctly. Requires the question to end in '?' so
    numbered sub-lists inside an answer (e.g. '1. In-situ Slum Redevelopment (ISSR)') aren't
    mistaken for a new question."""
    blob = re.sub(r"\s+", " ", " ".join(lines)).strip()
    q_re = re.compile(r"(?:^|(?<=\s))(\d{1,2})\.\s+([A-Z].{3,200}?\?)")
    matches = list(q_re.finditer(blob))
    rows = []
    for i, m in enumerate(matches):
        question = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(blob)
        answer = blob[start:end].strip()
        if answer:
            rows.append(f"{question} {answer}")
    return rows


def parse_bullets(lines):
    """Each line is already one self-contained fact (used for bullet-point pages)."""
    return [l for l in lines if len(l) > 20]


def parse_numbered(lines):
    """Plain numbered statements (e.g. '4. The cut-off date for minor children...'), not
    questions. Blob-based like parse_faq, split on 'N. ' markers."""
    blob = re.sub(r"\s+", " ", " ".join(lines)).strip()
    marker_re = re.compile(r"(?:^|(?<=\s))(\d{1,2})\.\s+(?=[A-Z])")
    matches = list(marker_re.finditer(blob))
    rows = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(blob)
        text = blob[start:end].strip()
        if text:
            rows.append(text)
    return rows


def parse_clauses(lines):
    """Decimal-numbered clauses (e.g. '5.1.6 The implementing agencies shall...') used in dense
    guideline PDFs with a legal-clause numbering scheme. Blob-based like parse_faq, so a clause
    that wraps across a PDF line/page break is still captured whole."""
    blob = re.sub(r"\s+", " ", " ".join(lines)).strip()
    marker_re = re.compile(r"(?:^|(?<=\s))(\d{1,2}\.\d{1,2}(?:\.\d{1,2})?)\s+(?=[A-Z])")
    matches = list(marker_re.finditer(blob))
    rows = []
    for i, m in enumerate(matches):
        marker = m.group(1)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(blob)
        text = blob[start:end].strip()
        if text:
            rows.append(f"{marker} {text}")
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


PARSERS = {
    "faq": parse_faq,
    "sections": parse_sections,
    "bullets": parse_bullets,
    "numbered": parse_numbered,
    "clauses": parse_clauses,
}


def collect(cfg):
    raw = fetch(cfg["url"])
    lines = pdf_to_lines(raw) if cfg["doc"] == "pdf" else html_to_lines(raw)
    section = slice_between(lines, cfg["start"], cfg["end"])
    facts = PARSERS[cfg["type"]](section)
    facts = [f for f in facts if len(f) > 20]
    if "limit" in cfg:
        facts = facts[: cfg["limit"]]
    return [{"category": categorize(f), "fact": f, "source_url": cfg["url"]} for f in facts]


if __name__ == "__main__":
    out_dir = Path(SCHEMES_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    for scheme, source_list in SOURCES.items():
        rows = []
        for cfg in source_list:
            cfg_rows = collect(cfg)
            print(f"{scheme}: {len(cfg_rows)} facts from {cfg['url']}")
            rows.extend(cfg_rows)

        out_path = out_dir / f"{scheme}.csv"
        with open(out_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["category", "fact", "source_url"])
            writer.writeheader()
            writer.writerows(rows)
        print(f"  wrote {len(rows)} total facts to {out_path}")
