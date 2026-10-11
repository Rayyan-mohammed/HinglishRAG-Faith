import { useRef, useState } from "react";
import { AnimatePresence, MotionConfig, motion } from "framer-motion";
import { AlertTriangle, BadgeCheck, FileSearch, Languages } from "lucide-react";

import { useTheme } from "./hooks/useTheme.js";
import Navbar from "./components/Navbar.jsx";
import QuestionForm from "./components/QuestionForm.jsx";
import ResultSkeleton from "./components/ResultSkeleton.jsx";
import AnswerCard from "./components/AnswerCard.jsx";
import ClaimsList from "./components/ClaimsList.jsx";
import SourcesPanel from "./components/SourcesPanel.jsx";
import HowItWorks from "./components/HowItWorks.jsx";
import SchemesSection from "./components/SchemesSection.jsx";

const TRUST_POINTS = [
  { icon: Languages, label: "Hinglish & code-switched input" },
  { icon: BadgeCheck, label: "Claim-level verification" },
  { icon: FileSearch, label: "Grounded in official sources" },
];

export default function App() {
  const { theme, toggle } = useTheme();
  const [question, setQuestion] = useState("");
  const [verify, setVerify] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [lastVerify, setLastVerify] = useState(true);
  const textareaRef = useRef(null);

  const ask = async () => {
    if (!question.trim() || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setLastVerify(verify);

    try {
      const body = JSON.stringify({ question: question.trim(), verify });
      const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(body));
      const payloadHash = Array.from(new Uint8Array(digest))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");

      // CloudFront signs requests to the Lambda URL (OAC); POST bodies need their SHA-256 up front.
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json", "x-amz-content-sha256": payloadHash },
        body,
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(data.detail || `Request failed (${res.status})`);
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Scheme cards prefill the question box (same as the example chips) and bring it into view.
  const prefillQuestion = (q) => {
    setQuestion(q);
    textareaRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
    textareaRef.current?.focus({ preventScroll: true });
  };

  return (
    <MotionConfig reducedMotion="user">
      <div id="top" className="min-h-screen">
        <a
          href="#question"
          className="sr-only z-50 rounded-lg bg-brand-700 px-4 py-2 text-sm font-semibold text-white focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
        >
          Skip to question
        </a>

        <Navbar theme={theme} onToggleTheme={toggle} />

        <main>
          <section className="relative overflow-hidden pb-20 pt-14 sm:pt-20">
            <div className="hero-grid pointer-events-none absolute inset-0" aria-hidden="true" />
            <div
              className="pointer-events-none absolute left-1/2 top-0 h-72 w-[42rem] -translate-x-1/2 rounded-full bg-brand-400/15 blur-3xl dark:bg-brand-500/10"
              aria-hidden="true"
            />

            <div className="relative mx-auto max-w-3xl px-4 sm:px-6">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.45 }}
                className="text-center"
              >
                <span className="eyebrow">
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-500" aria-hidden="true" />
                  Faithfulness-checked RAG for Indian government schemes
                </span>
                <h1 className="mt-6 text-4xl font-extrabold leading-[1.1] tracking-tight text-slate-900 sm:text-5xl md:text-[3.5rem] dark:text-white">
                  Scheme answers you can{" "}
                  <span className="text-brand-700 dark:text-brand-400">actually trust.</span>
                </h1>
                <p className="mx-auto mt-5 max-w-xl text-base leading-7 text-slate-600 sm:text-lg dark:text-slate-300">
                  Ask about PM-KISAN, Ayushman Bharat, Post-Matric Scholarship or PM Awas Yojana in
                  Hinglish. Every claim in the answer is checked against its official source.
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 }}
                className="mt-10"
              >
                <QuestionForm
                  question={question}
                  setQuestion={setQuestion}
                  verify={verify}
                  setVerify={setVerify}
                  onSubmit={ask}
                  loading={loading}
                  textareaRef={textareaRef}
                />
              </motion.div>

              <ul className="mt-5 flex flex-wrap justify-center gap-x-6 gap-y-2">
                {TRUST_POINTS.map((t) => (
                  <li key={t.label} className="flex items-center gap-1.5 text-sm text-slate-600 dark:text-slate-400">
                    <t.icon size={15} className="text-brand-500" aria-hidden="true" />
                    {t.label}
                  </li>
                ))}
              </ul>

              <div aria-live="polite">
                <AnimatePresence mode="wait">
                  {error && (
                    <motion.div
                      role="alert"
                      initial={{ opacity: 0, y: -6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      className="mt-6 flex items-start gap-3 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3
                        text-sm text-rose-800 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-300"
                    >
                      <AlertTriangle size={17} className="mt-0.5 shrink-0" />
                      <span>
                        <span className="font-semibold">Couldn't get an answer. </span>
                        {error}
                      </span>
                    </motion.div>
                  )}
                </AnimatePresence>

                {loading && <ResultSkeleton verifying={verify} />}

                <AnimatePresence>
                  {result && !loading && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-8 text-left"
                    >
                      <AnswerCard answer={result.answer} />
                      {lastVerify && result.claims && (
                        <ClaimsList claims={result.claims} truncated={result.claims_truncated} />
                      )}
                      <SourcesPanel sources={result.context_passages} />
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </section>

          <HowItWorks />
          <SchemesSection onAsk={prefillQuestion} />
        </main>

        <footer className="border-t border-slate-200 dark:border-slate-800">
          <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-8 text-sm text-slate-500 sm:flex-row sm:px-6 dark:text-slate-400">
            <p>
              <span className="font-semibold text-slate-700 dark:text-slate-200">CodeSwitch-Verify</span> — a
              faithfulness-checked RAG demo for Hinglish government-scheme Q&amp;A.
            </p>
            <p className="text-xs">Informational only. Confirm details on official portals before applying.</p>
          </div>
        </footer>
      </div>
    </MotionConfig>
  );
}
