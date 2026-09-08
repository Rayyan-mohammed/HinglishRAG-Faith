# Human review checklist — `eval/labels.csv`

Every row in `eval/labels.csv` is currently `reviewed_by_human=FALSE` — the labels below are an
AI-drafted first pass (ADR-012). Per ADR-006, this project's ground truth has to come from a human
specifically because the verifier being measured is also an LLM; an AI reviewing its own AI-drafted
labels doesn't satisfy that, so this step has to be done by you.

**Only the 18 answers below need checking.** The other 42 questions were labeled `fully_correct`
and aren't reviewed here — if you want to spot-check those too, they're in `eval/labels.csv`
directly, but they don't drive any of the reported precision/recall numbers the way these 18 do.

**For each one:** read the question, the generated answer, and the reasoning. Decide if you agree
the label is right. That's it — one judgment call per row, ~18 total.

**When you're done**, tell me which ones you disagree with (by question ID) and why, or just say
"all confirmed" if you agree with all 18. I'll then flip `reviewed_by_human` to `TRUE` for these
rows, fix any labels you flag, and re-run the metrics if anything changed.

---

### Q2 — PM-KISAN, eligibility
**Q:** Kya PM-KISAN scheme sirf un kisano ke liye hai jinke paas apni zameen hai ya kiraye ki zameen wale bhi apply kar sakte hain?
**A:** Nahin, PM-KISAN scheme sirf un kisano ke liye nahin hai jinke paas apni zameen hai, lekin ismein kya kiraye ki zameen wale apply kar sakte hain iske baare mein scheme ke context mein koi jankari nahin di gayi hai. Scheme ke mutabik, ismein landholding farmers' families ko financial benefit diya jaata hai, lekin yeh nahin bataya gaya hai ki kiraye ki zameen wale ismein shaamil hain ya nahin.
**Current label:** `partially_hallucinated` — claims no info is given on rented-land farmers; the source establishes land must be owned per land records in the farmer's own name, which implies tenant/rented-land farmers are excluded. The answer's "no info given" claim is itself the hallucination.
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q3 — PM-KISAN, eligibility
**Q:** Agar meri family mein koi government employee hai to kya hum PM-KISAN ka fayda le sakte hain?
**A:** Arre, yeh to context mein clearly nahi likha hai ki government employee hone se PM-KISAN ka fayda milta hai ya nahi. Bas itna likha hai ki shuruat mein sirf small aur marginal farmers ke liye tha, lekin baad mein sabhi farmer families ko include kar liya gaya. Lekin exclusion criteria ke baare mein kuch nahi likha hai, to hum keh nahi sakte ki government employee hone se fayda milega ya nahi.
**Current label:** `fully_hallucinated` — claims exclusion criteria aren't covered; the source explicitly excludes serving/retired government officers and employees from PM-KISAN benefits.
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q10 — PM-KISAN, amount
**Q:** Kya amount sabhi states ke kisano ke liye same hai?
**A:** Haan, PM-KISAN scheme ke hisab se, sabhi states ke kisano ke liye amount same hai, jo ki Rs. 6000 per annum per family hai, jo ki 3 equal installments mein diya jata hai, har installment Rs. 2000 ka hota hai.
**Current label:** `partially_hallucinated` — the Rs. 6000/Rs. 2000 figures are correct, but "same across all states" is asserted confidently even though the source never explicitly says that.
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q14 — PM-KISAN, documents
**Q:** Land ownership proof ke liye kaunsa document dena hota hai?
**A:** Land ownership proof ke liye aapko apna land ka document dena hota hai, jaise ki land record ya ownership certificate. PM Awas Yojana mein to yeh clearly likha hai ki beneficiaries ko ownership proof of land dena hota hai, aur PM-KISAN mein bhi land records ka mention hai, jahan par land ownership ki details hoti hain.
**Current label:** `partially_hallucinated` — vague, and cites a PM Awas Yojana fact as if it supports a PM-KISAN question (cross-scheme mixing).
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q16 — Ayushman Bharat, eligibility
**Q:** Ayushman Bharat card banwane ke liye kaun eligible hai?
**A:** Ayushman Bharat card banwane ke liye jo beneficiaries Haryana Mukhyamantri Antyodaya Parivar Utthan Yojana ke under aate hain, unka annual family income 1.80 lakh se kam hona chahiye, toh ve eligible hain. Unhe koi request letter ya entitlement letter dena nahi padta, bas Ayushman Kiosk ya Common Services Centers (CSC) se apna Ayushman Bharat card le sakte hain.
**Current label:** `partially_hallucinated` — answers using only the Haryana-specific sub-scheme's criteria, omitting the general SECC-2011 database eligibility criterion that's the primary/national answer.
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q24 — Ayushman Bharat, amount
**Q:** Kya yeh cover ek baar ke liye hai ya har saal renew hota hai?
**A:** Ayushman Bharat ke bare mein aapne sawal kiya hai, lekin diya gaya context iska jawaab nahin deta. Diye gaye context mein sirf Ayushman Bharat ke udeshya ke baare mein bataya gaya hai, lekin iske bare mein koi jaankari nahin hai ki yeh cover ek baar ke liye hai ya har saal renew hota hai.
**Current label:** `fully_hallucinated` — claims the context doesn't say whether cover is one-time or annual; the source explicitly says the cover is "per annum" (a yearly, renewing benefit) in multiple facts.
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q26 — Ayushman Bharat, amount
**Q:** Kya cover amount har state mein alag hota hai?
**A:** Nahin, context mein aisa koi information nahi hai ki cover amount har state mein alag hota hai. Sab jagah Rs. 5,00,000 per family per year ka cover diya jaata hai.
**Current label:** `partially_hallucinated` — the Rs. 5,00,000 figure is correct, but "not different by state" is asserted though never explicitly stated in the source. (This one was previously re-checked and judged an honestly-hedged true statement rather than an overclaim — worth a close look; see ADR-014.)
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q30 — Ayushman Bharat, documents
**Q:** Family details verify karne ke liye kya document submit karna hota hai?
**A:** Family details verify karne ke liye aapko apne documents jaise ki Aadhaar Card, Ration Card, aur anya prescribed documents jaise ki Driving Licence, Voters' ID Card, NREGA Job Card, etc. submit karne pad sakte hain.
**Current label:** `partially_hallucinated` — Driving Licence/Voter ID/NREGA Job Card are PM-KISAN's alternate-ID documents (for Assam/Meghalaya/J&K), not Ayushman Bharat's (whose actual documents are PM/CM entitlement letter, ration card, Aadhaar). Cross-scheme mixing.
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q40 — Post-Matric Scholarship, amount
**Q:** Hostel mein rehne wale students ko extra amount milta hai kya?
**A:** Haan, hostel mein rehne wale students ko maintenance allowance milta hai, jo ki 400 se 1350 rupees per month tak ho sakta hai.
**Current label:** `partially_hallucinated` — uses the Maharashtra-specific hostel rate (Rs 400-1350/month) without noting it's state-specific, and it's inconsistent with the general Group I-IV national rates already given correctly elsewhere (Q38). (Also previously re-checked and judged a real fact, just inconsistent with a different question's figure, not unsupported — see ADR-014.)
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q43 — Post-Matric Scholarship, documents
**Q:** Income certificate kis authority se banwana padta hai?
**A:** Income certificate kis authority se banwana padta hai, iska context mein koi jankari nahi hai. Context mein sirf income certificate ki jarurat ke bare mein bataya gaya hai, lekin yeh nahi bataya gaya hai ki kis authority se banwana padta hai.
**Current label:** `fully_hallucinated` — claims no info exists on which authority issues the certificate; the source specifies the employer for employed parents, and a self-declaration affidavit for self-employed parents.
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q44 — Post-Matric Scholarship, documents
**Q:** Kya caste certificate submit karna mandatory hai?
**A:** Nahin, caste certificate submit karna mandatory nahin hai, lekin category (SC/ST) ka information dena zaroori hai.
**Current label:** `fully_hallucinated` — claims the caste certificate isn't mandatory; the source explicitly lists it as a required application document (signed by an authorised Revenue Officer).
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q45 — Post-Matric Scholarship, documents
**Q:** Bank passbook ki copy ke alawa aur kya documents chahiye?
**A:** Bank passbook ki copy ke alawa, aapko Ayushman Bharat ke liye PM/CM entitlement letter, Ration Card, aur Aadhaar Card ki zarurat pad sakti hai. Lekin agar aap PM-KISAN ke liye apply kar rahe hain, to aapko apna Aadhaar number, bank account details, aur anya documents jaise ki Name, Age, Gender, Category (SC/ST) aur mobile number (optional) dena hoga. Agar aap Post-Matric Scholarship ke liye apply kar rahe hain, to aapko application form, passport size photo, certificates, caste certificate, income declaration, aur anya documents dena hoga.
**Current label:** `partially_hallucinated` — question is specifically about Post-Matric Scholarship documents, but the answer dumps document lists for all 3 other schemes instead of focusing on the one asked about.
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q49 — PM Awas Yojana, eligibility
**Q:** Kya yeh scheme sirf shehri areas ke logo ke liye hai?
**A:** Haan, Pradhan Mantri Awas Yojana (Urban) 2.0 scheme sirf shehri ilakon ke logo ke liye hai, jismein unhein affordable housing provide kiya jaata hai. Is scheme mein do models hain - ek public sector agencies dwara aur doosra private sector dwara.
**Current label:** `partially_hallucinated` — "two models" (public/private) actually describes just the AHP vertical's internal split, not the whole scheme's structure (which has 4 verticals: ISSR/CLSS/AHP/BLC).
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q51 — PM Awas Yojana, deadline
**Q:** Subsidy claim karne ke liye construction start hone ke baad kitne time tak apply karna hota hai?
**A:** Mujhe khed hai, lekin aapka sawal mere paas diye gaye context se related nahi hai. Diye gaye context me sirf PM-KISAN aur Post-Matric Scholarship ke bare me jankari hai, lekin subsidy claim ya construction ke bare me koi jankari nahi hai. Aapka sawal ka jawab dena mushkil hai.
**Current label:** `partially_hallucinated` — retrieval failure: claims the context only covers PM-KISAN and Post-Matric Scholarship, but relevant PM Awas Yojana facts on fund-release timelines exist in the source and just weren't surfaced.
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q52 — PM Awas Yojana, deadline
**Q:** Application status check karne ke liye kitna wait karna padta hai?
**A:** Application status check karne ke liye wait karne ki koi specific time limit nahin di gayi hai, lekin Ayushman Bharat ke liye to aap online check kar sakte hain, https://mera.pmjay.gov.in/search/login par jakar. Baaki schemes ke liye koi specific information nahin hai.
**Current label:** `partially_hallucinated` — cites Ayushman Bharat's status-check URL as if relevant to a PM Awas Yojana question; wrong scheme, no PMAY-specific info actually given.
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q57 — PM Awas Yojana, documents
**Q:** PM Awas Yojana ke liye kaunse documents chahiye application ke time?
**A:** PM Awas Yojana ke liye documents ke baare mein context mein kuchh specific jankari nahin hai, lekin yeh bataya gaya hai ki ismein female head of the family ko owner ya co-owner hone ki provision hai. Lekin application ke liye konsi documents chahiye, iske baare mein koi jankari nahin di gayi hai.
**Current label:** `fully_hallucinated` — claims no document info exists for PM Awas Yojana applications; the source specifies land ownership proof and a building plan as required documents.
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q58 — PM Awas Yojana, documents
**Q:** Income proof ke liye kya submit karna padta hai?
**A:** Income proof ke liye, agar aapke parents employed hain, toh unhe apne employer se income certificate lena hoga. Agar aapke parents self-employed hain, toh unhe affidavit on non-judicial stamp paper par income declaration dena hoga, jismein unki income from all sources ka detail hona chahiye.
**Current label:** `fully_hallucinated` — the entire answer is actually Post-Matric Scholarship's income-certificate rule; it has nothing to do with PM Awas Yojana at all.
**Your call:** [ ] Agree [ ] Disagree — why?

---

### Q60 — PM Awas Yojana, documents
**Q:** Kya Aadhaar aur PAN card dono zaroori hain is scheme ke liye?
**A:** Nahi, is scheme ke liye Aadhaar zaroori hai, lekin PAN card ki zaroorat nahi hai. Bank account details aur Aadhaar number diya jana zaroori hai, lekin PAN card ki koi zaroorat nahi hai.
**Current label:** `partially_hallucinated` — the Aadhaar/bank account requirement is correctly sourced, but the claim that PAN card is NOT required is asserted confidently even though the source never mentions PAN at all (silence isn't the same as "not required").
**Your call:** [ ] Agree [ ] Disagree — why?

---

## Where to check the actual source facts

If you want to verify against the government pages directly rather than trusting the "Current
label" reasoning above, the source CSVs are in `data/schemes/` — each row has a `source_url`
column pointing to the official `.gov.in` page or PDF it came from. Search the relevant CSV
(`PM-KISAN.csv`, `Ayushman Bharat.csv`, `Post-Matric Scholarship.csv`, `PM Awas Yojana.csv`) for
keywords from the claim you're checking.
