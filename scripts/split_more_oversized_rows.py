"""Second pass extending ADR-015's row-splitting fix (which only covered Post-Matric
Scholarship's worst row) to the remaining oversized rows found in PM-KISAN.csv and
PM Awas Yojana.csv -- see docs/error_analysis.md's "what's still open" list and the follow-up
ADR in docs/problems_and_decisions.md.

Each replacement condenses administrative/procedural bulk into fewer, denser facts while keeping
every consumer-relevant sub-fact (eligibility, amount, deadline, documents) as its own row --
matching the same rationale as ADR-015: reduce how much a single row's embedding gets diluted by
unrelated sub-topics crammed into one PDF section."""

import csv

PM_KISAN_PATH = "data/schemes/PM-KISAN.csv"
PM_KISAN_URL = "https://pmkisan.gov.in/Documents/RevisedPM-KISANOperationalGuidelines(English).pdf"

PMAY_PATH = "data/schemes/PM Awas Yojana.csv"
PMAY_URL = "https://pmay-urban.gov.in/uploads/guidelines/Operational-Guidelines-of-PMAY-U-2.pdf"

PM_KISAN_REPLACEMENTS = {
    # row 3: "5. Methodology for calculation of benefit" (8616 chars)
    "5. Methodology for calculation of benefit": [
        ("eligibility", "Benefit is paid only to farmers' families whose names are entered in land records. The cut-off date for determining eligibility is 01.02.2019, and no changes after this date are considered for the next 5 years, except when land ownership transfers due to succession after the landowner's death."),
        ("eligibility", "If cultivable land ownership transfers due to succession following the landowner's death, the successor's family remains entitled to PM-KISAN benefits, subject to meeting the scheme's other conditions and exclusion criteria."),
        ("amount", "If cultivable land ownership transferred between 01.12.2018 and 31.01.2019 due to purchase, succession, will, or gift, the first installment for that period is a proportionate amount calculated from the date of transfer."),
        ("eligibility", "If cultivable land is sold or transferred to another person after 01.02.2019 for reasons other than inheritance, the new owner (transferee) is not eligible for benefits, since they did not own the land as of the cut-off date. If the original owner's family has no remaining cultivable land after the transfer, they also become ineligible."),
        ("documents", "State/UT Governments are responsible for correcting land records to reflect inheritance-based ownership changes, and for updating the PM-KISAN portal so benefits continue for eligible successors or are discontinued for families no longer eligible."),
        ("eligibility", "In some North-Eastern states with community-based land ownership (e.g. Manipur, Nagaland), alternate certification via village council/chief, verified by administrative officers, is used to identify eligible beneficiaries instead of standard land records, subject to the scheme's usual exclusion criteria. A similar lineage-based (Vanshavali) verification process applies in Jharkhand."),
    ],
    # row 6: "8. Setting up of Project Monitoring Unit (PMU)" (5525 chars)
    "8. Setting up of Project Monitoring Unit (PMU)": [
        ("process", "A Project Monitoring Unit (PMU) at the central level, under the Department of Agriculture, Cooperation & Farmers Welfare, is responsible for overall monitoring and publicity of the scheme. State/UT Governments may set up similar units, partly funded (0.125% of transferred installment amounts) by the Central Government for administrative expenses."),
        ("documents", "The PM-KISAN Portal (pmkisan.gov.in) is used by State/UT Governments to upload beneficiary details. Required farmer attributes include State, District, Village, Farmer Name, Aadhaar Number (or enrollment number), Gender, Category, IFSC Code, and Bank Account Number; optional attributes include Father's Name, Address, Mobile Number, and Date of Birth."),
    ],
    # row 7: "10 Modalities for transfer of benefit" (6078 chars)
    "10 Modalities for transfer of benefit": [
        ("amount", "The Rs.6000/year benefit is released in 3 installments of Rs.2000 each every 4-month trimester: April-July, August-November, and December-March."),
        ("documents", "Benefit transfer requires an Aadhaar-linked bank account. Aadhaar number is mandatory for all beneficiaries for installments from the December 2019-March 2020 trimester onwards, except Assam, Meghalaya, and Jammu & Kashmir, which were exempted till 31.3.2021."),
        ("process", "The financial benefit is transferred via Direct Benefit Transfer (DBT) from the Central Government through the states' designated sponsoring banks to beneficiaries' bank accounts, using the PFMS (Public Financial Management System) portal. Beneficiaries are notified of credited amounts via SMS."),
        ("process", "Beneficiary lists are displayed at Panchayats for transparency. States/UTs are expected to check the eligibility of around 5% of beneficiaries during the year."),
    ],
}

PMAY_REPLACEMENTS = {
    # row 52: "5.2.16 The AHP vertical of the Scheme is a supply side intervention..." (8847 chars)
    "5.2.16 The AHP vertical of the Scheme is a supply side intervention": [
        ("eligibility", "The Affordable Housing in Partnership (AHP) vertical has two models: Model-1, construction of houses by public sector agencies and parastatals on encumbrance-free land they own; and Model-2, construction by private developers on their own encumbrance-free land, with beneficiaries purchasing from the open market."),
        ("documents", "Under Model-1 (public sector AHP), projects require ownership documents and a Detailed Project Report (DPR) covering housing and related infrastructure, approved by SLAC then SLSMC before being forwarded to CSMC for Central Assistance."),
        ("process", "Under Model-1, states may propose 'Redevelopment' or 'In-situ Improvement' of tenable slums with dilapidated buildings on government/ULB/public land, or 'Resettlement' of untenable slums from environmentally hazardous sites to alternate locations with civic amenities."),
        ("amount", "Central Assistance under AHP Model-1 is released to implementing agencies in three installments in a 40:40:20 ratio based on project progress; the remaining project cost is borne by the beneficiary, with States/UTs facilitating concessional home loans."),
        ("documents", "Under Model-2 (private sector AHP), developers submit project proposals to the ULB for scrutiny, then SLSMC approval for 'whitelisting', followed by CSMC sanctioning; whitelisted projects are listed on the Unified Web Portal for eligible beneficiaries to apply."),
        ("amount", "Under Model-2, Central Assistance is provided to EWS category beneficiaries as Redeemable Housing Vouchers (RHV), issued in the beneficiary's name upon verified occupancy and redeemed by the developer; States also contribute their financial share toward the housing voucher."),
    ],
}


def apply_replacements(path, url, replacements):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    total_replaced = 0
    for prefix, new_facts in replacements.items():
        idx = next((i for i, r in enumerate(rows) if r["fact"].startswith(prefix)), None)
        if idx is None:
            print(f"  WARNING: row starting with {prefix!r} not found -- already split, or source changed")
            continue
        original_len = len(rows[idx]["fact"])
        replacement_rows = [{"category": cat, "fact": fact, "source_url": url} for cat, fact in new_facts]
        rows[idx : idx + 1] = replacement_rows
        # re-scan from the same position onward since indices shifted
        rows = rows  # (list already mutated in place via slice assignment)
        total_replaced += 1
        print(f"  replaced {original_len} chars with {len(replacement_rows)} atomic facts ({prefix[:50]}...)")

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "fact", "source_url"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"{path}: {total_replaced} oversized rows replaced, {len(rows)} total rows now")


def main():
    print("PM-KISAN.csv:")
    apply_replacements(PM_KISAN_PATH, PM_KISAN_URL, PM_KISAN_REPLACEMENTS)
    print()
    print("PM Awas Yojana.csv:")
    apply_replacements(PMAY_PATH, PMAY_URL, PMAY_REPLACEMENTS)


if __name__ == "__main__":
    main()
