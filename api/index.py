import os
import sys
import traceback
from dotenv import load_dotenv

# Project root is parent of this file
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_FOLDER = os.path.join(PROJECT_ROOT, 'Laundry_Berkah')
for path in [PROJECT_ROOT, APP_FOLDER]:
    if path not in sys.path:
        sys.path.insert(0, path)

# Load environment variables
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
load_dotenv(os.path.join(APP_FOLDER, '.env'))

# Attempt to load the real Flask app. If anything goes wrong, we expose a
# minimal WSGI fallback that returns a 500 and prints the original traceback
# so Vercel logs show the root cause.
_init_exc = None
app = None
try:
    # Preferred: reuse entrypoint if present
    from entrypoint import app as _real_app  # type: ignore
    app = _real_app
    print('[API] Loaded app from entrypoint')
except Exception as e_entry:
    # Try to build directly from the package
    try:
        from app import create_app  # type: ignore
        config_name = os.getenv('FLASK_ENV', 'development')
        app = create_app(config_name)
        print('[API] Built app via create_app')
    except Exception as e_build:
        _init_exc = e_build
        # Combine tracebacks
        tb = traceback.format_exc()
        print('[API] Failed to initialize Flask app; storing fallback handler')
        print(tb)

if app is None:
    # Provide a simple WSGI app that surfaces the initialization error.
    def app(environ, start_response):
        body = 'Application initialization failed. Check logs for details.\n'
        if _init_exc is not None:
            body += 'Error: ' + repr(_init_exc) + '\n'
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return [body.encode('utf-8')]

application = app
