import os
import sys
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_FOLDER = os.path.join(PROJECT_ROOT, 'Laundry_Berkah')
for path in [PROJECT_ROOT, APP_FOLDER]:
    if path not in sys.path:
        sys.path.insert(0, path)

if os.getenv('VERCEL', '').strip() != '1':
    load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
    load_dotenv(os.path.join(APP_FOLDER, '.env'))

from app import create_app  # noqa: E402

config_name = os.getenv('FLASK_ENV') or (
    'production' if os.getenv('VERCEL', '').strip() == '1' else 'development'
)
app = create_app(config_name)
application = app
