---
name: stop-dev-servers
description: >-
  Stops the DietApp local dev processes listening on ports 8000 (backend) and
  5173 (frontend). Use when the user asks to stop, kill, or shut down the dev
  servers, uvicorn, or Vite.
---

# Stop dev servers

## Preferred (interactive)

In each terminal where `uvicorn` or `npm run dev` is running, press **Ctrl+C**.

## Windows PowerShell (ports 8000 and 5173)

If processes were started in the background or another session, stop listeners on the dev ports:

```powershell
foreach ($port in 8000, 5173) {
  Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}
```

Run from any directory; may require matching the user that owns the process (same Windows session is usually enough).

## Note

This targets **listen** processes on those ports only. It does not stop other apps that might coincidentally use the same ports after you switch projects.
