import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, BookOpen, FileText } from "lucide-react";

export default function SourcesPanel({ sources }) {
  const [open, setOpen] = useState(false);

  return (
    <section aria-label="Retrieved sources" className="card mt-4 overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls="sources-list"
        className="focus-ring flex w-full items-center justify-between gap-3 px-5 py-3.5 text-left transition
          hover:bg-slate-50 dark:hover:bg-slate-800/40"
      >
        <span className="section-label">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300">
            <BookOpen size={14} />
          </span>
          Retrieved sources
          <span className="mono rounded-md bg-slate-100 px-2 py-0.5 text-xs normal-case tracking-normal text-slate-600 dark:bg-slate-800 dark:text-slate-300">
            {sources.length}
          </span>
        </span>
        <span className="flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400">
          <span className="hidden sm:inline">{open ? "Hide" : "Show"} evidence</span>
          <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
            <ChevronDown size={16} />
          </motion.span>
        </span>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            id="sources-list"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <ol className="space-y-2.5 border-t border-slate-100 p-4 dark:border-slate-800">
              {sources.map((s, i) => (
                <li
                  key={i}
                  className="rounded-xl border border-slate-200 bg-slate-50/60 p-3.5 transition hover:border-brand-200
                    dark:border-slate-800 dark:bg-slate-800/30 dark:hover:border-brand-500/40"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
                      <span className="mono flex h-5 w-5 items-center justify-center rounded bg-brand-700 text-[10px] font-medium text-white dark:bg-brand-600">
                        {i + 1}
                      </span>
                      <FileText size={14} className="text-slate-400" aria-hidden="true" />
                      {s.source}
                    </span>
                    <span className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                      Relevance
                      <span className="h-1.5 w-12 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700" aria-hidden="true">
                        <span
                          className="block h-full rounded-full bg-brand-500"
                          style={{ width: `${Math.max(0, Math.min(1, s.score)) * 100}%` }}
                        />
                      </span>
                      <span className="mono text-slate-700 dark:text-slate-300">{s.score.toFixed(3)}</span>
                    </span>
                  </div>
                  <p className="mt-2 text-[13px] leading-6 text-slate-600 dark:text-slate-300">{s.text}</p>
                </li>
              ))}
            </ol>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
