import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, Stethoscope } from "lucide-react";

import { useTheme } from "./hooks/useTheme.js";
import ThemeToggle from "./components/ThemeToggle.jsx";
import QuestionForm from "./components/QuestionForm.jsx";
import ResultSkeleton from "./components/ResultSkeleton.jsx";
import AnswerCard from "./components/AnswerCard.jsx";
import ClaimsList from "./components/ClaimsList.jsx";
import SourcesPanel from "./components/SourcesPanel.jsx";

export default function App() {
  const { theme, toggle } = useTheme();
  const [question, setQuestion] = useState("");
  const [verify, setVerify] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const [lastVerify, setLastVerify] = useState(true);

  const ask = async () => {
    if (!question.trim() || loading) return;

    setLoading(true);
    setError(null);
    setResult(null);
    setLastVerify(verify);

    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question.trim(), verify }),
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

  return (
    <div className="min-h-screen">
      <header className="relative overflow-hidden bg-gradient-to-br from-indigo-600 via-indigo-600 to-purple-700 pb-14 pt-10">
        <div
          className="pointer-events-none absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 20%, white 0, transparent 40%), radial-gradient(circle at 80% 0%, white 0, transparent 35%)",
          }}
        />
        <div className="relative mx-auto flex max-w-2xl items-center justify-between px-5">
          <div className="flex items-center gap-2 text-white/90">
            <Stethoscope size={18} />
            <span className="text-sm font-medium">CodeSwitch-Verify</span>
          </div>
          <ThemeToggle theme={theme} onToggle={toggle} />
        </div>

        <div className="relative mx-auto mt-6 max-w-2xl px-5 text-center">
          <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Ask about government schemes.
            <br className="hidden sm:block" /> Get answers you can check.
          </h1>
          <p className="mx-auto mt-3 max-w-lg text-sm text-indigo-100/90 sm:text-base">
            PM-KISAN, Ayushman Bharat, Post-Matric Scholarship, PM Awas Yojana — ask in Hinglish,
            every claim in the answer gets checked against its source.
          </p>
        </div>
      </header>

      <main className="mx-auto -mt-8 max-w-2xl px-5 pb-16">
        <QuestionForm
          question={question}
          setQuestion={setQuestion}
          verify={verify}
          setVerify={setVerify}
          onSubmit={ask}
          loading={loading}
        />

        <AnimatePresence mode="wait">
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-4 flex items-center gap-2.5 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3
                text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-400"
            >
              <AlertTriangle size={16} className="shrink-0" />
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {loading && <ResultSkeleton verifying={verify} />}

        <AnimatePresence>
          {result && !loading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-6"
            >
              <AnswerCard answer={result.answer} />
              {lastVerify && result.claims && <ClaimsList claims={result.claims} />}
              <SourcesPanel sources={result.context_passages} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      <footer className="pb-10 text-center text-xs text-slate-400 dark:text-slate-600">
        CodeSwitch-Verify — a faithfulness-checked RAG demo for Hinglish government-scheme Q&amp;A.
      </footer>
    </div>
  );
}
