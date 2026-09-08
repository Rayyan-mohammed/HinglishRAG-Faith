import { motion } from "framer-motion";
import { MessageSquareText } from "lucide-react";

export default function AnswerCard({ answer }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="card p-5 sm:p-6"
    >
      <div className="mb-2.5 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-400 dark:text-slate-500">
        <MessageSquareText size={14} className="text-indigo-500" />
        Answer
      </div>
      <p className="text-[15px] leading-relaxed text-slate-800 dark:text-slate-100">{answer}</p>
    </motion.div>
  );
}
