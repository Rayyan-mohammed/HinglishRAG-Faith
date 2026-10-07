import { motion } from "framer-motion";
import { CheckCircle2, XCircle, HelpCircle, ListChecks } from "lucide-react";

const VERDICT_STYLE = {
  SUPPORTED: {
    label: "Supported",
    icon: CheckCircle2,
    badge: "bg-emerald-50 text-emerald-700 ring-emerald-600/20 dark:bg-emerald-500/10 dark:text-emerald-300 dark:ring-emerald-400/25",
    iconWrap: "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400",
    bar: "bg-emerald-500",
  },
  CONTRADICTED: {
    label: "Contradicted",
    icon: XCircle,
    badge: "bg-rose-50 text-rose-700 ring-rose-600/20 dark:bg-rose-500/10 dark:text-rose-300 dark:ring-rose-400/25",
    iconWrap: "bg-rose-50 text-rose-600 dark:bg-rose-500/10 dark:text-rose-400",
    bar: "bg-rose-500",
  },
  UNVERIFIABLE: {
    label: "Unverifiable",
    icon: HelpCircle,
    badge: "bg-amber-50 text-amber-800 ring-amber-600/20 dark:bg-amber-500/10 dark:text-amber-300 dark:ring-amber-400/25",
    iconWrap: "bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400",
    bar: "bg-amber-500",
  },
};

const ORDER = ["SUPPORTED", "CONTRADICTED", "UNVERIFIABLE"];

function styleFor(verdict) {
  return VERDICT_STYLE[verdict] ?? VERDICT_STYLE.UNVERIFIABLE;
}

function Summary({ claims }) {
  const counts = ORDER.map((v) => ({
    verdict: v,
    count: claims.filter((c) => (VERDICT_STYLE[c.verdict] ? c.verdict : "UNVERIFIABLE") === v).length,
  }));

  return (
    <div className="border-b border-slate-100 px-5 py-4 dark:border-slate-800">
      <div
        className="flex h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"
        role="img"
        aria-label={counts.map((c) => `${c.count} ${styleFor(c.verdict).label.toLowerCase()}`).join(", ")}
      >
        {counts.map(
          (c) =>
            c.count > 0 && (
              <motion.div
                key={c.verdict}
                initial={{ width: 0 }}
                animate={{ width: `${(c.count / claims.length) * 100}%` }}
                transition={{ duration: 0.6, ease: "easeOut" }}
                className={`${styleFor(c.verdict).bar} h-full first:rounded-l-full last:rounded-r-full`}
              />
            )
        )}
      </div>
      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5">
        {counts.map((c) => (
          <span key={c.verdict} className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-300">
            <span className={`h-2 w-2 rounded-full ${styleFor(c.verdict).bar}`} aria-hidden="true" />
            <span className="font-semibold text-slate-900 dark:text-white">{c.count}</span>
            {styleFor(c.verdict).label}
          </span>
        ))}
      </div>
    </div>
  );
}

function ConfidenceBar({ value, className }) {
  return (
    <div className="h-1.5 w-16 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800" aria-hidden="true">
      <div className={`h-full rounded-full ${className}`} style={{ width: `${Math.round(value * 100)}%` }} />
    </div>
  );
}

export default function ClaimsList({ claims }) {
  return (
    <section aria-label="Claim verification" className="card mt-4 overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3 dark:border-slate-800">
        <h2 className="section-label">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300">
            <ListChecks size={14} />
          </span>
          Claim verification
        </h2>
        <span className="mono rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          {claims.length} {claims.length === 1 ? "claim" : "claims"}
        </span>
      </div>

      {claims.length === 0 ? (
        <p className="px-5 py-5 text-sm italic text-slate-500 dark:text-slate-400">
          No individually-checkable claims were decomposed from this answer.
        </p>
      ) : (
        <>
          <Summary claims={claims} />
          <ul className="divide-y divide-slate-100 dark:divide-slate-800">
            {claims.map((c, i) => {
              const style = styleFor(c.verdict);
              const Icon = style.icon;
              return (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25, delay: i * 0.05 }}
                  className="flex gap-3.5 px-5 py-4 transition-colors hover:bg-slate-50/70 dark:hover:bg-slate-800/40"
                >
                  <span
                    className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${style.iconWrap}`}
                    aria-hidden="true"
                  >
                    <Icon size={17} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm leading-6 text-slate-800 dark:text-slate-200">{c.claim}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1.5">
                      <span
                        className={`inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ring-1 ring-inset ${style.badge}`}
                      >
                        {style.label}
                      </span>
                      <span className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                        Confidence
                        <ConfidenceBar value={c.confidence} className={style.bar} />
                        <span className="mono text-slate-700 dark:text-slate-300">{c.confidence.toFixed(2)}</span>
                      </span>
                    </div>
                  </div>
                </motion.li>
              );
            })}
          </ul>
        </>
      )}
    </section>
  );
}
