"""
Flask Application Entry Point
Run: python app.py
"""
import os
import sys
from dotenv import load_dotenv
from urllib.parse import urlparse

# Ensure the current package directory is on the import path.
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

# Load environment variables
load_dotenv()

# Create Flask app
from app import create_app, db

# Get configuration
config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)


def describe_database(uri):
    """Return a safe database label for startup logs."""
    parsed = urlparse(uri)
    if parsed.scheme.startswith('sqlite'):
        return f"SQLite ({parsed.path.lstrip('/')})"
    if parsed.hostname:
        return f"{parsed.scheme}://{parsed.hostname}:{parsed.port or ''}/{parsed.path.lstrip('/')}"
    return parsed.scheme or 'unknown'

# Shell context for flask shell
@app.shell_context_processor
def make_shell_context():
    """Add models and database to shell context"""
    from app.models.role import Role
    from app.models.user import User
    from app.models.pelanggan import Pelanggan
    from app.models.transaksi import Transaksi
    from app.models.detail_transaksi import DetailTransaksi
    from app.models.pembayaran import Pembayaran
    from app.models.layanan import Layanan
    from app.models.parfum import Parfum
    from app.models.promo import Promo
    from app.models.status import Status
    
    return {
        'db': db,
        'Role': Role,
        'User': User,
        'Pelanggan': Pelanggan,
        'Transaksi': Transaksi,
        'DetailTransaksi': DetailTransaksi,
        'Pembayaran': Pembayaran,
        'Layanan': Layanan,
        'Parfum': Parfum,
        'Promo': Promo,
        'Status': Status,
    }


@app.before_request
def before_request():
    """Before request hooks"""
    pass


@app.after_request
def after_request(response):
    """After request hooks"""
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  [APP] Laundry Berkah Application")
    print(f"  [ENV] Environment: {config_name}")
    print(f"  [DB] Database: {describe_database(app.config['SQLALCHEMY_DATABASE_URI'])}")
    print("="*60 + "\n")
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    try:
        print("[OK] Starting Flask application...")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=app.config['DEBUG']
        )
    except Exception as e:
        print(f"[ERROR] Error starting application: {e}")
        sys.exit(1)
