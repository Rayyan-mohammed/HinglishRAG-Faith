import { motion } from "framer-motion";

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
    >
      <div className="card space-y-3 p-5 sm:p-6">
        <Bar width="30%" />
        <Bar width="95%" />
        <Bar width="88%" />
        <Bar width="60%" />
      </div>
      {verifying && (
        <div className="space-y-2.5">
          {[0, 1, 2].map((i) => (
            <div key={i} className="card flex items-center gap-3 p-4">
              <div className="shimmer-bg h-6 w-24 animate-shimmer rounded-full" />
              <div className="shimmer-bg h-3.5 flex-1 animate-shimmer rounded-full" />
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
