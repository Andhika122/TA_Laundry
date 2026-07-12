Laundry Berkah - Deploy Notes

Quick deploy to Vercel

1. Ensure the repository contains these files at the project root:
   - `api/index.py`
   - `entrypoint.py`
   - `vercel.json`
   - `requirements.txt`

2. Set the Vercel environment variables:
   - `SECRET_KEY` set to a secure random string
   - `DATABASE_URL` with a TiDB/MySQL SQLAlchemy URL, or all of:
     `TIDB_HOST`, `TIDB_USER`, `TIDB_PASSWORD`, `TIDB_DB`
   - Optional for TiDB TLS: `TIDB_SSL_CA_CONTENT` containing the PEM certificate text
   - Fonnte: `FONTE_TOKEN` (device token) and
     `FONTE_API_URL=https://api.fonnte.com/send`
   - Optional receipt image attachment: `CLOUDINARY_CLOUD_NAME`,
     `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
   - Optional email: `RESEND_API_KEY`, `RESEND_FROM_EMAIL`,
     `CONTACT_RECIPIENT_EMAIL`

   Add the variables to **Production** (and Preview too if it is used for
   testing). Vercel provides the `VERCEL=1` runtime variable automatically;
   this project automatically selects production mode when it is present.
   Use `Laundry_Berkah/.env.example` as the complete key list, but never upload
   the actual `.env` file or tokens.

3. Commit, push, then redeploy from the Vercel dashboard. Every environment
   variable update only affects newly created deployments.

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
