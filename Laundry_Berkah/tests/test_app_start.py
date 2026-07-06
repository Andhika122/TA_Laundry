import importlib
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


def test_development_uses_local_sqlite_by_default(monkeypatch):
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

    assert app_config.SQLALCHEMY_DATABASE_URI.startswith("sqlite:///")
    assert app_config.SQLALCHEMY_DATABASE_URI.endswith("/instance/laundry.db")


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


def test_login_page_is_accessible(client):
    response = client.get("/auth/login")

    assert response.status_code == 200
    assert b"login" in response.data.lower() or b"username" in response.data.lower()


def test_dashboard_redirects_when_not_logged_in(client):
    response = client.get("/dashboard/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/auth/login")
