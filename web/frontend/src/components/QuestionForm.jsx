import { ArrowUp, Loader2, Sparkles } from "lucide-react";

const EXAMPLES = [
  "PM-KISAN ke liye eligibility kya hai?",
  "Ayushman Bharat card banwane ke liye kaun eligible hai?",
  "Post-Matric Scholarship ke liye kaunse documents chahiye?",
];

export default function QuestionForm({
  question,
  setQuestion,
  verify,
  setVerify,
  onSubmit,
  loading,
  textareaRef,
}) {
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) onSubmit();
  };

  return (
    <div
      className="rounded-2xl border border-slate-200 bg-white p-2 shadow-xl shadow-brand-950/[0.06]
        ring-1 ring-slate-900/[0.02] dark:border-slate-800 dark:bg-slate-900 dark:shadow-black/40"
    >
      <div
        className="rounded-xl border border-transparent bg-slate-50 transition
          focus-within:border-brand-300 focus-within:bg-white focus-within:ring-4 focus-within:ring-brand-500/10
          dark:bg-slate-800/50 dark:focus-within:border-brand-500/60 dark:focus-within:bg-slate-900"
      >
        <label htmlFor="question" className="sr-only">
          Your question
        </label>
        <textarea
          id="question"
          ref={textareaRef}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Hinglish mein poochiye — e.g. PM-KISAN ke liye eligibility kya hai?"
          rows={3}
          className="block w-full resize-none bg-transparent px-4 pb-2 pt-4 text-base leading-relaxed text-slate-900
            placeholder:text-slate-400 dark:text-slate-100 dark:placeholder:text-slate-500"
        />

        <div className="flex flex-wrap items-center justify-between gap-3 px-3 pb-3 pt-1">
          <button
            type="button"
            role="switch"
            aria-checked={verify}
            onClick={() => setVerify(!verify)}
            className={`focus-ring group flex items-center gap-2.5 rounded-lg border px-2.5 py-1.5 text-sm font-medium transition ${
              verify
                ? "border-brand-200 bg-brand-50 text-brand-700 dark:border-brand-500/40 dark:bg-brand-500/10 dark:text-brand-300"
                : "border-slate-200 bg-white text-slate-600 hover:border-slate-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
            }`}
          >
            <span
              aria-hidden="true"
              className={`relative h-5 w-9 shrink-0 rounded-full transition-colors ${
                verify ? "bg-brand-600" : "bg-slate-300 dark:bg-slate-600"
              }`}
            >
              <span
                className={`absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white shadow-sm transition-transform ${
                  verify ? "translate-x-4" : "translate-x-0"
                }`}
              />
            </span>
            Verify claims
            <span className="sr-only">{verify ? "(on)" : "(off)"}</span>
          </button>

          <div className="flex items-center gap-3">
            <span className="hidden text-xs text-slate-500 sm:inline dark:text-slate-400">
              <kbd className="mono rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] dark:border-slate-700 dark:bg-slate-800">
                Ctrl
              </kbd>{" "}
              +{" "}
              <kbd className="mono rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] dark:border-slate-700 dark:bg-slate-800">
                Enter
              </kbd>
            </span>
            <button
              onClick={onSubmit}
              disabled={loading || !question.trim()}
              className="focus-ring flex items-center gap-2 rounded-lg bg-brand-700 px-4 py-2 text-sm font-semibold text-white
                shadow-sm shadow-brand-700/30 transition hover:bg-brand-800 active:scale-[0.98]
                disabled:cursor-not-allowed disabled:bg-slate-300 disabled:text-slate-500 disabled:shadow-none
                dark:bg-brand-400 dark:text-slate-950 dark:hover:bg-brand-300 dark:disabled:bg-slate-700 dark:disabled:text-slate-400"
            >
              {loading ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <ArrowUp size={16} strokeWidth={2.5} />
              )}
              {loading ? "Sochte hain..." : "Ask"}
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 px-2 pb-1.5 pt-3">
        <span className="flex items-center gap-1 text-xs font-medium text-slate-500 dark:text-slate-400">
          <Sparkles size={13} className="text-brand-500" />
          Try:
        </span>
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            type="button"
            onClick={() => setQuestion(ex)}
            className="focus-ring rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600
              transition hover:-translate-y-px hover:border-brand-300 hover:bg-brand-50 hover:text-brand-700
              dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-300
              dark:hover:border-brand-500/50 dark:hover:bg-brand-500/10 dark:hover:text-brand-300"
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}
