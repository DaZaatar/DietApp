import { useEffect, useState } from "react";
import { Link, Outlet, Route, Routes, useLocation } from "react-router-dom";

import { clearAuth, fetchSession, getApiUserId, setApiUserId, type SessionUser } from "../shared/lib/api";
import { toggleStoredTheme, type ThemeMode } from "../shared/lib/theme";
import { ImportPage } from "../pages/ImportPage";
import { LoginPage } from "../pages/LoginPage";
import { RegisterPage } from "../pages/RegisterPage";
import { ShoppingPage } from "../pages/ShoppingPage";
import { TrackingPage } from "../pages/TrackingPage";

function MainLayout() {
  const location = useLocation();
  const [userId, setUserId] = useState(getApiUserId());
  const [session, setSession] = useState<SessionUser | null>(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [theme, setTheme] = useState<ThemeMode>(() =>
    typeof document !== "undefined" && document.documentElement.classList.contains("dark") ? "dark" : "light",
  );

  const nextParam = encodeURIComponent(`${location.pathname}${location.search || ""}`);

  useEffect(() => {
    let active = true;
    void (async () => {
      const s = await fetchSession();
      if (!active) return;
      setSession(s);
      if (s) {
        setApiUserId(String(s.id));
        setUserId(String(s.id));
      }
      setSessionLoading(false);
    })();
    return () => {
      active = false;
    };
  }, []);

  function onUserIdChange(nextUserId: string) {
    setUserId(nextUserId);
    setApiUserId(nextUserId);
  }

  async function onLogout() {
    await clearAuth();
    setSession(null);
  }

  function onToggleTheme() {
    const next = toggleStoredTheme();
    setTheme(next);
  }

  const loggedIn = Boolean(session);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <nav className="mx-auto flex max-w-4xl flex-wrap items-center justify-between gap-3 p-4">
          <Link to="/" className="text-lg font-semibold text-slate-900 dark:text-slate-100">
            DietApp
          </Link>
          <div className="flex flex-wrap gap-2">
            <Link
              className="rounded-md px-3 py-2 text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
              to="/"
            >
              Import
            </Link>
            <Link
              className="rounded-md px-3 py-2 text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
              to="/tracking"
            >
              Meal Tracker
            </Link>
            <Link
              className="rounded-md px-3 py-2 text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
              to="/shopping"
            >
              Shopping
            </Link>
          </div>
          <div className="flex w-full flex-col gap-2 sm:ml-auto sm:w-auto sm:min-w-[220px]">
            <div className="flex flex-wrap items-center justify-end gap-2">
              <button
                type="button"
                onClick={onToggleTheme}
                className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-800 dark:border-slate-600 dark:text-slate-200"
                title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
              >
                {theme === "dark" ? "Light" : "Dark"}
              </button>
              {!sessionLoading && !loggedIn && (
                <>
                  <Link
                    className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-800 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-100 dark:hover:bg-slate-800"
                    to={`/login?next=${nextParam}`}
                  >
                    Sign in
                  </Link>
                  <Link
                    className="rounded-md bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-800 dark:bg-brand-600 dark:hover:bg-brand-700"
                    to={`/register?next=${nextParam}`}
                  >
                    Register
                  </Link>
                </>
              )}
              {loggedIn && (
                <div className="flex flex-wrap items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
                  <span className="truncate" title={session?.email}>
                    {session?.email}
                  </span>
                  <button
                    type="button"
                    className="rounded-md border border-slate-300 px-2 py-1 text-xs text-slate-800 dark:border-slate-600 dark:text-slate-200"
                    onClick={() => void onLogout()}
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
            <label className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
              Dev user ID
              <input
                className="w-16 rounded-md border border-slate-300 bg-white px-2 py-1 text-xs text-slate-800 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
                type="number"
                min="1"
                value={userId}
                onChange={(e) => onUserIdChange(e.target.value)}
                placeholder="1"
                title="Used when no session cookie (local dev)"
              />
            </label>
          </div>
        </nav>
      </header>
      <main className="mx-auto w-full max-w-4xl p-4 sm:p-6">
        <Outlet />
      </main>
    </div>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<MainLayout />}>
        <Route path="/" element={<ImportPage />} />
        <Route path="/tracking" element={<TrackingPage />} />
        <Route path="/shopping" element={<ShoppingPage />} />
      </Route>
    </Routes>
  );
}
