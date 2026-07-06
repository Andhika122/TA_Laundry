"""
Application Factory
Initialize Flask app, database, and blueprints
"""
from flask import Flask
from sqlalchemy import inspect, text
import logging
from logging.handlers import RotatingFileHandler
import os

from app.extensions import db


def create_app(config_name='development'):
    """
    Application Factory - Create and configure Flask app
    
    Args:
        config_name: 'development', 'production', or 'testing'
    
    Returns:
        Flask application instance
    """
    from config import config, get_database_uri, get_engine_options
    
    app = Flask(__name__)
    config_name = config_name if config_name in config else 'default'
    app.config.from_object(config[config_name])
    is_testing = (
        config_name == 'testing'
        or app.config.get('TESTING', False)
        or os.getenv('FLASK_ENV', 'development').lower() == 'testing'
        or os.getenv('TESTING', 'false').lower() in {'1', 'true', 'yes', 'on'}
    )
    database_uri = 'sqlite:///:memory:' if is_testing else get_database_uri()
    app.config.update({
        'TESTING': is_testing,
        'USE_SQLITE_FALLBACK': os.getenv('USE_SQLITE_FALLBACK', 'false').lower() in {'1', 'true', 'yes', 'on'},
        'SQLALCHEMY_DATABASE_URI': database_uri,
        'SQLALCHEMY_ENGINE_OPTIONS': {} if is_testing else get_engine_options(database_uri),
    })

    # Bind the shared SQLAlchemy extension to this app.
    db.init_app(app)

    # Ensure Jinja templates can use Python builtins for pagination
    app.jinja_env.globals.update({
        'max': max,
        'min': min,
    })
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(app)

    register_root_route(app)
    
    # Setup logging
    setup_logging(app)
    
    # Create database tables when possible; fall back gracefully if the DB is unavailable.
    with app.app_context():
        try:
            db.create_all()
            ensure_database_schema(app)
            seed_default_data(app)
        except Exception as exc:
            app.logger.warning('Database initialization skipped: %s', exc)
    
    # Create CLI commands
    register_cli_commands(app)
    
    return app


def register_root_route(app):
    """Register the application home route."""

    @app.route('/')
    def index():
        from flask import redirect, session, url_for

        if 'user_id' in session:
            if session.get('role') == 'Kasir':
                return redirect(url_for('transaksi.index'))
            return redirect(url_for('dashboard.dashboard'))
        return redirect(url_for('auth.login'))


def ensure_database_schema(app):
    """Migrate existing SQLite schema to support newer columns."""
    try:
        inspector = inspect(db.engine)
        if inspector.dialect.name != 'sqlite':
            return

        if 'app_pembayaran' not in inspector.get_table_names():
            return

        columns = {column['name'] for column in inspector.get_columns('app_pembayaran')}
        needs_rebuild = 'metode' in columns or 'keterangan' in columns or 'metode_pembayaran' not in columns or 'catatan' not in columns

        if needs_rebuild:
            db.session.execute(text("DROP TABLE IF EXISTS app_pembayaran"))
            db.session.commit()
            db.create_all()
            return

        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        app.logger.warning('Schema migration skipped: %s', exc)


def seed_default_data(app):
    """Seed minimal data required for the app to be usable."""
    from app.models.role import Role
    from app.models.user import User
    from app.models.layanan import Layanan
    from app.models.parfum import Parfum
    from app.models.promo import Promo

    roles = [
        ('Admin', 'Administrator'),
        ('Kasir', 'Kasir'),
        ('Operator', 'Operator Laundry'),
    ]
    for nama, deskripsi in roles:
        if not Role.query.filter_by(nama=nama).first():
            db.session.add(Role(nama=nama, deskripsi=deskripsi))
    db.session.commit()

    admin_role = Role.query.filter_by(nama='Admin').first()
    admin_username = app.config.get('ADMIN_USERNAME', 'admin')
    admin_password = app.config.get('ADMIN_PASSWORD', 'admin')
    admin_email = app.config.get('ADMIN_EMAIL', 'admin@laundry.com')
    if admin_role and not User.query.filter_by(username=admin_username).first():
        admin_user = User(
            username=admin_username,
            email=admin_email,
            nama_lengkap='Administrator',
            id_role=admin_role.id_role,
            status=True,
        )
        admin_user.set_password(admin_password)
        db.session.add(admin_user)

    kasir_role = Role.query.filter_by(nama='Kasir').first()
    kasir_username = 'kasir'
    kasir_password = 'kasir'
    kasir_email = 'kasir@laundry.com'
    if kasir_role and not User.query.filter_by(username=kasir_username).first():
        kasir_user = User(
            username=kasir_username,
            email=kasir_email,
            nama_lengkap='Kasir',
            id_role=kasir_role.id_role,
            status=True,
        )
        kasir_user.set_password(kasir_password)
        db.session.add(kasir_user)

    layanan_defaults = [
        ('Cuci Kering Reguler', 7000, 2, 'hari', 'Cuci', 'Cuci dan kering reguler per kg'),
        ('Cuci Setrika Reguler', 9000, 2, 'hari', 'Cuci Setrika', 'Cuci, kering, dan setrika per kg'),
        ('Setrika Saja', 5000, 1, 'hari', 'Setrika', 'Setrika pakaian per kg'),
        ('Express 6 Jam', 15000, 6, 'jam', 'Express', 'Layanan cepat selesai 6 jam per kg'),
    ]
    for nama, harga, durasi, durasi_unit, kategori, deskripsi in layanan_defaults:
        if not Layanan.query.filter_by(nama=nama).first():
            db.session.add(Layanan(
                nama=nama,
                harga=harga,
                durasi=durasi,
                durasi_unit=durasi_unit,
                kategori=kategori,
                deskripsi=deskripsi,
                is_active=True,
            ))

    parfum_defaults = [
        ('Lavender', 'Aroma lavender lembut', 0),
        ('Ocean Fresh', 'Aroma segar tahan lama', 0),
        ('Baby Soft', 'Aroma lembut untuk pakaian keluarga', 0),
    ]
    for nama, deskripsi, harga_tambahan in parfum_defaults:
        if not Parfum.query.filter_by(nama=nama).first():
            db.session.add(Parfum(
                nama=nama,
                deskripsi=deskripsi,
                harga_tambahan=harga_tambahan,
                is_active=True,
            ))

    if not Promo.query.filter_by(nama='Member Baru').first():
        db.session.add(Promo(
            nama='Member Baru',
            deskripsi='Diskon 10% untuk pelanggan baru',
            tipe='persentase',
            nilai=10,
            minimal_transaksi=30000,
            is_active=True,
        ))

    db.session.commit()


def register_blueprints(app):
    """Register all blueprints"""
    from app.auth.routes import auth_bp
    from app.dashboard.routes import dashboard_bp
    from app.pelanggan.routes import pelanggan_bp
    from app.transaksi.routes import transaksi_bp
    from app.pembayaran.routes import pembayaran_bp
    from app.laundry.routes import laundry_bp
    from app.layanan.routes import layanan_bp
    from app.laporan.routes import laporan_bp
    from app.akun.routes import akun_bp
    from app.api.routes import api_bp
    
    # Auth blueprint (no URL prefix for login/logout)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Admin/Dashboard blueprints
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(pelanggan_bp, url_prefix='/pelanggan')
    app.register_blueprint(transaksi_bp, url_prefix='/transaksi')
    app.register_blueprint(pembayaran_bp, url_prefix='/pembayaran')
    app.register_blueprint(laundry_bp, url_prefix='/laundry')
    app.register_blueprint(layanan_bp, url_prefix='/layanan')
    app.register_blueprint(laporan_bp, url_prefix='/laporan')
    app.register_blueprint(akun_bp, url_prefix='/akun')
    
    # API blueprint
    app.register_blueprint(api_bp, url_prefix='/api')
    
    print("[OK] All blueprints registered successfully")


def register_error_handlers(app):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not Found', 'message': 'Resource not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal Server Error', 'message': 'An error occurred'}, 500
    
    @app.errorhandler(403)
    def forbidden(error):
        return {'error': 'Forbidden', 'message': 'Access denied'}, 403
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {'error': 'Unauthorized', 'message': 'Authentication required'}, 401


def setup_logging(app):
    """Setup application logging"""
    if not app.debug:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Create rotating file handler
        file_handler = RotatingFileHandler(
            'logs/laundry_berkah.log',
            maxBytes=10240000,
            backupCount=10
        )
        
        # Set logging format
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        # Set logging level
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Laundry Berkah startup')


def register_cli_commands(app):
    """Register Flask CLI commands"""
    import click

    @app.cli.command()
    def init_db():
        """Initialize database tables and seed defaults."""
        with app.app_context():
            db.create_all()
            ensure_database_schema(app)
            seed_default_data(app)
        click.echo('[OK] Database initialized')

    @app.cli.command()
    def seed_db():
        """Seed default roles, users, services, and promos."""
        with app.app_context():
            seed_default_data(app)
        click.echo('[OK] Database seeded with sample data')

    @app.cli.command()
    def drop_db():
        """Drop all database tables"""
        if click.confirm('Are you sure you want to drop all tables?'):
            db.drop_all()
            click.echo('[OK] All tables dropped')