import { GraduationCap, HeartPulse, Home, Sprout } from "lucide-react";

// Figures below are taken from the facts in web/data/schemes/*.csv (the same data the RAG index is built from).
export const SCHEMES = [
  {
    id: "pm-kisan",
    name: "PM-KISAN",
    fullName: "Pradhan Mantri Kisan Samman Nidhi",
    icon: Sprout,
    accent: "emerald",
    highlight: "₹6,000 / year",
    highlightLabel: "Income support per farmer family",
    facts: ["Paid in 3 equal instalments", "Direct Benefit Transfer to bank account"],
    question: "PM-KISAN ke liye eligibility kya hai?",
    sourceUrl: "https://pmkisan.gov.in/Documents/RevisedFAQ.pdf",
  },
  {
    id: "ayushman-bharat",
    name: "Ayushman Bharat",
    fullName: "Pradhan Mantri Jan Arogya Yojana (PM-JAY)",
    icon: HeartPulse,
    accent: "rose",
    highlight: "₹5 lakh cover",
    highlightLabel: "Per eligible family, per year",
    facts: ["Cashless secondary & tertiary care", "Covers listed hospital procedures"],
    question: "Ayushman Bharat card banwane ke liye kaun eligible hai?",
    sourceUrl: "https://ayushmanbharat.haryana.gov.in/frequently-asked-questions/",
  },
  {
    id: "post-matric",
    name: "Post-Matric Scholarship",
    fullName: "Post-Matric Scholarship for SC Students",
    icon: GraduationCap,
    accent: "sky",
    highlight: "≤ ₹2.5 lakh",
    highlightLabel: "Parental income limit (means test)",
    facts: ["For post-matric / post-secondary study", "Awarded by the student's home State/UT"],
    question: "Post-Matric Scholarship ke liye kaunse documents chahiye?",
    sourceUrl: "https://sjsa.maharashtra.gov.in/en/scheme/post-matric-scholarship-by-the-government-of-india/",
  },
  {
    id: "pmay",
    name: "PM Awas Yojana",
    fullName: "Pradhan Mantri Awas Yojana (Urban)",
    icon: Home,
    accent: "amber",
    highlight: "Up to ₹2.67 lakh",
    highlightLabel: "Interest subsidy per house (CLSS)",
    facts: ["Pucca houses for eligible urban families", "EWS, LIG and MIG categories covered"],
    question: "PM Awas Yojana mein interest subsidy kitni milti hai?",
    sourceUrl: "https://pmay-urban.gov.in/faq",
  },
];

export const ACCENTS = {
  emerald: "bg-emerald-50 text-emerald-700 ring-emerald-600/15 dark:bg-emerald-500/10 dark:text-emerald-300 dark:ring-emerald-400/20",
  rose: "bg-rose-50 text-rose-700 ring-rose-600/15 dark:bg-rose-500/10 dark:text-rose-300 dark:ring-rose-400/20",
  sky: "bg-sky-50 text-sky-700 ring-sky-600/15 dark:bg-sky-500/10 dark:text-sky-300 dark:ring-sky-400/20",
  amber: "bg-amber-50 text-amber-700 ring-amber-600/15 dark:bg-amber-500/10 dark:text-amber-300 dark:ring-amber-400/20",
};
