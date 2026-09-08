import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, BookOpen } from "lucide-react";

export default function SourcesPanel({ sources }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="card mt-4 overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm font-medium text-slate-500 dark:text-slate-400"
      >
        <span className="flex items-center gap-2">
          <BookOpen size={14} className="text-indigo-500" />
          Retrieved sources
          <span className="mono text-xs text-slate-300 dark:text-slate-600">
            ({sources.length})
          </span>
        </span>
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown size={16} />
        </motion.span>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="space-y-3 border-t border-slate-100 px-4 py-3 dark:border-slate-800">
              {sources.map((s, i) => (
                <div key={i}>
                  <div className="flex items-baseline gap-2">
                    <span className="text-xs font-semibold text-indigo-500">{s.source}</span>
                    <span className="mono text-[11px] text-slate-400 dark:text-slate-500">
                      score {s.score.toFixed(3)}
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
                    {s.text}
                  </p>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
