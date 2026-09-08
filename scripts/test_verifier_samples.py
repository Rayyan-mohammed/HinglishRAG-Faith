"""Week 1 (B1): sanity-check the verifier prompt on 5 hand-written claim/evidence pairs.
Needs a real ANTHROPIC_API_KEY in .env to run."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.verification import judge

SAMPLES = [
    {
        "claim": "PM-KISAN scheme mein har saal 6000 rupees milte hain.",
        "evidence": "Under PM-KISAN, an amount of Rs.6,000/- per year is transferred in three "
        "equal installments of Rs.2,000 each every four months.",
        "expected": "SUPPORTED",
    },
    {
        "claim": "PM-KISAN ke liye Aadhaar card zaroori nahi hai.",
        "evidence": "Aadhaar is mandatory for availing benefits under the PM-KISAN scheme, "
        "except in the states of Assam, Meghalaya and Jammu & Kashmir.",
        "expected": "CONTRADICTED",
    },
    {
        "claim": "Ayushman Bharat scheme 5 lakh rupees tak ka free treatment deta hai.",
        "evidence": "Ayushman Bharat PM-JAY provides a health cover of Rs. 5 lakh per family "
        "per year for secondary and tertiary care hospitalization.",
        "expected": "SUPPORTED",
    },
    {
        "claim": "Ayushman Bharat card sirf government hospitals mein use ho sakta hai.",
        "evidence": "Treatment under PM-JAY is available at both empanelled public and private "
        "hospitals across India.",
        "expected": "CONTRADICTED",
    },
    {
        "claim": "Scholarship application ke liye income certificate submit karna padta hai.",
        "evidence": "Applicants must upload a valid income certificate issued by the competent "
        "authority along with the application form.",
        "expected": "SUPPORTED",
    },
]


if __name__ == "__main__":
    correct = 0
    for i, sample in enumerate(SAMPLES, start=1):
        result = judge(sample["claim"], sample["evidence"])
        match = result.get("verdict") == sample["expected"]
        correct += match
        print(f"[{i}] claim: {sample['claim']}")
        print(
            f"    expected: {sample['expected']}  got: {result.get('verdict')}  "
            f"confidence: {result.get('confidence')}  {'OK' if match else 'MISMATCH'}"
        )
    print(f"\n{correct}/{len(SAMPLES)} matched expected verdict")
