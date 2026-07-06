import os
import sys
from dotenv import load_dotenv

# Ensure both the project root and app package folder are on the import path.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_FOLDER = os.path.join(PROJECT_ROOT, 'Laundry_Berkah')
for path in [PROJECT_ROOT, APP_FOLDER]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Load environment variables from root or Laundry_Berkah folder if present.
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
load_dotenv(os.path.join(APP_FOLDER, '.env'))

from app import create_app  # noqa: E402

config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)
application = app
# Debug marker for server logs to confirm this entrypoint is used
try:
    print('[ENTRYPOINT] Loaded entrypoint.py; using config:', config_name)
except Exception:
    pass
