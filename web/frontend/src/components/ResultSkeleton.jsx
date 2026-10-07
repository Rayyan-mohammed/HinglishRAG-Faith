import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";

function Bar({ width = "100%" }) {
  return (
    <div
      className="shimmer-bg h-3.5 animate-shimmer rounded-full"
      style={{ width }}
    />
  );
}

export default function ResultSkeleton({ verifying }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="mt-6 space-y-4"
      aria-busy="true"
    >
      <p
        role="status"
        className="flex items-center gap-2 text-sm font-medium text-brand-700 dark:text-brand-300"
      >
        <Loader2 size={15} className="animate-spin" />
        {verifying
          ? "Retrieving sources, generating an answer and checking each claim…"
          : "Retrieving sources and generating an answer…"}
      </p>
      <div className="card space-y-3 p-5 sm:p-6">
        <Bar width="22%" />
        <Bar width="95%" />
        <Bar width="88%" />
        <Bar width="60%" />
      </div>
      {verifying && (
        <div className="card divide-y divide-slate-100 dark:divide-slate-800">
          {[0, 1, 2].map((i) => (
            <div key={i} className="flex items-center gap-3.5 p-4">
              <div className="shimmer-bg h-8 w-8 shrink-0 animate-shimmer rounded-lg" />
              <div className="flex-1 space-y-2">
                <div className="shimmer-bg h-3.5 animate-shimmer rounded-full" />
                <div className="shimmer-bg h-3 w-28 animate-shimmer rounded-full" />
              </div>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
