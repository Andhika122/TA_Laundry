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

Notes & troubleshooting

- The repo contains `Laundry_Berkah` as the app package; `entrypoint.py` inserts that folder into `sys.path` at runtime so imports like `from app import create_app` resolve correctly.
- If VS Code shows a Pylance warning for `from app import create_app`, reload the window or use `.vscode/settings.json` (already added).
- If Vercel still crashes, paste the function log here and I'll analyze it.
