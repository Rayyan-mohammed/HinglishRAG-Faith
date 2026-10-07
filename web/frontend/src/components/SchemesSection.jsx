import { motion } from "framer-motion";
import { ArrowRight, Check, ExternalLink } from "lucide-react";
import { ACCENTS, SCHEMES } from "../data/schemes.js";

export default function SchemesSection({ onAsk }) {
  return (
    <section id="schemes" className="border-t border-slate-200 py-20 dark:border-slate-800">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold text-brand-700 dark:text-brand-400">Coverage</p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl dark:text-white">
              Popular government schemes
            </h2>
            <p className="mt-3 text-base leading-7 text-slate-600 dark:text-slate-300">
              Answers are grounded in official guidelines and FAQs for these four central schemes.
            </p>
          </div>
        </div>

        <ul className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {SCHEMES.map((s, i) => (
            <motion.li
              key={s.id}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.4, delay: i * 0.06 }}
              className="card group flex flex-col p-5 transition duration-200 hover:-translate-y-1 hover:border-brand-200
                hover:shadow-lg hover:shadow-brand-950/5 dark:hover:border-brand-500/40 dark:hover:shadow-black/30"
            >
              <span className={`flex h-10 w-10 items-center justify-center rounded-xl ring-1 ring-inset ${ACCENTS[s.accent]}`}>
                <s.icon size={19} />
              </span>
              <h3 className="mt-4 text-base font-semibold text-slate-900 dark:text-white">{s.name}</h3>
              <p className="mt-0.5 min-h-[2rem] text-xs leading-4 text-slate-500 dark:text-slate-400">{s.fullName}</p>

              <div className="mt-4 rounded-xl bg-slate-50 px-3.5 py-3 dark:bg-slate-800/50">
                <p className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">{s.highlight}</p>
                <p className="text-xs text-slate-600 dark:text-slate-400">{s.highlightLabel}</p>
              </div>

              <ul className="mt-4 space-y-2">
                {s.facts.map((f) => (
                  <li key={f} className="flex gap-2 text-sm text-slate-600 dark:text-slate-300">
                    <Check size={15} className="mt-0.5 shrink-0 text-brand-500" aria-hidden="true" />
                    {f}
                  </li>
                ))}
              </ul>

              <div className="mt-auto flex items-center justify-between gap-2 pt-5">
                <button
                  type="button"
                  onClick={() => onAsk(s.question)}
                  className="focus-ring inline-flex items-center gap-1.5 rounded-lg text-sm font-semibold text-brand-700
                    transition hover:text-brand-800 dark:text-brand-400 dark:hover:text-brand-300"
                >
                  Ask about this
                  <ArrowRight size={15} className="transition-transform group-hover:translate-x-0.5" />
                </button>
                <a
                  href={s.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={`Official ${s.name} source (opens in a new tab)`}
                  className="focus-ring inline-flex items-center gap-1 rounded-lg text-xs font-medium text-slate-500
                    transition hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
                >
                  Source
                  <ExternalLink size={12} />
                </a>
              </div>
            </motion.li>
          ))}
        </ul>
      </div>
    </section>
  );
}
