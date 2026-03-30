import { useEffect, useState } from "react";
import { Link, NavLink, Navigate, Outlet, Route, Routes, useLocation } from "react-router-dom";

import { clearAuth, fetchSession, getApiUserId, setApiUserId, type SessionUser } from "../shared/lib/api";
import { ThemeToggleButton } from "../shared/components/ThemeToggleButton";
import { AuthLayout } from "./AuthLayout";
import { ImportPage } from "../pages/ImportPage";
import { LoginPage } from "../pages/LoginPage";
import { RegisterPage } from "../pages/RegisterPage";
import { ReportsPage } from "../pages/ReportsPage";
import { ShoppingPage } from "../pages/ShoppingPage";
import { TrackingPage } from "../pages/TrackingPage";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    "rounded-md px-3 py-2 text-sm",
    isActive
      ? "bg-slate-200 font-medium text-slate-900 dark:bg-slate-800 dark:text-slate-50"
      : "text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800",
  ].join(" ");

function MainLayout() {
  const location = useLocation();
  const [userId, setUserId] = useState(getApiUserId());
  const [session, setSession] = useState<SessionUser | null>(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

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

  useEffect(() => {
    setMobileNavOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 768px)");
    const onChange = () => {
      if (mq.matches) setMobileNavOpen(false);
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  function onUserIdChange(nextUserId: string) {
    setUserId(nextUserId);
    setApiUserId(nextUserId);
  }

  async function onLogout() {
    await clearAuth();
    setSession(null);
  }

  const nextParam = encodeURIComponent(`${location.pathname}${location.search || ""}`);

  if (sessionLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950">
        <p className="text-sm text-slate-600 dark:text-slate-400">Loading…</p>
      </div>
    );
  }

  if (!session) {
    return <Navigate to={`/login?next=${nextParam}`} replace />;
  }

  const mainNav = (
    <>
      <NavLink to="/" end className={navLinkClass} onClick={() => setMobileNavOpen(false)}>
        Meal Tracker
      </NavLink>
      <NavLink to="/import" className={navLinkClass} onClick={() => setMobileNavOpen(false)}>
        Import
      </NavLink>
      <NavLink to="/shopping" className={navLinkClass} onClick={() => setMobileNavOpen(false)}>
        Shopping
      </NavLink>
      <NavLink to="/reports" className={navLinkClass} onClick={() => setMobileNavOpen(false)}>
        Reports
      </NavLink>
    </>
  );

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <header className="border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <nav className="mx-auto flex max-w-4xl flex-col gap-3 p-4" aria-label="Main">
          <div className="flex items-center justify-between gap-3">
            <div className="flex min-w-0 items-center gap-2">
              <button
                type="button"
                className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-md border border-slate-300 text-slate-800 md:hidden dark:border-slate-600 dark:text-slate-100"
                aria-expanded={mobileNavOpen}
                aria-controls="main-app-nav"
                aria-label={mobileNavOpen ? "Close menu" : "Open menu"}
                onClick={() => setMobileNavOpen((o) => !o)}
              >
                <span className="sr-only">Menu</span>
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  {mobileNavOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
              <Link to="/" className="truncate text-lg font-semibold text-slate-900 dark:text-slate-100">
                DietApp
              </Link>
            </div>
            <div className="flex flex-wrap items-center justify-end gap-2">
              <ThemeToggleButton />
              <div className="flex max-w-[min(200px,50vw)] flex-wrap items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
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
            </div>
          </div>

          <div id="main-app-nav" className="hidden flex-wrap gap-2 md:flex">
            {mainNav}
          </div>

          {mobileNavOpen ? (
            <div className="flex flex-col gap-1 border-t border-slate-200 pt-3 dark:border-slate-700 md:hidden">
              {mainNav}
            </div>
          ) : null}

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
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
      </Route>
      <Route element={<MainLayout />}>
        <Route path="/" element={<TrackingPage />} />
        <Route path="/tracking" element={<Navigate to="/" replace />} />
        <Route path="/import" element={<ImportPage />} />
        <Route path="/shopping" element={<ShoppingPage />} />
        <Route path="/reports" element={<ReportsPage />} />
      </Route>
    </Routes>
  );
}
