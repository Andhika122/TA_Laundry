Laundry Berkah — Deploy notes

Quick deploy to Vercel

1. Ensure repository contains these files at project root:
   - `entrypoint.py` (application entrypoint)
   - `vercel.json` (build config pointing to `entrypoint.py`)
   - `requirements.txt` (Python dependencies)

2. Commit and push changes:

```bash
git add entrypoint.py vercel.json requirements.txt Laundry_Berkah/requirements.txt .vscode/settings.json README.md
git commit -m "Prepare Vercel deploy: entrypoint + requirements + pylance config"
git push
```

3. Redeploy on Vercel (automatic on push) and check logs:
   - Open Vercel dashboard → Deployments → select latest deployment.
   - In Build / Function logs look for this marker to confirm entrypoint was used:
     `[ENTRYPOINT] Loaded entrypoint.py; using config: <env>`
   - If you see an import error (No module named 'app'), ensure `vercel.json` uses `entrypoint.py`.

Vercel-specific configuration notes

- Provide production database credentials via `DATABASE_URL` (preferred) or the `TIDB_*` vars below.
- If your TiDB provider requires an SSL CA, set either:
   - `TIDB_SSL_CA_CONTENT` to the full PEM text of the certificate (recommended), or
   - `TIDB_SSL_CA` to the PEM text (the app will accept PEM content), but do NOT point to a local filesystem path (that won't be available on Vercel).
- Environment variables to set in Vercel (Project → Settings → Environment Variables):
   - `FLASK_ENV=production`
   - `USE_SQLITE_FALLBACK=false`
   - `VERCEL=1`
   - `SECRET_KEY` (set to a secure random string)
   - `DATABASE_URL` (recommended) or `TIDB_HOST`, `TIDB_USER`, `TIDB_PASSWORD`, `TIDB_DB`
   - Optional writable paths for Vercel runtime: `UPLOAD_FOLDER=/tmp/uploads`, `LOG_DIR=/tmp/logs`

When troubleshooting login errors
- Reproduce the login attempt, then open Vercel → Deployments → select deployment → Logs → Function/Runtime and copy the traceback starting at `Traceback`.
- Check for messages like `OperationalError`, `Access denied`, `Timeout`, or the custom message `Unhandled exception in login` which indicates the server logged the error with more details.

CLI method to fetch function logs (recommended)

If you have the Vercel CLI installed, fetch recent logs and look for the traceback lines. Example commands:

```bash
# Last 10 minutes for your deployment domain
vercel logs your-project-name.vercel.app --since 10m --output=raw

# Or use the deployment URL (replace with your domain)
vercel logs ta-laundry-gilt.vercel.app --since 10m --output=raw
```

Copy the output starting from the first `Traceback` line through the end of the stack; paste that into the chat and I'll analyze it.

Vercel environment-variable checklist

- `FLASK_ENV=production`
- `USE_SQLITE_FALLBACK=false`
- `VERCEL=1`
- `SECRET_KEY` (secure random string)
- `DATABASE_URL` (preferred) or `TIDB_HOST`, `TIDB_USER`, `TIDB_PASSWORD`, `TIDB_DB`
- If TiDB requires TLS: `TIDB_SSL_CA_CONTENT` containing the PEM certificate text


Notes & troubleshooting

- The repo contains `Laundry_Berkah` as the app package; `entrypoint.py` inserts that folder into `sys.path` at runtime so imports like `from app import create_app` resolve correctly.
- If VS Code shows a Pylance warning for `from app import create_app`, reload the window or use `.vscode/settings.json` (already added).
- If Vercel still crashes, paste the function log here and I'll analyze it.
