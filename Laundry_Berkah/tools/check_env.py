import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / '.env')
load_dotenv(Path(__file__).resolve().parents[2] / '.env')


def env_value(name):
    value = os.getenv(name)
    return value.strip() if value else ''


def check_required(name, present):
    if not present:
        print(f'  - MISSING: {name}')
        return False
    print(f'  - OK: {name}')
    return True


def main():
    print('Checking required environment variables...')
    print('Note: local .env values are loaded only when present.')

    all_ok = True
    all_ok &= check_required('SECRET_KEY', bool(env_value('SECRET_KEY')))

    database_ok = bool(env_value('DATABASE_URL')) or (
        bool(env_value('TIDB_HOST')) and bool(env_value('TIDB_USER')) and bool(env_value('TIDB_DB'))
    )
    all_ok &= check_required('DATABASE_URL or TIDB_HOST+TIDB_USER+TIDB_DB', database_ok)
    all_ok &= check_required('FONTE_TOKEN', bool(env_value('FONTE_TOKEN')))
    all_ok &= check_required('FONTE_API_URL', bool(env_value('FONTE_API_URL')))

    if env_value('FONTE_API_URL'):
        print('  - Info: Fonte API URL set to', env_value('FONTE_API_URL'))
        if 'fonte.id' in env_value('FONTE_API_URL'):
            print('    * Warning: fonte.id URLs are normalized, but prefer https://api.fonnte.com/send')

    if not env_value('CLOUDINARY_CLOUD_NAME'):
        print('  - Info: CLOUDINARY_* not fully configured; image upload will fallback to signed URLs.')

    if all_ok:
        print('\nEnvironment validation succeeded. Ready for local run or Vercel deployment.')
        return 0

    print('\nEnvironment validation failed. Fix missing values before starting the app.')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
