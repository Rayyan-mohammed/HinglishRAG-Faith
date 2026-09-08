import { Loader2, Sparkles, ShieldCheck } from "lucide-react";

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
}) {
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) onSubmit();
  };

  return (
    <div className="card p-5 sm:p-6">
      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="e.g. PM-KISAN ke liye eligibility kya hai?"
        rows={3}
        className="w-full resize-none rounded-xl border border-slate-200 bg-slate-50/60 p-3.5 text-[15px]
          leading-relaxed text-slate-900 placeholder:text-slate-400 transition
          focus:border-indigo-400 focus:ring-2 focus:ring-indigo-400/30
          dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-100 dark:placeholder:text-slate-500
          dark:focus:border-indigo-500"
      />

      <div className="mt-2 flex flex-wrap gap-1.5">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            type="button"
            onClick={() => setQuestion(ex)}
            className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs text-slate-500 transition
              hover:border-indigo-300 hover:text-indigo-600
              dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400 dark:hover:border-indigo-500 dark:hover:text-indigo-400"
          >
            {ex}
          </button>
        ))}
      </div>

      <div className="mt-4 flex items-center justify-between gap-3">
        <label className="flex cursor-pointer items-center gap-2.5 select-none">
          <button
            type="button"
            role="switch"
            aria-checked={verify}
            onClick={() => setVerify(!verify)}
            className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${
              verify ? "bg-indigo-600" : "bg-slate-300 dark:bg-slate-700"
            }`}
          >
            <span
              className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                verify ? "translate-x-5" : "translate-x-0.5"
              }`}
            />
          </button>
          <span className="flex items-center gap-1.5 text-sm text-slate-600 dark:text-slate-300">
            <ShieldCheck size={15} className="text-indigo-500" />
            Verify claims
          </span>
        </label>

        <button
          onClick={onSubmit}
          disabled={loading || !question.trim()}
          className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 px-5 py-2.5
            text-sm font-semibold text-white shadow-lg shadow-indigo-500/25 transition
            hover:shadow-indigo-500/40 hover:brightness-110 active:scale-[0.98]
            disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none"
        >
          {loading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : (
            <Sparkles size={16} />
          )}
          {loading ? "Sochte hain..." : "Ask"}
        </button>
      </div>
    </div>
  );
}
