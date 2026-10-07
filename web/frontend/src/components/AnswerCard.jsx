import { motion } from "framer-motion";
import { MessageSquareText } from "lucide-react";

export default function AnswerCard({ answer }) {
  return (
    <motion.section
      aria-label="Answer"
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="card overflow-hidden"
    >
      <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3 dark:border-slate-800">
        <h2 className="section-label">
          <span className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-50 text-brand-700 dark:bg-brand-500/10 dark:text-brand-300">
            <MessageSquareText size={14} />
          </span>
          Answer
        </h2>
      </div>
      <p className="px-5 py-5 text-[15px] leading-7 text-slate-800 sm:px-6 sm:text-base sm:leading-7 dark:text-slate-100">
        {answer}
      </p>
    </motion.section>
  );
}
