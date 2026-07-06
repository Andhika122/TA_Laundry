import os
import sys
import pytest

os.environ.setdefault('FLASK_ENV', 'testing')
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(ROOT_DIR, 'Laundry_Berkah')
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import app as app_module


@pytest.fixture()
def app():
    application = app_module.create_app('testing')
    with application.app_context():
        from app import db

        db.drop_all()
        db.create_all()

    yield application

    with application.app_context():
        from app import db

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
