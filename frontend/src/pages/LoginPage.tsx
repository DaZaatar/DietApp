import { FormEvent, useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { fetchSession, loginRequest, setApiUserId } from "../shared/lib/api";

function safeNext(raw: string | null): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) {
    return "/";
  }
  return raw;
}

function EyeIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
      />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

function EyeSlashIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 15.338 7.244 18 12 18c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 2.662 10.065 6.006a1.125 1.125 0 01-.372 1.287l-1.293 1.293M6.228 6.228 3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"
      />
    </svg>
  );
}

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const next = safeNext(searchParams.get("next"));
  const registered = searchParams.get("registered") === "1";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    const fromRegister = (location.state as { email?: string } | undefined)?.email;
    if (fromRegister) {
      setEmail(fromRegister);
    }
  }, [location.state]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const session = await fetchSession();
      if (!cancelled && session) {
        setApiUserId(String(session.id));
        navigate(next, { replace: true });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [navigate, next]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const res = await loginRequest(email, password, rememberMe);
      setApiUserId(String(res.user_id));
      navigate(next, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-md">
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Sign in</h1>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Use your DietApp account. You will return to{" "}
          <span className="font-medium text-slate-800 dark:text-slate-200">{next}</span> after signing in.
        </p>
        {registered && (
          <p className="mt-3 rounded-lg bg-emerald-50 p-2 text-sm text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-200">
            Account created. Sign in below.
          </p>
        )}
        <form className="mt-6 space-y-4" onSubmit={onSubmit}>
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">Email</label>
            <input
              className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-slate-700 dark:text-slate-300" htmlFor="login-password">
              Password
            </label>
            <div className="relative mt-1">
              <input
                id="login-password"
                className="w-full rounded-md border border-slate-300 bg-white py-2 pl-3 pr-10 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button
                type="button"
                className="absolute inset-y-0 right-0 flex items-center justify-center rounded-r-md px-2.5 text-slate-500 outline-none ring-slate-400 ring-offset-2 hover:text-slate-800 focus-visible:ring-2 dark:text-slate-400 dark:hover:text-slate-200 dark:ring-offset-slate-900"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                aria-pressed={showPassword}
              >
                {showPassword ? <EyeSlashIcon /> : <EyeIcon />}
              </button>
            </div>
          </div>
          <label className="flex cursor-pointer items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
            />
            Remember me on this device (keeps you signed in via a secure cookie)
          </label>
          {error && (
            <p className="rounded-lg bg-rose-50 p-2 text-sm text-rose-800 dark:bg-rose-950/50 dark:text-rose-200">{error}</p>
          )}
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-slate-900 py-2.5 text-sm font-medium text-white disabled:opacity-50 dark:bg-brand-600 dark:hover:bg-brand-700"
          >
            {busy ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-600 dark:text-slate-400">
          No account?{" "}
          <Link
            className="font-medium text-brand-700 hover:underline dark:text-brand-400"
            to={`/register?next=${encodeURIComponent(next)}`}
          >
            Register
          </Link>
        </p>
        <p className="mt-4 text-center">
          <Link className="text-sm text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200" to="/">
            Back to meal tracker
          </Link>
        </p>
      </div>
    </div>
  );
}
