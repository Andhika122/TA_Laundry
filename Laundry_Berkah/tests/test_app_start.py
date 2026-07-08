import importlib
import os
import pytest


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("TIDB_HOST", "127.0.0.1")
    monkeypatch.setenv("TIDB_PORT", "1")
    monkeypatch.setenv("TIDB_USER", "root")
    monkeypatch.setenv("TIDB_PASSWORD", "")
    monkeypatch.setenv("TIDB_DB", "test_db")

    import app as app_module
    app_module = importlib.reload(app_module)
    test_app = app_module.create_app("testing")
    test_app.config.update(TESTING=True)
    return test_app


def test_development_uses_tidb_by_default(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("TIDB_HOST", "127.0.0.1")
    monkeypatch.setenv("TIDB_PORT", "4000")
    monkeypatch.setenv("TIDB_USER", "root")
    monkeypatch.setenv("TIDB_PASSWORD", "")
    monkeypatch.setenv("TIDB_DB", "test_db")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import config as config_module
    config_module = importlib.reload(config_module)

    app_config = config_module.config["development"]

    assert app_config.SQLALCHEMY_DATABASE_URI.startswith("mysql+pymysql://")
    assert "sqlite" not in app_config.SQLALCHEMY_DATABASE_URI


def test_production_uses_tidb_mysql_by_default(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("TIDB_HOST", "127.0.0.1")
    monkeypatch.setenv("TIDB_PORT", "4000")
    monkeypatch.setenv("TIDB_USER", "root")
    monkeypatch.setenv("TIDB_PASSWORD", "")
    monkeypatch.setenv("TIDB_DB", "test_db")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("USE_SQLITE_FALLBACK", raising=False)

    import config as config_module
    config_module = importlib.reload(config_module)

    app_config = config_module.config["production"]

    assert app_config.SQLALCHEMY_DATABASE_URI.startswith("mysql+pymysql://")


def test_sqlite_fallback_uses_local_file(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("USE_SQLITE_FALLBACK", "1")
    monkeypatch.setenv("TIDB_HOST", "127.0.0.1")
    monkeypatch.setenv("TIDB_PORT", "4000")
    monkeypatch.setenv("TIDB_USER", "root")
    monkeypatch.setenv("TIDB_PASSWORD", "")
    monkeypatch.setenv("TIDB_DB", "test_db")

    import config as config_module
    config_module = importlib.reload(config_module)

    app_config = config_module.config["development"]

    assert app_config.SQLALCHEMY_DATABASE_URI.startswith("sqlite:///")
    assert app_config.SQLALCHEMY_DATABASE_URI.endswith("/instance/laundry.db")


def test_vercel_production_uses_tidb_when_configured(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("USE_SQLITE_FALLBACK", raising=False)
    monkeypatch.setenv("TIDB_HOST", "127.0.0.1")
    monkeypatch.setenv("TIDB_PORT", "4000")
    monkeypatch.setenv("TIDB_USER", "root")
    monkeypatch.setenv("TIDB_PASSWORD", "")
    monkeypatch.setenv("TIDB_DB", "test_db")

    import config as config_module
    config_module = importlib.reload(config_module)

    app_config = config_module.config["production"]

    assert app_config.SQLALCHEMY_DATABASE_URI.startswith("mysql+pymysql://")


def test_ssl_ca_path_resolves_from_project_root(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("USE_SQLITE_FALLBACK", raising=False)
    monkeypatch.setenv("TIDB_HOST", "127.0.0.1")
    monkeypatch.setenv("TIDB_PORT", "4000")
    monkeypatch.setenv("TIDB_USER", "root")
    monkeypatch.setenv("TIDB_PASSWORD", "")
    monkeypatch.setenv("TIDB_DB", "test_db")
    monkeypatch.setenv("TIDB_SSL_CA", "CA.pem")

    import config as config_module
    config_module = importlib.reload(config_module)

    options = config_module.get_engine_options("mysql+pymysql://root:@127.0.0.1:4000/test_db")

    assert "connect_args" in options
    assert os.path.exists(options["connect_args"]["ssl_ca"])


def test_login_page_is_accessible(client):
    response = client.get("/auth/login")

    assert response.status_code == 200
    assert b"login" in response.data.lower() or b"username" in response.data.lower()


def test_dashboard_redirects_when_not_logged_in(client):
    response = client.get("/dashboard/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")
