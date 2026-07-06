import os
import sys
from dotenv import load_dotenv

# Project root is parent of this file
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_FOLDER = os.path.join(PROJECT_ROOT, 'Laundry_Berkah')
if APP_FOLDER not in sys.path:
    sys.path.insert(0, APP_FOLDER)

# Load environment variables
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
load_dotenv(os.path.join(APP_FOLDER, '.env'))

# Prefer entrypoint if present (it builds the app and sets config)
try:
    from entrypoint import app  # type: ignore
    print('[API] Loaded app from entrypoint')
except Exception:
    # Fallback: build app directly
    from app import create_app  # type: ignore
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(config_name)
    print('[API] Built app via create_app')
