import { Link, Outlet } from "react-router-dom";

import { ThemeToggleButton } from "../shared/components/ThemeToggleButton";

/**
 * Auth-only shell: no main app navigation or dev controls — only brand, theme, and page content.
 */
export function AuthLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50 dark:bg-slate-950">
      <header className="flex shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
        <Link to="/" className="text-lg font-semibold text-slate-900 dark:text-slate-100">
          DietApp
        </Link>
        <ThemeToggleButton />
      </header>
      <main className="flex flex-1 flex-col justify-center px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
