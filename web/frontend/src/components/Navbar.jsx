import { ShieldCheck } from "lucide-react";
import ThemeToggle from "./ThemeToggle.jsx";

const LINKS = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#schemes", label: "Schemes" },
];

export default function Navbar({ theme, onToggleTheme }) {
  return (
    <header
      className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/85 backdrop-blur-md
        dark:border-slate-800/80 dark:bg-slate-950/85"
    >
      <nav
        aria-label="Primary"
        className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6"
      >
        <a href="#top" className="focus-ring flex items-center gap-2.5 rounded-lg">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white shadow-sm shadow-brand-600/30">
            <ShieldCheck size={17} strokeWidth={2.25} />
          </span>
          <span className="text-[15px] font-semibold tracking-tight text-slate-900 dark:text-white">
            CodeSwitch<span className="text-brand-700 dark:text-brand-400">-Verify</span>
          </span>
        </a>

        <div className="flex items-center gap-1 sm:gap-2">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="focus-ring hidden rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition
                hover:bg-slate-100 hover:text-slate-900 sm:block
                dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
            >
              {l.label}
            </a>
          ))}
          <span
            className="mx-1 hidden items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1
              text-xs font-medium text-emerald-700 md:flex
              dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-300"
          >
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-500 opacity-60 motion-reduce:hidden" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
            </span>
            Live demo
          </span>
          <ThemeToggle theme={theme} onToggle={onToggleTheme} />
        </div>
      </nav>
    </header>
  );
}
