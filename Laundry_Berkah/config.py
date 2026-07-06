"""
Flask Configuration
Database: SQLite for local development, TiDB/MySQL for production
"""
import os
from datetime import timedelta
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

BASE_DIR = os.path.dirname(__file__)
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)

_CONFIG_IMPORTED = False


def env_flag(name, default='false'):
    """Read an environment flag from the current process environment."""
    return os.getenv(name, default).lower() in {'1', 'true', 'yes', 'on'}


def is_testing_environment():
    return os.getenv('FLASK_ENV', 'development').lower() == 'testing' or env_flag('TESTING')


def should_use_sqlite_fallback():
    return env_flag('USE_SQLITE_FALLBACK')


def get_sqlite_uri(filename='laundry.db'):
    """Return a SQLite URI stored inside the Flask instance folder."""
    database_path = os.path.join(INSTANCE_DIR, filename)
    return f"sqlite:///{database_path.replace(os.sep, '/')}"


def build_tidb_uri(user, password, host, port, database):
    """Build a TiDB/MySQL SQLAlchemy URI without exposing credentials in code."""
    encoded_user = quote_plus(user)
    encoded_password = quote_plus(password)
    return f"mysql+pymysql://{encoded_user}:{encoded_password}@{host}:{port}/{database}"


def get_database_uri():
    """Resolve the SQLAlchemy database URI from the current environment."""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    if is_testing_environment():
        return 'sqlite:///:memory:'
    if os.getenv('FLASK_ENV', 'development').lower() != 'production':
        return get_sqlite_uri()
    if should_use_sqlite_fallback():
        return get_sqlite_uri()

    return build_tidb_uri(
        os.getenv('TIDB_USER', 'root'),
        os.getenv('TIDB_PASSWORD', ''),
        os.getenv('TIDB_HOST', 'localhost'),
        os.getenv('TIDB_PORT', '4000'),
        os.getenv('TIDB_DB', 'db_laundry'),
    )


def get_engine_options(database_uri=None):
    """Build SQLAlchemy engine options for the active database backend."""
    database_uri = database_uri or get_database_uri()
    options = {}
    if database_uri and database_uri.startswith('mysql'):
        options = {
            'pool_size': 10,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'echo': env_flag('SQLALCHEMY_ECHO'),
        }
        ssl_ca = os.getenv('TIDB_SSL_CA')
        if ssl_ca:
            options['connect_args'] = {'ssl_ca': ssl_ca}
    else:
        options = {'echo': env_flag('SQLALCHEMY_ECHO')}
    return options


class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = FLASK_ENV == 'development'
    TESTING = is_testing_environment()
    USE_SQLITE_FALLBACK = should_use_sqlite_fallback()
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set True untuk HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database - TiDB
    TIDB_HOST = os.getenv('TIDB_HOST', 'localhost')
    TIDB_PORT = os.getenv('TIDB_PORT', '4000')
    TIDB_USER = os.getenv('TIDB_USER', 'root')
    TIDB_PASSWORD = os.getenv('TIDB_PASSWORD', '')
    TIDB_DB = os.getenv('TIDB_DB', 'db_laundry')
    TIDB_SSL_CA = os.getenv('TIDB_SSL_CA', None)
    SQLALCHEMY_ECHO = env_flag('SQLALCHEMY_ECHO')

    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    if TESTING:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    elif USE_SQLITE_FALLBACK:
        SQLALCHEMY_DATABASE_URI = get_sqlite_uri()
    elif FLASK_ENV == 'production' and not SQLALCHEMY_DATABASE_URI.startswith('mysql'):
        raise RuntimeError('Production database must use TiDB/MySQL or a DATABASE_URL value.')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = get_engine_options(SQLALCHEMY_DATABASE_URI)
    
    # Upload Files
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'app/static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    
    # Resend (Email)
    RESEND_API_KEY = os.getenv('RESEND_API_KEY')
    RESEND_FROM_EMAIL = os.getenv('RESEND_FROM_EMAIL')
    CONTACT_RECIPIENT_EMAIL = os.getenv('CONTACT_RECIPIENT_EMAIL')
    
    # Admin Credentials
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin')
    
    # Pagination
    ITEMS_PER_PAGE = 20
    
    # Application
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = DEBUG


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Only send cookie over HTTPS


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
