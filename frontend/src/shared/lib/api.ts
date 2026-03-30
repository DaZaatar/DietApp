/** Same-origin default (/api/v1) works with Vite dev proxy and with production Docker (API + static). */
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
const DEFAULT_USER_ID = import.meta.env.VITE_DEFAULT_USER_ID ?? "";
const USER_ID_STORAGE_KEY = "dietapp_user_id";

function readStoredUserId(): string {
  if (typeof window === "undefined") {
    return DEFAULT_USER_ID;
  }
  return window.localStorage.getItem(USER_ID_STORAGE_KEY) ?? DEFAULT_USER_ID;
}

/** @deprecated Prefer HttpOnly session cookie; kept for migration / tooling */
export function getAccessToken(): string {
  return "";
}

export function setAccessToken(_token: string | null): void {
  /* Token lives in HttpOnly cookie set by POST /auth/login */
}

export async function clearAuth(): Promise<void> {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: buildHeaders(),
      credentials: "include",
    });
  } catch {
    /* ignore */
  }
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(USER_ID_STORAGE_KEY);
  }
}

export function getApiUserId(): string {
  return readStoredUserId();
}

export function setApiUserId(userId: string): void {
  if (typeof window === "undefined") return;
  const trimmed = userId.trim();
  if (!trimmed) {
    window.localStorage.removeItem(USER_ID_STORAGE_KEY);
    return;
  }
  window.localStorage.setItem(USER_ID_STORAGE_KEY, trimmed);
}

export type SessionUser = { id: number; email: string };

function buildHeaders(baseHeaders?: HeadersInit): Headers {
  const headers = new Headers(baseHeaders);
  const userId = readStoredUserId();
  if (userId) {
    headers.set("X-User-Id", userId);
  }
  return headers;
}

function networkErrorMessage(err: unknown): string {
  if (err instanceof TypeError) {
    return (
      `Cannot reach the API (${API_BASE}). Start the backend (e.g. uvicorn on port 8000). ` +
      `With Vite dev, requests use the /api proxy to localhost:8000 — ensure nothing blocks that port.`
    );
  }
  return err instanceof Error ? err.message : "Request failed";
}

function formatDetail(detail: unknown): string {
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          const loc = "loc" in item && Array.isArray((item as { loc: unknown }).loc)
            ? `${(item as { loc: string[] }).loc.filter((x) => x !== "body").join(".")}: `
            : "";
          return `${loc}${String((item as { msg: unknown }).msg)}`;
        }
        try {
          return JSON.stringify(item);
        } catch {
          return String(item);
        }
      })
      .join("; ");
  }
  if (detail && typeof detail === "object") {
    try {
      return JSON.stringify(detail);
    } catch {
      return "Request failed";
    }
  }
  if (detail == null) {
    return "Something went wrong.";
  }
  return String(detail);
}

/** Turns FastAPI / proxy error bodies into a single readable line for UI copy. */
export function parseApiErrorBody(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) {
    return "Something went wrong.";
  }
  try {
    const parsed = JSON.parse(trimmed) as { detail?: unknown };
    if (parsed && typeof parsed === "object" && "detail" in parsed) {
      return formatDetail(parsed.detail);
    }
  } catch {
    /* plain text or HTML */
  }
  if (trimmed.length > 280) {
    return `${trimmed.slice(0, 280)}…`;
  }
  return trimmed;
}

async function errorMessageFromResponse(response: Response): Promise<string> {
  const text = await response.text();
  return parseApiErrorBody(text);
}

const fetchDefaults: RequestInit = {
  credentials: "include",
};

export async function fetchSession(): Promise<SessionUser | null> {
  try {
    const response = await fetch(`${API_BASE}/auth/me`, {
      ...fetchDefaults,
      headers: buildHeaders(),
    });
    if (!response.ok) {
      return null;
    }
    return response.json() as Promise<SessionUser>;
  } catch {
    return null;
  }
}

export async function postForm<T>(path: string, formData: FormData): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...fetchDefaults,
      method: "POST",
      headers: buildHeaders(),
      body: formData,
    });
    if (!response.ok) {
      throw new Error(await errorMessageFromResponse(response));
    }
    return response.json() as Promise<T>;
  } catch (err) {
    throw new Error(networkErrorMessage(err));
  }
}

export async function postJson<T>(path: string, payload: unknown): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...fetchDefaults,
      method: "POST",
      headers: buildHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(await errorMessageFromResponse(response));
    }
    return response.json() as Promise<T>;
  } catch (err) {
    throw new Error(networkErrorMessage(err));
  }
}

export async function patchJson<T>(path: string, payload: unknown): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...fetchDefaults,
      method: "PATCH",
      headers: buildHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error(await errorMessageFromResponse(response));
    }
    return response.json() as Promise<T>;
  } catch (err) {
    throw new Error(networkErrorMessage(err));
  }
}

export async function getJson<T>(path: string): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...fetchDefaults,
      headers: buildHeaders(),
    });
    if (!response.ok) {
      throw new Error(await errorMessageFromResponse(response));
    }
    return response.json() as Promise<T>;
  } catch (err) {
    throw new Error(networkErrorMessage(err));
  }
}

export function getApiBasePath(): string {
  return API_BASE;
}

export function buildApiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

export async function deleteJson<T>(path: string): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      ...fetchDefaults,
      method: "DELETE",
      headers: buildHeaders(),
    });
    if (!response.ok) {
      throw new Error(await errorMessageFromResponse(response));
    }
    const text = await response.text();
    if (!text.trim()) {
      return {} as T;
    }
    return JSON.parse(text) as T;
  } catch (err) {
    throw new Error(networkErrorMessage(err));
  }
}

export async function loginRequest(
  email: string,
  password: string,
  rememberMe: boolean,
): Promise<{ user_id: number; email: string }> {
  return postJson("/auth/login", { email, password, remember_me: rememberMe });
}

export async function registerRequest(email: string, password: string): Promise<{ id: number; email: string }> {
  return postJson("/auth/register", { email, password });
}
