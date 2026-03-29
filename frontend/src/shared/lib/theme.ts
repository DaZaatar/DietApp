const STORAGE_KEY = "dietapp-theme";

export type ThemeMode = "light" | "dark";

function getStoredMode(): ThemeMode | null {
  if (typeof window === "undefined") return null;
  const v = window.localStorage.getItem(STORAGE_KEY);
  if (v === "dark" || v === "light") return v;
  return null;
}

export function applyTheme(mode: ThemeMode): void {
  if (typeof document === "undefined") return;
  document.documentElement.classList.toggle("dark", mode === "dark");
}

export function initThemeFromStorage(): ThemeMode {
  if (typeof window === "undefined") return "light";
  const stored = getStoredMode();
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const mode: ThemeMode = stored ?? (prefersDark ? "dark" : "light");
  applyTheme(mode);
  return mode;
}

export function toggleStoredTheme(): ThemeMode {
  const next: ThemeMode = document.documentElement.classList.contains("dark") ? "light" : "dark";
  window.localStorage.setItem(STORAGE_KEY, next);
  applyTheme(next);
  return next;
}
