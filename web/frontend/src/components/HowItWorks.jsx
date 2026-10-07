import { motion } from "framer-motion";
import { FileSearch, MessageSquareText, ShieldCheck } from "lucide-react";

const STEPS = [
  {
    icon: FileSearch,
    title: "Retrieve",
    body: "Your Hinglish question is matched against official scheme documents using multilingual semantic search.",
  },
  {
    icon: MessageSquareText,
    title: "Generate",
    body: "An LLM writes an answer grounded only in the retrieved passages — no outside knowledge.",
  },
  {
    icon: ShieldCheck,
    title: "Verify",
    body: "The answer is split into atomic claims, and each one is checked against the evidence and tagged.",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="border-t border-slate-200 bg-slate-50 py-20 dark:border-slate-800 dark:bg-slate-900/40">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold text-brand-700 dark:text-brand-400">How it works</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl dark:text-white">
            Every answer comes with receipts.
          </h2>
          <p className="mt-3 text-base leading-7 text-slate-600 dark:text-slate-300">
            Language models can sound confident and still be wrong. CodeSwitch-Verify checks each
            statement against its source, so you can see exactly what's backed up.
          </p>
        </div>

        <ol className="mt-12 grid gap-5 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <motion.li
              key={s.title}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.4, delay: i * 0.08 }}
              className="card relative p-6"
            >
              <div className="flex items-center justify-between">
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white shadow-sm shadow-brand-600/30 dark:bg-brand-600">
                  <s.icon size={19} />
                </span>
                <span className="mono text-sm font-medium text-slate-400 dark:text-slate-500">0{i + 1}</span>
              </div>
              <h3 className="mt-5 text-lg font-semibold text-slate-900 dark:text-white">{s.title}</h3>
              <p className="mt-1.5 text-sm leading-6 text-slate-600 dark:text-slate-300">{s.body}</p>
            </motion.li>
          ))}
        </ol>
      </div>
    </section>
  );
}
