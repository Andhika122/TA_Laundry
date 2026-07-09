Laundry Berkah - Deploy Notes

Quick deploy to Vercel

1. Ensure the repository contains these files at the project root:
   - `api/index.py`
   - `entrypoint.py`
   - `vercel.json`
   - `requirements.txt`

2. Set the Vercel environment variables:
   - `FLASK_ENV=production`
   - `USE_SQLITE_FALLBACK=false`
   - `VERCEL=1`
   - `SECRET_KEY` set to a secure random string
   - `DATABASE_URL` with a TiDB/MySQL SQLAlchemy URL, or all of:
     `TIDB_HOST`, `TIDB_USER`, `TIDB_PASSWORD`, `TIDB_DB`
   - Optional for TiDB TLS: `TIDB_SSL_CA_CONTENT` containing the PEM certificate text
   - Optional writable paths: `UPLOAD_FOLDER=/tmp/uploads`, `LOG_DIR=/tmp/logs`

3. Commit, push, then redeploy from the Vercel dashboard.

Database behavior

- TiDB/MySQL is required outside tests.
- SQLite is only used for automated tests with in-memory databases.
- Default roles, users, services, perfumes, and promos are seeded automatically into TiDB during app startup.

Troubleshooting

- If a dropdown is empty on Vercel, check the latest deployment logs for TiDB connection or schema errors.
- Confirm the TiDB database has the `app_layanan` table and that seed startup completed.
- For recent function logs with Vercel CLI:

```bash
vercel logs your-project-name.vercel.app --since 10m --output=raw
```
