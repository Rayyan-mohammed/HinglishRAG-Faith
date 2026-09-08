import { motion } from "framer-motion";
import { CheckCircle2, XCircle, HelpCircle, ListChecks } from "lucide-react";

const VERDICT_STYLE = {
  SUPPORTED: {
    icon: CheckCircle2,
    border: "border-l-emerald-500",
    badge: "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400",
    iconColor: "text-emerald-500",
  },
  CONTRADICTED: {
    icon: XCircle,
    border: "border-l-rose-500",
    badge: "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-400",
    iconColor: "text-rose-500",
  },
  UNVERIFIABLE: {
    icon: HelpCircle,
    border: "border-l-amber-500",
    badge: "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400",
    iconColor: "text-amber-500",
  },
};

function ConfidenceBar({ value }) {
  return (
    <div className="h-1 w-16 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
      <div
        className="h-full rounded-full bg-current opacity-70"
        style={{ width: `${Math.round(value * 100)}%` }}
      />
    </div>
  );
}

export default function ClaimsList({ claims }) {
  return (
    <div className="mt-4">
      <div className="mb-2.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400 dark:text-slate-500">
        <ListChecks size={14} className="text-indigo-500" />
        Claims{" "}
        <span className="mono normal-case tracking-normal text-slate-300 dark:text-slate-600">
          ({claims.length})
        </span>
      </div>

      {claims.length === 0 ? (
        <p className="text-sm italic text-slate-400 dark:text-slate-500">
          No individually-checkable claims were decomposed from this answer.
        </p>
      ) : (
        <div className="space-y-2">
          {claims.map((c, i) => {
            const style = VERDICT_STYLE[c.verdict] ?? VERDICT_STYLE.UNVERIFIABLE;
            const Icon = style.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.25, delay: i * 0.05 }}
                className={`card border-l-4 p-3.5 ${style.border}`}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-bold tracking-wide ${style.badge}`}
                  >
                    <Icon size={12} />
                    {c.verdict}
                  </span>
                  <div className={style.iconColor}>
                    <ConfidenceBar value={c.confidence} />
                  </div>
                  <span className="mono text-[11px] text-slate-400 dark:text-slate-500">
                    {c.confidence.toFixed(2)}
                  </span>
                </div>
                <p className="mt-1.5 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                  {c.claim}
                </p>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
