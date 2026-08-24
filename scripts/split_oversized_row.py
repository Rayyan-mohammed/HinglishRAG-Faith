"""One-off fix (P-008 follow-up): splits the oversized "V. Value of Scholarship" row in
Post-Matric Scholarship.csv into atomic sub-facts. That single row (11,268 chars) diluted
retrieval so badly that the Group I-IV maintenance allowance table it contains never got
surfaced for claims specifically about it -- confirmed in P-008's evidence-text diagnosis.
Not part of scripts/fetch_scheme_data.py since this is a manual data-quality fix, not something
the live-fetch parser produces -- see docs/problems_and_decisions.md."""

import csv

PATH = "data/schemes/Post-Matric Scholarship.csv"
SOURCE_URL = "https://cdnbbsr.s3waas.gov.in/s3229754d7799160502a143a72f6789927/uploads/2023/02/2023020129-1.pdf"

REPLACEMENT_FACTS = [
    (
        "amount",
        "V. Value of Scholarship: the scholarship covers maintenance allowance, "
        "reimbursement of compulsory non-refundable fees, study tour charges, thesis "
        "typing/printing charges for research scholars, book allowance for correspondence "
        "course students, book bank facility for specified courses, and additional "
        "allowance for students with disabilities, for the complete duration of the course.",
    ),
    (
        "eligibility",
        "Maintenance allowance course groupings: Group I covers degree/PG courses in "
        "Medicine, Engineering, Technology, Architecture, Agriculture, Veterinary Sciences, "
        "Management, Computer Science, Commercial Pilot License, M.Phil/Ph.D, and L.L.M. "
        "Group II covers professional courses like Pharmacy, Nursing, LLB, Mass "
        "Communication, Hotel Management (entrance qualification minimum 10+2), and PG "
        "courses not in Group I. Group III covers all other graduate degree courses not in "
        "Group I or II (e.g. BA/B.Sc/B.Com). Group IV covers post-matriculation non-degree "
        "courses (entrance qualification Class X), e.g. ITI courses and 3-year diploma "
        "courses in Polytechnics.",
    ),
    (
        "amount",
        "Rate of Maintenance allowance (in Rupees per month): Group I - Rs.1200 for "
        "hostellers, Rs.550 for day scholars. Group II - Rs.820 for hostellers, Rs.530 for "
        "day scholars. Group III - Rs.570 for hostellers, Rs.300 for day scholars. Group IV "
        "- Rs.380 for hostellers, Rs.230 for day scholars.",
    ),
    (
        "amount",
        "Commercial Pilot License (CPL) course, including helicopter pilot and "
        "multi-engine rating training, is covered under Group I for maintenance allowance "
        "purposes. The number of CPL awards is capped at 50 per annum nationally, on a "
        "first-come-first-served basis, with all compulsory fees including flight charges "
        "provided in addition.",
    ),
    (
        "documents",
        "A student unable to get accommodation in the college hostel may be treated as "
        "residing in a Hostel for scheme purposes if in an approved place of residence (a "
        "group of at least 5 students with common mess arrangements), with a certificate "
        "from the Head of the Institution. Scholars entitled to free board and/or lodging "
        "are paid maintenance charge at 1/3rd of the Hostellers' rate.",
    ),
    (
        "amount",
        "Additional allowances for SC students with disabilities: Reader Allowance for "
        "blind scholars is Rs.240/month for Group I & II courses, Rs.200/month for Group "
        "III, and Rs.160/month for Group IV. Transport allowance up to Rs.160/month for "
        "disabled day scholars not residing in hostel. Escort Allowance of Rs.160/month for "
        "severely handicapped day scholar students with low extremity disability. Special "
        "Pay of Rs.160/month for a hostel employee assisting a severely orthopaedically "
        "handicapped student. Extra coaching allowance of Rs.240/month for mentally "
        "retarded and mentally ill students.",
    ),
    (
        "amount",
        "Fees reimbursed under the scheme: enrolment/registration, tuition, games, Union, "
        "Library, Magazine, and Medical Examination fees compulsorily payable to the "
        "institution or University/Board. Refundable deposits like caution money and "
        "security deposit are excluded.",
    ),
    (
        "amount",
        "Study tour charges up to a maximum of Rs.1600 per annum, limited to actual "
        "transportation expenditure, are paid to scholars in professional and technical "
        "courses, provided the Head of the Institution certifies the study tour is "
        "essential for course completion.",
    ),
    (
        "amount",
        "Thesis typing/printing charges up to a maximum of Rs.1600 are paid to research "
        "scholars on the recommendation of the Head of the Institution.",
    ),
    (
        "amount",
        "Students pursuing correspondence or distance education courses are eligible for "
        "an annual book allowance of Rs.1200 for essential/prescribed books, besides "
        "reimbursement of course fees.",
    ),
    (
        "documents",
        "Book Banks are set up in Medical, Engineering, Agriculture, Law, Veterinary, "
        "Chartered Accountancy, MBA, and Polytechnic institutions where SC students receive "
        "Post-Matric Scholarship. Book sets are shared between 2 SC students at most "
        "levels, except Post-Graduate and Chartered Accountancy courses which get one set "
        "per student.",
    ),
    (
        "amount",
        "Book Bank ceiling per set of books (or actual cost, whichever is less): Rs.7,500 "
        "for Medical/Engineering degree courses, Rs.5,000 for Veterinary degree courses, "
        "Rs.4,500 for Agriculture degree courses, Rs.2,400 for Polytechnics, and Rs.5,000 "
        "for PG/Law/Chartered Accountancy/MBA/Bio-Sciences courses.",
    ),
]


def main():
    with open(PATH, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    target_idx = None
    for i, r in enumerate(rows):
        if r["fact"].startswith("V. Value of Scholarship"):
            target_idx = i
            break
    if target_idx is None:
        raise ValueError("Oversized row not found -- already split, or source changed")

    original_len = len(rows[target_idx]["fact"])
    replacement_rows = [
        {"category": cat, "fact": fact, "source_url": SOURCE_URL} for cat, fact in REPLACEMENT_FACTS
    ]
    rows[target_idx : target_idx + 1] = replacement_rows

    with open(PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "fact", "source_url"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Replaced 1 row ({original_len} chars) with {len(replacement_rows)} atomic facts.")
    print(f"Post-Matric Scholarship.csv now has {len(rows)} rows.")


if __name__ == "__main__":
    main()
